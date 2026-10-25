"""
Content Generator Module — UPGRADED v3.0
- Drama/Movies/Stories niche support for "Yummy Dramaz" channel
- YouTube Analytics check before each new video (avoid repeat topics)
- Strong hook-first script structure (retain viewers in first 3 sec)
- Fully SEO-optimized title, description, tags, hashtags
- High-CPM Tier-1 audience targeting (US/UK/CA/AU)
"""

import os
import json
import re
import random
from typing import Dict, Any, List, Optional
import requests

from src.config import config
from utils.logger import logger


# ── NICHE CONFIGURATION ──────────────────────────────────────────────────────
# Channel: "Yummy Dramaz" — Drama/Movies/Stories/Psychology
# Targeting: US, UK, Canada, Australia (High-CPM Tier-1)
CHANNEL_NICHE = "drama-stories"   # options: "drama-stories" | "finance" | "psychology" | "tech"

DRAMA_TOPICS = [
    "a shocking betrayal that changed a family forever",
    "a love story that ended in tragedy no one saw coming",
    "the darkest secret hidden inside a rich family",
    "a woman who discovered her husband's double life",
    "the forbidden romance that destroyed two families",
    "a psychological thriller story about obsession and revenge",
    "a true crime story that shocked the entire city",
    "the twisted mind games inside a toxic relationship",
    "a mother who found out her child was not hers",
    "the millionaire who lost everything because of one mistake",
    "a story of betrayal between best friends",
    "the secret affair that no one was supposed to know about",
    "a girl who uncovered a dark conspiracy in her own home",
    "the husband who disappeared on their wedding night",
    "a revenge story that took 10 years to complete",
    "dark psychology tricks used to manipulate your partner",
    "the wife who planned the perfect revenge",
    "a story about greed, power, and ultimate downfall",
]


