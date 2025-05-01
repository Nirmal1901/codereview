from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from fastapi.middleware.cors import CORSMiddleware

# Step 1: Setup FastAPI app
app = FastAPI()



# Step 2: Define base URL for Groq API
groq_api_url = "https://api.groq.com/openai/v1/chat/completions"
groq_api_key = "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"  # Replace with your API key

def run_groq(prompt, model="llama3-8b-8192"):
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(groq_api_url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

# Step 3: Define input models
class CodeConversionInput(BaseModel):
    source_language: str
    target_language: str
    code: str

class CodeReviewInput(BaseModel):
    language: str
    code: str

class CodeExplanationInput(BaseModel):
    language: str
    code: str

# Step 4: Define dynamic prompt templates
def generate_conversion_prompt(source_language, target_language, code):
    return f"""
    You are an expert in converting {source_language} code to {target_language}. Convert the following {source_language} code into clean, efficient {target_language} code.
    
    Ensure the {target_language} code:
    1. Follows best practices.
    2. Is optimized for performance.
    3. Includes clear comments explaining the logic.
    
    {source_language} Code:
    {code}
    """

def generate_review_prompt(language, code):
    return f"""
    You are a {language} code review expert. Analyze the following {language} code for:
    1. Performance and memory optimization.
    2. Readability and structure.
    3. Adherence to best practices.
    4. Potential bugs or improvements.
    5. Error handling and edge cases.
    
    {language} Code:
    {code}
    """

def generate_explanation_prompt(language, code):
    return f"""
    You are a programming expert. Explain the following {language} code in detail, covering:
    1. What the code does.
    2. Key programming concepts used.
    3. Its overall functionality.
    
    {language} Code:
    {code}
    """

# Step 5: Define FastAPI endpoints
@app.post("/convert-code/")
def convert_code(input_data: CodeConversionInput):
    try:
        prompt = generate_conversion_prompt(input_data.source_language, input_data.target_language, input_data.code)
        converted_code = run_groq(prompt)
        return {"converted_code": converted_code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/review-code/")
def review_code(input_data: CodeReviewInput):
    try:
        prompt = generate_review_prompt(input_data.language, input_data.code)
        review_output = run_groq(prompt)
        return {"code_review": review_output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/explain-code/")
def explain_code(input_data: CodeExplanationInput):
    try:
        prompt = generate_explanation_prompt(input_data.language, input_data.code)
        explanation = run_groq(prompt)
        return {"explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
