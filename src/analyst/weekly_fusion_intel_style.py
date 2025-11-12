"""
Weekly Fusion Intel Style Report Generator
Takes pre-classified article buckets and generates an intelligence-style PDF report.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Import NLP modules
from src.nlp import dedup, classifier, geotag

logger = logging.getLogger(__name__)

def build(
    terrorism_bucket: List[Dict[str, Any]],
    organised_bucket: List[Dict[str, Any]],
    financial_bucket: List[Dict[str, Any]],
    cyber_bucket: List[Dict[str, Any]],
    start: datetime,
    end: datetime
) -> str:
    """
    Generate weekly fusion intelligence-style report from classified article buckets.
    
    Args:
        terrorism_bucket: Articles classified as terrorism-related
        organised_bucket: Articles classified as organised crime
        financial_bucket: Articles classified as financial crime
        cyber_bucket: Articles classified as cybercrime
        start: Start datetime for the report period
        end: End datetime for the report period
    
    Returns:
        HTML string of the generated report
    """
    
    logger.info(f"Building weekly fusion report for {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
    
    # Combine all articles
    all_articles = []
    all_articles.extend(terrorism_bucket)
    all_articles.extend(organised_bucket)
    all_articles.extend(financial_bucket)
    all_articles.extend(cyber_bucket)
    
    logger.info(f"Total articles collected: {len(all_articles)}")
    
    # Remove duplicates
    articles = dedup.remove_duplicates(all_articles)
    logger.info(f"After deduplication: {len(articles)} articles")
    
    # Process through NLP pipeline
    for article in articles:
        # Predict crime tags
        article["crime_tags"] = classifier.predict(article.get("body_en", ""))
        
        # Extract geolocation
        article["geo"] = geotag.extract(article)
        
        # Get confidence score
        article["confidence"] = classifier.confidence(article)
    
    # Build report data structure
    report_data = {
        "period": {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "week_str": start.strftime('%Y-W%U')
        },
        "pillars": {
            "terrorism": terrorism_bucket,
            "organised": organised_bucket,
            "financial": financial_bucket,
            "cyber": cyber_bucket
        },
        "all_articles": articles,
        "summary": {
            "total_articles": len(articles),
            "terrorism_count": len(terrorism_bucket),
            "organised_count": len(organised_bucket),
            "financial_count": len(financial_bucket),
            "cyber_count": len(cyber_bucket)
        },
        "top_articles": sorted(articles, key=lambda x: x.get("confidence", 0), reverse=True)[:10]
    }
    
    # Generate HTML report
    html_report = generate_html_report(report_data)
    
    # Also save to JSON for archival
    save_weekly_bundle(report_data)
    
    return html_report

def generate_html_report(data: Dict[str, Any]) -> str:
    """
    Generate HTML report from report data.
    """
    
    # Calculate credibility matrix
    matrix = build_credibility_matrix(data["all_articles"])
    
    # HTML Template (Intelligence Style)
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>African Crime Weekly - {week_str}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                background: #f5f5f5;
            }}
            .header {{
                background: #2c3e50;
                color: white;
                padding: 20px;
                text-align: center;
                margin-bottom: 30px;
            }}
            .classification {{
                background: #c0392b;
                color: white;
                padding: 5px 15px;
                font-weight: bold;
                text-align: center;
                margin: 10px 0;
            }}
            .section {{
                background: white;
                padding: 20px;
                margin-bottom: 20px;
                border-left: 5px solid #3498db;
            }}
            .pillar {{
                margin-bottom: 30px;
            }}
            .article {{
                border-bottom: 1px solid #eee;
                padding: 15px 0;
            }}
            .article:last-child {{
                border-bottom: none;
            }}
            .meta {{
                font-size: 0.9em;
                color: #666;
                margin-top: 5px;
            }}
            .confidence {{
                display: inline-block;
                padding: 3px 8px;
                background: #27ae60;
                color: white;
                border-radius: 3px;
                font-size: 0.8em;
                margin-left: 10px;
            }}
            .matrix {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 10px;
                margin: 20px 0;
            }}
            .matrix-cell {{
                background: #ecf0f1;
                padding: 15px;
                text-align: center;
            }}
            .matrix-header {{
                font-weight: bold;
                background: #34495e;
                color: white;
            }}
            .footer {{
                text-align: center;
                margin-top: 40px;
                font-size: 0.9em;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="classification">UNCLASSIFIED // FOR OFFICIAL USE ONLY</div>
        
        <div class="header">
            <h1>AFRICAN CRIME WEEKLY</h1>
            <h2>Period: {period_start} to {period_end}</h2>
            <h3>Report {week_str}</h3>
        </div>
        
        <div class="section">
            <h2>Executive Summary</h2>
            <p>Total Articles Analyzed: <strong>{total_articles}</strong></p>
            <ul>
                <li>Terrorism & Extremism: {terrorism_count} articles</li>
                <li>Organised Crime: {organised_count} articles</li>
                <li>Financial Crime: {financial_count} articles</li>
                <li>Cybercrime: {cyber_count} articles</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>Credibility Matrix</h2>
            <div class="matrix">
                <div class="matrix-cell matrix-header">Source Grade →</div>
                <div class="matrix-cell matrix-header">A (Official)</div>
                <div class="matrix-cell matrix-header">B (Vetted Media)</div>
                <div class="matrix-cell matrix-header">C (NGO/Other)</div>
                
                <div class="matrix-cell matrix-header">↓ Confidence</div>
                {matrix_cells}
            </div>
        </div>
        
        <div class="section">
            <h2>Top Priority Items</h2>
            {top_articles}
        </div>
        
        <div class="section">
            <h2>Terrorism & Extremism</h2>
            {terrorism_section}
        </div>
        
        <div class="section">
            <h2>Organised Crime</h2>
            {organised_section}
        </div>
        
        <div class="section">
            <h2>Financial Crime</h2>
            {financial_section}
        </div>
        
        <div class="section">
            <h2>Cybercrime</h2>
            {cyber_section}
        </div>
        
        <div class="footer">
            <p>Generated: {generation_time}</p>
            <p>African Crime Weekly Intelligence Fusion System</p>
        </div>
    </body>
    </html>
    """
    
    # Format sections
    def format_article(article):
        confidence = article.get("confidence", 0)
        geo = article.get("geo", {})
        location = f"{geo.get('city', '')}, {geo.get('country', '')}" if geo else "Unknown"
        
        return f"""
        <div class="article">
            <h3>{article.get("title", "No Title")} 
                <span class="confidence">{confidence:.1f}%</span>
            </h3>
            <p>{article.get("summary", "")}</p>
            <div class="meta">
                Source: {article.get("source", "Unknown")} | 
                Location: {location} | 
                Published: {article.get("date", "Unknown")}
            </div>
        </div>
        """
    
    # Build matrix cells
    matrix_html = ""
    for confidence_level in ["Confirmed", "Probable", "Possible", "Doubtful"]:
        matrix_html += f'<div class="matrix-cell matrix-header">{confidence_level}</div>'
        for grade in ["A", "B", "C", "D"]:
            count = matrix.get(grade, {}).get(confidence_level, 0)
            matrix_html += f'<div class="matrix-cell">{count}</div>'
    
    # Build sections
    top_articles_html = "".join(format_article(a) for a in data["top_articles"])
    
    terrorism_html = "".join(format_article(a) for a in data["pillars"]["terrorism"])
    organised_html = "".join(format_article(a) for a in data["pillars"]["organised"])
    financial_html = "".join(format_article(a) for a in data["pillars"]["financial"])
    cyber_html = "".join(format_article(a) for a in data["pillars"]["cyber"])
    
    # Fill template
    html = html_template.format(
        week_str=data["period"]["week_str"],
        period_start=data["period"]["start"][:10],
        period_end=data["period"]["end"][:10],
        total_articles=data["summary"]["total_articles"],
        terrorism_count=data["summary"]["terrorism_count"],
        organised_count=data["summary"]["organised_count"],
        financial_count=data["summary"]["financial_count"],
        cyber_count=data["summary"]["cyber_count"],
        matrix_cells=matrix_html,
        top_articles=top_articles_html,
        terrorism_section=terrorism_html or "<p>No items this week.</p>",
        organised_section=organised_html or "<p>No items this week.</p>",
        financial_section=financial_html or "<p>No items this week.</p>",
        cyber_section=cyber_html or "<p>No items this week.</p>",
        generation_time=datetime.utcnow().isoformat()
    )
    
    return html

