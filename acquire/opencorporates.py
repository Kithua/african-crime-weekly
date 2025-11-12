#!/usr/bin/env python3
import logging
import requests
from typing import List, Dict, Any
from datetime import datetime

log = logging.getLogger(__name__)

class CorporateDataCollector:
    def __init__(self):
        self.sources = {
            "opencorporates": "https://api.opencorporates.com",
            "african_registries": [
                {"country": "Nigeria", "url": "https://search.cac.gov.ng", "type": "company_registry"},
                {"country": "Kenya", "url": "https://e-citizen.go.ke", "type": "company_registry"},
                {"country": "South Africa", "url": "https://bizportal.gov.za", "type": "company_registry"},
                {"country": "Ghana", "url": "https://rgd.gov.gh", "type": "company_registry"},
            ]
        }
        
        self.suspicious_indicators = [
            "shell company", "offshore", "tax haven", "nominee director",
            "bearer shares", "complex ownership", "circular ownership",
            "recently incorporated", "no physical address", "virtual office"
        ]
    
    def fetch_registry_data(self, company_name: str = None, country: str = None) -> List[Dict[str, Any]]:
        results = []
        
        for registry in self.sources["african_registries"]:
            if country and country.lower() != registry["country"].lower():
                continue
            
            try:
                if registry["country"] == "Nigeria":
                    data = self._fetch_nigeria_cac(company_name)
                    results.extend(data)
                elif registry["country"] == "South Africa":
                    data = self._fetch_south_africa_cipc(company_name)
                    results.extend(data)
            except Exception as e:
                log.warning(f"Failed to fetch from {registry['country']}: {e}")
        
        return results
    
    def _fetch_nigeria_cac(self, company_name: str) -> List[Dict[str, Any]]:
        companies = []
        
        try:
            search_url = f"{self.sources['african_registries'][0]['url']}/search"
            params = {"q": company_name} if company_name else {}
            
            response = requests.get(search_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for company in data.get("results", [])[:10]:
                    company_data = {
                        "name": company.get("name"),
                        "registration_number": company.get("rc_number"),
                        "incorporation_date": company.get("incorporation_date"),
                        "address": company.get("address"),
                        "status": company.get("status"),
                        "country": "Nigeria",
                        "source": "CAC",
                        "suspicious_indicators": self._check_suspicious_indicators(company)
                    }
                    companies.append(company_data)
        
        except Exception as e:
            log.error(f"Error fetching Nigeria CAC data: {e}")
        
        return companies
    
    def _fetch_south_africa_cipc(self, company_name: str) -> List[Dict[str, Any]]:
        companies = []
        
        try:
            search_url = f"{self.sources['african_registries'][2]['url']}/search"
            params = {"companyName": company_name} if company_name else {}
            
            response = requests.get(search_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for company in data.get("companies", [])[:10]:
                    company_data = {
                        "name": company.get("entityName"),
                        "registration_number": company.get("registrationNumber"),
                        "incorporation_date": company.get("incorporationDate"),
                        "address": company.get("physicalAddress"),
                        "status": company.get("status"),
                        "country": "South Africa",
                        "source": "CIPC",
                        "suspicious_indicators": self._check_suspicious_indicators(company)
                    }
                    companies.append(company_data)
        
        except Exception as e:
            log.error(f"Error fetching South Africa CIPC data: {e}")
        
        return companies
    
    def _check_suspicious_indicators(self, company_data: Dict[str, Any]) -> List[str]:
        indicators = []
        
        for indicator in self.suspicious_indicators:
            company_str = str(company_data).lower()
            if indicator.lower() in company_str:
                indicators.append(indicator)
        
        incorporation_date = company_data.get("incorporation_date")
        if incorporation_date:
            try:
                date_obj = datetime.strptime(incorporation_date, "%Y-%m-%d")
                days_since_incorporation = (datetime.now() - date_obj).days
                
                if days_since_incorporation < 90:
                    indicators.append("recently incorporated")
            except:
                pass
        
        return indicators
    
    def monitor_suspicious_companies(self) -> List[Dict[str, Any]]:
        alerts = []
        
        suspicious_names = [
            "offshore", "consulting", "services", "global", "international",
            "investment", "trading", "enterprise", "solutions", "partners"
        ]
        
        for registry in self.sources["african_registries"]:
            try:
                companies = self.fetch_registry_data(None, registry["country"])
                
                for company in companies:
                    if company["suspicious_indicators"]:
                        alerts.append({
                            "company": company,
                            "risk_level": "high" if len(company["suspicious_indicators"]) > 3 else "medium",
                            "detected_date": datetime.now().isoformat()
                        })
            except Exception as e:
                log.warning(f"Failed to monitor {registry['country']}: {e}")
        
        return alerts
