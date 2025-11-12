#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from acquire.pipeline import AutoSourcePipeline
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="ACW Automated Source Discovery")
    parser.add_argument("--serpapi-key", required=True, help="SerpAPI key for Google searches")
    parser.add_argument("--dry-run", action="store_true", help="Run discovery without updating whitelist")
    parser.add_argument("--output", type=Path, help="Save discovery results to JSON file")
    args = parser.parse_args()

    log.info("Starting ACW source discovery...")
    
    pipeline = AutoSourcePipeline(serpapi_key=args.serpapi_key)
    results = pipeline.run_daily_discovery()

    if args.output:
        args.output.write_text(str(results))
        log.info(f"Results saved to {args.output}")

    log.info("Discovery complete!")

if __name__ == "__main__":
    main()
