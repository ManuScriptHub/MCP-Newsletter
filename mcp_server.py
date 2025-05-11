from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from curated_newsletter import CuratedNewsletter
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

class NewsletterRequest(BaseModel):
    email: str
    websites: Optional[dict] = None  # Dict of {site_name: rss_url}

@app.post("/generate_and_send_newsletter")
def generate_and_send_newsletter(req: NewsletterRequest, background_tasks: BackgroundTasks):
    # Use default feeds if none provided
    default_feeds = {
        'techcrunch': 'https://techcrunch.com/feed/',
        'mashable': 'https://mashable.com/feed/',
        'cnet': 'https://www.cnet.com/rss/all/'
    }
    # If user provides feeds, use only those; otherwise, use default feeds
    if req.websites and len(req.websites) > 0:
        feeds = req.websites.copy()
    else:
        feeds = default_feeds.copy()

    newsletter = CuratedNewsletter(rss_feeds=feeds, recipient_email=req.email)
    newsletter.scrape_all_feeds()
    background_tasks.add_task(newsletter.send_newsletter)
    return {"status": f"Newsletter is being sent to {req.email}"}
