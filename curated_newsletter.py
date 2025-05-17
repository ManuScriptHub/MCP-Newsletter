import os
import tempfile
import uuid
import smtplib
import re
import logging
import requests
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from dotenv import load_dotenv
from exa_py import Exa
from typing import List, Dict, Any, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExaNewsletter:
    """
    A class to generate and send curated newsletters using Exa API for content discovery.
    """
    
    def __init__(self, query: str, recipient_emails: Union[str, List[str]], num_results: int = 5):
        """
        Initialize the newsletter generator.
        
        Args:
            query: Search query for content discovery
            recipient_emails: Email address(es) to send the newsletter to
            num_results: Number of search results to include
        """
        load_dotenv()
        # Enhance the query to get more informative results
        self.query = self._enhance_query(query)
        self.recipient_emails = recipient_emails if isinstance(recipient_emails, list) else [recipient_emails]
        self.num_results = num_results
        self.temp_dir = tempfile.mkdtemp()
        self.items = []
        
    def _enhance_query(self, query: str) -> str:
        """
        Enhance the search query to get better, more informative results.
        
        Args:
            query: Original search query
            
        Returns:
            Enhanced search query
        """
        # Add specificity to avoid vague results
        if len(query.split()) < 3:
            return f"{query} detailed information recent developments"
        return query
    
    @staticmethod
    def _strip_html(text: Optional[str]) -> str:
        """
        Remove HTML tags from text.
        
        Args:
            text: Text that may contain HTML tags
            
        Returns:
            Clean text without HTML tags
        """
        if not text:
            return ''
            
        # Remove HTML tags
        clean_text = re.sub('<[^<]+?>', '', text)
        
        # Remove excessive whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text
    
    @staticmethod
    def _create_summary(text: str, max_sentences: int = 5) -> str:
        """
        Create a concise summary from text.
        
        Args:
            text: Text to summarize
            max_sentences: Maximum number of sentences to include
            
        Returns:
            Summarized text
        """
        if not text or not text.strip():
            return 'Click the source link to learn more about this topic.'
            
        # Check if the text is a loading screen or verification message
        if re.search(r'please wait|being verified|loading', text.lower()):
            # Extract any useful information from the title or URL if available
            title_match = re.search(r'about\s+([^\.]+)', text.lower())
            if title_match:
                topic = title_match.group(1).strip()
                return f"This article discusses {topic}. The content appears to be relevant to the search topic. Click the source link to access the full information."
            else:
                return f"This article contains relevant information to the search topic. Click the source link to access the complete content."
            
        # Split by sentence endings and rejoin limited number
        sentences = re.split(r'(?<=[.!?])\s+', text)
        summary = ' '.join(sentences[:max_sentences])
        
        # Ensure proper ending
        if not summary.endswith(('.', '!', '?')):
            summary += '.'
            
        return summary
        
    @staticmethod
    def _process_markdown(text: str) -> str:
        """
        Process basic Markdown formatting in text.
        
        Args:
            text: Text that may contain Markdown formatting
            
        Returns:
            Text with HTML formatting instead of Markdown
        """
        if not text:
            return ''
            
        # Convert *text* to <strong>text</strong> (bold)
        text = re.sub(r'\*([^*]+)\*', r'<strong>\1</strong>', text)
        
        # Convert _text_ to <em>text</em> (italics)
        text = re.sub(r'_([^_]+)_', r'<em>\1</em>', text)
        
        # Convert `code` to <code>code</code>
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        
        return text
    
    def search_exa(self) -> None:
        """
        Search for content using Exa API and process the results.
        """
        exa_api_key = os.getenv('EXA_API_KEY')
        if not exa_api_key:
            raise RuntimeError("EXA_API_KEY not found in environment or .env file")
            
        exa = Exa(exa_api_key)
        
        # Configure search parameters for better results
        results = exa.search_and_contents(
            self.query,
            type="auto",
            livecrawl="always",
            livecrawl_timeout=9999,  # Increased timeout for better results
            text={
                "max_characters": 500,  # Optimal for most content
                "include_html_tags": True  # Include HTML for better parsing
            },
            extras={
                "links": 5,
                "image_links": 5
            },
            summary={
                "query": f"Summarize the entire content about {self.query}, focusing on key information and insights. Use Markdown formatting like *bold* for emphasis on important terms. If you can't find complete content, you should answer with what you have without mentioning about not having enough data or context."
            },
            num_results=self.num_results
        )
        
        self._process_search_results(results.results)
    
    def _process_search_results(self, results: List[Any]) -> None:
        """
        Process search results and extract relevant information.
        
        Args:
            results: List of search result objects
        """
        for idx, result in enumerate(results):
            # Extract basic information
            url = getattr(result, 'url', None)
            title = getattr(result, 'title', url or 'Untitled')
            
            # Get text content and strip HTML if present
            text_content = getattr(result, 'text', '')
            snippet = self._strip_html(text_content)
            
            # Get summary and ensure HTML is stripped
            summary = getattr(result, 'summary', '')
            if summary:
                summary = self._strip_html(summary)
            
            # Generate summary from available content
            summary_short = (
                self._create_summary(summary) if summary 
                else self._create_summary(snippet) if snippet 
                else f'Information about {title}. Click the source link to learn more.'
            )
            
            # Process markdown in summary (convert *text* to <strong>text</strong>)
            summary_short = self._process_markdown(summary_short)
            
            # Handle favicon
            favicon = getattr(result, 'favicon', None)
            # Use a default favicon if none is provided or if it's invalid
            if not favicon or not favicon.startswith(('http://', 'https://')):
                # Extract domain from URL to use for favicon service
                domain = None
                if url:
                    domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
                    if domain_match:
                        domain = domain_match.group(1)
                
                # Use Google's favicon service as a fallback
                if domain:
                    favicon = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
                else:
                    favicon = 'cid:default-favicon'
            
            # Handle image - try different possible attributes
            image_url = getattr(result, 'image', None)
            if not image_url:
                images = getattr(result, 'images', None) or getattr(result, 'image_urls', None)
                image_url = images[0] if images and isinstance(images, list) and len(images) > 0 else None
            
            # Log the result for debugging
            logger.info(f"Result #{idx+1}: {title} - {url}")
            
            # Download image if available
            image_path = self.download_image(image_url) if image_url else None
            
            # Store processed item
            self.items.append({
                'title': title,
                'excerpt': snippet,
                'summary': summary_short,
                'date': '',
                'source': url,
                'image': image_path,
                'favicon': favicon,
                'image_url': image_url
            })
    
    def download_image(self, url: str) -> Optional[str]:
        """
        Download an image from a URL.
        
        Args:
            url: URL of the image to download
            
        Returns:
            Path to the downloaded image or None if download failed
        """
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                img_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}.jpg")
                with open(img_path, 'wb') as f:
                    f.write(response.content)
                return img_path
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
        return None
    
    def generate_html_newsletter(self) -> str:
        """
        Generate HTML content for the newsletter.
        
        Returns:
            HTML content as a string
        """
        html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <title>Curated Newsletter</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; text-align: center; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; }}
        .date {{ color: #666; font-size: 0.9em; text-align: center; margin-bottom: 20px; }}
        .news-item {{ margin-bottom: 30px; padding: 20px; background: #f9f9f9; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .news-item h2 {{ color: #2a5db0; margin-top: 0; }}
        .news-item .excerpt {{ color: #444; margin: 10px 0; line-height: 1.5; }}
        .news-item .summary {{ color: #333; margin: 15px 0; background: #f0f0f0; padding: 10px; border-left: 3px solid #2a5db0; }}
        .news-item .source {{ color: #666; font-size: 0.9em; margin-top: 10px; }}
        .news-item img {{ max-width: 100%; height: auto; border-radius: 4px; margin: 10px 0; }}
        .category-header {{ margin: 30px 0 20px; padding: 15px; background: #e9f0f7; border-radius: 8px; text-align: center; }}
        .category-header h2 {{ color: #333; margin: 0; }}
        a {{ color: #2a5db0; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>Curated Newsletter</h1>
    <div class="date">{datetime.now().strftime('%B %d, %Y')}</div>
    <div class="category-header">
        <h2>Today's Insights: {self.query}</h2>
    </div>
    {''.join([f'''
    <div class="news-item">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; justify-content: center; width: 24px; height: 24px;">
                <img src="{item['favicon']}" alt="favicon" style="width: 16px; height: 16px; border-radius: 4px; object-fit: contain; display: block;">
            </div>
            <h2 style="margin: 0; font-size: 1.2em; line-height: 1.2;">{item['title']}</h2>
        </div>
        <div class="summary">{item['summary']}</div>
        <p class="excerpt">{item['excerpt'][:300]}{'...' if len(item['excerpt']) > 300 else ''}</p>
        <div class="source">Source: <a href='{item['source']}' target="_blank">{item['source']}</a></div>
        {f'<img src="cid:{os.path.basename(item["image"])}" alt="{item["title"]}" style="margin-top: 10px;">' if item.get('image') else (f'<img src="{item["image_url"]}" alt="{item["title"]}" style="margin-top: 10px; max-width:100%; border-radius:4px;">' if item.get('image_url') else '')}
    </div>
    ''' for item in self.items])}
</body>
</html>
'''
        return html_content
    
    def send_newsletter(self) -> None:
        """
        Send the newsletter to the specified recipients.
        """
        sender_email = os.getenv('EMAIL_USER')
        sender_password = os.getenv('EMAIL_APP_PASSWORD')
        
        if not sender_email or not sender_password:
            raise ValueError("Email credentials not found in environment variables")
        
        recipient_emails = self.recipient_emails
        if isinstance(recipient_emails, str):
            recipient_emails = [e.strip() for e in recipient_emails.split(',') if e.strip()]
            
        # Create email message
        msg = MIMEMultipart('related')
        msg['Subject'] = f"Curated Newsletter - {datetime.now().strftime('%B %d, %Y')}"
        msg['From'] = sender_email
        msg['To'] = ', '.join(recipient_emails)
        
        # Attach HTML content
        html_content = self.generate_html_newsletter()
        msg.attach(MIMEText(html_content, 'html'))
        
        # Attach images
        self._attach_images_to_email(msg)
        
        # Send email
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.ehlo()
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_emails, msg.as_string())
            logger.info(f"Newsletter sent to {recipient_emails}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise
    
    def _attach_images_to_email(self, msg: MIMEMultipart) -> None:
        """
        Attach images to the email message.
        
        Args:
            msg: Email message object
        """
        for item in self.items:
            if item.get('image'):
                try:
                    with open(item['image'], 'rb') as img:
                        img_data = img.read()
                    img_cid = os.path.basename(item['image'])
                    img_mime = MIMEImage(img_data)
                    img_mime.add_header('Content-ID', f'<{img_cid}>')
                    img_mime.add_header('Content-Disposition', 'inline', filename=img_cid)
                    msg.attach(img_mime)
                except Exception as e:
                    logger.error(f"Error attaching image: {e}")
    
    def cleanup(self) -> None:
        """
        Clean up temporary files and directories.
        """
        try:
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    os.remove(os.path.join(root, file))
            os.rmdir(self.temp_dir)
            logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
