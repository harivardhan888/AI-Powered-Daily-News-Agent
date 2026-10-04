from fastapi import FastAPI, BackgroundTasks, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import json
import sys
from dotenv import load_dotenv
from pymongo import MongoClient
import urllib.parse

# Load environments
load_dotenv()

# API Key Configuration
API_KEY = os.getenv("NEWSCRAFT_API_KEY", "default_secret_key_change_me")
API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(header_value: str = Depends(api_key_header)):
    if header_value == API_KEY:
        return header_value
    raise HTTPException(status_code=403, detail="Could not validate API Key")

# Ensure root directory is in path so we can import local modules
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from Preprocessing.preprocessing import fetch_and_process_data
from Mail_SMTP import mail
import app

api = FastAPI(
    title="NewsCraft Controller",
    description="API to control the NewsCraft pipeline",
    version="1.0.0"
)

# Mount the static directory to serve index.html at root
api.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

class SubscribeRequest(BaseModel):
    email: str
    genres: list[str] = []

@api.get("/")
def read_root():
    # Return the UI from the static folder
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))

@api.get("/ping")
def ping():
    """Tiny endpoint to wake up the server without returning a massive HTML file."""
    return {"status": "awake"}

@api.get("/news/raw")
def get_raw_news(api_key: str = Depends(get_api_key)):
    """Fetches news from BBC, CNN, and YouTube without summarizing."""
    try:
        data = fetch_and_process_data()
        return {"count": len(data), "articles": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.get("/news/summaries")
def get_latest_summaries(api_key: str = Depends(get_api_key)):
    """Returns the most recent summarized news from the local JSON file."""
    if os.path.exists("summarized_news.json"):
        with open("summarized_news.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {"message": "No summaries found. Run /pipeline/run first."}

@api.post("/pipeline/run")
def run_full_pipeline(background_tasks: BackgroundTasks, send_email: bool = True, api_key: str = Depends(get_api_key)):
    """
    Triggers the full pipeline: Fetch -> Summarize -> Email.
    It runs in the background so you don't have to wait.
    """
    def task():
        print("Starting background pipeline...")
        # 1. Run the app logic (Fetch & Summarize)
        app.main()
        # 2. Run the mailer if requested
        if send_email:
            mail.main()
            print("Background pipeline complete: News sent!")
    
    background_tasks.add_task(task)
    
    return {
        "status": "started",
        "message": "The news pipeline is running in the background. You'll receive an email shortly if successful."
    }

@api.post("/subscribe")
def subscribe_user(req: SubscribeRequest, background_tasks: BackgroundTasks):
    email = req.email.strip()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email address")

    mongo_uri = os.environ.get("MONGODB_URI")
    if not mongo_uri:
        raise HTTPException(status_code=500, detail="Database not configured")
        
    import certifi
    client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
    db = client.newscraft
    subscribers_col = db.subscribers
    
    # Upsert subscriber
    subscribers_col.update_one(
        {"email": email},
        {"$set": {"genres": req.genres}},
        upsert=True
    )
        
    # Send welcome email in background
    def send_welcome():
        mail.send_welcome_email(email)
        
    background_tasks.add_task(send_welcome)
    
    return {"status": "success", "message": "Subscribed successfully!"}

@api.get("/unsubscribe", response_class=HTMLResponse)
def unsubscribe_user(email: str):
    mongo_uri = os.environ.get("MONGODB_URI")
    if mongo_uri:
        import certifi
        client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
        db = client.newscraft
        db.subscribers.delete_one({"email": email})
            
    return f"""
    <html>
        <head>
            <title>NewsCraft - Unsubscribed</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
                body {{
                    font-family: 'Inter', sans-serif;
                    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    text-align: center;
                }}
                .container {{
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    padding: 40px;
                    border-radius: 15px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                    max-width: 400px;
                    width: 90%;
                }}
                h2 {{
                    color: #e74c3c;
                    margin-top: 0;
                }}
                p {{
                    color: rgba(255, 255, 255, 0.8);
                    line-height: 1.6;
                    margin-bottom: 30px;
                }}
                a.btn {{
                    display: inline-block;
                    background: linear-gradient(45deg, #00b4db, #0083b0);
                    color: white;
                    text-decoration: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-weight: 600;
                    transition: transform 0.2s, box-shadow 0.2s;
                }}
                a.btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 15px rgba(0, 180, 219, 0.4);
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Successfully Unsubscribed</h2>
                <p><b>{email}</b> has been removed from our mailing list.</p>
                <p>We're sorry to see you go! You will no longer receive daily news summaries from NewsCraft.</p>
                <a href="/?email={email}" class="btn">Subscribe again</a>
            </div>
        </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="127.0.0.1", port=8000)
