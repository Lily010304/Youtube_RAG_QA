document.addEventListener("DOMContentLoaded", function() {
    console.log("DOM fully loaded and parsed");

    const form = document.getElementById('qa_form');
    console.log(form); // Should not be null

    form.addEventListener('submit', async function(event) {
        event.preventDefault();
        console.log("Form submitted");

        const videoUrl = document.getElementById('video_url').value;
        const question = document.getElementById('question').value;
        const answerDiv = document.getElementById('answerr');
        const spinner = document.getElementById('loading-spinner');

        spinner.style.display = "flex";
        answerDiv.innerHTML = "";
        try{
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    video_url: videoUrl,
                    question: question
                })
            });

            if (!response.ok) {
                const errText = await response.text();
                throw new Error(errText || `Request failed (${response.status})`);
            }

            const data = await response.json();
            answerDiv.textContent = data.answer ?? "";

        }catch (error) {
        answerDiv.innerHTML = `<p style="color:red;">Error: ${error.message}</p>`;
        
        } finally {
        spinner.style.display = "none";
    }
    });
});
