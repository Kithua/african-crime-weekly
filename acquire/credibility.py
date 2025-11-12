#!/usr/bin/env python3
import re
import logging
from typing import Dict, Any, List
from urllib.parse import urlparse
import tldextract
import requests
from datetime import datetime
import yaml
from pathlib import Path

log = logging.getLogger(__name__)

class CredibilityScorer:
    def __init__(self):
        self.blacklist_path = Path("data/blacklist.yml")
        self.blacklist = self._load_blacklist()
        self.cached_scores = {}
        
        self.trusted_domains = {
            "high": ["bbc.com", "reuters.com", "apnews.com", "aljazeera.com", 
                     "guardian.com", "nytimes.com", "washingtonpost.com", "africanews.com"],
            "medium": ["allafrica.com", "irinnews.org", "thedefensepost.com", 
                       "janes.com", "defenseone.com", "bellingcat.com"],
            "gov": [".gov", ".gouv", ".go.tz", ".go.ke", ".gov.ng", ".gov.za", 
                    ".gov.eg", ".gov.ma", ".gov.gh"]
        }
        
        self.suspicious_keywords = [
            "stream", "movie", "casino", "poker", "betting", "gambling",
            "viagra", "cialis", "pharma", "porn", "xxx", "naked",
            "conspiracy", "illuminati", "fake news", "satire", "parody"
        ]
    
    def _load_blacklist(self) -> Dict[str, List[str]]:
        if self.blacklist_path.exists():
            return yaml.safe_load(self.blacklist_path.read_text()) or {}
        return {"domains": [], "ips": [], "patterns": []}
    
    def score_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        domain = urlparse(source["url"]).netloc
        
        if domain in self.cached_scores:
            return self.cached_scores[domain]
        
        scores = {
            "domain_reputation": self._score_domain_reputation(domain),
            "freshness": self._score_freshness(source),
            "content_quality": self._score_content_quality(source),
            "geographic_alignment": self._score_geographic_alignment(source),
            "technical_trust": self._score_technical_trust(domain),
            "historical_performance": self._score_historical_performance(domain)
        }
        
        weights = {
            "domain_reputation": 0.25,
            "freshness": 0.20,
            "content_quality": 0.20,
            "geographic_alignment": 0.15,
            "technical_trust": 0.10,
            "historical_performance": 0.10
        }
        
        overall_score = sum(scores[k] * weights[k] for k in scores)
        
        result = {
            "overall_score": overall_score,
            "component_scores": scores,
            "tier": self.tier_from_score(overall_score),
            "risk_factors": self._identify_risk_factors(source)
        }
        
        self.cached_scores[domain] = result
        return result
    
    def tier_from_score(self, score: float) -> str:
        if score >= 0.8:
            return "A"
        elif score >= 0.6:
            return "B"
        elif score >= 0.4:
            return "C"
        else:
            return "D"
    
    def is_blacklisted(self, domain: str) -> bool:
        extracted = tldextract.extract(domain)
        root_domain = f"{extracted.domain}.{extracted.suffix}"
        
        if root_domain in self.blacklist.get("domains", []):
            return True
        
        for pattern in self.blacklist.get("patterns", []):
            if re.search(pattern, domain, re.IGNORECASE):
                return True
        
        return False
    
    def _score_domain_reputation(self, domain: str) -> float:
        extracted = tldextract.extract(domain)
        root_domain = f"{extracted.domain}.{extracted.suffix}"
        
        if root_domain in self.trusted_domains["high"]:
            return 1.0
        
        for gov_domain in self.trusted_domains["gov"]:
            if gov_domain in domain:
                return 0.95
        
        if root_domain in self.trusted_domains["medium"]:
            return 0.75
        
        for keyword in self.suspicious_keywords:
            if keyword in domain.lower():
                return 0.1
        
        return 0.5
    
    def _score_freshness(self, source: Dict[str, Any]) -> float:
        sample = source.get("content_sample")
        if not sample:
            return 0.5
        
        if "published_parsed" in source:
            try:
                pub_date = datetime(*source["published_parsed"][:6])
                days_old = (datetime.now() - pub_date).days
                
                if days_old <= 1:
                    return 1.0
                elif days_old <= 7:
                    return 0.8
                elif days_old <= 30:
                    return 0.6
                else:
                    return 0.3
            except:
                pass
        
        return 0.5
    
    def _score_content_quality(self, source: Dict[str, Any]) -> float:
        sample = source.get("content_sample")
        if not sample or not sample.get("title"):
            return 0.3
        
        title = sample["title"]
        summary = sample.get("summary", "")
        
        title_length = len(title.split())
        if title_length < 3:
            return 0.2
        elif title_length > 10:
            return 0.8
        
        has_keywords = any(kw in title.lower() for kw in ["terror", "attack", "crime", "fraud"])
        if has_keywords:
            return 0.7
        
        return 0.5
    
    def _score_geographic_alignment(self, source: Dict[str, Any]) -> float:
        domain = urlparse(source["url"]).netloc
        
        africa_indicators = [
            "africa", "afrique", "afrik", "afri", "afric",
            "kenya", "nigeria", "egypt", "south africa", "ghana",
            "morocco", "algeria", "tunisia", "libya", "somalia",
            "ethiopia", "sudan", "senegal", "ivory coast", "cameroon"
        ]
        
        for indicator in africa_indicators:
            if indicator in domain.lower():
                return 1.0
        
        sample = source.get("content_sample", {})
        text = (sample.get("title", "") + " " + sample.get("summary", "")).lower()
        
        africa_countries = [
            "kenya", "nigeria", "egypt", "south africa", "ghana", "morocco",
            "algeria", "tunisia", "libya", "somalia", "ethiopia", "sudan",
            "senegal", "ivory coast", "cameroon", "angola", "zimbabwe", "zambia"
        ]
        
        mentions = sum(1 for country in africa_countries if country in text)
        
        if mentions >= 3:
            return 0.9
        elif mentions >= 1:
            return 0.7
        
        return 0.4
    
    def _score_technical_trust(self, domain: str) -> float:
        try:
            resp = requests.head(f"https://{domain}", timeout=5)
            if resp.status_code == 200:
                return 0.8
        except:
            pass
        
        try:
            resp = requests.head(f"http://{domain}", timeout=5)
            if resp.status_code == 200:
                return 0.6
        except:
            pass
        
        return 0.2
    
    def _score_historical_performance(self, domain: str) -> float:
        cache_path = Path("data/credibility_cache.json")
        if cache_path.exists():
            cache = json.loads(cache_path.read_text())
            if domain in cache:
                last_score = cache[domain].get("last_score", 0.5)
                return last_score
        
        return 0.5
    
    def _identify_risk_factors(self, source: Dict[str, Any]) -> List[str]:
        risks = []
        domain = urlparse(source["url"]).netloc
        
        if "https" not in source["url"]:
            risks.append("no_https")
        
        if len(domain.split(".")) > 3:
            risks.append("subdomain_heavy")
        
        sample = source.get("content_sample", {})
        if sample:
            text = sample.get("title", "") + sample.get("summary", "")
            if len(text) < 100:
                risks.append("very_short_content")
        
        for keyword in self.suspicious_keywords:
            if keyword in domain.lower():
                risks.append(f"suspicious_keyword:{keyword}")
                break
        
        return risks
    
    def save_cache(self):
        cache_path = Path("data/credibility_cache.json")
        cache_path.parent.mkdir(exist_ok=True)
        cache_path.write_text(json.dumps(self.cached_scores, indent=2))

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True, help="Input whitelist file")
    parser.add_argument("--output", type=Path, required=True, help="Output directory for tiered whitelists")
    args = parser.parse_args()
    
    sources = yaml.safe_load(args.input.read_text())
    
    scorer = CredibilityScorer()
    results = []
    
    for source in sources['feeds']:
        score = scorer.score_source(source)
        results.append({
            'source': source,
            'score': score,
            'tier': scorer.tier_from_score(score['overall_score'])
        })
    
    print("\nCredibility Scoring Results:")
    print("=" * 50)
    
    for result in results:
        source = result['source']
        tier = result['tier']
        score = result['score']['overall_score']
        print(f"{tier:3s} | {score:.2f} | {source['url']}")
    
    for tier in ['A', 'B', 'C']:
        tier_sources = [
            r['source'] for r in results 
            if r['tier'] == tier
        ]
        
        output_file = args.output.parent / f"whitelist_tier_{tier.lower()}.yml"
        output_file.write_text(yaml.dump({'feeds': tier_sources}))
        print(f"Saved {len(tier_sources)} tier {tier} sources to {output_file}")
    
    scorer.save_cache()

if __name__ == "__main__":
    main()
