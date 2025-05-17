import os
import tempfile
import uuid
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from dotenv import load_dotenv
import re
from exa_py import Exa

class ExaNewsletter:
    def __init__(self, query, recipient_emails, num_results=5):
        load_dotenv()
        self.query = query
        self.recipient_emails = recipient_emails if isinstance(recipient_emails, list) else [recipient_emails]
        self.num_results = num_results
        self.temp_dir = tempfile.mkdtemp()
        self.items = []

    def search_exa(self):
        exa_api_key = os.getenv('EXA_API_KEY')
        if not exa_api_key:
            raise RuntimeError("EXA_API_KEY not found in environment or .env file")
        exa = Exa(exa_api_key)
        results = exa.search_and_contents(
            self.query,
            type="auto",
            livecrawl="always",
            livecrawl_timeout=5000,
            text={
                "max_characters": 400,
                "include_html_tags": True
            },
            extras={
                "links": 5,
                "image_links": 5
            },
            summary={
                "query": "Summarize the main content of the news article"
            },
            num_results=self.num_results
        )
        for idx, r in enumerate(results.results):
            url = getattr(r, 'url', None)
            title = getattr(r, 'title', url)
            snippet = getattr(r, 'text', '')
            summary = getattr(r, 'summary', None)
            # Strip HTML tags from summary and snippet
            def strip_html(text):
                return re.sub('<[^<]+?>', '', text) if text else ''
            summary = strip_html(summary)
            snippet = strip_html(snippet)
            # Always generate a summary from available content
            if summary and summary.strip():
                lines = summary.split('. ')
                summary_short = '. '.join(lines[:5]) + ('.' if not summary.endswith('.') else '')
            elif snippet and snippet.strip():
                lines = snippet.split('. ')
                summary_short = '. '.join(lines[:5]) + ('.' if not snippet.endswith('.') else '')
            else:
                summary_short = 'No summary available.'
            # Favicon logic: use Exa favicon or fallback
            favicon = getattr(r, 'favicon', None)
            if not favicon:
                favicon = 'cid:default-favicon'
            # Prefer 'image' if present, else fallback to first in 'images' or 'image_urls'
            image_url = getattr(r, 'image', None)
            if not image_url:
                images = getattr(r, 'images', None) or getattr(r, 'image_urls', None)
                image_url = images[0] if images and isinstance(images, list) and len(images) > 0 else None
            print(f"Result #{idx+1} URL: {url}")
            print(f"  Title: {title}")
            print(f"  Snippet: {snippet[:60]}...")
            print(f"  Summary: {summary_short}")
            print(f"  Image: {image_url}")
            print(f"  Favicon: {favicon}")
            image_path = self.download_image(image_url) if image_url else None
            self.items.append({
                'title': title,
                'excerpt': snippet,
                'summary': summary_short,
                'date': '',
                'source': url,
                'image': image_path,  # downloaded, for inline embedding
                'favicon': favicon,
                'image_url': image_url  # for fallback in HTML
            })

    def download_image(self, url):
        try:
            import requests
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                img_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}.jpg")
                with open(img_path, 'wb') as f:
                    f.write(response.content)
                return img_path
        except Exception as e:
            print(f"Error downloading image: {e}")
        return None

    def generate_html_newsletter(self):
        html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <title>Curated Newsletter</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; text-align: center; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; }}
        .date {{ color: #666; font-size: 0.9em; text-align: center; margin-bottom: 20px; }}
        .news-item {{ margin-bottom: 30px; padding: 20px; background: #f9f9f9; border-radius: 8px; }}
        .news-item h2 {{ color: #2a5db0; margin-top: 0; }}
        .news-item .excerpt {{ color: #666; margin: 10px 0; }}
        .news-item .source {{ color: #999; font-size: 0.9em; margin-top: 5px; }}
        .news-item img {{ max-width: 100%; height: auto; border-radius: 4px; margin: 10px 0; }}
        .category-header {{ margin: 30px 0 20px; padding: 15px; background: #f0f0f0; border-radius: 8px; text-align: center; }}
        .category-header h2 {{ color: #333; margin: 0; }}
    </style>
</head>
<body>
    <h1>Curated Newsletter</h1>
    <div class="date">{datetime.now().strftime('%B %d, %Y')}</div>
    <div class="category-header">
        <h2>Results for: {self.query}</h2>
    </div>
    {''.join([f'''
    <div class="news-item">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
            <img src="{item['favicon']}" alt="favicon" style="width: 24px; height: 24px; border-radius: 4px;">
            <h2 style="margin: 0; font-size: 1.2em;">{item['title']}</h2>
        </div>
        <p class="excerpt">{item['excerpt']}</p>
        {f'<div class="summary">{item["summary"]}</div>' if item.get('summary') else ''}
        <div class="source">Source: <a href='{item['source']}'>{item['source']}</a></div>
        {f'<img src="cid:{os.path.basename(item["image"])}" alt="{item["title"]}" style="margin-top: 10px;">' if item.get('image') else (f'<img src="{item["image_url"]}" alt="{item["title"]}" style="margin-top: 10px; max-width:100%; border-radius:4px;">' if item.get('image_url') else '')}
    </div>
    ''' for item in self.items])}
</body>
</html>
'''
        return html_content

    def send_newsletter(self):
        sender_email = os.getenv('EMAIL_USER')
        sender_password = os.getenv('EMAIL_APP_PASSWORD')
        recipient_emails = self.recipient_emails
        if isinstance(recipient_emails, str):
            recipient_emails = [e.strip() for e in recipient_emails.split(',') if e.strip()]
        msg = MIMEMultipart('related')
        msg['Subject'] = f"Curated Newsletter - {datetime.now().strftime('%B %d, %Y')}"
        msg['From'] = sender_email
        msg['To'] = ', '.join(recipient_emails)
        html_content = self.generate_html_newsletter()
        msg.attach(MIMEText(html_content, 'html'))
        for item in self.items:
            if item.get('image'):
                with open(item['image'], 'rb') as img:
                    img_data = img.read()
                img_cid = os.path.basename(item['image'])
                img_mime = MIMEImage(img_data)
                img_mime.add_header('Content-ID', f'<{img_cid}>')
                img_mime.add_header('Content-Disposition', 'inline', filename=img_cid)
                msg.attach(img_mime)

        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.ehlo()
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_emails, msg.as_string())
            print(f"Newsletter sent to {recipient_emails}")
        except Exception as e:
            print(f"Failed to send email: {e}")

    def cleanup(self):
        for root, dirs, files in os.walk(self.temp_dir):
            for file in files:
                os.remove(os.path.join(root, file))
        os.rmdir(self.temp_dir)
