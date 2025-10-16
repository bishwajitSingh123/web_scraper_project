# parsers/site_example_com.py
from bs4 import BeautifulSoup

def parse_site_example_com(html: str, source_url: str) -> dict:
    """Site-specific extractor using CSS selectors"""
    soup = BeautifulSoup(html, "lxml")
    data = {}

    # Example: <h1 class="company-title">
    h1_tag = soup.select_one("h1.company-title")
    data['company_name'] = h1_tag.get_text(strip=True) if h1_tag else None

    # Example: description inside <div class="company-description">
    desc_tag = soup.select_one("div.company-description")
    data['description'] = desc_tag.get_text(strip=True) if desc_tag else None

    # Add social links, email, phone using generic regex
    import re
    EMAIL_REGEX = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
    PHONE_REGEX = re.compile(r'(\+?\d{1,3}?[-.\s]?\(?\d{1,4}?\)?[-.\s]?\d{2,4}[-.\s]?\d{2,4})')
    data['email'] = list(set(EMAIL_REGEX.findall(html)))
    data['phone'] = list(set(PHONE_REGEX.findall(html)))
    data['social_links'] = []
    for key, pattern in {"linkedin": "linkedin.com", "facebook": "facebook.com"}.items():
        data['social_links'].extend([a['href'] for a in soup.select(f'a[href*="{pattern}"]') if a.has_attr('href')])

    data['website'] = source_url
    data['address'] = None
    data['category'] = None
    data['source_url'] = source_url

    return data
