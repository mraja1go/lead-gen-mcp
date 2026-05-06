import os
import csv
import re
import requests
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("Lead Generator")

HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

SERPER_SEARCH_URL = "https://google.serper.dev/search"
HUNTER_BASE_URL = "https://api.hunter.io/v2"


def _build_query(job_titles: list[str], industries: list[str] | None, locations: list[str] | None) -> str:
    parts = []
    if job_titles:
        parts.append(" OR ".join(f'"{t}"' for t in job_titles))
    if industries:
        parts.append(" OR ".join(f'"{i}"' for i in industries))
    if locations:
        parts.append(" OR ".join(f'"{l}"' for l in locations))
    return " ".join(parts)


def _parse_result(item: dict) -> dict:
    title_raw = item.get("title", "")
    link = item.get("link", "N/A")
    snippet = item.get("snippet", "")

    # LinkedIn titles are usually   : "Name - Title at Company | LinkedIn"
    name, job_title, company = "N/A", "N/A", "N/A"

    title_clean = re.sub(r"\s*\|.*$", "", title_raw).strip()
    if " - " in title_clean:
        parts = title_clean.split(" - ", 1)
        name = parts[0].strip()
        rest = parts[1].strip()
        if " at " in rest.lower():
            idx = rest.lower().index(" at ")
            job_title = rest[:idx].strip()
            company = rest[idx + 4:].strip()
        else:
            job_title = rest

    return {
        "name": name,
        "title": job_title,
        "company": company,
        "linkedin_url": link,
        "snippet": snippet,
    }


@mcp.tool()
def search_leads(
    job_titles: list[str],
    industries: list[str] | None = None,
    locations: list[str] | None = None,
    num_results: int = 10,
) -> str:
    """
    Search for B2B leads via Google Custom Search on LinkedIn profiles.

    Args:
        job_titles: Job titles to target, e.g. ["CEO", "VP of Sales"]
        industries: Industries to filter, e.g. ["SaaS", "Healthcare"]
        locations: Locations to filter, e.g. ["United States", "United Kingdom"]
        num_results: Number of leads to return (max 10 per query, free limit: 100/day)
    """
    query = _build_query(job_titles, industries, locations)
    response = requests.post(
        SERPER_SEARCH_URL,
        headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
        json={"q": query, "num": min(num_results, 10)},
        timeout=10,
    )
    data = response.json()

    if "error" in data:
        return f"Serper search error: {data['error']}"

    items = data.get("organic", [])
    if not items:
        return "No leads found. Try different job titles, industries, or locations."

    leads = [_parse_result(item) for item in items]

    lines = [f"Found {len(leads)} lead(s):\n"]
    for i, lead in enumerate(leads, 1):
        lines.append(
            f"{i}. {lead['name']}\n"
            f"   Title:    {lead['title']}\n"
            f"   Company:  {lead['company']}\n"
            f"   LinkedIn: {lead['linkedin_url']}\n"
            f"   Snippet:  {lead['snippet']}\n"
        )
    return "\n".join(lines)


@mcp.tool()
def find_email(first_name: str, last_name: str, company_domain: str) -> str:
    """
    Find a professional email address for a specific person using Hunter.io.

    Args:
        first_name: Person's first name
        last_name: Person's last name
        company_domain: Company website domain, e.g. "acme.com"
    """
    params = {
        "domain": company_domain,
        "first_name": first_name,
        "last_name": last_name,
        "api_key": HUNTER_API_KEY,
    }
    response = requests.get(f"{HUNTER_BASE_URL}/email-finder", params=params, timeout=10)
    data = response.json()

    email_data = data.get("data", {})
    email = email_data.get("email")
    if not email:
        return f"No email found for {first_name} {last_name} at {company_domain}."

    score = email_data.get("score", "N/A")
    status = email_data.get("verification", {}).get("status", "N/A")
    return (
        f"Email:       {email}\n"
        f"Confidence:  {score}%\n"
        f"Verified:    {status}"
    )


@mcp.tool()
def verify_email(email: str) -> str:
    """
    Verify whether an email address is valid and deliverable using Hunter.io.

    Args:
        email: The email address to verify
    """
    params = {"email": email, "api_key": HUNTER_API_KEY}
    response = requests.get(f"{HUNTER_BASE_URL}/email-verifier", params=params, timeout=10)
    data = response.json()

    result_data = data.get("data", {})
    if not result_data:
        return f"Could not verify {email}. Response: {data}"

    return (
        f"Email:       {email}\n"
        f"Status:      {result_data.get('status', 'N/A')}\n"
        f"Result:      {result_data.get('result', 'N/A')}\n"
        f"Score:       {result_data.get('score', 'N/A')}%"
    )


@mcp.tool()
def search_company_emails(company_domain: str, num_results: int = 10) -> str:
    """
    Find all known professional email addresses at a company domain using Hunter.io.

    Args:
        company_domain: Company website domain, e.g. "acme.com"
        num_results: Number of emails to return (max 10 on free plan)
    """
    params = {
        "domain": company_domain,
        "limit": min(num_results, 10),
        "api_key": HUNTER_API_KEY,
    }
    response = requests.get(f"{HUNTER_BASE_URL}/domain-search", params=params, timeout=10)
    data = response.json()

    emails = data.get("data", {}).get("emails", [])
    if not emails:
        return f"No emails found for {company_domain}."

    lines = [f"Found {len(emails)} email(s) at {company_domain}:\n"]
    for e in emails:
        name = f"{e.get('first_name', '')} {e.get('last_name', '')}".strip()
        lines.append(
            f"- {e.get('value', 'N/A')}\n"
            f"  Name:       {name or 'N/A'}\n"
            f"  Title:      {e.get('position', 'N/A')}\n"
            f"  Confidence: {e.get('confidence', 'N/A')}%\n"
        )
    return "\n".join(lines)


@mcp.tool()
def export_leads_csv(
    job_titles: list[str],
    industries: list[str] | None = None,
    locations: list[str] | None = None,
    num_results: int = 10,
    filename: str | None = None,
) -> str:
    """
    Search for leads via Google and export them to a CSV file.

    Args:
        job_titles: Job titles to target, e.g. ["CEO", "CTO"]
        industries: Industries to filter, e.g. ["SaaS", "Fintech"]
        locations: Locations to filter, e.g. ["United States"]
        num_results: Number of leads to export (max 10)
        filename: Output CSV filename (auto-generated if not provided)
    """
    query = _build_query(job_titles, industries, locations)
    response = requests.post(
        SERPER_SEARCH_URL,
        headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
        json={"q": query, "num": min(num_results, 10)},
        timeout=10,
    )
    data = response.json()

    if "error" in data:
        return f"Serper search error: {data['error']}"

    items = data.get("organic", [])
    if not items:
        return "No leads found. CSV not created."

    if not filename:
        filename = f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    fieldnames = ["name", "title", "company", "linkedin_url", "snippet"]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            lead = _parse_result(item)
            writer.writerow({k: lead[k] for k in fieldnames})

    return f"Exported {len(items)} lead(s) to {filename}"


if __name__ == "__main__":
    mcp.run()
