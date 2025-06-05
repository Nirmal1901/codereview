

from fastapi import FastAPI, HTTPException, Request, Depends, File, UploadFile
from pydantic import BaseModel
import httpx
import logging
import hmac
import hashlib
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import ast
import javalang
from typing import List, Dict
import re
from crewai import Agent, Task, Crew, LLM
from urllib.parse import urlparse

app = FastAPI()

webhook_configs = {}

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_webhook_signature(request: Request, body: bytes, repo_url: str):
    """
    Verify the GitHub webhook signature to ensure the request is authentic.
    """
    if repo_url not in webhook_configs:
        logger.error(f"Repo URL {repo_url} not found in webhook configurations")
        raise HTTPException(status_code=403, detail="Repository not configured")
    
    config = webhook_configs[repo_url]
    signature = request.headers.get("X-Hub-Signature-256", "")
    logger.info(f"Received signature: {signature}")
    
    if not signature:
        logger.error("Missing signature")
        raise HTTPException(status_code=403, detail="Missing signature")
    
    secret = config['webhook_secret'].encode()
    hmac_gen = hmac.new(secret, body, hashlib.sha256)
    expected_signature = "sha256=" + hmac_gen.hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        logger.error("Invalid signature")
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    logger.info("Signature verification successful")

async def fetch_file_content(repo_url: str, file_path: str, access_token: str, branch: str = "main") -> str:
    """
    Fetch the content of a file from GitHub.
    """
    # Parse the repo URL to get owner and repo name
    parsed_url = urlparse(repo_url)
    path_parts = parsed_url.path.strip('/').split('/')
    if len(path_parts) < 2:
        raise HTTPException(status_code=400, detail="Invalid GitHub repository URL")
    
    owner, repo = path_parts[0], path_parts[1]
    file_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3.raw"
    }
    
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(file_url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            logger.error(f"Failed to fetch file content: {file_path}. Status code: {response.status_code}")
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch file content.")

def split_python_code(file_content: str) -> List[Dict]:
    chunks = []
    
    try:
        # Parse the code into an AST
        tree = ast.parse(file_content)
        
        # Capture imports
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        if imports:
            import_code = "\n".join(ast.unparse(imp) for imp in imports)
            chunks.append({
                "type": "imports",
                "name": "imports",
                "code": import_code
            })
        
        # Capture classes, functions, and async functions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Capture the entire class, including methods and nested functions
                class_code = ast.unparse(node)
                chunks.append({
                    "type": "class",
                    "name": node.name,
                    "code": class_code
                })
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Capture the function, including its decorators
                decorators = [ast.unparse(dec) for dec in node.decorator_list]
                function_code = ast.unparse(node)
                if decorators:
                    function_code = "\n".join(decorators) + "\n" + function_code
                
                # Check if the function is part of a class
                parent_class = None
                for parent in ast.walk(tree):
                    if isinstance(parent, ast.ClassDef) and node in parent.body:
                        parent_class = parent.name
                        break
                
                if parent_class:
                    # Add the function under its class
                    for chunk in chunks:
                        if chunk["type"] == "class" and chunk["name"] == parent_class:
                            if "methods" not in chunk:
                                chunk["methods"] = []
                            chunk["methods"].append({
                                "type": "method",
                                "name": node.name,
                                "code": function_code
                            })
                            break
                else:
                    # Add as a standalone function
                    chunks.append({
                        "type": "function",
                        "name": node.name,
                        "code": function_code
                    })
        
        # Capture global variables and standalone code
        global_code = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and not any(isinstance(parent, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) for parent in ast.walk(tree)):
                global_code.append(ast.unparse(node))
        
        if global_code:
            chunks.append({
                "type": "global_code",
                "name": "global_code",
                "code": "\n".join(global_code)
            })
    
    except SyntaxError:
        # Fallback: Split the code into logical blocks
        chunks.append({
            "type": "code_block",
            "name": "full_code",
            "code": file_content
        })
    
    return chunks

def split_java_code(file_content: str) -> List[Dict]:
    chunks = []
    lines = file_content.splitlines()
    
    try:
        # Parse the Java code
        tree = javalang.parse.parse(file_content)
        
        # Capture package and imports first
        package = getattr(tree, 'package', None)
        if package:
            package_code = f"package {package.name};"
            chunks.append({
                "type": "package",
                "name": "package",
                "code": package_code
            })
        
        imports = getattr(tree, 'imports', [])
        if imports:
            import_code = "\n".join(f"import {imp.path};" for imp in imports)
            chunks.append({
                "type": "imports",
                "name": "imports",
                "code": import_code
            })
        
        # Process class declarations
        for type_decl in tree.types:
            if isinstance(type_decl, javalang.tree.ClassDeclaration):
                class_start = type_decl.position.line - 1
                class_end = find_closing_brace(lines, class_start)
                
                class_code = "\n".join(lines[class_start:class_end+1])
                methods = []
                
                # Process methods
                for method in type_decl.methods:
                    method_start = method.position.line - 1
                    method_end = find_closing_brace(lines, method_start)
                    
                    method_code = "\n".join(lines[method_start:method_end+1])
                    methods.append({
                        "type": "method",
                        "name": method.name,
                        "code": method_code
                    })
                
                chunks.append({
                    "type": "class",
                    "name": type_decl.name,
                    "code": class_code,
                    "methods": methods
                })
                
    except javalang.parser.javaSyntaxError as e:
        logger.error(f"Java parsing error: {e}")
        # Fallback to simple splitting
        chunks.append({
            "type": "code_block",
            "name": "full_code",
            "code": file_content
        })
    
    return chunks

def find_closing_brace(lines: List[str], start_line: int) -> int:
    """
    Find the closing brace for a code block starting at start_line.
    """
    brace_count = 0
    for i in range(start_line, len(lines)):
        line = lines[i]
        brace_count += line.count('{') - line.count('}')
        if brace_count <= 0:
            return i
    return len(lines) - 1

llm = LLM(model="ollama/codellama", base_url="http://127.0.0.1:11434/api/generate")

high_level_review_agent = Agent(
    role="Code Review Expert",
    goal="Perform a concise high-level review of the entire codebase, highlighting only critical issues.",
    backstory="You are an experienced software engineer with expertise in code reviews.",
    tools=[],
    verbose=True,
    llm=llm  
)

detailed_review_agent = Agent(
    role="Code Enhancement Expert",
    goal="Quickly identify and highlight code issues with specific, actionable suggestions.",
    backstory="You are a code optimization specialist with a focus on improving code quality.",
    tools=[],
    verbose=True,
    llm=llm  
)

async def review_code_chunks(language: str, chunks: List[Dict]) -> List[Dict]:
    """
    Review each code chunk using CrewAI agents.
    """
    reviewed_chunks = []
    for chunk in chunks:
        try:
            # Create a review task for this chunk
            review_task = Task(
                description=f"""
                STRICTLY review this {language} {chunk['type']}:
                {chunk['code']}
                
                Respond ONLY in this format:
                1. [STATUS] Good/Needs Fix
                2. [ISSUES] (if any):
                   - Type: [BUG/PERF/READ]
                   - Where: line X
                   - Severity: [H/M/L]
                   - Fix: (1 line)
                   ```{language}
                   [CORRECTED CODE] (if needed)
                   ```
                3. [SUMMARY] (1 line)
                """,
                agent=detailed_review_agent,
                expected_output=f"Strictly formatted review of {chunk['type']} {chunk['name']}"
            )
            
            crew = Crew(
                agents=[detailed_review_agent],
                tasks=[review_task],
                verbose=True
            )
            review_output = crew.kickoff()
            
            reviewed_chunks.append({
                "type": chunk["type"],
                "name": chunk["name"],
                "code": chunk["code"],
                "review": review_output
            })
        except Exception as e:
            logger.error(f"Error reviewing chunk {chunk['name']}: {e}")
            reviewed_chunks.append({
                "type": chunk["type"],
                "name": chunk["name"],
                "code": chunk["code"],
                "review": f"Error: {str(e)}"
            })
    return reviewed_chunks

async def review_repo_code(repo_url: str, commit_hash: str, commit_author: str, files_to_review: list):
    try:
        if repo_url not in webhook_configs:
            raise HTTPException(status_code=400, detail="Repository not configured")
            
        config = webhook_configs[repo_url]
        logger.info(f"Starting code review for repository: {repo_url}")
        review_summaries = []
        issue_body = ""  # Initialize as empty string

        for file_name in files_to_review:
            logger.info(f"Checking file: {file_name}")
            if file_name.endswith((".py", ".java")):  
                logger.info(f"File {file_name} matches the allowed extensions (.py or .java)")
                
                file_path = file_name
                try:
                    file_content = await fetch_file_content(repo_url, file_path, config['access_token'])
                    logger.info(f"File content fetched successfully: {file_name}")
                    
                    # Initialize issue_body here only when we find a file to review
                    if not issue_body:
                        issue_body = f"**Commit:** {commit_hash[:8]}\n**Author:** {commit_author}\n\n"
                    
                    language = "python" if file_name.endswith(".py") else "java"
                    
                    if language == "python":
                        chunks = split_python_code(file_content)
                    else:
                        chunks = split_java_code(file_content)
                    
                    # High-level review
                    high_level_review_task = Task(
                        description=f"""
                        STRICTLY analyze this {language} code and respond ONLY in this format:
                        {file_content}
                        
                        ---
                        1. [OVERVIEW] (1 sentence)
                        2. [CRITICAL] (ONLY if issues exist)
                           - [ISSUE] Description (severity: HIGH/MEDIUM)
                           - [FIX] Brief suggestion
                        3. [VERDICT] ✅ Good/⚠️ Needs Attention
                        """,
                        agent=high_level_review_agent,
                        expected_output="Concise high-level review following exact format"
                    )
                    
                    detailed_reviews = []
                    for chunk in chunks:
                        # Main chunk review
                        detailed_review_task = Task(
                            description=f"""
                            STRICTLY review this {language} {chunk['type']}:
                            {chunk['code']}
                            
                            Respond ONLY in this format:
                            1. [STATUS] Good/Needs Fix
                            2. [ISSUES] (if any):
                               - Type: [BUG/PERF/READ]
                               - Where: line X
                               - Severity: [H/M/L]
                               - Fix: (1 line)
                               ```{language}
                               [CORRECTED CODE] (if needed)
                               ```
                            3. [SUMMARY] (1 line)
                            """,
                            agent=detailed_review_agent,
                            expected_output=f"Strictly formatted review of {chunk['type']} {chunk['name']}"
                        )
                        
                        crew = Crew(
                            agents=[detailed_review_agent],
                            tasks=[detailed_review_task],
                            verbose=True
                        )
                        chunk_review = crew.kickoff()

                        # Method reviews (if any)
                        method_reviews = []
                        if chunk.get('methods'):
                            for method in chunk['methods']:
                                method_review_task = Task(
                                    description=f"""
                                    STRICTLY review this {language} method {method['name']}:
                                    {method['code']}
                                    
                                    Same format as above.
                                    """,
                                    agent=detailed_review_agent,
                                    expected_output=f"Review of method {method['name']}"
                                )
                                
                                crew = Crew(
                                    agents=[detailed_review_agent],
                                    tasks=[method_review_task],
                                    verbose=True
                                )
                                method_review = crew.kickoff()
                                method_reviews.append({
                                    "method": method['name'],
                                    "review": method_review
                                })
                        
                        detailed_reviews.append({
                            "type": chunk["type"],
                            "name": chunk["name"],
                            "code": chunk["code"],
                            "review": chunk_review,
                            "method_reviews": method_reviews if method_reviews else None
                        })
                    
                    # Run high-level review
                    crew = Crew(
                        agents=[high_level_review_agent],
                        tasks=[high_level_review_task],
                        verbose=True
                    )
                    high_level_review_result = crew.kickoff()
                    
                    # Add to issue body
                    issue_body += f"## File: {file_name}\n\n"
                    issue_body += f"**High-Level Review:**\n\n{high_level_review_result}\n\n**Detailed Reviews:**\n\n"
                    
                    for review in detailed_reviews:
                        issue_body += f"**{review['type']}: {review['name']}**\n\n{review['review']}\n\n"
                        if review.get('method_reviews'):
                            issue_body += "**Methods:**\n\n"
                            for method in review['method_reviews']:
                                issue_body += f"▸ {method['method']}:\n{method['review']}\n\n"
                    
                    issue_body += "\n---\n\n"
                    review_summaries.append({"file": file_name, "review": issue_body})
                    
                except Exception as e:
                    logger.error(f"Failed to process file: {file_name}. Error: {e}")
                    review_summaries.append({
                        "file": file_name,
                        "error": str(e)
                    })
            else:
                logger.info(f"File {file_name} does not match the allowed extensions (.py or .java)")
        
        # Only create issue if we actually reviewed files
        if issue_body:  # Now this will only be true if we found Python/Java files
            issue_title = f"Code Review: {commit_author} - {commit_hash[:8]}"
            await create_github_issue(repo_url, config['access_token'], issue_title, issue_body)
        
        logger.info(f"Code review completed for {len(review_summaries)} files")
        return {"reviews": review_summaries}
    except Exception as e:
        logger.error(f"Review Repo Code Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def create_github_issue(repo_url: str, access_token: str, title: str, body: str):
    """
    Create a GitHub issue in the specified repository.
    """
    try:
        # Parse the repo URL to get owner and repo name
        parsed_url = urlparse(repo_url)
        path_parts = parsed_url.path.strip('/').split('/')
        if len(path_parts) < 2:
            raise HTTPException(status_code=400, detail="Invalid GitHub repository URL")
        
        owner, repo = path_parts[0], path_parts[1]
        issues_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        payload = {"title": title, "body": body}

        logger.info(f"Creating issue in repository: {owner}/{repo}")
        logger.info(f"Issue title: {title}")
        logger.info(f"Issue body: {body}")

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(issues_url, headers=headers, json=payload)
            if response.status_code != 201:
                logger.error(f"Create Issue Error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail="Failed to create GitHub issue.")
            logger.info(f"Issue created successfully: {response.json()}")
            return response.json()
    except Exception as e:
        logger.error(f"Create Issue Error: {e}")
        raise HTTPException(status_code=500, detail=f"Create Issue Error: {e}")

class WebhookConfig(BaseModel):
    repo_url: str  # GitHub repository URL (e.g., https://github.com/owner/repo)
    access_token: str
    webhook_secret: str
    webhook_url: str = "https://51cd-2401-4900-1c1b-e9bf-7ce9-50d6-d34c-407e.ngrok-free.app/webhook/"

@app.post("/webhook/")
async def github_webhook(request: Request):
    """
    Handle GitHub webhook events.
    """
    body = await request.body()
    logger.info(f"Received webhook payload: {body.decode()}")
    
    # First parse the JSON to get the repository URL for verification
    try:
        payload = await request.json()
        repo_url = payload.get("repository", {}).get("html_url", "")
        if not repo_url:
            raise HTTPException(status_code=400, detail="Repository URL not found in payload")
        
        verify_webhook_signature(request, body, repo_url)
    except Exception as e:
        logger.error(f"Error verifying webhook: {e}")
        raise
    
    event = request.headers.get("X-GitHub-Event", "")
    logger.info(f"Received event: {event}")
    
    if event == "push":
        commits = payload.get("commits", [])
        if commits:
            # Process each commit separately
            for commit in commits:
                commit_hash = commit.get("id", "")
                commit_author = commit.get("author", {}).get("name", "Unknown Author")
                if not commit_hash:
                    continue
                
                added_files = commit.get("added", [])
                modified_files = commit.get("modified", [])
                files_to_review = added_files + modified_files
                
                if files_to_review:
                    logger.info(f"Processing commit {commit_hash[:8]} by {commit_author} with {len(files_to_review)} files to review")
                    await review_repo_code(repo_url, commit_hash, commit_author, files_to_review)
                else:
                    logger.info(f"No files to review in commit {commit_hash[:8]} by {commit_author}")
            
            return {"status": "Review process started for all commits"}
        else:
            logger.info("No commits found in the payload")
            return {"status": "No commits to review"}
    
    return {"status": "Event ignored"}     

@app.post("/setup-webhook/")
async def setup_webhook(config: WebhookConfig):
    """
    Set up a webhook for the specified GitHub repository using the repository URL.
    """
    try:
        repo_url = config.repo_url
        
        # Parse the repo URL to get owner and repo name
        parsed_url = urlparse(repo_url)
        path_parts = parsed_url.path.strip('/').split('/')
        if len(path_parts) < 2:
            raise HTTPException(status_code=400, detail="Invalid GitHub repository URL")
        
        owner, repo = path_parts[0], path_parts[1]
        
        webhook_configs[repo_url] = {
            'access_token': config.access_token,
            'webhook_secret': config.webhook_secret,
            'webhook_url': config.webhook_url
        }
        
        webhook_url = f"https://api.github.com/repos/{owner}/{repo}/hooks"
        headers = {
            "Authorization": f"token {config.access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        payload = {
            "name": "web",
            "active": True,
            "events": ["push"],
            "config": {
                "url": config.webhook_url,
                "content_type": "json",
                "secret": config.webhook_secret,
                "insecure_ssl": "1"  # Accept self-signed certs
            }
        }

        logger.info(f"Setting up webhook for repository: {owner}/{repo}")
        logger.info(f"Webhook URL: {payload['config']['url']}")

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(webhook_url, headers=headers, json=payload)
            if response.status_code != 201:
                logger.error(f"Webhook Setup Error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail="Failed to set up webhook.")
            return response.json()
    except Exception as e:
        logger.error(f"Webhook Setup Error: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook Setup Error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
