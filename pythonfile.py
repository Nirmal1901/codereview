
from fastapi import FastAPI, HTTPException from pydantic import BaseModel import requests import httpx from langchain.prompts import PromptTemplate import base64
 
app = FastAPI()
 
# Step 2: Define base URL for Groq API groq_api_url = "https://api.groq.com/openai/v1/chat/completions" groq_api_key = "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"  # Replace with your API key
 
class RepoRequest(BaseModel):     access_token: str     repo_url: str
 
def run_groq(prompt, model="llama3-8b-8192"):     headers = {         "Authorization": f"Bearer {groq_api_key}",         "Content-Type": "application/json"     }     payload = {         "model": model,         "messages": [{"role": "user", "content": prompt}]     }     response = requests.post(groq_api_url, json=payload, headers=headers)     response.raise_for_status()     return response.json()["choices"][0]["message"]["content"]
