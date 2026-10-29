"""
Content Generator Module — UPGRADED v5.0 (Animals & Wildlife Facts Edition)
- Focus: Mind-Blowing Animal Facts, Wildlife Survival, Predators & Rare Abilities
- High Retention Hooks & Emotional Storytelling for Animal lovers worldwide
- Full SEO metadata for Tier-1 audience (US, UK, CA, AU)
- Auto-Pinned engagement debate comment
"""

import os
import json
import re
import random
from typing import Dict, Any, List, Optional
import requests

from src.config import config
from utils.logger import logger


CHANNEL_NICHE = "animal-facts"

ANIMAL_TOPICS = [
    "the immortal jellyfish that can reset its biological age forever",
    "why the honey badger is biologically feared by lions and venomous snakes",
    "the terrifying hunting strategy of the pistol shrimp that boils water",
    "how the peregrine falcon reaches speeds over 240 miles per hour",
    "the unbelievable intelligence of the octopus with nine brains and three hearts",
    "the electric eel that discharges 860 volts of pure electricity",
    "why the mantis shrimp punches with the acceleration of a gunshot",
    "how the tardigrade can survive the cold vacuum of outer space",
    "the deadly poison dart frog with enough venom to kill 10 grown men",
    "the secret language that killer whales use to hunt great white sharks",
    "why the crocodile has remained unchanged for 200 million years",
    "the bizarre defense mechanism of the horned lizard shooting blood from its eyes",
    "the massive blue whale whose heart is the size of a car",
    "how the golden eagle throws mountain goats off cliffs to hunt",
    "the black mamba whose venom can shut down an adult human in 20 minutes",
    "the wood frog that freezes 70 percent of its body solid in winter and comes back to life",
    "the bullet ant whose single sting feels like being shot by a pistol",
    "how army ants construct living bridges out of their own bodies",
    "the axolotl that can regenerate its entire brain, heart, and limbs",
    "the deep sea anglerfish that thrives under crushing oceanic pressure"
]


