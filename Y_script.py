from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi

app = FastAPI()

class VideoURL(BaseModel):
    video_url: str

def get_video_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = ''
        
        for caption in transcript_list:
            if 'text' in caption:
                transcript_text += ' ' + caption['text']
        
        return transcript_text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get('/get_transcript/{video_url}')
async def fetch_transcript(video_url: str):
    transcript = get_video_transcript(video_url)
    
    if transcript:
        return {"transcript": transcript}
    else:
        raise HTTPException(status_code=404, detail="Failed to fetch transcript. Please check the provided video URL.")
