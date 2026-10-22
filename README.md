# 🚀 YouTube Automated Content Engine

A zero-cost, fully automated, headless YouTube Shorts production and publishing pipeline. It generates factual, high-retention vertical videos (1080x1920) on a daily Cron schedule and publishes them directly to your YouTube channel using the YouTube Data API v3.

---

## 🏗️ Architecture & Technology Stack

| Stage | Technology | Cost | Description |
|---|---|---|---|
| **Orchestration & Cron** | GitHub Actions | **$0.00** | Runs daily at 12:00 UTC with 2,000 free monthly build minutes |
| **Script & Metadata** | OpenAI GPT-4o-mini | **~$0.0001 / run** | High-CTR titles, engaging 40s scripts, SEO tags & descriptions |
| **Voiceover Synthesis** | Edge-TTS Neural Audio | **$0.00** | Natural human voices (`en-US-ChristopherNeural` / `en-US-JennyNeural`) |
| **Visual Footage** | Pexels Video API | **$0.00** | Free HD vertical stock videos matching keyword queries |
| **Video Assembly** | MoviePy + FFmpeg | **$0.00** | 1080x1920 vertical auto-crop, audio-sync, and high-contrast title overlays |
| **Auto-Publishing** | YouTube Data API v3 | **$0.00** | Headless OAuth 2.0 refresh-token uploader (Free 10,000 quota units/day) |
| **Telemetry & Alerts** | Discord / Telegram Webhooks | **$0.00** | Instant embeds reporting execution success, video URLs, or tracebacks |

---

## 📁 Repository Directory Structure

```text
yt-automation-engine/
├── .github/
│   └── workflows/
│       └── pipeline.yml       # Production Cron & manual trigger configuration
├── src/
│   ├── __init__.py
│   ├── config.py              # Environment variables & Pydantic settings
│   ├── content_generator.py   # GPT-4o-mini script, title, tags & monetization block
│   ├── audio_generator.py     # Free Edge-TTS neural voiceover synthesizer
│   ├── media_fetcher.py       # Pexels HD visual footage downloader & fallbacks
│   ├── video_renderer.py      # MoviePy 1080x1920 vertical shorts assembler
│   └── youtube_uploader.py    # YouTube Data API v3 OAuth refresh-token publisher
├── tests/
│   └── test_pipeline.py       # Modular health-check suite
├── utils/
│   ├── logger.py              # Centralized logging & Discord webhook alerts
│   └── get_youtube_token.py   # Local one-time OAuth token generation script
├── requirements.txt           # Production dependencies
├── .env.example               # Configuration and secrets template
├── .gitignore                 # Excludes secrets, temporary files, and video renders
├── README.md                  # Comprehensive documentation and setup guide
└── main.py                    # Master orchestrator with retry loops and telemetry
```

---

## ⚡ Quick Start: Local Testing

### 1. Create Virtual Environment & Install Dependencies
Open PowerShell or your preferred terminal in `yt-automation-engine/`:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

*(On macOS/Linux: `source venv/bin/activate`)*

### 2. Configure Local Credentials
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Open `.env` and provide your `OPENAI_API_KEY` and `PEXELS_API_KEY`.

### 3. Run a Local Dry-Run (Renders Video without Uploading)
```powershell
python main.py --dry-run
```
The rendered vertical video will be saved in `output/final_output.mp4` and its metadata in `output/metadata.json`!

---

## 🔑 YouTube API Setup (One-Time Procedure)

To allow the cloud runner to upload videos without browser popups, generate a permanent refresh token once locally:

1. **Google Cloud Console**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/).
   - Create a project (e.g., `YouTube-Automation-Engine`).
   - Navigate to **APIs & Services $\rightarrow$ Library**, search for **YouTube Data API v3**, and click **Enable**.
   - Navigate to **OAuth consent screen**:
     - User Type: **External**.
     - Add your Gmail as a **Test User**.
   - Navigate to **Credentials $\rightarrow$ Create Credentials $\rightarrow$ OAuth client ID**:
     - Application type: **Desktop App**.
     - Name: `YouTube Uploader`.
     - Click **Download JSON** and save the file in this folder as `client_secret.json`.

2. **Generate Your Refresh Token**:
   Run the interactive helper:
   ```powershell
   python utils/get_youtube_token.py
   ```
   A browser window opens. Log into your Google channel account and grant permission.
   The script outputs your `YOUTUBE_REFRESH_TOKEN` and the minified `YOUTUBE_CLIENT_SECRET_JSON`.

---

## ☁️ Deploying to GitHub Actions (24/7 Headless Automation)

1. **Initialize Git & Push to GitHub**:
   ```powershell
   git init
   git add .
   git commit -m "feat: complete headless youtube automated content engine"
   git branch -M main
   git remote add origin https://github.com/<your-username>/yt-automated-pipeline.git
   git push -u origin main
   ```

2. **Set Repository Secrets**:
   In your GitHub repository, go to **Settings $\rightarrow$ Secrets and variables $\rightarrow$ Actions $\rightarrow$ New repository secret** and add:

   | Secret Name | Description / Value |
   |---|---|
   | `OPENAI_API_KEY` | Your OpenAI API key (`sk-proj-...`) |
   | `PEXELS_API_KEY` | Your free Pexels API key |
   | `YOUTUBE_CLIENT_SECRET_JSON` | The full minified JSON content from `client_secret.json` |
   | `YOUTUBE_REFRESH_TOKEN` | The refresh token string from `get_youtube_token.py` |
   | `DISCORD_WEBHOOK_URL` | Your Discord Channel Webhook URL |
   | `AMAZON_AFFILIATE_TAG` | *(Optional)* Your Amazon Associates tag |
   | `VIDIQ_AFFILIATE_ID` | *(Optional)* Your VidIQ affiliate ID |

3. **Trigger First Live Run**:
   - Go to the **Actions** tab on GitHub.
   - Select **YouTube Automated Content Pipeline**.
   - Click **Run workflow** (you can optionally check `Dry Run` for testing).
   - Once executed, verify your Discord channel receives the success embed with the YouTube video URL!

---

## 💰 Built-in Monetization Architecture

The system automatically appends affiliate blocks into the video description upon generation:
1. **Amazon Associates**: Contextual links to creator gear or topic-related books.
2. **SaaS Tools**: VidIQ / TubeBuddy creator ranking referral links.
3. **Digital Store / Bio Link**: Direct viewers to Gumroad templates or Linktree.
4. **AdSense Ready**: Videos meet standard monetization criteria when eligibility thresholds are reached.
