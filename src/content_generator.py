"""
Content Generator Module — UPGRADED v3.1 (Multi-Voice Acting Edition)
- Generates structured drama dialogues with Speaker tags (Narrator, Male, Female)
- Strong hook-first script structure for Yummy Dramaz
- Full SEO metadata & YouTube Analytics awareness
"""

import os
import json
import re
import random
from typing import Dict, Any, List, Optional
import requests

from src.config import config
from utils.logger import logger


CHANNEL_NICHE = "drama-stories"

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
    """Handles script generation with multi-character acting dialogues and SEO."""

    def __init__(self, openai_key: Optional[str] = None, gemini_key: Optional[str] = None):
        self.openai_key = openai_key or config.openai_api_key
        self.gemini_key = gemini_key or config.gemini_api_key
        self._used_topics_cache: List[str] = []

    def generate(self, niche: str = None) -> Dict[str, Any]:
        """
        Generates complete video package with multi-voice dialogues.
        """
        topic = self._pick_smart_topic(niche)
        logger.info(f"Generating multi-voice content for topic: '{topic}'")

        prompt = self._build_drama_prompt(topic)

        # Try Gemini free tier first
        if self.gemini_key and len(self.gemini_key) > 20:
            try:
                logger.info("Attempting via Google Gemini API (Free Multi-Voice)...")
                data = self._generate_gemini(prompt)
                if data and self._validate_content(data):
                    data = self._enrich_metadata(data, topic)
                    logger.info(f"✅ Gemini generated: '{data['title']}' with {len(data.get('dialogues', []))} lines")
                    return data
            except Exception as e:
                logger.warning(f"Gemini error: {e}")

        # Try OpenAI if available
        if self.openai_key and "sk-proj-xxxx" not in self.openai_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self.openai_key)
                logger.info("Attempting via OpenAI GPT-4o-mini...")
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": "You are a viral YouTube Shorts script writer specialized in multi-character dramatic acting scripts. Output only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.82,
                    max_tokens=800
                )
                data = json.loads(response.choices[0].message.content)
                if self._validate_content(data):
                    data = self._enrich_metadata(data, topic)
                    logger.info(f"✅ OpenAI generated: '{data['title']}'")
                    return data
            except Exception as e:
                logger.warning(f"OpenAI error: {e}")

        # Curated fallback
        logger.warning("Using curated multi-voice drama content pool.")
        return self._generate_fallback(topic)

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Fetches last uploaded video titles from YouTube to avoid repeating topics."""
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

    def _pick_smart_topic(self, niche_override: str = None) -> str:
        """Picks a topic not recently used."""
        if niche_override:
            return niche_override

        analytics = self.get_analytics_summary()
        recent_titles = [t.lower() for t in analytics.get("recent_titles", [])]

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
            available = DRAMA_TOPICS

        return random.choice(available)

    def _build_drama_prompt(self, topic: str) -> str:
        """Builds a multi-character dialogue prompt."""
        return f"""
You are a top-tier viral YouTube Shorts drama producer for the channel "Yummy Dramaz".
Target Audience: US, UK, Canada, Australia (High-CPM viewers).
Topic: "{topic}"

Generate an intense 35-45 second dramatic short script structured as a realistic multi-character scene.
Characters can be:
- "narrator" (suspenseful narrator setting up the scene and emotional reactions)
- "male" (husband, boyfriend, detective, ex, or brother)
- "female" (wife, girlfriend, sister, or mother)

STRICT RULES:
1. "hook": First 2-3 sentences. Shocking, high curiosity, instant tension.
2. "dialogues": Array of 4 to 6 dialogue turns. Each turn has:
   - "speaker": exactly "narrator", "male", or "female"
   - "text": the exact words spoken (punchy, emotional, realistic, no long monologues)
3. "script": Full concatenated spoken text of all dialogues combined (75-95 words).
4. "title": Ultra-clickbait, high CTR, emotional under 90 chars + emojis + #Shorts.
5. "description": 2-3 emotional sentences + call to action + 5 hashtags.
6. "tags": Exactly 12 high-search drama tags.
7. "search_keyword": 1-2 words visual search term (e.g. "couple arguing", "luxury mansion", "crying woman").
8. "thumbnail_text": 3-5 word bold emotional text (e.g. "HE HAD TWO WIVES 😱").
9. "category": "Drama" or "Psychology" or "Revenge".
10. "hashtags": Array of 5 hashtags including #YummyDramaz and #Shorts.

