# 🛰️ CourseVision (ClassClerkBot)

## English

**CourseVision** is an AI-integrated academic assistant designed to automate the bridge between static college schedules and real-time mobile coordination. Now powered by Gemini 2.0/1.5 Flash with Structured Outputs.

### ✨ Features

- **Screenshot Parsing:** Upload a photo of your schedule; Gemini extracts class details (Subject, Code, Professor, Classroom). Day and date information is then *deterministically assigned* based on the current week's Monday (first two classes to Monday, next two to Tuesday, etc., up to Friday). Existing classes for the current week are automatically replaced upon new upload.
- **Exam Countdown:** Track exam dates and receive 24-hour and same-day notifications.
- **Privacy Lock:** User ID verification ensures only YOU can access the bot.

### 🛠️ Tech Stack

- **Language:** Python 3.10+
- **AI Brain:** Google Gemini (google-genai SDK)
- **Bot Framework:** `python-telegram-bot`
- **Database:** SQLite3
- **Data Validation:** Pydantic
- **Deployment:** Docker & Docker Compose

### 🚀 Deployment Guide

#### 1. Prerequisites
- A **Gemini API Key** from [Google AI Studio](https://aistudio.google.com/).
- A **Telegram Bot Token** from [@BotFather](https://t.me/botfather).
- Your **Telegram User ID** (Get it from [@userinfobot](https://t.me/userinfobot)).

#### 2. File Structure
```text
CourseVision/
├── main.py            # Telegram Bot & Logic
├── parsing.py         # Standalone Extraction Tool
├── database.db        # SQLite Storage (Auto-generated)
├── Dockerfile         # Container Definition
├── docker-compose.yml # Service Configuration
└── requirements.txt   # Python Dependencies
```

### ▶️ Quick Start

1.  Create `.env` in project root:

    ```bash
    TELEGRAM_TOKEN=your_bot_token
    AUTHORIZED_USER_ID=your_telegram_user_id
    GEMINI_API_KEY=your_gemini_api_key
    GEMINI_MODEL=gemini-2.0-flash (optional)
    DATABASE_PATH=database.db
    DEBUG=TRUE (optional)
    ```

2.  Install dependencies:

    ```bash
    python3 -m pip install -r requirements.txt
    ```

3.  Run locally:

    ```bash
    python3 main.py
    ```

4.  Or run with Docker:

    ```bash
    docker compose up --build -d
    ```

### 📌 Telegram Commands

-   `/start` (or `/help`): Displays the welcome message and command usage.
-   `/upload`: Notifies the bot that you will send a schedule image. The bot will process the image, assign dates for the current week (2 classes per day, Monday to Friday), and replace any existing schedules for the week.
-   Send the image after `/upload`: Gemini will analyze it and insert the classes into the database.
-   `/schedule`: Lists all classes for the current week (Monday to Friday) with dates formatted as DD/MM and enhanced display.
-   `/today`: Displays only the classes scheduled for the current day with dates formatted as DD/MM and enhanced display.
-   `/add_exam YYYY-MM-DD Subject [notes]`: Adds an exam to the schedule.
-   `/exams`: Lists all scheduled exams.
-   `/stats`: Shows attendance statistics (attended/missed), if applicable. (Note: attendance tracking is currently disabled.)

### 💡 Notes

-   **Smart Parsing:** The bot uses Gemini's Structured Output to extract tabular data from images. Day and date information is deterministically assigned after extraction, and uploading a new schedule automatically replaces the current week's schedule.
-   **Model Fallback:** If the primary model (e.g., Gemini 2.0 Flash) runs out of quota, it automatically tries other available models.
-   **Exam Alerts:** Notifications are sent 24h before and on the day of the exam.
-   **Security:** `AUTHORIZED_USER_ID` restricts interaction to only your Telegram account.
-   **Attendance Tracking:** Attendance tracking is currently disabled due to the removal of detailed time extraction.

---

## Português (Brasil)

**CourseVision** é um assistente acadêmico integrado a IA, projetado para automatizar a ponte entre horários estáticos de faculdade e a coordenação móvel em tempo real. Agora alimentado pelo Gemini 2.0/1.5 Flash com Saídas Estruturadas.

### ✨ Funcionalidades

-   **Análise de Imagem de Horário:** Envie uma foto do seu horário; o Gemini extrai os detalhes da aula (Assunto, Código, Professor, Sala de Aula). As informações de dia e data são então *atribuídas deterministicamente* com base na segunda-feira da semana atual (duas primeiras aulas para segunda, as próximas duas para terça, etc., até sexta-feira). As aulas existentes para a semana atual são automaticamente substituídas ao fazer um novo upload.
-   **Contagem Regressiva para Exames:** Acompanhe as datas dos exames e receba notificações 24 horas antes e no dia do exame.
-   **Bloqueio de Privacidade:** A verificação do ID de usuário garante que apenas VOCÊ possa acessar o bot.

### 🛠️ Pilha de Tecnologia

-   **Linguagem:** Python 3.10+
-   **IA Central:** Google Gemini (SDK google-genai)
-   **Estrutura do Bot:** `python-telegram-bot`
-   **Banco de Dados:** SQLite3
-   **Validação de Dados:** Pydantic
-   **Implantação:** Docker e Docker Compose

### 🚀 Guia de Implantação

#### 1. Pré-requisitos
-   Uma **Chave de API do Gemini** do [Google AI Studio](https://aistudio.google.com/).
-   Um **Token de Bot do Telegram** do [@BotFather](https://t.me/botfather).
-   Seu **ID de Usuário do Telegram** (Obtenha-o em [@userinfobot](https://t.me/userinfobot)).

#### 2. Estrutura de Arquivos
```text
CourseVision/
├── main.py            # Lógica e Bot do Telegram
├── parsing.py         # Ferramenta de Extração Independente
├── database.db        # Armazenamento SQLite (Gerado Automaticamente)
├── Dockerfile         # Definição do Contêiner
├── docker-compose.yml # Configuração do Serviço
└── requirements.txt   # Dependências Python
```

### ▶️ Início Rápido

1.  Crie o arquivo `.env` na raiz do projeto:

    ```bash
    TELEGRAM_TOKEN=seu_token_do_bot
    AUTHORIZED_USER_ID=seu_id_de_usuario_do_telegram
    GEMINI_API_KEY=sua_chave_de_api_do_gemini
    GEMINI_MODEL=gemini-2.0-flash (opcional)
    DATABASE_PATH=database.db
    DEBUG=TRUE (opcional)
    ```

2.  Instale as dependências:

    ```bash
    python3 -m pip install -r requirements.txt
    ```

3.  Execute localmente:

    ```bash
    python3 main.py
    ```

4.  Ou execute com Docker:

    ```bash
    docker compose up --build -d
    ```

### 📌 Comandos do Telegram

-   `/start` (ou `/help`): Mostra a mensagem de boas-vindas e uso dos comandos.
-   `/upload`: Notifica o bot que você enviará uma imagem de horário. O bot processará a imagem, atribuirá datas para a semana atual (2 aulas por dia, de segunda a sexta) e substituirá quaisquer horários existentes para a semana.
-   Envie a imagem após `/upload`: O Gemini a analisará e inserirá as aulas no banco de dados.
-   `/schedule`: Lista todas as aulas da semana atual (segunda a sexta-feira) em português, com datas formatadas como DD/MM e exibição aprimorada.
-   `/today`: Exibe apenas as aulas programadas para o dia atual em português, com datas formatadas como DD/MM e exibição aprimorada.
-   `/add_exam AAAA-MM-DD Assunto [notas]`: Adiciona um exame à agenda.
-   `/exams`: Lista todos os exames agendados.
-   `/stats`: Mostra as estatísticas de presença (presente/faltou), se aplicável. (Nota: o acompanhamento de presença está atualmente desativado.)

### 💡 Notas

-   **Análise Inteligente:** O bot usa a Saída Estruturada do Gemini para extrair dados tabulares de imagens. As informações de dia e data são atribuídas deterministicamente após a extração, e o upload de um novo horário substitui automaticamente o horário da semana atual.
-   **Fallback de Modelo:** Se o modelo principal (por exemplo, Gemini 2.0 Flash) ficar sem cota, ele tenta automaticamente outros modelos disponíveis.
-   **Alertas de Exame:** As notificações são enviadas 24h antes e no dia do exame.
-   **Segurança:** `AUTHORIZED_USER_ID` restringe a interação apenas à sua conta do Telegram.
-   **Acompanhamento de Presença:** O acompanhamento de presença está atualmente desativado devido à remoção da extração detalhada de tempo.
