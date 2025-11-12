#!/usr/bin/env python3
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse
import re

log = logging.getLogger(__name__)

class GovernmentScraper:
    def __init__(self):
        self.african_gov_domains = [
            {"country": "Nigeria", "domain": "nigeria.gov.ng", "type": "federal"},
            {"country": "Kenya", "domain": "go.ke", "type": "country_tld"},
            {"country": "South Africa", "domain": "gov.za", "type": "country_tld"},
            {"country": "Egypt", "domain": "gov.eg", "type": "country_tld"},
            {"country": "Morocco", "domain": "gov.ma", "type": "country_tld"},
            {"country": "Ghana", "domain": "gov.gh", "type": "country_tld"},
            {"country": "Algeria", "domain": "gov.dz", "type": "country_tld"},
            {"country": "Tunisia", "domain": "gov.tn", "type": "country_tld"},
            {"country": "Ethiopia", "domain": "gov.et", "type": "country_tld"},
            {"country": "Tanzania", "domain": "go.tz", "type": "country_tld"},
            {"country": "Uganda", "domain": "go.ug", "type": "country_tld"},
        ]
        
        self.security_keywords = [
            "defense", "security", "intelligence", "police", "military",
            "terrorism", "crime", "cybersecurity", "financial crime",
            "border", "immigration", "customs", "drug enforcement"
        ]
    
    def discover_agencies(self) -> List[Dict[str, Any]]:
        sources = []
        
        for gov in self.african_gov_domains:
            try:
                if gov["type"] == "country_tld":
                    found = self._scan_gov_domain(gov["domain"], gov["country"])
                    sources.extend(found)
                else:
                    found = self._scan_specific_agency(gov["domain"], gov["country"])
                    sources.extend(found)
            except Exception as e:
                log.warning(f"Failed to scan {gov['domain']}: {e}")
        
        return sources
    
    def _scan_gov_domain(self, domain_suffix: str, country: str) -> List[Dict[str, Any]]:
        sources = []
        
        security_agencies = [
            f"defense.{domain_suffix}",
            f"interior.{domain_suffix}",
            f"police.{domain_suffix}",
            f"intelligence.{domain_suffix}",
            f"security.{domain_suffix}",
            f"justice.{domain_suffix}",
            f"finance.{domain_suffix}",
            f"cybersecurity.{domain_suffix}"
        ]
        
        for agency_domain in security_agencies:
            try:
                url = f"https://{agency_domain}"
                resp = requests.head(url, timeout=5)
                if resp.status_code == 200:
                    feed_sources = self._find_gov_feeds(url, country, agency_domain)
                    sources.extend(feed_sources)
            except:
                pass
        
        return sources
    
    def _scan_specific_agency(self, domain: str, country: str) -> List[Dict[str, Any]]:
        return self._find_gov_feeds(f"https://{domain}", country, domain)
    
    def _find_gov_feeds(self, url: str, country: str, agency: str) -> List[Dict[str, Any]]:
        sources = []
        
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                return sources
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            rss_links = soup.find_all('link', type=lambda t: t and 'rss' in t.lower())
            atom_links = soup.find_all('link', type=lambda t: t and 'atom' in t.lower())
            
            for link in rss_links + atom_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(url, href)
                    if 'defense' in full_url or 'security' in full_url:
                        sources.append({
                            "url": full_url,
                            "title": f"RSS Feed - {agency}",
                            "source_type": "gov_rss",
                            "crime_type": "general",
                            "agency": agency,
                            "country": country
                        })
            
            sitemap_url = url.rstrip('/') + '/sitemap.xml'
            try:
                sitemap_resp = requests.get(sitemap_url, timeout=5)
                if sitemap_resp.status_code == 200:
                    sources.append({
                        "url": sitemap_url,
                        "title": f"Sitemap - {agency}",
                        "source_type": "gov_sitemap",
                        "crime_type": "general",
                        "agency": agency,
                        "country": country
                    })
            except:
                pass
                
        except Exception as e:
            log.warning(f"Cannot reach {url}: {e}")
        
        return sources

    def get_intelligence_reports(self) -> List[Dict[str, Any]]:
        documents = []
        
        intelligence_pages = [
            {"url": "https://www.cia.gov/readingroom/docs", "country": "USA", "type": "declassified"},
            {"url": "https://www.state.gov/jct/series/counterterrorism", "country": "USA", "type": "reports"},
        ]
        
        for page in intelligence_pages:
            try:
                docs = self._scrape_intelligence_page(page["url"], page["country"], page["type"])
                documents.extend(docs)
            except Exception as e:
                log.warning(f"Failed to scrape {page['url']}: {e}")
        
        return documents
    
    def _scrape_intelligence_page(self, url: str, country: str, doc_type: str) -> List[Dict[str, Any]]:
        documents = []
        
        try:
            resp = requests.get(url, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text().lower()
                
                if any(keyword in text for keyword in self.security_keywords + ["africa", "terrorism"]):
                    full_url = urljoin(url, href)
                    
                    if full_url.endswith(('.pdf', '.html', '.txt', '.doc')):
                        documents.append({
                            "url": full_url,
                            "title": link.get_text().strip(),
                            "country": country,
                            "type": doc_type,
                            "source_type": "intelligence_report"
                        })
        except Exception as e:
            log.error(f"Error scraping {url}: {e}")
        
        return documents
