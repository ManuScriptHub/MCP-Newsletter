# Curated Tech Newsletter

A Python project for generating and sending a daily curated tech newsletter via email. The newsletter aggregates top stories from popular tech news sources (TechCrunch, Mashable, CNET by default) using their RSS feeds, formats them into a visually appealing HTML email, and sends it to a specified recipient.

## Features

- **Automated News Aggregation:** Scrapes and parses RSS feeds from configurable tech news sources.
- **HTML Email Generation:** Formats news items (title, excerpt, image, date, source) into a modern HTML email.
- **Image Handling:** Downloads and embeds images inline in the email.
- **Customizable Sources:** Easily extendable to new RSS feeds or websites.
- **Environment-based Configuration:** Uses `.env` for secrets and settings.
- **API Support:** Exposes a FastAPI endpoint for triggering newsletter generation and delivery.
- **Command-Line Client:** Includes a CLI client with LLM-powered extraction of user intent and source URLs.

## Project Structure

```
MCP/
├── curated_newsletter.py    # Main logic for scraping, formatting, and sending newsletters
├── mcp_client.py           # CLI client, LLM integration, RSS discovery
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
   GROQ_API_KEY=your_groq_api_key
   MCP_SERVER_URL=http://localhost:8000/generate_and_send_newsletter
   ```
   > **Note:** For Gmail, you need an App Password (not your main password). See [Google App Passwords](https://support.google.com/accounts/answer/185833?hl=en).

## Usage

### 1. Command-Line Client

Run the CLI client to interactively specify sources and recipient:

```bash
python mcp_client.py
```

- Enter a prompt like: `Send me top TechCrunch and Mashable stories to alice@example.com`.
- The client uses LLM (GROQ API) to extract the recipient and sources, discovers RSS feeds, and calls the server API.

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
    "email": "recipient@example.com",
    "websites": {
      "techcrunch": "https://techcrunch.com/feed/",
      "mashable": "https://mashable.com/feed/"
    }
  }
  ```
- If `websites` is omitted, defaults to TechCrunch, Mashable, and CNET.
- Responds immediately; email sending runs in the background.

### 3. Standalone Script

You can also run the newsletter script directly:

```bash
python curated_newsletter.py
```

This will scrape default sources, generate, send the newsletter, and clean up temporary files.

## Adding New Sources
- Update the `rss_feeds` dictionary in `curated_newsletter.py` or provide custom feeds via the API/client.
- The client can auto-discover RSS feeds for many popular sites.

## Environment Variables
- `EMAIL_USER`: Gmail address to send from
- `EMAIL_APP_PASSWORD`: Gmail app password
- `EMAIL_RECIPIENT`: Default recipient (can be overridden)
- `GROQ_API_KEY`: API key for LLM-powered extraction (optional for CLI)
- `MCP_SERVER_URL`: Server endpoint for newsletter requests

## Dependencies
- Python 3.8+
- yagmail
- python-dotenv
- beautifulsoup4
- requests
- filetype
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
- **No news items?**
  - Check RSS feed URLs for accuracy.
  - Some sites may block scraping or change feed URLs.

## Contributing
Pull requests and suggestions are welcome! Please open an issue or PR for improvements or bug fixes.

## License
MIT License. See `LICENSE` file (if present) for details.
