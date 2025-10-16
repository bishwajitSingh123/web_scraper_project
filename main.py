# main.py
import argparse
import pandas as pd
from fetcher import fetch_with_retries

def main(input_csv: str, retries: int, backoff: float, rate: float):
    df = pd.read_csv(input_csv)
    urls = df['url'].dropna().unique().tolist()
    print(f"Found {len(urls)} unique URLs. Starting downloads...")
    for i, url in enumerate(urls, start=1):
        print(f"[{i}/{len(urls)}] Fetching: {url}")
        fetch_with_retries(url, retries=retries, backoff=backoff, rate_delay=rate)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", "-i", default="company_urls.csv", help="CSV with column 'url'")
    p.add_argument("--retries", type=int, default=3)
    p.add_argument("--backoff", type=float, default=2.0)
    p.add_argument("--rate", type=float, default=1.0, help="seconds delay between requests")
    args = p.parse_args()
    main(args.input, args.retries, args.backoff, args.rate)
