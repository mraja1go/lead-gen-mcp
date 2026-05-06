# Lead Generator MCP Plugin

A Claude MCP plugin that generates B2B leads using Apollo.io and Hunter.io.

## Tools Available

| Tool | Description |
|------|-------------|
| `search_leads` | Search leads by job title, industry, location, company size |
| `find_email` | Find email for a specific person by name + company domain |
| `verify_email` | Check if an email is valid and deliverable |
| `search_company_emails` | Find all known emails at a company domain |
| `export_leads_csv` | Search leads and save results to a CSV file |

---

## Setup (Each Team Member)

### 1. Prerequisites
- Python 3.10 or higher
- Claude Desktop or Claude Code installed

### 2. Clone / Copy the project
Share this folder with your team via Git, Google Drive, or a zip file.

### 3. Install dependencies
```bash
cd lead-gen-mcp
pip install -r requirements.txt
```

### 4. Add your API keys
Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```

Edit `.env`:
```
APOLLO_API_KEY=your_actual_apollo_key
HUNTER_API_KEY=your_actual_hunter_key
```

> Each team member uses their own API keys. Never commit `.env` to git.

### 5. Connect to Claude Desktop
Open your Claude Desktop config file:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Add the following (replace the path with your actual path):
```json
{
  "mcpServers": {
    "lead-generator": {
      "command": "python",
      "args": ["C:/path/to/lead-gen-mcp/server.py"]
    }
  }
}
```

Restart Claude Desktop. You should see the lead generator tools available.

### 6. Connect to Claude Code (CLI)
Run:
```bash
claude mcp add lead-generator python /absolute/path/to/lead-gen-mcp/server.py
```

---

## Usage Examples

**Search for leads:**
> "Find 10 CEOs in the SaaS industry based in the United States at companies with 50 to 500 employees"

**Find an email:**
> "Find the email for John Smith at acme.com"

**Verify an email:**
> "Verify the email john.smith@acme.com"

**Export to CSV:**
> "Search for VP of Sales in Fintech in the UK and export to a CSV"

---

## API Limits (Free Tiers)

| Service | Free Limit |
|---------|-----------|
| Apollo.io | 50 credits/month |
| Hunter.io | 25 searches/month |

Upgrade plans available on each platform for higher volume.
