"""
Content Generator Module.
Leverages OpenAI GPT-4o-mini to produce high-CTR titles, scripts, tags,
SEO descriptions, and visual stock search queries.
"""

import os
import json
from typing import Dict, Any, List
from openai import OpenAI

from src.config import config
from utils.logger import logger


class ContentGenerator:
    """Handles prompt engineering, JSON-mode completions, and metadata synthesis."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or config.openai_api_key
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None

    def generate(self, niche: str = None) -> Dict[str, Any]:
        """
        Generates complete video package in JSON format.
        Falls back to a structured default if OpenAI is unreachable or offline.
        """
        topic = niche or config.video_niche
        logger.info(f"Generating content for niche: '{topic}'")

        if not self.client:
            logger.warning("OPENAI_API_KEY is not set. Generating fallback offline content package.")
            return self._generate_fallback(topic)

        prompt = f"""
You are a viral YouTube Shorts creator and algorithmic strategist.
Generate an irresistible, factual, 30-to-45-second vertical video script about: "{topic}".

Rules:
1. "title": Must have high Click-Through-Rate (CTR), punchy, curiosity-inducing, under 90 characters.
2. "script": Spoken narrative, around 70-90 words. Start with an immediate curiosity hook in the first 3 seconds (no intro/filler like 'Hey guys'). Deliver high-value factual content and end with an engaging retention thought.
3. "description": 2-3 engaging sentences explaining the topic, followed by 5 relevant viral hashtags.
4. "tags": An array of exactly 10 high-search-volume tags.
5. "search_keyword": A single, high-relevance, simple visual search term (1-2 words) suitable for finding free stock background footage on Pexels (e.g. 'space galaxy', 'microscope cell', 'deep ocean', 'robotics').

Return ONLY a valid JSON object matching this schema:
{{
  "title": "string",
  "script": "string",
  "description": "string",
  "tags": ["tag1", "tag2", ...],
  "search_keyword": "string"
}}
"""

        try:
            response = self.client.chat.completions.create(
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

            # Validate keys
            required_keys = ["title", "script", "description", "tags", "search_keyword"]
            for key in required_keys:
                if key not in data:
                    raise KeyError(f"Missing required key in generated content: {key}")

            # Enhance description with automated monetization links
            data["description"] = self._append_monetization(data["description"])
            logger.info(f"Content generated successfully: '{data['title']}'")
            return data

        except Exception as e:
            logger.error(f"OpenAI generation error: {e}. Falling back to default payload.")
            return self._generate_fallback(topic)

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
        """Provides a safe, offline default payload when API is unavailable."""
        title = "The Mystery of Black Holes That Stuns Physicists"
        script = (
            "Did you know that inside a black hole, space and time literally swap roles? "
            "Once you cross the event horizon, moving forward in time becomes as inevitable "
            "as moving toward the singularity. Even light, travelling at 300,000 kilometers "
            "per second, cannot escape its gravitational grasp. What do you think happens "
            "on the other side? Let us know below."
        )
        description = (
            "Explore the strange reality inside a black hole where space and time reverse. "
            "#ScienceFacts #Space #Physics #Shorts #Cosmos"
        )
        tags = [
            "space facts", "black hole", "astrophysics", "science",
            "cosmos", "physics mysteries", "universe", "nasa", "shorts", "education"
        ]
        search_keyword = "space galaxy"

        return {
            "title": title,
            "script": script,
            "description": self._append_monetization(description),
            "tags": tags,
            "search_keyword": search_keyword
        }


if __name__ == "__main__":
    generator = ContentGenerator()
    content = generator.generate()
    print(json.dumps(content, indent=2))
