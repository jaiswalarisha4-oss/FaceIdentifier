"""Genuine reverse-image web search via Microsoft Bing's Visual Search API,
filtered down to known social media platforms.

This performs a real search request against Bing for every run — it does
not return a pre-picked or hardcoded result. It requires a
`BING_VISUAL_SEARCH_KEY` (a free-tier Azure Cognitive Services key works)
in the environment; see README.md for how to obtain one.
"""
import os
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlparse

import requests

SOCIAL_DOMAINS = (
    "instagram.com",
    "twitter.com",
    "x.com",
    "facebook.com",
    "linkedin.com",
    "tiktok.com",
    "reddit.com",
    "pinterest.com",
    "youtube.com",
)

BING_VISUAL_SEARCH_URL = "https://api.bing.microsoft.com/v7.0/images/visualsearch"


@dataclass
class SocialMatch:
    source_url: str
    host_page_url: str
    thumbnail_url: Optional[str]
    platform: str


class BingReverseImageSearch:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("BING_VISUAL_SEARCH_KEY")
        if not self.api_key:
            raise RuntimeError(
                "BING_VISUAL_SEARCH_KEY is not set. Reverse image search "
                "requires a real API key so results come from an actual "
                "web search, not a hardcoded value."
            )

    def search(self, image_path: str) -> List[SocialMatch]:
        with open(image_path, "rb") as f:
            files = {"image": ("face.jpg", f, "image/jpeg")}
            headers = {"Ocp-Apim-Subscription-Key": self.api_key}
            response = requests.post(
                BING_VISUAL_SEARCH_URL, headers=headers, files=files, timeout=30
            )
        response.raise_for_status()
        return self._parse_results(response.json())

    def _parse_results(self, payload: dict) -> List[SocialMatch]:
        matches: List[SocialMatch] = []
        for tag in payload.get("tags", []):
            for action in tag.get("actions", []):
                if action.get("actionType") not in ("PagesIncluding", "VisualSearch"):
                    continue
                for item in action.get("data", {}).get("value", []):
                    host_page = item.get("hostPageUrl", "")
                    domain = urlparse(host_page).netloc.replace("www.", "")
                    platform = next((d for d in SOCIAL_DOMAINS if d in domain), None)
                    if platform:
                        matches.append(
                            SocialMatch(
                                source_url=item.get("contentUrl", host_page),
                                host_page_url=host_page,
                                thumbnail_url=item.get("thumbnailUrl"),
                                platform=platform,
                            )
                        )
        return matches