class ContentGenerator:
    """Handles script generation with analytics feedback and SEO optimization."""

    def __init__(self, openai_key: Optional[str] = None, gemini_key: Optional[str] = None):
        self.openai_key = openai_key or config.openai_api_key
        self.gemini_key = gemini_key or config.gemini_api_key
        self._used_topics_cache: List[str] = []

    # ── PUBLIC METHODS ────────────────────────────────────────────────────────

    def generate(self, niche: str = None) -> Dict[str, Any]:
        """
        Generates complete video package.
        1. Checks analytics to pick a fresh topic
        2. Tries Gemini API (free)
        3. Falls back to curated pool
        """
        topic = self._pick_smart_topic(niche)
        logger.info(f"Generating content for topic: '{topic}'")

        prompt = self._build_drama_prompt(topic)

        # Try Gemini free tier first
        if self.gemini_key and len(self.gemini_key) > 20:
            try:
                logger.info("Attempting via Google Gemini API (Free)...")
                data = self._generate_gemini(prompt)
                if data and self._validate_content(data):
                    data = self._enrich_metadata(data, topic)
                    logger.info(f"✅ Gemini generated: '{data['title']}'")
                    return data
            except Exception as e:
                logger.warning(f"Gemini error: {e}")

        # Try OpenAI
        if self.openai_key and "sk-proj-xxxx" not in self.openai_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self.openai_key)
                logger.info("Attempting via OpenAI GPT-4o-mini...")
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": "You are a viral YouTube Shorts script writer. Output only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.82,
                    max_tokens=700
                )
                data = json.loads(response.choices[0].message.content)
                if self._validate_content(data):
                    data = self._enrich_metadata(data, topic)
                    logger.info(f"✅ OpenAI generated: '{data['title']}'")
                    return data
            except Exception as e:
                logger.warning(f"OpenAI error: {e}")

        # Curated fallback
        logger.warning("Using curated drama content pool.")
        return self._generate_fallback(topic)

    def get_analytics_summary(self) -> Dict[str, Any]:
        """
        Fetches last 5 uploaded video titles from YouTube to avoid repeating topics.
        Returns dict with list of recent titles.
        """
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build

            client_dict = config.get_client_secret_dict()
            creds_info = client_dict.get("installed") or client_dict.get("web", {})

            creds = Credentials(
                token=None,
                refresh_token=config.youtube_refresh_token,
                token_uri=creds_info.get("token_uri", "https://oauth2.googleapis.com/token"),
                client_id=creds_info.get("client_id"),
                client_secret=creds_info.get("client_secret"),
                scopes=["https://www.googleapis.com/auth/youtube.readonly"]
            )
            creds.refresh(Request())
            youtube = build("youtube", "v3", credentials=creds)

            # Get channel's own videos
            search_resp = youtube.search().list(
                part="snippet",
                forMine=True,
                type="video",
                maxResults=10,
                order="date"
            ).execute()

            recent_titles = [
                item["snippet"]["title"]
                for item in search_resp.get("items", [])
            ]
            self._used_topics_cache = recent_titles
            logger.info(f"📊 Analytics: found {len(recent_titles)} recent videos.")
            return {"recent_titles": recent_titles}

        except Exception as e:
            logger.warning(f"Could not fetch analytics (non-critical): {e}")
            return {"recent_titles": []}

    # ── PRIVATE METHODS ───────────────────────────────────────────────────────

    def _pick_smart_topic(self, niche_override: str = None) -> str:
        """Picks a topic not recently used, based on analytics."""
        if niche_override:
            return niche_override

        # Fetch recent titles to avoid repetition
        analytics = self.get_analytics_summary()
        recent_titles = [t.lower() for t in analytics.get("recent_titles", [])]

        # Filter out topics that are similar to recent ones
        available = []
        for topic in DRAMA_TOPICS:
            topic_words = set(topic.lower().split())
            is_too_similar = any(
                len(topic_words & set(rt.split())) >= 2
                for rt in recent_titles
            )
            if not is_too_similar:
                available.append(topic)

        if not available:
            available = DRAMA_TOPICS  # reset if all used

        return random.choice(available)

    def _build_drama_prompt(self, topic: str) -> str:
        """Builds a drama-focused viral Shorts prompt with strong hook."""
        return f"""
You are a VIRAL YouTube Shorts creator for the channel "Yummy Dramaz".
Your audience is in the US, UK, Canada, and Australia (High-CPM viewers).
Content niche: dramatic stories, dark psychology, betrayal, revenge, love gone wrong, shocking twists.

Create a 35-45 second YouTube Short script about: "{topic}"

STRICT RULES:
1. "hook": First 2-3 sentences ONLY. Must be SHOCKING and make viewer UNABLE to scroll away. 
   Start with phrases like: "Nobody knew that...", "She had no idea...", "What he discovered changed everything...", "For 5 years, she hid the truth..."
2. "script": Full 75-95 word spoken narrative. Hook first, then story build-up, end with cliffhanger or question. NO filler intro. Immediate tension.
3. "title": Ultra-clickbait, emotional, under 90 chars. Examples: "She Faked Her Own Death To Escape Him 💔", "He Didn't Know His Wife Had A Secret Family 😱"
4. "description": 2-3 emotional sentences about the story + call to action + 5-7 hashtags. Include: #YummyDramaz #Shorts #Drama
5. "tags": Exactly 12 high-search tags targeting US/UK drama audience. Include: shorts, drama, betrayal, story, shocking, etc.
6. "search_keyword": 1-2 word visual search term for background footage (e.g. "couple arguing", "luxury house", "sad woman", "dark room", "city night").
7. "thumbnail_text": 3-5 word bold emotional text to overlay on thumbnail (e.g. "SHE FAKED HER DEATH 😱").
8. "category": One of: Drama, Psychology, True Crime, Love Story, Revenge.
9. "hashtags": Array of 5 trending hashtags starting with #.

Return ONLY valid JSON:
{{
  "title": "string",
  "hook": "string",
  "script": "string",
  "description": "string",
  "tags": ["tag1",...],
  "hashtags": ["#tag1",...],
  "search_keyword": "string",
  "thumbnail_text": "string",
  "category": "string"
}}
"""

    def _generate_gemini(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Calls Gemini 1.5 Flash via REST."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }
        res = requests.post(url, json=payload, timeout=25)
        if res.status_code == 200:
            raw = res.json()["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw)
        raise RuntimeError(f"Gemini HTTP {res.status_code}: {res.text[:200]}")

    def _validate_content(self, data: Dict) -> bool:
        """Ensures required fields present."""
        return all(k in data for k in ["title", "script", "description", "tags"])

    def _enrich_metadata(self, data: Dict, topic: str) -> Dict:
        """Adds missing fields and appends channel branding."""
        # Ensure hook is prepended to script for TTS if hook exists separately
        if "hook" in data and data["hook"] and data["hook"] not in data["script"]:
            data["script"] = data["hook"] + " " + data["script"]

        # Add hashtags to description if not present
        if "hashtags" not in data:
            data["hashtags"] = ["#YummyDramaz", "#Shorts", "#Drama", "#Story", "#Viral"]

        hashtag_str = " ".join(data["hashtags"])
        if hashtag_str not in data["description"]:
            data["description"] = data["description"].strip() + f"\n\n{hashtag_str}"

        # Channel branding footer
        data["description"] += (
            "\n\n🔔 Subscribe to Yummy Dramaz for daily shocking stories!"
            "\n💬 Comment your reaction below!"
            "\n❤️ Like if this story shocked you!"
        )

        # SEO fields
        data.setdefault("category_id", "24")  # 24 = Entertainment
        data.setdefault("thumbnail_text", data["title"][:30].upper())
        data.setdefault("search_keyword", "drama")

        # Ensure #Shorts tag for YouTube algorithm
        if "shorts" not in [t.lower() for t in data.get("tags", [])]:
            data.setdefault("tags", []).append("shorts")
        if "#Shorts" not in data.get("hashtags", []):
            data.setdefault("hashtags", []).append("#Shorts")

        return data

    def _generate_fallback(self, topic: str) -> Dict[str, Any]:
        """High-retention drama fallback pool for Yummy Dramaz."""
        pool = [
            {
                "title": "She Found Texts That Destroyed Her Marriage 💔 #Shorts",
                "hook": "Nobody warned her. She grabbed his phone for a second — and found 5 years of lies.",
                "script": "Nobody warned her. She grabbed his phone for a second — and found 5 years of lies. Over 200 messages. Another woman. Another family. Her hands shook as she scrolled through the photos — her husband at a birthday party she never knew existed. Three kids smiled back at her from the screen. She had been the wife. But she was never his only one. What would YOU do in her place?",
                "description": "A shocking story of betrayal that no wife should ever experience. Sometimes the person you trust most hides the darkest secrets. #YummyDramaz #Shorts #Drama #Betrayal #Story",
                "tags": ["drama shorts", "betrayal story", "shocking story", "marriage betrayal", "true story", "drama", "shorts", "yummy dramaz", "cheating husband", "viral story", "emotional story", "relationship"],
                "hashtags": ["#YummyDramaz", "#Shorts", "#Drama", "#Betrayal", "#ShockingStory"],
                "search_keyword": "sad woman",
                "thumbnail_text": "5 YEARS OF LIES 😱",
                "category": "Drama",
                "category_id": "24"
            },
            {
                "title": "He Discovered His Wife Had A Secret Family 😱 #Shorts",
                "hook": "For 7 years, he thought he was her only husband. He was wrong.",
                "script": "For 7 years, he thought he was her only husband. He was wrong. It started with a stranger calling his home asking for \"Mrs. Karen.\" Then a lawyer's letter arrived — his wife had filed for divorce in another state. She had a second husband. Two daughters. A whole life he knew nothing about. When he confronted her, she simply said — you were never supposed to find out. What would you do?",
                "description": "When trust is shattered beyond repair — a shocking story of a double life no one saw coming. #YummyDramaz #Shorts #Drama #ShockingStory #TrueCrime",
                "tags": ["shocking story", "drama shorts", "double life", "betrayal", "story time", "drama", "shorts", "yummy dramaz", "viral", "emotional", "true crime", "relationship drama"],
                "hashtags": ["#YummyDramaz", "#Shorts", "#Drama", "#DoubleLife", "#Shocking"],
                "search_keyword": "couple arguing",
                "thumbnail_text": "DOUBLE LIFE EXPOSED 😳",
                "category": "Drama",
                "category_id": "24"
            },
            {
                "title": "Dark Psychology: How Toxic People Control You 🧠 #Shorts",
                "hook": "If someone does THIS to you — run. They are using your emotions as a weapon.",
                "script": "If someone does THIS to you — run immediately. They are using your emotions as a weapon. Toxic people use a technique called \"intermittent reinforcement\" — they hurt you, then love bomb you. Hot and cold. Push and pull. Your brain becomes addicted to their approval like a drug. They control your self-worth until you cannot imagine life without their validation. This is not love. This is manipulation. Have you experienced this?",
                "description": "Dark psychology tactics that toxic and narcissistic people use to control and manipulate those around them. Awareness is your protection. #YummyDramaz #Shorts #Psychology #Manipulation #DarkPsychology",
                "tags": ["dark psychology", "toxic relationship", "narcissist", "manipulation tactics", "psychology shorts", "drama", "shorts", "yummy dramaz", "mental health", "toxic people", "red flags", "self improvement"],
                "hashtags": ["#YummyDramaz", "#Shorts", "#DarkPsychology", "#Manipulation", "#ToxicRelationship"],
                "search_keyword": "dark room",
                "thumbnail_text": "THEY CONTROL YOU 🧠",
                "category": "Psychology",
                "category_id": "24"
            },
            {
                "title": "She Waited 10 Years To Destroy Him 😤 Revenge Story #Shorts",
                "hook": "She smiled at her ex at the party. He had no idea she had been planning this for a decade.",
                "script": "She smiled at her ex at the party. He had no idea she had been planning this for a decade. Ten years ago he humiliated her publicly, took her savings, and left her with nothing. She rebuilt herself — quietly, methodically. She bought the company he worked for. And on a Monday morning, she sat in the CEO chair and called him into her office. He went pale. She simply said — you're fired. Revenge is a dish best served cold.",
                "description": "A story of patience, rebuilding, and ultimate revenge that proves karma always comes back around. #YummyDramaz #Shorts #Revenge #Drama #Story",
                "tags": ["revenge story", "drama shorts", "karma story", "shocking ending", "story time", "drama", "shorts", "yummy dramaz", "viral story", "emotional", "revenge", "satisfying"],
                "hashtags": ["#YummyDramaz", "#Shorts", "#Revenge", "#Drama", "#KarmaStory"],
                "search_keyword": "luxury office",
                "thumbnail_text": "10 YEAR REVENGE 😤",
                "category": "Revenge",
                "category_id": "24"
            },
        ]

        selected = random.choice(pool)
        return self._enrich_metadata(selected.copy(), topic)


if __name__ == "__main__":
    gen = ContentGenerator()
    content = gen.generate()
    print(json.dumps(content, indent=2))
