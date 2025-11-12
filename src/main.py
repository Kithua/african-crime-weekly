#!/usr/bin/env python3
"""
African Crime Weekly - Main Orchestration Script
Coordinates collection, analysis, and reporting of crime intelligence across Africa.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# CRITICAL FIX: Import the weekly fusion module
from src.analyst import weekly_fusion_intel_style
from src.collectors import rss, telegram, api_sportal, multilingual
from src.nlp import geotag, dedup, classifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger("ACW")

def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime object."""
    return datetime.strptime(date_str, "%Y-%m-%d")

def main():
    """Main execution pipeline"""
    parser = argparse.ArgumentParser(
        description="African Crime Weekly - Intelligence Collection Pipeline"
    )
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        default="configs/weekly.yml",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--start",
        type=str,
        help="Start date (YYYY-MM-DD). Defaults to 7 days ago."
    )
    
    parser.add_argument(
        "--end",
        type=str,
        help="End date (YYYY-MM-DD). Defaults to today."
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output bundle file path"
    )
    
    parser.add_argument(
        "--cache",
        type=str,
        default="data/cache",
        help="Cache directory path"
    )
    
    parser.add_argument(
        "--auto-discover",
        action="store_true",
        help="Run automated source discovery"
    )
    
    parser.add_argument(
        "--test-feeds",
        action="store_true",
        help="Test all feeds and exit"
    )
    
    args = parser.parse_args()
    
    # Set default dates if not provided
    if not args.start:
        args.start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    if not args.end:
        args.end = datetime.now().strftime("%Y-%m-%d")
    
    # Set default output if not provided
    if not args.output:
        week_str = datetime.now().strftime("%G-W%V")
        args.output = f"data/weekly/{week_str}.json"
    
    log.info(f"Weekly bundle → {args.output}")
    
    # Run feed test if requested
    if args.test_feeds:
        log.info("Running feed test mode...")
        from scripts.test_feeds import main as test_main
        sys.argv = ["test_feeds.py", "--verbose"]
        test_main()
        return
    
    # Auto-discover new sources if requested
    if args.auto_discover:
        log.info("Running automated source discovery...")
        try:
            from acquire.pipeline import AutoSourcePipeline
            pipeline = AutoSourcePipeline(serpapi_key=os.getenv("SERPAPI_KEY"))
            pipeline.run_daily_discovery()
        except ImportError:
            log.warning("Acquire module not found. Skipping auto-discovery.")
        except Exception as e:
            log.error(f"Auto-discovery failed: {e}")
    
    # Run collection phase
    log.info("=== COLLECTION PHASE ===")
    articles = []
    
    # Collect from multilingual sources
    log.info("Collect RSS")
    articles.extend(rss.collect(parse_date(args.start), parse_date(args.end)))
    
    # Collect from Telegram
    log.info("Collect Telegram")
    try:
        articles.extend(telegram.collect(parse_date(args.start), parse_date(args.end)))
    except Exception as e:
        log.warning(f"Telegram collection failed: {e}")
    
    # Collect from Sentinel ICF API
    log.info("Collect Sentinel ICF")
    try:
        articles.extend(api_sportal.collect(parse_date(args.start), parse_date(args.end)))
    except Exception as e:
        log.warning(f"Sentinel ICF collection failed: {e}")
    
    # Collect from multilingual sources
    log.info("Collect multilingual")
    try:
        articles.extend(multilingual.collect(parse_date(args.start), parse_date(args.end)))
    except Exception as e:
        log.warning(f"Multilingual collection failed: {e}")
    
    log.info(f"Total articles collected: {len(articles)}")
    
    if not articles:
        log.error("No articles collected. Exiting.")
        sys.exit(1)
    
    # Run NLP processing phase
    log.info("=== NLP PROCESSING PHASE ===")
    log.info("Deduplication")
    articles = dedup.remove_duplicates(articles)
    
    log.info(f"After deduplication: {len(articles)} articles")
    
    log.info("Classification & Geotagging")
    for article in articles:
        # Classify crime type
        article["crime_tags"] = classifier.predict(article.get("body_en", ""))
        
        # Extract geolocation
        article["geo"] = geotag.extract(article)
        
        # Calculate confidence score
        article["confidence"] = classifier.confidence(article)
    
    # Build crime buckets
    log.info("=== BUCKETING PHASE ===")
    buckets = {
        "terrorism": [],
        "organised": [],
        "financial": [],
        "cyber": []
    }
    
    for article in articles:
        tags = article.get("crime_tags", [])
        if "terrorism" in tags:
            buckets["terrorism"].append(article)
        if "organised" in tags:
            buckets["organised"].append(article)
        if "financial" in tags:
            buckets["financial"].append(article)
        if "cyber" in tags:
            buckets["cyber"].append(article)
    
    log.info(f"Terrorism: {len(buckets['terrorism'])} | Organised: {len(buckets['organised'])} | "
             f"Financial: {len(buckets['financial'])} | Cyber: {len(buckets['cyber'])}")
    
    # Generate report using weekly_fusion_intel_style
    log.info("=== REPORT GENERATION PHASE ===")
    try:
        report_html = weekly_fusion_intel_style.build(
            terrorism_bucket=buckets["terrorism"],
            organised_bucket=buckets["organised"],
            financial_bucket=buckets["financial"],
            cyber_bucket=buckets["cyber"],
            start=parse_date(args.start),
            end=parse_date(args.end)
        )
        
        # Save HTML report
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        html_output = output_path.with_suffix('.html')
        html_output.write_text(report_html, encoding='utf-8')
        
        log.info(f"HTML report saved to {html_output}")
        
        # Optionally generate PDF (requires weasyprint)
        try:
            from weasyprint import HTML
            pdf_output = output_path.with_suffix('.pdf')
            HTML(string=report_html).write_pdf(pdf_output)
            log.info(f"PDF report saved to {pdf_output}")
        except ImportError:
            log.warning("weasyprint not installed. PDF generation skipped.")
        
    except Exception as e:
        log.error(f"Report generation failed: {e}")
        log.error("Falling back to legacy weekly_fusion...")
        # Fallback to legacy if needed
        from src.analyst import weekly_fusion
        weekly_fusion.main()

if __name__ == "__main__":
    main()