Return ONLY valid JSON matching this schema:
{{
  "title": "string",
  "hook": "string",
  "dialogues": [
    {{"speaker": "narrator", "text": "Nobody warned her. She grabbed his phone..."}},
    {{"speaker": "male", "text": "Why are you touching my phone? Put it back!"}},
    {{"speaker": "female", "text": "Who is Karen? And why are there photos of three kids?"}},
    {{"speaker": "narrator", "text": "His face went pale. The marriage was over."}}
  ],
  "script": "string",
  "description": "string",
  "tags": ["tag1", "tag2"],
  "hashtags": ["#tag1", "#tag2"],
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
        return all(k in data for k in ["title", "script", "description", "tags"])

    def _enrich_metadata(self, data: Dict, topic: str) -> Dict:
        """Enriches metadata and ensures valid dialogues array."""
        # Ensure dialogues exist
        if "dialogues" not in data or not isinstance(data["dialogues"], list) or len(data["dialogues"]) == 0:
            # Fallback construct dialogues from script
            script = data.get("script", "")
            data["dialogues"] = [
                {"speaker": "narrator", "text": script}
            ]

        # Re-derive clean concatenated script from dialogues
        data["script"] = " ".join([d.get("text", "").strip() for d in data["dialogues"] if d.get("text")])

        if "hashtags" not in data:
            data["hashtags"] = ["#YummyDramaz", "#Shorts", "#Drama", "#Story", "#Viral"]

        hashtag_str = " ".join(data["hashtags"])
        if hashtag_str not in data["description"]:
            data["description"] = data["description"].strip() + f"\n\n{hashtag_str}"

        data["description"] += (
            "\n\n🔔 Subscribe to Yummy Dramaz for daily shocking drama stories!"
            "\n💬 Comment your reaction below!"
            "\n❤️ Like if this story shocked you!"
        )

        data.setdefault("category_id", "24")
        data.setdefault("thumbnail_text", data["title"][:30].upper())
        data.setdefault("search_keyword", "drama")
        data.setdefault("pinned_comment", (
            f"💬 Who do you think was in the wrong here? Let's settle this in the comments! 👇\n\n"
            f"🔔 Subscribe to @YummyDramaz for daily drama & revenge stories!"
        ))

        if "shorts" not in [t.lower() for t in data.get("tags", [])]:
            data.setdefault("tags", []).append("shorts")
        if "#Shorts" not in data.get("hashtags", []):
            data.setdefault("hashtags", []).append("#Shorts")

        return data

    def _generate_fallback(self, topic: str) -> Dict[str, Any]:
        """Multi-character dramatic fallback pool."""
        pool = [
            {
                "title": "She Found 5 Years of Lies in 30 Seconds 💔 #Shorts",
                "hook": "Nobody warned her. She picked up his ringing phone and her entire world shattered.",
                "dialogues": [
                    {"speaker": "narrator", "text": "Nobody warned her. She picked up his ringing phone and her entire life shattered."},
                    {"speaker": "female", "text": "Hello? Who is this? Why are you calling my husband at midnight?"},
                    {"speaker": "narrator", "text": "The voice on the other end went silent, before whispering six chilling words."},
                    {"speaker": "female", "text": "Your husband? Honey, he’s been married to me for seven years."},
                    {"speaker": "male", "text": "Give me the phone! You were never supposed to answer that!"},
                    {"speaker": "narrator", "text": "Two hundred photos. Another family. What would you do in her place? Comment below."}
                ],
                "description": "A shocking true story of betrayal that no wife should ever experience. When the person you trust most lives a complete double life. #YummyDramaz #Shorts #Drama #Betrayal #Story",
                "tags": ["drama shorts", "betrayal story", "shocking story", "marriage betrayal", "true story", "drama", "shorts", "yummy dramaz", "cheating husband", "viral story", "emotional story", "relationship"],
                "hashtags": ["#YummyDramaz", "#Shorts", "#Drama", "#Betrayal", "#ShockingStory"],
                "search_keyword": "sad woman phone",
                "thumbnail_text": "HE HAD TWO WIVES 😱",
                "category": "Drama",
                "category_id": "24"
            },
            {
                "title": "His Secret Family Was Finally Exposed 😳 #Shorts",
                "hook": "For seven years, he thought he was her only husband. He was dead wrong.",
                "dialogues": [
                    {"speaker": "narrator", "text": "For seven years, he thought he was her only husband. He was dead wrong."},
                    {"speaker": "male", "text": "Who is Karen? A lawyer just served divorce papers at our door!"},
                    {"speaker": "female", "text": "It was never personal. You were just my backup plan."},
                    {"speaker": "narrator", "text": "She packed her bags without shedding a single tear."},
                    {"speaker": "male", "text": "Ten years together, and you feel nothing? Absolutely nothing?"},
                    {"speaker": "narrator", "text": "She looked right into his eyes and smiled. Karma has no deadline."}
                ],
                "description": "When trust is shattered beyond repair. A shocking confrontation uncovering a double life. #YummyDramaz #Shorts #Drama #ShockingStory #TrueCrime",
                "tags": ["shocking story", "drama shorts", "double life", "betrayal", "story time", "drama", "shorts", "yummy dramaz", "viral", "emotional", "true crime", "relationship drama"],
                "hashtags": ["#YummyDramaz", "#Shorts", "#Drama", "#DoubleLife", "#Shocking"],
                "search_keyword": "couple arguing",
                "thumbnail_text": "DOUBLE LIFE EXPOSED 😳",
                "category": "Drama",
                "category_id": "24"
            },
            {
                "title": "Dark Psychology: How Toxic People Hook You 🧠 #Shorts",
                "hook": "If someone does this to you, run immediately. They are weaponizing your emotions.",
                "dialogues": [
                    {"speaker": "narrator", "text": "If someone does this to you, run immediately. They are weaponizing your emotions."},
                    {"speaker": "male", "text": "You're crazy! I never said that. You're imagining things again."},
                    {"speaker": "female", "text": "Why do you always make me feel like I am losing my mind?"},
                    {"speaker": "narrator", "text": "This psychological tactic is called intermittent reinforcement. They break you down, then love-bomb you."},
                    {"speaker": "narrator", "text": "Your brain gets addicted to their validation like a drug. Have you ever experienced this?"}
                ],
                "description": "Dark psychology tactics that toxic and narcissistic people use to control and manipulate those around them. #YummyDramaz #Shorts #Psychology #Manipulation #DarkPsychology",
                "tags": ["dark psychology", "toxic relationship", "narcissist", "manipulation tactics", "psychology shorts", "drama", "shorts", "yummy dramaz", "mental health", "toxic people", "red flags", "self improvement"],
                "hashtags": ["#YummyDramaz", "#Shorts", "#DarkPsychology", "#Manipulation", "#ToxicRelationship"],
                "search_keyword": "dark room shadow",
                "thumbnail_text": "THEY CONTROL YOU 🧠",
                "category": "Psychology",
                "category_id": "24"
            },
            {
                "title": "She Waited 10 Years For This Revenge 😤 #Shorts",
                "hook": "She smiled at her arrogant ex in the boardroom. He had no idea she owned the building.",
                "dialogues": [
                    {"speaker": "narrator", "text": "She smiled at her arrogant ex in the boardroom. He had no clue she owned the entire company."},
                    {"speaker": "male", "text": "What are you doing in the CEO seat? Get out before security removes you!"},
                    {"speaker": "female", "text": "Ten years ago, you stole my life savings and left me with nothing."},
                    {"speaker": "narrator", "text": "She slid the termination contract across the polished marble desk."},
                    {"speaker": "female", "text": "Today, I sign your termination letter. Security is already behind you."},
                    {"speaker": "narrator", "text": "Revenge is a dish best served cold. Like and subscribe for more drama!"}
                ],
                "description": "A story of patience, quiet rebuilding, and ultimate poetic justice. #YummyDramaz #Shorts #Revenge #Drama #Story",
                "tags": ["revenge story", "drama shorts", "karma story", "shocking ending", "story time", "drama", "shorts", "yummy dramaz", "viral story", "emotional", "revenge", "satisfying"],
                "hashtags": ["#YummyDramaz", "#Shorts", "#Revenge", "#Drama", "#KarmaStory"],
                "search_keyword": "luxury office building",
                "thumbnail_text": "10 YEAR REVENGE 😤",
                "category": "Revenge",
                "category_id": "24"
            }
        ]
        selected = random.choice(pool)
        return self._enrich_metadata(selected.copy(), topic)


if __name__ == "__main__":
    gen = ContentGenerator()
    content = gen.generate()
    print(json.dumps(content, indent=2))
