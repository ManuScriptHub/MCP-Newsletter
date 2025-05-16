import os
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import filetype
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import tempfile
import uuid
import feedparser

class CuratedNewsletter:
    def __init__(self, rss_feeds=None, recipient_email=None):
        self.rss_feeds = rss_feeds or {
            'techcrunch': 'https://techcrunch.com/feed/',
            'mashable': 'https://mashable.com/feed/',
            'cnet': 'https://www.cnet.com/rss/all/'
        }
        self.news_items = []
        self.temp_dir = tempfile.mkdtemp()
        self.recipient_email = recipient_email

    def scrape_all_feeds(self):
        for name, url in self.rss_feeds.items():
            print(f"Scraping {name}: {url}")
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                title = entry.title
                excerpt = entry.summary if hasattr(entry, 'summary') else ''
                date = entry.published if hasattr(entry, 'published') else ''
                img_url = ''
                if 'media_content' in entry and len(entry.media_content) > 0:
                    img_url = entry.media_content[0].get('url', '')
                elif 'content' in entry and len(entry.content) > 0:
                    soup = BeautifulSoup(entry.content[0].value, 'html.parser')
                    img_tag = soup.find('img')
                    if img_tag:
                        img_url = img_tag.get('src', '')
                self.news_items.append({
                    'title': title,
                    'excerpt': excerpt,
                    'date': date,
                    'source': name,
                    'image': self.download_image(img_url) if img_url else None
                })

    def download_image(self, url):
        """
        Download and save image locally
        """
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                img_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}.jpg")
                with open(img_path, 'wb') as f:
                    f.write(response.content)
                return img_path
        except Exception as e:
            print(f"Error downloading image: {e}")
        return None

    def scrape_mashable(self):
        """
        Scrape Mashable using RSS feed
        """
        print("Scraping Mashable RSS...")
        feed = feedparser.parse(self.rss_feeds['mashable'])
        for entry in feed.entries[:5]:
            title = entry.title
            excerpt = entry.summary if hasattr(entry, 'summary') else ''
            date = entry.published if hasattr(entry, 'published') else ''
            img_url = ''
            if 'media_content' in entry and len(entry.media_content) > 0:
                img_url = entry.media_content[0].get('url', '')
            elif 'content' in entry and len(entry.content) > 0:
                soup = BeautifulSoup(entry.content[0].value, 'html.parser')
                img_tag = soup.find('img')
                if img_tag:
                    img_url = img_tag.get('src', '')
            self.news_items.append({
                'title': title,
                'excerpt': excerpt,
                'date': date,
                'source': 'Mashable',
                'image': self.download_image(img_url) if img_url else None
            })

    def scrape_techcrunch(self):
        """
        Scrape TechCrunch using RSS feed
        """
        print("Scraping TechCrunch RSS...")
        feed = feedparser.parse(self.rss_feeds['techcrunch'])
        for entry in feed.entries[:5]:
            title = entry.title
            excerpt = entry.summary if hasattr(entry, 'summary') else ''
            date = entry.published if hasattr(entry, 'published') else ''
            img_url = ''
            # Try to extract image from media:content or content
            if 'media_content' in entry and len(entry.media_content) > 0:
                img_url = entry.media_content[0].get('url', '')
            elif 'content' in entry and len(entry.content) > 0:
                soup = BeautifulSoup(entry.content[0].value, 'html.parser')
                img_tag = soup.find('img')
                if img_tag:
                    img_url = img_tag.get('src', '')
            self.news_items.append({
                'title': title,
                'excerpt': excerpt,
                'date': date,
                'source': 'TechCrunch',
                'image': self.download_image(img_url) if img_url else None
            })

    def scrape_cnet(self):
        """
        Scrape CNET using RSS feed
        """
        print("Scraping CNET RSS...")
        feed = feedparser.parse(self.rss_feeds['cnet'])
        for entry in feed.entries[:5]:
            title = entry.title
            excerpt = entry.summary if hasattr(entry, 'summary') else ''
            date = entry.published if hasattr(entry, 'published') else ''
            img_url = ''
            if 'media_content' in entry and len(entry.media_content) > 0:
                img_url = entry.media_content[0].get('url', '')
            elif 'content' in entry and len(entry.content) > 0:
                soup = BeautifulSoup(entry.content[0].value, 'html.parser')
                img_tag = soup.find('img')
                if img_tag:
                    img_url = img_tag.get('src', '')
            self.news_items.append({
                'title': title,
                'excerpt': excerpt,
                'date': date,
                'source': 'CNET',
                'image': self.download_image(img_url) if img_url else None
            })

    def generate_html_newsletter(self):
        """
        Generate HTML content for the newsletter
        """
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Daily Tech Newsletter</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; text-align: center; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; }}
        .date {{ color: #666; font-size: 0.9em; text-align: center; margin-bottom: 20px; }}
        .news-item {{ margin-bottom: 30px; padding: 20px; background: #f9f9f9; border-radius: 8px; }}
        .news-item h2 {{ color: #2a5db0; margin-top: 0; }}
        .news-item .excerpt {{ color: #666; margin: 10px 0; }}
        .news-item .source {{ color: #999; font-size: 0.9em; margin-top: 5px; }}
        .news-item img {{ max-width: 100%; height: auto; border-radius: 4px; margin: 10px 0; }}
        .category-header {{ 
            margin: 30px 0 20px; 
            padding: 15px;
            background: #f0f0f0;
            border-radius: 8px;
            text-align: center;
        }}
        .category-header h2 {{ color: #333; margin: 0; }}
    </style>
</head>
<body>
    <h1>Daily Tech Newsletter</h1>
    <div class="date">{datetime.now().strftime('%B %d, %Y')}</div>

    <div class="category-header">
        <h2>Tech News</h2>
    </div>
    {"".join([f"""
    <div class="news-item">
        <h2>{item['title']}</h2>
        <p class="excerpt">{item['excerpt']}</p>
        <div class="source">Source: {item['source']} - {item['date']}</div>
        {f'<img src="cid:{os.path.basename(item["image"])}" alt="{item["title"]}">' if item.get('image') else ''}
    </div>
    """ for item in self.news_items])}
</body>
</html>
"""
        return html_content

    def send_newsletter(self):
        """
        Send the newsletter email using smtplib and email.mime
        """
        load_dotenv()

        sender_email = os.getenv('EMAIL_USER')
        sender_password = os.getenv('EMAIL_APP_PASSWORD')
        recipient_email = self.recipient_email or os.getenv('EMAIL_RECIPIENT')

        # Create the root message
        msg = MIMEMultipart('related')
        msg['Subject'] = f"Daily Tech Newsletter - {datetime.now().strftime('%B %d, %Y')}"
        msg['From'] = sender_email
        msg['To'] = recipient_email

        # Attach the HTML body
        html_content = self.generate_html_newsletter()
        msg.attach(MIMEText(html_content, 'html'))

        # Attach images as inline attachments
        for item in self.news_items:
            if item.get('image'):
                with open(item['image'], 'rb') as img_file:
                    img_data = img_file.read()
                    kind = filetype.guess(img_data)
                    if kind and kind.mime.startswith('image/'):
                        img = MIMEImage(img_data, _subtype=kind.extension)
                        img.add_header('Content-ID', f'<{os.path.basename(item["image"])}>' )
                        img.add_header('Content-Disposition', 'inline', filename=os.path.basename(item['image']))
                        msg.attach(img)
                    else:
                        print(f"Skipped attaching image {item['image']}: unknown or invalid image type")

        # Send the email via Gmail SMTP
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.ehlo()
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_email, msg.as_string())
            print(f"Newsletter sent to {recipient_email}")
        except Exception as e:
            print(f"Failed to send email: {e}")

    def cleanup(self):
        """
        Clean up temporary files
        """
        for root, dirs, files in os.walk(self.temp_dir):
            for file in files:
                os.remove(os.path.join(root, file))
        os.rmdir(self.temp_dir)

def main():
    newsletter = CuratedNewsletter()
    
    print("Scraping TechCrunch...")
    newsletter.scrape_techcrunch()
    
    print("Scraping Mashable...")
    newsletter.scrape_mashable()
    
    print("Scraping CNET...")
    newsletter.scrape_cnet()
    
    print("Generating and sending newsletter...")
    newsletter.send_newsletter()
    
    print("Cleaning up...")
    newsletter.cleanup()
    
    print("Newsletter process completed!")

if __name__ == "__main__":
    main()
