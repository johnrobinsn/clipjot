# ClipJot API Examples

Example code for using the ClipJot API.

## sync_watch.py

A Python script demonstrating the sync API with long polling. Useful for building clients that stay in sync with the server.

### Setup

```bash
# Install dependencies
pip install requests python-dotenv

# Copy and configure environment
cp .env.example .env
# Edit .env with your API token and server URL
```

### Usage

```bash
python sync_watch.py
```

The script will:
1. Perform an initial sync to get all bookmarks
2. Enter long polling mode to receive new bookmarks in real-time
3. Print bookmark details as they arrive

### Configuration

Edit `.env`:

```
CLIPJOT_API_URL=https://your-domain.com
CLIPJOT_TOKEN=your-api-token
```

Get an API token from Settings > API Tokens in the ClipJot web interface.
