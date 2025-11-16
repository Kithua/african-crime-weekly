#!/usr/bin/env python3
"""
Government-reports collector stub
Returns an empty list so the pipeline never breaks.
Extend this file later to scrape real government PDFs.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any

log = logging.getLogger(__name__)

def collect_all(start: datetime, end: datetime) -> List[Dict[str, Any]]:
    log.info("Government-reports collector: stub – nothing to fetch yet.")
    return []
