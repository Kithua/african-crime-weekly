#!/usr/bin/env python3
"""
Automated Source Discovery Pipeline
Discovers and validates new intelligence sources across:
- News feeds
- Social media
- Dark web mentions
- Government domains
- Corporate registries
- Leak sites
"""

import os
import sys
import logging
import requests
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import urlparse
import yaml
from serpapi import GoogleSearch
from bs4 import BeautifulSoup
import tldextract
import json

from acquire.credibility import CredibilityScorer
from acquire.gov_scraper import GovernmentScraper
from acquire.opencorporates import CorporateDataCollector

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class AutoSourcePipeline:
    """Automated intelligence source discovery and validation"""
    
    def __init__(self, serpapi_key: str = None):
        self.serpapi_key = serpapi_key or os.getenv("SERPAPI_KEY")
        self.scorer = CredibilityScorer()
        self.gov_scraper = GovernmentScraper()
        self.corporate = CorporateDataCollector()
        
        # Intelligence search patterns
        self.search_patterns = {
            "terrorism": [
                "African terrorism news RSS feed",
                "extremist group monitoring Africa",
                "jihadist activity reports Africa",
                "counter-terrorism intelligence Africa"
            ],
            "organised": [
                "African organized crime news",
                "drug trafficking Africa RSS",
                "smuggling routes Africa",
                "transnational crime monitoring"
            ],
            "financial": [
                "African financial crime news",
                "money laundering Africa RSS",
                "cryptocurrency fraud Africa",
                "investment scam Africa"
            ],
            "cybercrime": [
                "African cybercrime news",
                "ransomware Africa RSS",
                "dark web Africa monitoring",
                "hacking groups Africa"
            ]
        }
        
        # Trusted base domains for seeding
        self.trusted_domains = {
            "news": ["bbc.com", "reuters.com", "apnews.com", "aljazeera.com", "africanews.com"],
            "security": ["icct.nl", "globalinitiative.net", "issafrica.org", "sant.ox.ac.uk"],
            "gov": [".gov", ".gouv", ".go.tz", ".go.ke", ".gov.ng", ".gov.za"],
            "financial": ["fatf-gafi.org", "worldbank.org", "imf.org"]
        }
        
    def run_daily_discovery(self):
        """Run complete discovery pipeline"""
        log.info("Starting daily source discovery...")
        
        # Phase 1: Discover potential sources
        discovered = []
        for crime_type, patterns in self.search_patterns.items():
            for pattern in patterns:
                log.info(f"Searching: {pattern}")
                sources = self.search_sources(pattern, crime_type)
                discovered.extend(sources)
        
        # Phase 2: Validate and score
        validated = []
        for source in discovered:
            try:
                result = self.validate_source(source)
                if result['is_valid']:
                    validated.append(result)
            except Exception as e:
                log.warning(f"Validation failed for {source.get('url')}: {e}")
        
        # Phase 3: Score credibility
        scored = []
        for source in validated:
            credibility = self.scorer.score_source(source)
            source['credibility'] = credibility
            scored.append(source)
        
        # Phase 4: Auto-add credible sources
        auto_added = self.update_whitelist(scored)
        
        # Phase 5: Discover government sources
        gov_sources = self.gov_scraper.discover_agencies()
        gov_validated = [self.validate_source(s) for s in gov_sources if self.validate_source(s)['is_valid']]
        
        log.info(f"Discovered {len(discovered)} sources")
        log.info(f"Validated {len(validated)} sources")
        log.info(f"Scored {len(scored)} sources")
        log.info(f"Auto-added {auto_added} sources to whitelist")
        log.info(f"Found {len(gov_validated)} government sources")
        
        return {
            'discovered': discovered,
            'validated': validated,
            'scored': scored,
            'auto_added': auto_added,
            'gov_sources': gov_validated
        }
    
    def search_sources(self, query: str, crime_type: str) -> List[Dict[str, Any]]:
        """Search for intelligence sources using multiple methods"""
        sources = []
        
        # Method 1: Google Search API
        if self.serpapi_key:
            try:
                google_sources = self._search_google(query, crime_type)
                sources.extend(google_sources)
            except Exception as e:
                log.warning(f"Google search failed: {e}")
        
        # Method 2: Direct domain enumeration
        domain_sources = self._enumerate_domains(crime_type)
        sources.extend(domain_sources)
        
        # Method 3: Dark web mention monitoring (via public indexes)
        dark_sources = self._monitor_darkweb_mentions(crime_type)
        sources.extend(dark_sources)
        
        # Remove duplicates
        seen_urls = set()
        unique_sources = []
        for s in sources:
            if s['url'] not in seen_urls:
                seen_urls.add(s['url'])
                unique_sources.append(s)
        
        return unique_sources
    
    def _search_google(self, query: str, crime_type: str) -> List[Dict[str, Any]]:
        """Search using SerpAPI"""
        sources = []
        
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.serpapi_key,
            "num": 20
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        for result in results.get("organic_results", []):
            url = result["link"]
            domain = urlparse(url).netloc
            
            # Skip blacklisted domains
            if self.scorer.is_blacklisted(domain):
                continue
            
            sources.append({
                "url": url,
                "title": result.get("title", ""),
                "description": result.get("snippet", ""),
                "source_type": "news",
                "crime_type": crime_type,
                "discovery_method": "google_search"
            })
        
        # Search for RSS feeds specifically
        params["q"] = query + " RSS feed"
        search = GoogleSearch(params)
        results = search.get_dict()
        
        for result in results.get("organic_results", []):
            if "rss" in result["link"].lower() or "feed" in result["link"].lower():
                sources.append({
                    "url": result["link"],
                    "title": result.get("title", ""),
                    "description": result.get("snippet", ""),
                    "source_type": "rss_feed",
                    "crime_type": crime_type,
                    "discovery_method": "google_rss_search"
                })
        
        return sources
    
    def _enumerate_domains(self, crime_type: str) -> List[Dict[str, Any]]:
        """Enumerate potential sources from trusted domains"""
        sources = []
        
        # Check for RSS feeds on trusted domains
        for domain in self.trusted_domains["news"]:
            rss_candidates = [
                f"https://{domain}/rss",
                f"https://{domain}/feed",
                f"https://{domain}/news/rss",
                f"https://{domain}/world/africa/rss"
            ]
            
            for url in rss_candidates:
                try:
                    resp = requests.head(url, timeout=5)
                    if resp.status_code == 200:
                        sources.append({
                            "url": url,
                            "title": f"RSS Feed - {domain}",
                            "source_type": "rss_feed",
                            "crime_type": crime_type,
                            "discovery_method": "domain_enumeration"
                        })
                except:
                    continue
        
        return sources
    
    def _monitor_darkweb_mentions(self, crime_type: str) -> List[Dict[str, Any]]:
        """Monitor public dark web indexes and security reports"""
        # Note: This uses publicly accessible security research, not direct Tor access
        # For direct Tor access, use collectors/darkweb.py instead
        
        sources = []
        
        # Public dark web monitoring services
        monitoring_sites = [
            "https://darknetdiaries.com",
            "https://krebsonsecurity.com",
            "https://therecord.media"
        ]
        
        for site in monitoring_sites:
            try:
                # Check if they have RSS feeds
                for feed_path in ["/rss", "/feed", "/feed.xml"]:
                    url = f"{site}{feed_path}"
                    resp = requests.head(url, timeout=5)
                    if resp.status_code == 200:
                        sources.append({
                            "url": url,
                            "title": f"Dark Web Monitor - {site}",
                            "source_type": "darkweb_monitor",
                            "crime_type": crime_type,
                            "discovery_method": "darkweb_index",
                            "tier": "C"  # Lower tier for indirect sources
                        })
            except:
                continue
        
        return sources
    
    def validate_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """Validate if a source is working and accessible"""
        url = source["url"]
        domain = urlparse(url).netloc
        
        result = {
            "url": url,
            "domain": domain,
            "is_valid": False,
            "error": None,
            "response_time": None,
            "has_recent_content": False,
            "content_sample": None
        }
        
        try:
            # Test accessibility
            start = time.time()
            resp = requests.get(
                url,
                timeout=15,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; ACW-Discovery/1.0)"
                }
            )
            result["response_time"] = time.time() - start
            
            if resp.status_code != 200:
                result["error"] = f"HTTP {resp.status_code}"
                return result
            
            # Test if it's actually an RSS feed
            if source.get("source_type") == "rss_feed":
                feed = feedparser.parse(resp.text)
                if feed.bozo:
                    result["error"] = f"Not valid RSS: {feed.bozo_exception}"
                    return result
                
                # Check for recent content
                recent_entries = 0
                for entry in feed.entries[:10]:
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        # Check if entry is from last 30 days
                        from datetime import datetime
                        entry_date = datetime(*entry.published_parsed[:6])
                        days_old = (datetime.now() - entry_date).days
                        if days_old <= 30:
                            recent_entries += 1
                
                result["has_recent_content"] = recent_entries > 0
                result["entries_count"] = len(feed.entries)
                
                # Grab content sample
                if feed.entries and hasattr(feed.entries[0], "title"):
                    result["content_sample"] = {
                        "title": feed.entries[0].title,
                        "summary": getattr(feed.entries[0], "summary", "")[:200]
                    }
            
            result["is_valid"] = True
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def update_whitelist(self, scored_sources: List[Dict[str, Any]]) -> int:
        """Auto-add credible sources to whitelist"""
        added_count = 0
        
        # Load existing whitelist
        whitelist_path = Path("data/whitelist_multilingual.yml")
        if whitelist_path.exists():
            whitelist = yaml.safe_load(whitelist_path.read_text()) or {"feeds": []}
        else:
            whitelist = {"feeds": []}
        
        existing_urls = {feed["url"] for feed in whitelist["feeds"]}
        
        # Add sources with credibility >= 0.7
        for source in scored_sources:
            cred = source.get("credibility", {})
            if cred.get("overall_score", 0) >= 0.7 and source["url"] not in existing_urls:
                whitelist["feeds"].append({
                    "url": source["url"],
                    "lang": source.get("lang", "en"),
                    "tier": "B",
                    "crime_type": source.get("crime_type", "general"),
                    "credibility_score": cred.get("overall_score"),
                    "auto_added": True,
                    "discovery_date": datetime.now().isoformat()
                })
                added_count += 1
                log.info(f"Auto-added: {source['url']}")
        
        # Save updated whitelist
        whitelist_path.write_text(yaml.dump(whitelist, default_flow_style=False))
        
        return added_count

if __name__ == "__main__":
    # Test the pipeline
    pipeline = AutoSourcePipeline()
    results = pipeline.run_daily_discovery()
    
    # Save discovery results
    output_path = Path("data/discovery_results.json")
    output_path.write_text(json.dumps(results, indent=2))
    log.info(f"Discovery results saved to {output_path}")
