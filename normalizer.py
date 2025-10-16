import re

def normalize_email(email_list):
    return [e.strip().lower() for e in email_list if re.match(r'[\w\.-]+@[\w\.-]+\.\w+', e)]

def normalize_phone(phone_list):
    # simple: keep only digits and leading '+'
    normalized = []
    for p in phone_list:
        digits = re.sub(r'[^\d+]', '', p)
        if digits:
            normalized.append(digits)
    return normalized

def normalize_text(text):
    return text.strip() if text else None

def normalize_url(url):
    return url.strip().lower() if url else None
