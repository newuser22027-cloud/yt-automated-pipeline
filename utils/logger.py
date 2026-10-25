"""
Centralized Logging and Webhook Telemetry.
Dispatches formatted status notifications to Discord and Telegram webhooks.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import requests

from src.config import config

# Setup file & console logging
LOG_DIR = config.base_dir / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "pipeline.log"

logger = logging.getLogger("yt_pipeline")
logger.setLevel(logging.INFO)

# Avoid duplicate handlers on reload
if not logger.handlers:
    # Console formatting
    c_handler = logging.StreamHandler(sys.stdout)
    c_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    c_handler.setFormatter(c_format)
    logger.addHandler(c_handler)

    # File logging
    f_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    f_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    f_handler.setFormatter(f_format)
    logger.addHandler(f_handler)


def send_alert(
    status: str,
    title: str,
    details: str,
    fields: Optional[Dict[str, str]] = None
) -> None:
    """
    Sends rich telemetry alerts to Discord and/or Telegram.
    Status can be: 'SUCCESS', 'FAILURE', 'WARNING', 'INFO'.
    """
    logger.info(f"Dispatching Alert [{status}] - {title}")

    # Color codes for Discord Embeds
    color_map = {
        "SUCCESS": 0x2ECC71,  # Green
        "FAILURE": 0xE74C3C,  # Red
        "WARNING": 0xF39C12,  # Orange
        "INFO": 0x3498DB       # Blue
    }
    color = color_map.get(status.upper(), 0x95A5A6)

    # 1. Discord Webhook
    if config.discord_webhook_url and "xxxxxxxx" not in config.discord_webhook_url:
        discord_fields = []
        if fields:
            for k, v in fields.items():
                discord_fields.append({
                    "name": k,
                    "value": str(v),
                    "inline": True
                })

        embed = {
            "title": f"[{status.upper()}] {title}",
            "description": details[:2000],  # Discord limit protection
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "YouTube Automation Engine • Headless Runner"
            }
        }
        if discord_fields:
            embed["fields"] = discord_fields

        payload = {"embeds": [embed]}

        try:
            res = requests.post(
                config.discord_webhook_url,
                json=payload,
                timeout=10
            )
            if res.status_code not in (200, 204):
                logger.warning(f"Discord webhook responded with code {res.status_code}: {res.text}")
        except Exception as e:
            logger.error(f"Failed to transmit Discord webhook: {e}")
    else:
        logger.debug("DISCORD_WEBHOOK_URL not configured. Skipping Discord alert.")

    # 2. Telegram Alert (Optional)
    if config.telegram_bot_token and config.telegram_chat_id:
        tg_text = f"<b>[{status.upper()}] {title}</b>\n\n{details}"
        if fields:
            tg_text += "\n\n" + "\n".join([f"• <b>{k}</b>: {v}" for k, v in fields.items()])

        tg_url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
        try:
            requests.post(
                tg_url,
                json={
                    "chat_id": config.telegram_chat_id,
                    "text": tg_text[:4000],
                    "parse_mode": "HTML"
                },
                timeout=10
            )
        except Exception as e:
            logger.error(f"Failed to transmit Telegram message: {e}")
