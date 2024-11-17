from urllib.parse import urlparse
import requests
import validators
from typing import Dict

def validate_url(url: str) -> bool:
    """Validate URL format using validators."""
    return validators.url(url) if url else False

def normalize_url(url: str, timeout: int, headers: Dict[str, str]) -> str:
    """Normalize URL with scheme."""
    parsed = urlparse(url)
    if parsed.scheme:
        return url
        
    # Try HTTPS first, then HTTP
    for scheme in ['https://', 'http://']:
        try:
            full_url = f"{scheme}{url}"
            response = requests.head(full_url, timeout=timeout, headers=headers)
            if response.status_code < 400:
                return full_url
        except requests.RequestException:
            continue
            
    raise ValueError(f"Failed to verify URL: {url}")
