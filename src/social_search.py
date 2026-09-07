"""Genuine reverse-image web search via Google Cloud Vision's Web Detection
feature, filtered down to known social media platforms.

This performs a real request to the Cloud Vision API for every run -- it
does not return a pre-picked or hardcoded result. It requires a
`GOOGLE_VISION_API_KEY` in the environment; see README.md for how to
obtain one (free tier: 1,000 units/month).

Note: this project originally targeted Microsoft's Bing Visual Search API,
but Bing Search APIs (Web/Image/Visual Search) were retired by Microsoft
on August 11, 2025 and can no longer be provisioned -- Google Cloud
Vision's Web Detection is the still-live replacement used here.
"""
import base64
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

VISION_API_URL = "https://vision.googleapis.com/v1/images:annotate"


@dataclass
class SocialMatch:
    source_url: str
    host_page_url: str
    thumbnail_url: Optional[str]
    platform: str


class GoogleVisionReverseImageSearch:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GOOGLE_VISION_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "GOOGLE_VISION_API_KEY is not set. Reverse image search "
                "requires a real API key so results come from an actual "
                "web search, not a hardcoded value."
            )

    def search(self, image_path: str) -> List[SocialMatch]:
        with open(image_path, "rb") as f:
            encoded_image = base64.b64encode(f.read()).decode()

        payload = {
            "requests": [
                {
                    "image": {"content": encoded_image},
                    "features": [{"type": "WEB_DETECTION", "maxResults": 25}],
                }
            ]
        }
        response = requests.post(
            VISION_API_URL, params={"key": self.api_key}, json=payload, timeout=30
        )
        response.raise_for_status()
        return self._parse_results(response.json())

    def _parse_results(self, payload: dict) -> List[SocialMatch]:
        matches: List[SocialMatch] = []
        responses = payload.get("responses", [{}])
        web_detection = responses[0].get("webDetection", {}) if responses else {}

        for page in web_detection.get("pagesWithMatchingImages", []):
            host_page = page.get("url", "")
            domain = urlparse(host_page).netloc.replace("www.", "")
            platform = next((d for d in SOCIAL_DOMAINS if d in domain), None)
            if not platform:
                continue

            images = page.get("fullMatchingImages") or page.get("partialMatchingImages") or []
            image_url = images[0]["url"] if images else host_page

            matches.append(
                SocialMatch(
                    source_url=image_url,
                    host_page_url=host_page,
                    thumbnail_url=image_url,
                    platform=platform,
                )
            )
        return matches
