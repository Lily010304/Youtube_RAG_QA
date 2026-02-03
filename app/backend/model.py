import os
import re
import httpx
import numpy as np
from dotenv import load_dotenv

from urllib.parse import urlparse, parse_qs

from youtube_transcript_api import YouTubeTranscriptApi

from langchain_text_splitters import RecursiveCharacterTextSplitter 

import faiss 

from sentence_transformers import SentenceTransformer

load_dotenv()

HF_API_TOKEN = os.getenv("HF_TOKEN")
# This is a great, lightweight model for creating embeddings.
EMBEDDING_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
# This is a powerful, instruction-following model for generating answers.
GENERATION_MODEL_ID = "moonshotai/Kimi-K2.5"


def _extract_video_id(video_url: str) -> str:
    """Extract a YouTube video id from several common URL formats.

    Supported examples:
    - https://youtu.be/<id>?si=...
    - https://www.youtube.com/watch?v=<id>&...
    - https://www.youtube.com/shorts/<id>
    - https://www.youtube.com/embed/<id>

    Also supports a *bare id* (when user pastes only the id).
    """
    url = (video_url or "").strip()
    if not url:
        raise ValueError("Missing YouTube URL")

    # If user pasted a bare video id (no slashes/query params).
    if "/" not in url and "?" not in url and "&" not in url and len(url) >= 8:
        return url

    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()

    # Short link format: https://youtu.be/<id>
    if "youtu.be" in host:
        video_id = parsed.path.strip("/").split("/")[0]
        if video_id:
            return video_id

    # Standard YouTube host(s): https://www.youtube.com/...
    if "youtube.com" in host or "m.youtube.com" in host:
        # Watch page format: /watch?v=<id>
        if parsed.path.startswith("/watch"):
            qs = parse_qs(parsed.query)
            v = qs.get("v", [""])[0]
            if v:
                return v

        # Shorts format: /shorts/<id>
        if parsed.path.startswith("/shorts/"):
            video_id = parsed.path.split("/shorts/", 1)[1].split("/", 1)[0]
            if video_id:
                return video_id

        # Embed format: /embed/<id>
        if parsed.path.startswith("/embed/"):
            video_id = parsed.path.split("/embed/", 1)[1].split("/", 1)[0]
            if video_id:
                return video_id

    raise ValueError("Invalid YouTube URL")

def _call_hf_api(payload: dict) -> dict:

    api_url = "https://router.huggingface.co/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    with httpx.Client(timeout=120) as client:
            response =  client.post(api_url, headers=headers, json=payload)
    return response.json()


_embedder: SentenceTransformer | None = None
def _get_embedder() -> SentenceTransformer:
    """
    Lazily load (and then reuse) the local SentenceTransformer embedder.
    This avoids re-downloading / re-loading the model every request.
    """
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBEDDING_MODEL_ID)
    return _embedder

def generate_answer(video_url:str, question: str) -> str:

    try:
        # Get transcript using youtube transcript api
        video_id = _extract_video_id(video_url) # get_transcript(video_id)
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id)
        transcript_list = transcript.to_raw_data()
        full_transcript = " ".join([item['text'] for item in transcript_list])

        # 2... Chunk the transcript into smaller pieces
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_text(full_transcript)

        # 3.... Create Embeddings (via hf API)
        emb_payload = {"inputs": chunks}
        embedder = _get_embedder()
        embeddings = embedder.encode(chunks)
        embeddings_np = np.array(embeddings, dtype="float32")
        # 4.... Build FAISS Index
        index = faiss.IndexFlatL2(embeddings_np.shape[1])
        index.add(embeddings_np)

        # 5.... Embed the user's question 
        question_embedding = embedder.encode([question])
        question_embedding_np = np.array(question_embedding, dtype="float32")

        # 6.... find relevant context
        distance, indices = index.search(question_embedding_np, k=3)
        retrieved_chunks = [chunks[i] for i in indices[0]]
        context = "\n\n".join(retrieved_chunks)

        # 7.... Build a prompt
        prompt = f"""You are a helpful assistant that answers questions based ONLY on the provided YouTube video transcript context.
If the answer is not in the context, say "The answer is not available in the provided transcript."

Context from the video:
---
{context}
---

Question: {question}

Answer:"""
        
        
        
        generation_payload= {
            "model": GENERATION_MODEL_ID,
            "messages": [
                {
                    "role": "system",
                    "content": (prompt),
                },
            ],

            "max_tokens": 250,
            "temperature": 0.95,
            "top_p": 0.9,
            "stream": False,
        }

        generation_response = _call_hf_api(generation_payload)
        # The response format is typically a list with one dictionary: [{'generated_text': '...'}]
        final_answer = generation_response['choices'][0]['message']['content']

        # --- 9. Return the Answer ---
        return final_answer.strip()
    except Exception as e:
        # If anything goes wrong in the pipeline, we catch the error and return a helpful message.
        print(f"Error in RAG pipeline: {e}")
        return f"An error occurred while generating the answer: {e}"