def build_credibility_matrix(articles: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """
    Build 4x4 credibility matrix (Grades A-D x Confidence levels).
    """
    matrix = {
        "A": {"Confirmed": 0, "Probable": 0, "Possible": 0, "Doubtful": 0},
        "B": {"Confirmed": 0, "Probable": 0, "Possible": 0, "Doubtful": 0},
        "C": {"Confirmed": 0, "Probable": 0, "Possible": 0, "Doubtful": 0},
        "D": {"Confirmed": 0, "Probable": 0, "Possible": 0, "Doubtful": 0}
    }
    
    # Map numeric confidence to textual levels
    def confidence_to_level(confidence: float) -> str:
        if confidence >= 0.8:
            return "Confirmed"
        elif confidence >= 0.6:
            return "Probable"
        elif confidence >= 0.4:
            return "Possible"
        else:
            return "Doubtful"
    
    for article in articles:
        grade = article.get("source_grade", "C")  # Default to C if not graded
        confidence = article.get("confidence", 0)
        level = confidence_to_level(confidence)
        
        if grade in matrix:
            matrix[grade][level] += 1
    
    return matrix

def save_weekly_bundle(data: Dict[str, Any]):
    """
    Save weekly data to JSON file for archival.
    """
    week_str = data["period"]["week_str"]
    output_dir = Path("data/weekly")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"{week_str}.json"
    
    # Convert datetime objects to strings for JSON serialization
    def json_serial(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=json_serial, ensure_ascii=False)
    
    logger.info(f"Saved weekly bundle to {output_file}")
