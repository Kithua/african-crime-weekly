#!/usr/bin/env python3
"""
Feed Testing Script
Tests all multilingual feeds and reports which ones are working.

Usage:
    python scripts/test_feeds.py
    python scripts/test_feeds.py --limit 20  # Test first 20 feeds only
"""

import sys
import argparse
import requests
import feedparser
import yaml
from pathlib import Path
from urllib.parse import urlparse
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Create session with proper headers
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; ACW-FeedTester/1.0; +https://github.com/Kithua/african-crime-weekly)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
})

def test_feed(url: str, timeout: int = 15) -> dict:
    """
    Test a single feed URL and return detailed results.
    """
    result = {
        "url": url,
        "status": "unknown",
        "entries": 0,
        "error": None,
        "response_time": None,
        "content_type": None,
        "is_rss": False
    }
    
    start_time = time.time()
    
    try:
        # Try to fetch the URL
        resp = session.get(url, timeout=timeout)
        result["response_time"] = time.time() - start_time
        result["status"] = resp.status_code
        result["content_type"] = resp.headers.get("content-type", "")
        
        if resp.status_code == 200:
            # Parse as RSS
            feed = feedparser.parse(resp.text)
            
            if feed.bozo:  # Parsing error
                result["error"] = f"RSS Parse Error: {feed.bozo_exception}"
                result["status"] = "parse_error"
            else:
                result["entries"] = len(feed.entries)
                result["is_rss"] = True
                
                if feed.entries:
                    result["status"] = "success"
                    # Check publication dates
                    recent_entries = sum(1 for e in feed.entries 
                                       if hasattr(e, 'published_parsed') and e.published_parsed)
                    result["recent_entries"] = recent_entries
                else:
                    result["status"] = "empty"
        else:
            result["error"] = f"HTTP {resp.status_code}"
            
    except requests.exceptions.Timeout:
        result["status"] = "timeout"
        result["error"] = f"Timeout after {timeout}s"
    except requests.exceptions.ConnectionError as e:
        result["status"] = "connection_error"
        result["error"] = f"Connection failed: {str(e)}"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

def print_results(results: list, verbose: bool = False):
    """
    Print test results in a formatted way.
    """
    print("\n" + "="*80)
    print("FEED TEST RESULTS")
    print("="*80)
    
    # Summary statistics
    total = len(results)
    working = sum(1 for r in results if r["status"] == "success" and r["entries"] > 0)
    empty = sum(1 for r in results if r["status"] == "empty")
    failed = sum(1 for r in results if r["status"] in ["timeout", "connection_error", "error", "parse_error"])
    http_errors = sum(1 for r in results if str(r["status"]).startswith("4") or str(r["status"]).startswith("5"))
    
    print(f"\nTotal feeds tested: {total}")
    print(f"✅ Working feeds: {working}")
    print(f"⚠️  Empty feeds: {empty}")
    print(f"❌ Failed feeds: {failed + http_errors}")
    print(f"\nDetailed Results:")
    print("-"*80)
    
    for i, result in enumerate(results, 1):
        status_icon = {
            "success": "✅",
            "empty": "⚠️ ",
            "timeout": "⏱️ ",
            "connection_error": "🔌",
            "parse_error": "📄❌",
            "error": "❌"
        }.get(result["status"], "❓")
        
        domain = urlparse(result["url"]).netloc[:30]
        
        print(f"{i:3d}. {status_icon} {domain:30s} | ", end="")
        
        if result["status"] == "success":
            print(f"{result['entries']:3d} entries | {result['response_time']:.2f}s")
        elif result["status"] == "empty":
            print(f"No entries | {result['response_time']:.2f}s")
        else:
            print(f"Error: {result['error'][:50]}")
        
        if verbose and result["error"]:
            print(f"     {result['error']}")

def save_working_feeds(results: list, output_path: Path):
    """
    Save working feeds to a new YAML whitelist file.
    """
    working_feeds = []
    
    for result in results:
        if result["status"] == "success" and result["entries"] > 0:
            working_feeds.append({
                "url": result["url"],
                "tier": "B",  # Default tier
                "lang": "en"  # Default language
            })
    
    output_data = {"feeds": working_feeds}
    
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(output_data, f, default_flow_style=False, allow_unicode=True)
    
    print(f"\n💾 Saved {len(working_feeds)} working feeds to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Test multilingual RSS feeds")
    parser.add_argument("--limit", type=int, help="Limit number of feeds to test")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--save", type=Path, help="Save working feeds to YAML file")
    args = parser.parse_args()
    
    # Load whitelist
    whitelist_path = Path("data/whitelist_multilingual.yml")
    if not whitelist_path.exists():
        log.error(f"Whitelist file not found: {whitelist_path}")
        sys.exit(1)
    
    whitelist = yaml.safe_load(whitelist_path.read_text(encoding="utf-8"))
    feeds = whitelist.get("feeds", [])
    
    if args.limit:
        feeds = feeds[:args.limit]
    
    print(f"Testing {len(feeds)} feeds from {whitelist_path}")
    
    results = []
    for i, feed_info in enumerate(feeds, 1):
        url = feed_info["url"]
        print(f"Testing {i}/{len(feeds)}: {urlparse(url).netloc}...", end=" ", flush=True)
        
        result = test_feed(url)
        results.append(result)
        
        if result["status"] == "success":
            print(f"✓ ({result['entries']} entries)")
        else:
            print(f"✗ ({result['error']})")
        
        # Be polite: rate limit requests
        time.sleep(0.5)
    
    # Print summary
    print_results(results, verbose=args.verbose)
    
    # Save working feeds if requested
    if args.save:
        save_working_feeds(results, args.save)

if __name__ == "__main__":
    main()
