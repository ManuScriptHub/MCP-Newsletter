import os
import requests
from dotenv import load_dotenv
import json

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/generate_and_send_newsletter")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def get_user_input():
    return input("What do you want to do? (e.g., 'Send me top NYT stories to alice@example.com')\n> ")


def extract_info_with_groq(prompt):
    """
    Calls GROQ LLM API to extract email and, for each mentioned website, the homepage and RSS URLs if available.
    """
    system_prompt = (
        "You are an assistant that extracts the following from a user's message:\n"
        "1. The target email address (if any)\n"
        "2. For each mentioned website, extract:\n"
        "   a. The official website homepage URL (if possible)\n"
        "   b. The RSS or Atom feed URL (if possible)\n"
        "Respond in JSON as follows:\n"
        "{ 'email': string or null, 'websites': [ { 'name': string, 'homepage_url': string or null, 'rss_url': string or null } ] }"
    )
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 512,
        "temperature": 0.2
    }
    response = requests.post(GROQ_API_URL, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()["choices"][0]["message"]["content"]
    try:
        parsed = json.loads(result)
    except Exception:
        import re
        match = re.search(r"\{.*\}", result, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
        else:
            raise ValueError("GROQ response did not contain valid JSON.")
    return parsed


from bs4 import BeautifulSoup
import re
import requests
import urllib.parse

def find_rss_feed_url(site_name):
    """
    Try to find the RSS feed URL for a given site name by searching and scraping the homepage.
    Returns the feed URL if found, else None.
    """
    # Step 1: Try to get the homepage URL via DuckDuckGo search
    search_url = f"https://duckduckgo.com/html/?q={urllib.parse.quote(site_name)}"
    try:
        resp = requests.get(search_url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.select('.result__a')
        homepage_url = None
        for link in links:
            url = link.get('href')
            if url and not url.startswith('/y.js'):
                homepage_url = url
                break
        if not homepage_url:
            return None
    except Exception:
        return None

    # Step 2: Scrape homepage for RSS/Atom links
    try:
        resp = requests.get(homepage_url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        feed_links = soup.find_all('link', type=re.compile(r'(rss|atom)', re.I))
        for link in feed_links:
            href = link.get('href')
            if href:
                if not href.startswith('http'):
                    href = urllib.parse.urljoin(homepage_url, href)
                return href
    except Exception:
        return None
    return None

def map_websites_to_rss(llm_websites):
    """
    Accepts a list of dicts [{name, homepage_url, rss_url}] from the LLM.
    Uses LLM-provided RSS/homepage URLs if available, otherwise falls back to known_feeds and scraping.
    Returns a dict {site_name: rss_url}.
    """
    # Expanded known feeds for global and Indian news
    known_feeds = {
        "new york times": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "nyt": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "techcrunch": "https://techcrunch.com/feed/",
        "mashable": "https://mashable.com/feed/",
        "cnet": "https://www.cnet.com/rss/all/",
        "the hindu": "https://www.thehindu.com/feeder/default.rss",
        "hindu": "https://www.thehindu.com/feeder/default.rss",
        "the times of india": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "times of india": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "indiatimes": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "india times": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "toi": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"
    }
    rss_dict = {}
    for item in llm_websites:
        name = item.get('name')
        rss_url = item.get('rss_url')
        homepage_url = item.get('homepage_url')
        # Use LLM-provided RSS if available
        if rss_url:
            rss_dict[name] = rss_url
            continue
        # Try known feeds
        key = name.strip().lower().replace("the ", "").replace(" ", "")
        found = False
        for feed_key in known_feeds:
            norm_feed_key = feed_key.strip().lower().replace("the ", "").replace(" ", "")
            if key == norm_feed_key or key in norm_feed_key or norm_feed_key in key:
                rss_dict[name] = known_feeds[feed_key]
                found = True
                break
        if found:
            continue
        # Try to auto-discover RSS feed for unknown sites
        url_to_scrape = homepage_url or name
        rss_url = find_rss_feed_url(url_to_scrape)
        if not rss_url:
            # Try to find <a> tags with 'rss' in href if <link> tags fail
            import requests, re
            import urllib.parse
            search_url = f"https://duckduckgo.com/html/?q={urllib.parse.quote(url_to_scrape)}"
            try:
                resp = requests.get(search_url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                links = soup.select('.result__a')
                homepage_url2 = None
                for link in links:
                    url = link.get('href')
                    if url and not url.startswith('/y.js'):
                        homepage_url2 = url
                        break
                if homepage_url2:
                    resp = requests.get(homepage_url2, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
                    soup = BeautifulSoup(resp.text, "html.parser")
                    a_links = soup.find_all('a', href=True)
                    for a in a_links:
                        href = a['href']
                        if 'rss' in href.lower():
                            if not href.startswith('http'):
                                href = urllib.parse.urljoin(homepage_url2, href)
                            rss_url = href
                            break
            except Exception:
                pass
        if rss_url:
            rss_dict[name] = rss_url
        else:
            print(f"[WARN] No RSS feed found for '{name}'. It will be skipped.")
    return rss_dict


def send_newsletter_request(email, rss_dict):
    """
    Send the newsletter request to the MCP server, passing websites as a dict {site_name: rss_url}.
    """
    payload = {
        "email": email,
        "websites": rss_dict if rss_dict else None
    }
    response = requests.post(MCP_SERVER_URL, json=payload)
    response.raise_for_status()
    return response.json()


def main():
    prompt = get_user_input()
    info = extract_info_with_groq(prompt)
    email = info.get("email")
    llm_websites = info.get("websites", [])
    rss_dict = map_websites_to_rss(llm_websites)
    if not email:
        print("No email address found in your prompt.")
        return
    result = send_newsletter_request(email, rss_dict)
    print(result.get("status", result))


if __name__ == "__main__":
    main()
