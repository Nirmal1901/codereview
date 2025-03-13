from fastapi import FastAPI, Request, HTTPException
import httpx
import os
from github import Github

app = FastAPI()

# GitHub and Groq API configurations
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize GitHub client
github_client = Github(GITHUB_ACCESS_TOKEN)

@app.post("/webhook")
async def webhook(request: Request):
    event = request.headers.get("X-GitHub-Event")
    if event != "push":
        return {"message": "Not a push event"}

    payload = await request.json()
    repo_name = payload["repository"]["full_name"]
    commits = payload["commits"]

    # Fetch the repository
    repo = github_client.get_repo(repo_name)

    for commit in commits:
        commit_sha = commit["id"]
        commit_message = commit["message"]
        modified_files = commit["modified"]

        for file in modified_files:
            try:
                # Fetch the file content from the default branch (e.g., main)
                file_content = repo.get_contents(file, ref="main").decoded_content.decode("utf-8")

                # Send code to Groq API for review
                review = get_code_review(file_content)

                # Create an issue with the review
                repo.create_issue(
                    title=f"Code Review for {file} in commit {commit_sha[:7]}",
                    body=review,
                    labels=["code-review"]
                )
            except Exception as e:
                print(f"Error processing file {file}: {e}")

    return {"message": "Code review completed and issues created"}

def get_code_review(code: str) -> str:
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "codellama",
        "messages": [
            {"role": "system", "content": "You are a code reviewer. Provide a detailed review of the following code."},
            {"role": "user", "content": code}
        ]
    }

    response = httpx.post(GROQ_API_URL, headers=headers, json=data)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to get code review from Groq API")

    return response.json()["choices"][0]["message"]["content"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)