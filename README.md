# 🛰️ CourseVision (ClassClerkBot)

**CourseVision** is an AI-integrated academic assistant designed to automate the bridge between static college schedules and real-time mobile coordination. Now powered by Gemini 2.0/1.5 Flash with Structured Outputs.

## ✨ Features

- **Screenshot Parsing:** Upload a photo of your schedule; Gemini extracts class details (Day, Time, Subject, Room, Professor) with high precision using Structured Outputs.
- **Precision Reminders:** Telegram alerts 10 minutes before class with your specific Room/Lab location.
- **Attendance Tracker:** Interactive `[✅ Attended]` and `[❌ Skipped]` buttons to log your presence.
- **Exam Countdown:** Track exam dates and receive 24-hour and same-day notifications.
- **Attendance Analytics:** Use `/stats` to see your skip rate and presence history.
- **Privacy Lock:** User ID verification ensures only YOU can access the bot.

## 🛠️ Tech Stack

- **Language:** Python 3.10+
- **AI Brain:** Google Gemini (google-genai SDK)
- **Bot Framework:** `python-telegram-bot`
- **Database:** SQLite3
- **Data Validation:** Pydantic
- **Deployment:** Docker & Docker Compose

## 🚀 Deployment Guide

### 1. Prerequisites
- A **Gemini API Key** from [Google AI Studio](https://aistudio.google.com/).
- A **Telegram Bot Token** from [@BotFather](https://t.me/botfather).
- Your **Telegram User ID** (Get it from [@userinfobot](https://t.me/userinfobot)).

### 2. File Structure
```text
CourseVision/
├── main.py            # Telegram Bot & Logic
├── parsing.py         # Standalone Extraction Tool
├── database.db        # SQLite Storage (Auto-generated)
├── Dockerfile         # Container Definition
├── docker-compose.yml # Service Configuration
└── requirements.txt   # Python Dependencies
```

## ▶️ Quick Start

1. Create `.env` in project root:

```bash
TELEGRAM_TOKEN=your_bot_token
AUTHORIZED_USER_ID=your_telegram_user_id
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash (optional)
DATABASE_PATH=database.db
```

2. Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

3. Run locally:

```bash
python3 main.py
```

4. Or run with Docker:

```bash
docker compose up --build -d
```


## 📌 Telegram Commands

- `/start` (or `/help`): Show welcome text and usage
- `/upload`: tell the bot you are about to send the schedule image
- Send the image after `/upload`: Gemini will parse it and insert classes into the database
- `/schedule`: list stored classes
- `/add_exam YYYY-MM-DD Subject [notes]`: add upcoming exam
- `/exams`: list all exams
- `/stats`: attendance analytics (attended/skipped ratio)

## 💡 Notes

- **Smart Parsing:** The bot uses Gemini's Structured Output to reliably extract tabular data from images, handling complex layouts better than traditional OCR.
- **Model Fallback:** If the primary model (e.g., Gemini 2.0 Flash) is out of quota, it automatically tries Gemini 1.5 Flash.
- **Class Reminders:** Sent 10 minutes before class time with attendance buttons.
- **Exam Alerts:** Sent 24h before and on exam day.
- **Security:** `AUTHORIZED_USER_ID` restricts interaction to your Telegram account only.


