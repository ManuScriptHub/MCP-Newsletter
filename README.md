# Curated AI Newsletter

A Python project for generating and sending curated AI newsletters via email. The newsletter uses the Exa API to search for and aggregate content based on user-specified topics, formats them into a visually appealing HTML email, and sends it to specified recipients.

## Features

- **AI-Powered Content Discovery:** Uses Exa API to find relevant, up-to-date content on any topic.
- **Smart Summarization:** Automatically generates concise summaries of articles.
- **HTML Email Generation:** Formats content items (title, summary, image, source) into a modern HTML email.
- **Image Handling:** Downloads and embeds images inline in the email.
- **Favicon Integration:** Displays website favicons for better visual identification of sources.
- **Environment-based Configuration:** Uses `.env` for secrets and settings.
- **API Support:** Exposes a FastAPI endpoint for triggering newsletter generation and delivery.
- **Command-Line Client:** Includes a CLI client for easy specification of topics and recipients.

## Project Structure

```
MCP/
├── curated_newsletter.py    # Main logic for content discovery, formatting, and sending newsletters
├── mcp_client.py           # CLI client for user interaction
├── mcp_server.py           # FastAPI server exposing newsletter API
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not committed)
├── .gitignore              # Git ignore rules
```

## Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd MCP
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up environment variables:**
   Create a `.env` file in the project root with the following variables:
   ```env
   EMAIL_USER=your_gmail_address@gmail.com
   EMAIL_APP_PASSWORD=your_gmail_app_password
   EMAIL_RECIPIENT=recipient@example.com
   EXA_API_KEY=your_exa_api_key
   MCP_SERVER_URL=http://localhost:8000/generate_and_send_newsletter
   ```
   > **Note:** For Gmail, you need an App Password (not your main password). See [Google App Passwords](https://support.google.com/accounts/answer/185833?hl=en).

## Usage

### 1. Command-Line Client

Run the CLI client to specify topics and recipients:

```bash
python mcp_client.py
```

- Enter a prompt like: `Send a newsletter about AI advancements to user@example.com with 6 results`.
- The client extracts the topic, recipient email, and number of results, then calls the server API.

### 2. FastAPI Server

Start the server to expose the newsletter endpoint:

```bash
uvicorn mcp_server:app --reload
```

#### API Endpoint
- **POST** `/generate_and_send_newsletter`
- **Body:**
  ```json
  {
    "query": "Latest AI developments in natural language processing",
    "emails": ["recipient@example.com"],
    "num_results": 6
  }
  ```
- The `num_results` parameter is optional and defaults to 5.
- Responds immediately; email sending runs in the background.

### 3. Standalone Script

You can also run the newsletter script directly by modifying and executing:

```bash
python curated_newsletter.py
```

## Environment Variables
- `EMAIL_USER`: Gmail address to send from
- `EMAIL_APP_PASSWORD`: Gmail app password
- `EMAIL_RECIPIENT`: Default recipient (can be overridden)
- `EXA_API_KEY`: API key for Exa content discovery
- `MCP_SERVER_URL`: Server endpoint for newsletter requests

## Dependencies
- Python 3.8+
- exa-py
- python-dotenv
- requests
- fastapi, uvicorn (for API server)

Install all dependencies with:
```bash
pip install -r requirements.txt
```

## Troubleshooting
- **Email not sending?**
  - Ensure your Gmail account allows app passwords and SMTP access.
  - Check for correct credentials in `.env`.
  - Review any error messages in the console.
- **No content in newsletter?**
  - Verify your Exa API key is valid.
  - Try a more specific search query.
  - Check your internet connection for API access.

## Contributing
Pull requests and suggestions are welcome! Please open an issue or PR for improvements or bug fixes.

## License
MIT License. See `LICENSE` file (if present) for details.
