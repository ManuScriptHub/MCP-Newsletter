from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import List
from curated_newsletter import ExaNewsletter
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

class NewsletterRequest(BaseModel):
    query: str
    emails: List[str]
    num_results: int = 5

@app.post("/generate_and_send_newsletter")
def generate_and_send_newsletter(req: NewsletterRequest, background_tasks: BackgroundTasks):
    newsletter = ExaNewsletter(req.query, req.emails, req.num_results)
    newsletter.search_exa()
    background_tasks.add_task(newsletter.send_newsletter)
    background_tasks.add_task(newsletter.cleanup)
    return {"status": f"Newsletter is being sent to {req.emails}"}

