import os
import requests
from dotenv import load_dotenv

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/generate_and_send_newsletter")

def main():
    query = input("Enter your search query (e.g., 'new products this week'): ")
    emails = input("Enter recipient emails (comma separated): ")
    email_list = [e.strip() for e in emails.split(',') if e.strip()]
    num_results = input("How many results to include? (default 5): ")
    try:
        num_results = int(num_results)
    except Exception:
        num_results = 5
    payload = {
        "query": query,
        "emails": email_list,
        "num_results": num_results
    }
    try:
        resp = requests.post(MCP_SERVER_URL, json=payload)
        resp.raise_for_status()
        print(resp.json().get("status", resp.text))
    except Exception as e:
        print(f"Failed to send request: {e}")

if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
