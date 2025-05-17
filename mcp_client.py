import os
import re
import requests
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default server URL
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/generate_and_send_newsletter")

def parse_input(user_input):
    """
    Parse a single user input string to extract query, emails, and number of results.
    
    Format: "Send a newsletter about [TOPIC] to [EMAIL1, EMAIL2, ...] with [N] results"
    
    Args:
        user_input: The user's input string
        
    Returns:
        tuple: (query, email_list, num_results)
    """
    # Default values
    query = None
    email_list = []
    num_results = 5
    
    # Extract query (topic)
    topic_match = re.search(r'(?:about|on|for|regarding)\s+([^"]*?)(?:\s+to\s+|$)', user_input, re.IGNORECASE)
    if topic_match:
        query = topic_match.group(1).strip()
    
    # Extract emails
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    emails = re.findall(email_pattern, user_input)
    if emails:
        email_list = emails
    
    # Extract number of results
    results_match = re.search(r'(?:with|using|include)\s+(\d+)\s+(?:results|articles)', user_input, re.IGNORECASE)
    if results_match:
        try:
            num_results = int(results_match.group(1))
        except ValueError:
            pass
    
    return query, email_list, num_results

def main():
    parser = argparse.ArgumentParser(description='Generate and send a newsletter with a single command')
    parser.add_argument('prompt', nargs='?', help='A prompt like "Send a newsletter about AI advancements to user@example.com with 6 results"')
    
    args = parser.parse_args()
    
    if args.prompt:
        user_input = args.prompt
    else:
        user_input = input("Enter your request (e.g., 'Send a newsletter about AI advancements to user@example.com with 6 results'): ")
    
    query, email_list, num_results = parse_input(user_input)
    
    # Validate extracted information
    if not query:
        query = input("Topic not detected. Please enter a topic for your newsletter: ")
    
    if not email_list:
        emails = input("No email addresses detected. Please enter recipient emails (comma separated): ")
        email_list = [e.strip() for e in emails.split(',') if e.strip()]
    
    # Prepare the payload
    payload = {
        "query": query,
        "emails": email_list,
        "num_results": num_results
    }
    
    print(f"\nGenerating newsletter about: {query}")
    print(f"Sending to: {', '.join(email_list)}")
    print(f"Including {num_results} results")
    
    # Send the request
    try:
        resp = requests.post(MCP_SERVER_URL, json=payload)
        resp.raise_for_status()
        print(resp.json().get("status", resp.text))
    except Exception as e:
        print(f"Failed to send request: {e}")

if __name__ == "__main__":
    main()