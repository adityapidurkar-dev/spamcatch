"""
Spamerno - URL Analysis Module
Extracts URLs and performs risk assessment with domain reputation checking.
"""

import re
import requests
from urllib.parse import urlparse


# Known URL shortener domains
SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd",
    "buff.ly", "short.to", "adf.ly", "tiny.cc", "lnkd.in", "db.tt",
    "qr.ae", "rebrand.ly", "bl.ink", "shorturl.at", "cutt.ly"
}

# Suspicious top-level domains
SUSPICIOUS_TLDS = {
    ".xyz", ".tk", ".ml", ".ga", ".cf", ".gq", ".ru", ".cn", ".top",
    ".buzz", ".club", ".work", ".date", ".racing", ".win", ".bid",
    ".stream", ".download", ".cricket", ".science", ".party"
}

# Phishing-related keywords
PHISHING_WORDS = {
    "login", "verify", "secure", "account", "update", "confirm",
    "password", "signin", "banking", "paypal", "billing", "suspend"
}


def extract_urls(text):
    """
    Extract all URLs from text using regex.

    Args:
        text (str): Input text

    Returns:
        list: List of extracted URL strings
    """
    if not isinstance(text, str):
        return []

    url_pattern = r'https?://[^\s<>\"\')\],;]+'
    urls = re.findall(url_pattern, text, re.IGNORECASE)

    # Clean trailing punctuation from URLs
    cleaned_urls = []
    for url in urls:
        url = url.rstrip(".,;:!?")
        if len(url) > 10:  # Filter out very short false matches
            cleaned_urls.append(url)

    return cleaned_urls


def analyze_url(url):
    """
    Analyze a single URL for risk indicators.

    Checks for:
        - URL shorteners (bit.ly, tinyurl, etc.)
        - Suspicious TLDs (.xyz, .ru, .tk, etc.)
        - Excessive digits in domain
        - Phishing keywords (login, verify, secure, etc.)
        - Unusually long domain names

    Args:
        url (str): URL to analyze

    Returns:
        dict: {
            "url": str,
            "domain": str,
            "risk": str (LOW/MEDIUM/HIGH),
            "reasons": list of str
        }
    """
    reasons = []
    risk_score = 0

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        full_url_lower = url.lower()
        path_lower = parsed.path.lower() if parsed.path else ""
    except Exception:
        return {
            "url": url,
            "domain": "unknown",
            "risk": "HIGH",
            "reasons": ["Could not parse URL"]
        }

    if not domain:
        domain = url.split("/")[2] if len(url.split("/")) > 2 else "unknown"

    # Check for URL shorteners
    base_domain = domain.replace("www.", "")
    if base_domain in SHORTENERS:
        reasons.append("Uses URL shortener service")
        risk_score += 3

    # Check for suspicious TLDs
    for tld in SUSPICIOUS_TLDS:
        if domain.endswith(tld):
            reasons.append(f"Suspicious TLD: {tld}")
            risk_score += 3
            break

    # Check for too many digits in domain
    domain_digits = sum(1 for c in domain if c.isdigit())
    if domain_digits > 4:
        reasons.append(f"Excessive digits in domain ({domain_digits} digits)")
        risk_score += 2

    # Check for phishing keywords in URL
    found_phishing = []
    for keyword in PHISHING_WORDS:
        if keyword in domain or keyword in path_lower:
            found_phishing.append(keyword)

    if found_phishing:
        reasons.append(f"Phishing keywords detected: {', '.join(found_phishing)}")
        risk_score += 2 * len(found_phishing)

    # Check for unusually long domain
    if len(domain) > 40:
        reasons.append(f"Unusually long domain name ({len(domain)} chars)")
        risk_score += 2

    # Check for IP address as domain
    ip_pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
    if re.match(ip_pattern, domain):
        reasons.append("Uses IP address instead of domain name")
        risk_score += 3

    # Check for multiple subdomains (potential spoofing)
    subdomain_count = domain.count(".")
    if subdomain_count > 3:
        reasons.append(f"Suspicious number of subdomains ({subdomain_count})")
        risk_score += 2

    # Check for hyphens in domain (common in phishing)
    hyphen_count = domain.count("-")
    if hyphen_count >= 3:
        reasons.append(f"Multiple hyphens in domain ({hyphen_count})")
        risk_score += 1

    # Determine risk level and numeric score (0-100)
    numeric_risk = min(risk_score * 10, 100)  # Normalize to 0-100

    if risk_score >= 4:
        risk = "HIGH"
    elif risk_score >= 2:
        risk = "MEDIUM"
    else:
        risk = "LOW"
        if not reasons:
            reasons.append("No suspicious indicators detected")

    return {
        "url": url,
        "domain": domain,
        "risk": risk,
        "risk_score": numeric_risk,
        "reasons": reasons
    }


def analyze_all_urls(text):
    """
    Extract and analyze all URLs in text.

    Args:
        text (str): Input text

    Returns:
        list: List of URL analysis results
    """
    urls = extract_urls(text)
    return [analyze_url(url) for url in urls]


def get_overall_url_risk(url_analyses):
    """
    Determine overall URL risk level from individual analyses.

    Args:
        url_analyses (list): List of URL analysis dictionaries

    Returns:
        str: Overall risk level (LOW/MEDIUM/HIGH)
    """
    if not url_analyses:
        return "LOW"

    risk_levels = [a["risk"] for a in url_analyses]

    if "HIGH" in risk_levels:
        return "HIGH"
    elif "MEDIUM" in risk_levels:
        return "MEDIUM"
    return "LOW"


def check_domain_reputation(url, api_key):
    """
    Check domain reputation using VirusTotal API.

    Args:
        url (str): URL to check
        api_key (str): VirusTotal API key

    Returns:
        dict: {
            "success": bool,
            "domain": str,
            "result": dict or str,
            "error": str or None
        }
    """
    if not api_key or not api_key.strip():
        return {
            "success": False,
            "domain": "",
            "result": None,
            "error": "No API key provided"
        }

    try:
        parsed = urlparse(url)
        domain = parsed.netloc or url.split("/")[2] if "/" in url else url
        domain = domain.replace("www.", "")

        headers = {"x-apikey": api_key.strip()}
        vt_url = f"https://www.virustotal.com/api/v3/domains/{domain}"

        response = requests.get(vt_url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            attributes = data.get("data", {}).get("attributes", {})
            stats = attributes.get("last_analysis_stats", {})

            return {
                "success": True,
                "domain": domain,
                "result": {
                    "harmless": stats.get("harmless", 0),
                    "malicious": stats.get("malicious", 0),
                    "suspicious": stats.get("suspicious", 0),
                    "undetected": stats.get("undetected", 0),
                    "reputation": attributes.get("reputation", "N/A"),
                },
                "error": None
            }
        elif response.status_code == 401:
            return {
                "success": False,
                "domain": domain,
                "result": None,
                "error": "Invalid API key"
            }
        elif response.status_code == 404:
            return {
                "success": False,
                "domain": domain,
                "result": None,
                "error": f"Domain '{domain}' not found in VirusTotal database"
            }
        else:
            return {
                "success": False,
                "domain": domain,
                "result": None,
                "error": f"API returned status {response.status_code}"
            }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "domain": "",
            "result": None,
            "error": "Request timed out"
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "domain": "",
            "result": None,
            "error": "Could not connect to VirusTotal API"
        }
    except Exception as e:
        return {
            "success": False,
            "domain": "",
            "result": None,
            "error": f"Error: {str(e)}"
        }
