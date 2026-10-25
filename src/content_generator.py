"""
Content Generator Module.
Leverages Google Gemini API (Free Tier) or OpenAI GPT-4o-mini to produce
high-CTR titles, scripts, tags, SEO descriptions, and visual stock search queries.
"""

import os
import json
import re
from typing import Dict, Any, List, Optional
import requests
from openai import OpenAI

from src.config import config
from utils.logger import logger


class ContentGenerator:
    """Handles prompt engineering, completions, and metadata synthesis."""

    def __init__(self, openai_key: Optional[str] = None, gemini_key: Optional[str] = None):
        self.openai_key = openai_key or config.openai_api_key
        self.gemini_key = gemini_key or config.gemini_api_key
        
        self.openai_client = None
        if self.openai_key and "sk-proj-xxxx" not in self.openai_key:
            try:
                self.openai_client = OpenAI(api_key=self.openai_key)
            except Exception:
                pass

    def generate(self, niche: str = None) -> Dict[str, Any]:
        """
        Generates complete video package in JSON format.
        Tries Gemini API first (100% free), then OpenAI, then offline fallback.
        """
        topic = niche or config.video_niche
        logger.info(f"Generating content for niche: '{topic}'")

        prompt = f"""
You are a viral YouTube Shorts creator and algorithmic strategist.
Generate an irresistible, factual, 30-to-45-second vertical video script about: "{topic}".

Rules:
1. "title": Must have high Click-Through-Rate (CTR), punchy, curiosity-inducing, under 90 characters.
2. "script": Spoken narrative, around 70-90 words. Start with an immediate curiosity hook in the first 3 seconds (no intro/filler like 'Hey guys'). Deliver high-value factual content and end with an engaging retention thought.
3. "description": 2-3 engaging sentences explaining the topic, followed by 5 relevant viral hashtags.
4. "tags": An array of exactly 10 high-search-volume tags.
5. "search_keyword": A single, high-relevance, simple visual search term (1-2 words) suitable for finding free stock background footage (e.g. 'space galaxy', 'deep ocean', 'robotics').

Return ONLY a valid JSON object matching this schema:
{{
  "title": "string",
  "script": "string",
  "description": "string",
  "tags": ["tag1", "tag2", ...],
  "search_keyword": "string"
}}
"""

        # 1. Try Gemini API (Free tier)
        if self.gemini_key and "AIzaSy" in self.gemini_key:
            try:
                logger.info("Attempting generation via Google Gemini API (Free Tier)...")
                data = self._generate_gemini(prompt)
                if data:
                    data["description"] = self._append_monetization(data["description"])
                    logger.info(f"Gemini generated: '{data['title']}'")
                    return data
            except Exception as e:
                logger.warning(f"Gemini API generation error: {e}")

        # 2. Try OpenAI API
        if self.openai_client:
            try:
                logger.info("Attempting generation via OpenAI GPT-4o-mini...")
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    response_format={"type": "json_object"},
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an automated YouTube Shorts production engine that outputs strictly JSON."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.75,
                    max_tokens=600
                )
                raw_content = response.choices[0].message.content
                data = json.loads(raw_content)
                data["description"] = self._append_monetization(data["description"])
                logger.info(f"OpenAI generated: '{data['title']}'")
                return data
            except Exception as e:
                logger.error(f"OpenAI generation error: {e}")

        # 3. Fallback
        logger.warning("Falling back to curated procedural/offline content package.")
        return self._generate_fallback(topic)

    def _generate_gemini(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Invokes Gemini 1.5/2.0 Flash via standard REST API."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        if res.status_code == 200:
            result = res.json()
            raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw_text)
        else:
            raise RuntimeError(f"Gemini API responded with HTTP {res.status_code}: {res.text}")

    def _append_monetization(self, base_description: str) -> str:
        """Appends contextual monetization and affiliate links to the description."""
        monetization_block = (
            f"\n\n--- RECOMMENDED RESOURCES ---\n"
            f"⚡ Automated Production Toolkit: https://amazon.com/?tag={config.amazon_affiliate_tag}\n"
            f"📈 Grow & Rank Your Channel Faster: https://vidiq.com/{config.vidiq_affiliate_id}\n\n"
            f"🔔 Subscribe for daily science & tech discoveries!"
        )
        return base_description.strip() + monetization_block

    def _generate_fallback(self, topic: str) -> Dict[str, Any]:
        """Provides high-retention Tier-1 viral scripts targeting US/UK/Canada audiences."""
        import random

        high_cpm_pool = [
            {
                "title": "The 1% Rule of Compounding That Banks Hide From You",
                "script": "What if I told you that 90% of millionaires didn't get rich by saving money? They mastered the rule of geometric leverage. If you invest just 10 dollars a day at a 10 percent annual return, compound interest turns that into over one million dollars. The rich make money work for them 24 hours a day while they sleep. Which asset do you think beats inflation best? Comment below.",
                "description": "Discover how the wealthiest 1% leverage compounding interest and smart money habits to build generational wealth. #Wealth #Money #MillionaireMindset #Investing #Finance #Shorts",
                "tags": ["wealth mindset", "how to get rich", "compound interest", "passive income", "finance hacks", "investing", "money tips", "millionaire habits", "shorts", "financial freedom"],
                "search_keyword": "money"
            },
            {
                "title": "3 Dark Psychology Tricks That Make Anyone Respect You",
                "script": "Here is a psychological hack that command respect in any room within 3 seconds. First, never break eye contact first when someone finishes speaking. Second, master the power of the 2-second pause before answering any question. It signals supreme confidence. Third, never explain yourself when you say no. Which of these psychological laws have you noticed people using on you?",
                "description": "Master behavioral psychology and instant social dominance with these subtle human interaction secrets. #Psychology #Mindset #BodyLanguage #Confidence #DarkPsychology #Shorts",
                "tags": ["psychology tricks", "dark psychology", "body language", "human behavior", "confidence hacks", "mind tricks", "social skills", "self improvement", "shorts", "facts"],
                "search_keyword": "luxury"
            },
            {
                "title": "The AI Revolution That Is Terrifying Silicon Valley",
                "script": "Silicon Valley researchers are sounding the alarm over a breakthrough in autonomous artificial intelligence. AI models are now writing and debugging their own neural architecture with zero human engineers involved. Within the next 3 years, more computing power will be generated than in the entire history of humanity combined. Will AI surpass human intelligence sooner than expected? Tell us below.",
                "description": "The rapid exponential evolution of artificial intelligence and autonomous machine learning is transforming reality. #AI #Technology #FutureTech #SiliconValley #Robotics #Shorts",
                "tags": ["artificial intelligence", "future tech", "ai news", "robotics", "singularity", "tech trends", "quantum computing", "silicon valley", "shorts", "innovation"],
                "search_keyword": "technology"
            },
            {
                "title": "The Mystery of Time Dilation That Stuns Physicists",
                "script": "Did you know that time ticks slower on your feet than on your head? According to Einstein's general relativity, the closer you are to a massive gravitational center like Earth, the slower time passes. Astronauts orbiting on the Space Station age slower than everyone on Earth. If you spent just 1 hour near a supermassive black hole, 7 years would pass back home. Mind-blowing, right?",
                "description": "Explore the strange laws of general relativity and gravitational time dilation across the cosmos. #Physics #ScienceFacts #Cosmos #Space #Universe #Shorts",
                "tags": ["time dilation", "einstein", "physics facts", "space mysteries", "black hole", "cosmos", "quantum physics", "science", "shorts", "astrophysics"],
                "search_keyword": "space"
            }
        ]

        selected = random.choice(high_cpm_pool)
        return {
            "title": selected["title"],
            "script": selected["script"],
            "description": self._append_monetization(selected["description"]),
            "tags": selected["tags"],
            "search_keyword": selected["search_keyword"]
        }


if __name__ == "__main__":
    generator = ContentGenerator()
    content = generator.generate()
    print(json.dumps(content, indent=2))
