# extract_common.py
from bs4 import BeautifulSoup
import re
import os
import json
import urllib.parse

EXTRACTED_DIR = "extracted"
os.makedirs(EXTRACTED_DIR, exist_ok=True)

# Regex patterns
PHONE_REGEX = re.compile(r'(\+?\d{1,3}?[-.\s]?\(?\d{1,4}?\)?[-.\s]?\d{2,4}[-.\s]?\d{2,4})')
EMAIL_REGEX = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
SOCIAL_REGEX = {
    "linkedin": re.compile(r'https?://(?:www\.)?linkedin\.com/[\w/-]+', re.I),
    "facebook": re.compile(r'https?://(?:www\.)?facebook\.com/[\w/-]+', re.I),
    "twitter": re.compile(r'https?://(?:www\.)?twitter\.com/[\w/-]+', re.I),
}

def extract_common(html: str, source_url: str) -> dict:
    """Extract generic fields from any HTML."""
    soup = BeautifulSoup(html, "lxml")
    data = {}

    # Company name: prefer <meta property="og:title"> or <h1>
    og_title = soup.find("meta", property="og:title")
    data['company_name'] = (og_title["content"] if og_title else None) or (soup.h1.get_text(strip=True) if soup.h1 else None)

    # Description: meta[name="description"]
    meta_desc = soup.find("meta", attrs={"name":"description"})
    data['description'] = meta_desc["content"].strip() if meta_desc else None

    # Emails
    data['email'] = list(set(EMAIL_REGEX.findall(html)))

    # Phone numbers
    data['phone'] = list(set(PHONE_REGEX.findall(html)))

    # Social links
    social_links = []
    for key, regex in SOCIAL_REGEX.items():
        matches = regex.findall(html)
        social_links.extend(matches)
    data['social_links'] = social_links

    # URLs (website)
    data['website'] = source_url

    # Address: check <address> tags or common patterns
    address_tag = soup.find("address")
    data['address'] = address_tag.get_text(strip=True) if address_tag else None

    # Category placeholder
    data['category'] = None

    # Source URL
    data['source_url'] = source_url

    return data

def save_extracted_json(data: dict):
    """Save extracted dict as JSON in extracted/<sha1>.json"""
    import hashlib
    h = hashlib.sha1(data['source_url'].encode("utf-8")).hexdigest()
    path = os.path.join(EXTRACTED_DIR, f"{h}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path
