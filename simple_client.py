import os
import re
import json
import requests
import argparse
import logging
from typing import Tuple, List, Optional
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Default server URL
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/generate_and_send_newsletter")

def parse_with_groq(user_input: str) -> Tuple[Optional[str], List[str]]:
    """
    Use Groq API to parse the user input and extract the topic and emails.
    
    Args:
        user_input: The user's input string
        
    Returns:
        A tuple containing (topic, list of emails)
    """
    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        logger.warning("GROQ_API_KEY not found in environment variables")
        return None, []
    
    # Prepare the API request
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    
    # Create a prompt that asks the model to extract information
    prompt = f"""
    Extract the newsletter topic and email addresses from the following user input:
    
    "{user_input}"
    
    Return ONLY a JSON object with the following format:
    {{
        "topic": "the extracted topic",
        "emails": ["email1@example.com", "email2@example.com"]
    }}
    
    If no topic is found, set "topic" to null.
    If no emails are found, set "emails" to an empty array.
    """
    
    payload = {
        "model": "llama3-70b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1024
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            
            # Extract the JSON part from the response
            json_match = re.search(r'({.*})', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                data = json.loads(json_str)
                
                topic = data.get("topic")
                emails = data.get("emails", [])
                
                return topic, emails
    
    except Exception as e:
        logger.error(f"Error using Groq API: {e}")
    
    return None, []

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
    
    # Try to use Groq API to parse the user input
    try:
        query, emails = parse_with_groq(user_input)
        if query:
            logger.info(f"Topic extracted with Groq API: {query}")
    except Exception as e:
        logger.warning(f"Error using Groq API to parse input: {e}")
        query = None
        emails = []
    
    # Fallback to regex if Groq API failed or returned no results
    if not query:
        # Extract query (topic)
        topic_match = re.search(r'(?:about|on|for|regarding)\s+([^"]*?)(?:\s+to\s+|$)', user_input, re.IGNORECASE)
        if topic_match:
            query = topic_match.group(1).strip()
            logger.info(f"Topic extracted with regex: {query}")
    
    # If still no topic, try more general patterns
    if not query:
        general_match = re.search(r'newsletter\s+(?:about\s+)?(.+?)(?:\s+to\s+|\s+with\s+|$)', user_input, re.IGNORECASE)
        if general_match:
            query = general_match.group(1).strip()
            logger.info(f"Topic extracted with general regex: {query}")
    
    # If no emails were found by Groq, use regex
    if not emails:
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