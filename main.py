# main.py
import argparse
import pandas as pd
from fetcher import fetch_with_retries
from extract_common import extract_common, save_extracted_json
from urllib.parse import urlparse
import importlib
import os
from normalizer import normalize_email, normalize_phone, normalize_text, normalize_url  # <-- added

def main(input_csv: str, retries: int, backoff: float, rate: float):
    # ensure extracted/ folder exists
    os.makedirs("extracted", exist_ok=True)

    # read input URLs
    df = pd.read_csv(input_csv)
    urls = df['url'].dropna().unique().tolist()
    print(f"Found {len(urls)} unique URLs. Starting downloads...")

    for i, url in enumerate(urls, start=1):
        print(f"\n[{i}/{len(urls)}] Fetching: {url}")
        html_content = fetch_with_retries(url, retries=retries, backoff=backoff, rate_delay=rate)

        if not html_content:
            print(f"❌ Failed to fetch: {url}")
            continue

        # determine domain
        domain = urlparse(url).netloc
        module_name = f"parsers.site_{domain.replace('.', '_')}"

        # Try site-specific parser if available
        try:
            site_parser = importlib.import_module(module_name)
            data = site_parser.parse_site_example_com(html_content, url)
            print(f"✅ Used site-specific parser for {domain}")
        except ModuleNotFoundError:
            # fallback to generic extractor
            data = extract_common(html_content, url)
            print(f"⚙️ Used generic extractor for {domain}")

        # -------------------------------
        # 🔹 Normalize extracted fields
        # -------------------------------
        data['email'] = normalize_email(data.get('email', []))
        data['phone'] = normalize_phone(data.get('phone', []))
        data['company_name'] = normalize_text(data.get('company_name'))
        data['description'] = normalize_text(data.get('description'))
        data['website'] = normalize_url(data.get('website'))

        # save the extracted JSON
        save_extracted_json(data)

    print("\n🎉 Extraction complete! All normalized JSON files saved in 'extracted/' folder.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", "-i", default="company_urls.csv", help="CSV with column 'url'")
    p.add_argument("--retries", type=int, default=3)
    p.add_argument("--backoff", type=float, default=2.0)
    p.add_argument("--rate", type=float, default=1.0, help="seconds delay between requests")
    args = p.parse_args()
    main(args.input, args.retries, args.backoff, args.rate)