class ContentGenerator:
    """Handles viral animal facts script generation with SEO and engagement hooks."""

    def __init__(self, openai_key: Optional[str] = None, gemini_key: Optional[str] = None):
        self.openai_key = openai_key or config.openai_api_key
        self.gemini_key = gemini_key or config.gemini_api_key
        self._used_topics_cache: List[str] = []

    def generate(self, niche: str = None) -> Dict[str, Any]:
        """Generates complete viral animal facts video package."""
        topic = self._pick_smart_topic(niche)
        logger.info(f"Generating viral animal fact for: '{topic}'")

        prompt = self._build_animal_prompt(topic)

        # 1. Try Gemini free tier first
        if self.gemini_key and len(self.gemini_key) > 20:
            try:
                logger.info("Attempting via Google Gemini API (Free Animal Facts)...")
                data = self._generate_gemini(prompt)
                if data and self._validate_content(data):
                    data = self._enrich_metadata(data, topic)
                    logger.info(f"✅ Gemini generated: '{data['title']}'")
                    return data
            except Exception as e:
                logger.warning(f"Gemini error: {e}")

        # 2. Try OpenAI if available
        if self.openai_key and "sk-proj-xxxx" not in self.openai_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self.openai_key)
                logger.info("Attempting via OpenAI GPT-4o-mini...")
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": "You are a National Geographic style viral YouTube Shorts creator specializing in mind-blowing animal facts. Output strictly JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.75,
                    max_tokens=800
                )
                data = json.loads(response.choices[0].message.content)
                if self._validate_content(data):
                    data = self._enrich_metadata(data, topic)
                    logger.info(f"✅ OpenAI generated: '{data['title']}'")
                    return data
            except Exception as e:
                logger.warning(f"OpenAI error: {e}")

        # 3. Curated High-Retention Fallback
        logger.warning("Using curated animal facts content pool.")
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
                scopes=["https://www.googleapis.com/auth/youtube.upload"]
            )
            creds.refresh(Request())
            youtube = build("youtube", "v3", credentials=creds)

            # Search channel uploads
            channel_resp = youtube.channels().list(part="contentDetails", mine=True).execute()
            items = channel_resp.get("items", [])
            if not items:
                return {"recent_titles": []}

            uploads_list_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
            playlist_resp = youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_list_id,
                maxResults=10
            ).execute()

            recent_titles = [
                item["snippet"]["title"]
                for item in playlist_resp.get("items", [])
            ]
            self._used_topics_cache = recent_titles
            logger.info(f"📊 Analytics: found {len(recent_titles)} recent videos.")
            return {"recent_titles": recent_titles}

        except Exception as e:
            logger.warning(f"Could not fetch analytics (non-critical): {e}")
            return {"recent_titles": []}

    def _pick_smart_topic(self, niche_override: str = None) -> str:
        """Picks an animal topic not recently used."""
        if niche_override:
            return niche_override

        analytics = self.get_analytics_summary()
        recent_titles = [t.lower() for t in analytics.get("recent_titles", [])]

        available = []
        for topic in ANIMAL_TOPICS:
            topic_words = set(topic.lower().split())
            is_too_similar = any(
                len(topic_words & set(rt.split())) >= 2
                for rt in recent_titles
            )
            if not is_too_similar:
                available.append(topic)

        if not available:
            available = ANIMAL_TOPICS

        return random.choice(available)

    def _build_animal_prompt(self, topic: str) -> str:
        """Builds a high-retention animal facts prompt."""
        return f"""
You are a viral YouTube Shorts creator and wildlife documentary narrator.
Target Audience: US, UK, Canada, Australia (High-CPM viewers who love wild animals and nature).
Topic: "{topic}"

Generate an intense 30-40 second factual script that hooks viewers instantly and keeps them mesmerized.

STRICT RULES:
1. "hook": First 2 sentences ONLY. Must be SHOCKING and impossible to scroll away from. 
   Examples: "This creature literally refuses to die.", "Scientists still cannot explain how this predator survives."
2. "script": Fast-paced, intense 70-85 words. No filler greetings ("Hey guys"). Immediate facts, jaw-dropping numbers, and an interactive question at the end.
3. "title": Ultra-clickbait, high CTR under 85 characters with emojis and #Shorts. (e.g. "The Creature That Literally Refuses To Die 🤯 #Shorts")
4. "description": 2-3 fascinating sentences + call to action + 5 hashtags.
5. "tags": Exactly 15 high-search animal tags (e.g. "animals", "wildlife", "animal facts", "nature", "predators", "shorts", "dangerous animals").
6. "search_keyword": 1-2 words specific animal visual search term (e.g. "lion", "octopus", "falcon", "snake", "eagle", "tiger").
7. "thumbnail_text": 3-4 word punchy bold text (e.g. "IT CANNOT DIE 🤯").
8. "category": "Animals" or "Nature" or "Wild Predators".
9. "hashtags": 5 viral hashtags including #AnimalFacts #WildLife #Shorts #Nature.
10. "pinned_comment": An engaging debate question that compels viewers to comment (e.g. "Would you survive 1 hour in a room with this creature? Tell us below! 👇").

Return ONLY valid JSON matching this schema:
{{
  "title": "string",
  "hook": "string",
  "script": "string",
  "description": "string",
  "tags": ["tag1", "tag2"],
  "hashtags": ["#tag1", "#tag2"],
  "search_keyword": "string",
  "thumbnail_text": "string",
  "category": "string",
  "pinned_comment": "string"
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
        """Enriches metadata and appends wildlife channel branding."""
        if "hashtags" not in data:
            data["hashtags"] = ["#AnimalFacts", "#WildLife", "#Nature", "#Shorts", "#Predators"]

        hashtag_str = " ".join(data["hashtags"])
        if hashtag_str not in data["description"]:
            data["description"] = data["description"].strip() + f"\n\n{hashtag_str}"

        data["description"] += (
            "\n\n🐾 Welcome to Wild Discoveries!"
            "\n🔔 Subscribe for daily mind-blowing animal facts and wildlife mysteries!"
            "\n💬 Comment below what animal we should cover next!"
            "\n❤️ Like if this animal shocked you!"
        )

        data.setdefault("category_id", "15")  # 15 = Pets & Animals on YouTube
        data.setdefault("thumbnail_text", data["title"][:25].upper())
        data.setdefault("search_keyword", "wildlife animal")

        data.setdefault("pinned_comment", (
            f"🐾 What do you think is the most terrifying animal on Earth? Let us know below! 👇\n\n"
            f"🔔 Subscribe for daily mind-blowing animal facts!"
        ))

        if "shorts" not in [t.lower() for t in data.get("tags", [])]:
            data.setdefault("tags", []).append("shorts")
        if "#Shorts" not in data.get("hashtags", []):
            data.setdefault("hashtags", []).append("#Shorts")

        return data

    def _generate_fallback(self, topic: str) -> Dict[str, Any]:
        """Curated high-retention animal facts fallback pool."""
        pool = [
            {
                "title": "Why Lions Are Terrified Of This Tiny Creature 🦡 #Shorts",
                "hook": "This creature has thick biological armor, immunity to venom, and zero fear.",
                "script": "This creature has thick biological armor, complete immunity to venom, and zero fear. The honey badger is so relentlessly aggressive that even prides of lions avoid fighting it. Its skin is thick enough to withstand machetes, bee stings, and porcupine quills. When bitten by a deadly king cobra, it simply takes a two-hour nap, digests the venom, and wakes up to finish eating the snake. Would you survive against this animal? Tell us below.",
                "description": "Meet the honey badger — the world's most fearless mammal that fights lions and survives lethal snake venom. #AnimalFacts #WildLife #HoneyBadger #Nature #Shorts",
                "tags": ["honey badger", "animal facts", "wildlife", "nature", "dangerous animals", "lion fight", "cobra venom", "shorts", "predator", "crazy animals", "wild animals", "fascinating facts"],
                "hashtags": ["#AnimalFacts", "#HoneyBadger", "#WildLife", "#Nature", "#Shorts"],
                "search_keyword": "badger wildlife",
                "thumbnail_text": "FEARED BY LIONS 🦡",
                "category": "Wild Predators",
                "category_id": "15",
                "pinned_comment": "💬 Who wins in a fight: 1 Honey Badger or 3 Wolves? Settle it below! 👇"
            },
            {
                "title": "The Pistol Shrimp Can Boil Water In 1 Millisecond 🦐 #Shorts",
                "hook": "This tiny shrimp produces temperatures hotter than the surface of the sun.",
                "script": "This tiny shrimp produces temperatures hotter than the surface of the sun. The pistol shrimp snaps its claw so fast that it creates a cavitation bubble traveling at sixty miles per hour. When the bubble collapses, it generates a flash of light, an ear-splitting sound of two hundred and eighteen decibels, and temperatures exceeding eight thousand degrees. It literally boils prey alive in one millisecond. Nature is unbelievable.",
                "description": "The pistol shrimp shoots underwater shockwaves hotter than the sun to vaporize its prey. #AnimalFacts #OceanLife #PistolShrimp #DeepSea #Shorts",
                "tags": ["pistol shrimp", "ocean facts", "animal facts", "deep sea", "sea creatures", "crazy nature", "shrimp punch", "marine biology", "shorts", "wildlife", "facts"],
                "hashtags": ["#AnimalFacts", "#OceanLife", "#PistolShrimp", "#Nature", "#Shorts"],
                "search_keyword": "underwater ocean",
                "thumbnail_text": "HOTTER THAN SUN 🦐",
                "category": "Marine Life",
                "category_id": "15",
                "pinned_comment": "🌊 Did you know ocean creatures had this superpower? Tell us your favorite sea animal! 👇"
            },
            {
                "title": "Peregrine Falcon: The Fastest Creature On Earth 🦅 #Shorts",
                "hook": "This bird dives faster than a Formula One race car.",
                "script": "This bird dives faster than a Formula One race car. When hunting in mid-air, the peregrine falcon folds its wings and enters a supersonic dive reaching over two hundred and forty miles per hour. At that speed, air pressure would rupture human lungs, but the falcon has specialized nostrils that baffle airflow. The impact of its strike knocks prey unconscious instantly before it even knows what hit it. Is this the ultimate predator?",
                "description": "Reaching over 240 mph, the Peregrine Falcon is the fastest hunter in the history of planet Earth. #AnimalFacts #Falcon #BirdsOfPrey #Speed #Shorts",
                "tags": ["peregrine falcon", "fastest animal", "birds of prey", "eagle", "falcon dive", "wildlife", "animal facts", "nature", "shorts", "predator", "speed of light"],
                "hashtags": ["#AnimalFacts", "#PeregrineFalcon", "#WildLife", "#FastestAnimal", "#Shorts"],
                "search_keyword": "falcon eagle flying",
                "thumbnail_text": "240 MPH DIVE 🦅",
                "category": "Birds of Prey",
                "category_id": "15",
                "pinned_comment": "🦅 Could any modern jet out-maneuver a Peregrine Falcon? Comment your thoughts! 👇"
            },
            {
                "title": "Octopus Secrets That Terrify Marine Biologists 🐙 #Shorts",
                "hook": "Nine brains, three hearts, and blue copper blood. This creature is practically an alien.",
                "script": "Nine brains, three hearts, and blue copper blood. The octopus is practically an alien living in our oceans. Two-thirds of its neurons reside inside its arms, allowing each tentacle to think, taste, and solve puzzles independently. They can change color, texture, and shape in two hundred milliseconds to blend invisibly into coral. Many scientists believe octopuses arrived through panspermia from outer space. What do you think?",
                "description": "With 9 brains and decentralized intelligence, octopuses are the closest thing to extraterrestrial life on Earth. #AnimalFacts #Octopus #OceanMysteries #SeaLife #Shorts",
                "tags": ["octopus", "alien creature", "ocean mysteries", "animal facts", "sea life", "marine biology", "tentacles", "shorts", "nature", "crazy animals", "underwater"],
                "hashtags": ["#AnimalFacts", "#Octopus", "#OceanLife", "#WildLife", "#Shorts"],
                "search_keyword": "octopus underwater",
                "thumbnail_text": "9 BRAINS 3 HEARTS 🐙",
                "category": "Marine Mysteries",
                "category_id": "15",
                "pinned_comment": "🐙 Do you believe octopuses evolved on Earth, or are they alien? Vote in the comments! 👇"
            }
        ]
        selected = random.choice(pool)
        return self._enrich_metadata(selected.copy(), topic)


if __name__ == "__main__":
    gen = ContentGenerator()
    content = gen.generate()
    print(json.dumps(content, indent=2))
