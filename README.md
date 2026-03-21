# 🛰️ CourseVision (ClassClerkBot)

**CourseVision** is an AI-integrated academic assistant designed to automate the bridge between static college schedules and real-time mobile coordination. Now powered by Gemini 2.0/1.5 Flash with Structured Outputs.

## ✨ Features

- **Screenshot Parsing:** Upload a photo of your schedule; Gemini extracts class details (Subject, Code, Professor, Classroom). Day and date information is then *deterministically assigned* based on the current week's Monday (first two classes to Monday, next two to Tuesday, etc., up to Friday). Existing classes for the current week are automatically replaced upon new upload.
- **Exam Countdown:** Track exam dates and receive 24-hour and same-day notifications.
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
DEBUG=TRUE (optional)
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

- `/start` (or `/help`): Mostra o texto de boas-vindas e uso dos comandos.
- `/upload`: Notifica o bot que você enviará uma imagem de horário. O bot processará a imagem, atribuirá datas para a semana atual (2 aulas por dia, de segunda a sexta) e substituirá quaisquer horários existentes para a semana.
- Envie a imagem após `/upload`: O Gemini irá analisá-la e inserir as aulas no banco de dados.
- `/schedule`: Lista todas as aulas da semana atual (segunda a sexta-feira) em português, com datas formatadas como DD/MM e exibição aprimorada.
- `/today`: Exibe apenas as aulas programadas para o dia atual em português, com datas formatadas como DD/MM e exibição aprimorada.
- `/add_exam YYYY-MM-DD Assunto [notas]`: Adiciona um exame à agenda.
- `/exams`: Lista todos os exames agendados.
- `/stats`: Mostra as estatísticas de presença (atendido/faltou), se aplicável. (Note: o acompanhamento de presença está atualmente desativado.)

## 💡 Notes

- **Smart Parsing:** O bot usa o Structured Output do Gemini para extrair dados tabulares de imagens. As informações de dia e data são atribuídas deterministicamente após a extração, e o upload de um novo horário substitui automaticamente o horário da semana atual.
- **Model Fallback:** Se o modelo principal (por exemplo, Gemini 2.0 Flash) estiver sem cota, ele tenta automaticamente outros modelos disponíveis.
- **Alertas de Exame:** Notificações são enviadas 24h antes e no dia do exame.
- **Segurança:** `AUTHORIZED_USER_ID` restringe a interação apenas à sua conta do Telegram.
- **Acompanhamento de Presença:** O acompanhamento de presença está atualmente desativado devido à remoção da extração de tempo detalhada.


