# YouTube Transcript QA (RAG)

Ask questions about any YouTube video using its transcript. This project uses a simple RAG pipeline (transcript → chunks → embeddings → FAISS retrieval → answer generation) and stores Q&A history in MongoDB.

Origin Code from : [Link](https://github.com/hashemk2/Youtube-Qa-RAG)
## Features
- Fetches YouTube transcripts and answers questions grounded in the content
- FAISS similarity search for retrieval
- Hugging Face Router for generation (configurable)
- MongoDB logging for video URL, question, answer, timestamp
- Minimal frontend for quick testing

## Project Structure
```
YoutubeRAGQA/
	app/
		backend/
			fastApi.py
			model.py
			database.py
		frontend/
			templates/
				index.html
			static/
				style.css
				app.js
	requirements.txt
	.env
```

## Requirements
- Python 3.11+
- MongoDB (Atlas recommended)
- Hugging Face token (for generation)

## Setup
1) Create and activate a virtual environment (Windows PowerShell):
```
cd d:\D\YoutubeRag\YoutubeRAGQA
python -m venv qa
.
\qa\Scripts\Activate.ps1
```

2) Install dependencies:
```
pip install -r requirements.txt
```

3) Create a `.env` file in the project root:
```
MONGO_URI=mongodb+srv://<user>:<pass>@<cluster>/?retryWrites=true&w=majority
MONGO_DB=youtube_rag
MONGO_QA_COLLECTION=queries
HF_TOKEN=hf_xxx
GEN_MODEL_ID=google/flan-t5-base
```

## Run the App
From the project root:
```
python -m uvicorn app.backend.fastApi:app --reload --host 127.0.0.1 --port 8000
```
Open: http://127.0.0.1:8000

## Usage
1) Paste a YouTube URL
2) Ask a question
3) Read the answer (grounded in the transcript)

## Notes
- Some videos do not have transcripts; those will fail.
- Large transcripts can take longer to process.
- Ensure your MongoDB IP allowlist allows your local machine (if using Atlas).

## Troubleshooting
- **403 from HF Router:** your token likely lacks inference permission.
- **Timeouts:** reduce chunk count or try a smaller model.
- **Module not found:** ensure you're using the correct virtual environment.
