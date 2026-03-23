# 🛰️ CourseVision (ClassClerkBot)

## English

**CourseVision** is an AI-integrated academic assistant designed to automate the bridge between static college schedules and real-time mobile coordination. Now powered by Gemini 2.0/1.5 Flash with Structured Outputs.

### ✨ Features

- **Screenshot Parsing:** Upload a photo of your schedule; Gemini extracts class details (Subject, Code, Professor, Classroom). Day and date information is then *deterministically assigned* based on the current week's Monday (first two classes to Monday, next two to Tuesday, etc., up to Friday). Existing classes for the current week are automatically replaced upon new upload.
- **Privacy Lock:** User ID verification ensures only who YOU choose can access the bot.

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
- **Authorized Telegram User IDs** (optional, comma-separated).

#### 2. File Structure
```text
CourseVision/
├── main.py            # Entry point for the bot (simplified description for README)
├── Dockerfile         # Container Definition
├── docker-compose.yml # Service Configuration
├── requirements.txt   # Python Dependencies
├── .env.example       # Example environment variables
├── core/
│   ├── config.py      # Configuration settings
│   ├── database.py    # Database interactions
│   ├── handlers.py    # Telegram bot command handlers
│   ├── i18n.py        # Internationalization setup
│   ├── main.py        # Core bot logic
│   ├── parsing.py     # Gemini vision parsing logic
│   └── responses.json # Bot response messages
└── data/
    └── database.db    # SQLite Storage (Auto-generated)
```

### ▶️ Quick Start

1.  Create `.env` in project root:

    ```bash
    TELEGRAM_TOKEN=your_bot_token
    AUTHORIZED_USER_ID=your_telegram_user_id
    TELEGRAM_USERS_IDS=authorized_user_ids (optional, comma-separated)
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

### 💡 Notes

-   **Smart Parsing:** The bot uses Gemini's Structured Output to extract tabular data from images. Day and date information is deterministically assigned after extraction, and uploading a new schedule automatically replaces the current week's schedule.
-   **Model Fallback:** If the primary model (e.g., Gemini 2.0 Flash) runs out of quota, it automatically tries other available models.
-   **Security:** `AUTHORIZED_USER_ID` and `TELEGRAM_USERS_IDS` restricts interaction to only the Telegram accounts you choose.

### 📚 Future Enhancements (To-Dos)

-   **Enhanced Exam Management:** Implement the ability to add and manage exam dates, including customizable reminders (e.g., one day before, and right before the exam).
-   **Attendance Tracking:** Develop features to track attendance for classes and record instances of skipped classes.
-   **Configurable Class Reminders:** Allow users to set reminders for regular classes (e.g., 15 minutes before they start).
-   **Manual Schedule Editing:** Enable users to manually add, remove, or modify individual classes in their schedule.
-   **Multi-week and Recurring Schedules:** Extend the system to support parsing and managing schedules spanning multiple weeks, and implement functionality for recurring schedules across semesters or academic years.
-   **User Preferences and Customization:** Introduce user-specific settings for reminder timings, default language, and other personalized options.

---

## Português (Brasil)

**CourseVision** é um assistente acadêmico integrado a IA, projetado para automatizar a ponte entre horários estáticos de faculdade e a coordenação móvel em tempo real. Agora alimentado pelo Gemini 2.0/1.5 Flash com Saídas Estruturadas.

### ✨ Funcionalidades

-   **Análise de Imagem de Horário:** Envie uma foto do seu horário; o Gemini extrai os detalhes da aula (Assunto, Código, Professor, Sala de Aula). As informações de dia e data são então *atribuídas deterministicamente* com base na segunda-feira da semana atual (duas primeiras aulas para segunda, as próximas duas para terça, etc., até sexta-feira). As aulas existentes para a semana atual são automaticamente substituídas ao fazer um novo upload.
-   **Bloqueio de Privacidade:** A verificação do ID de usuário garante que apenas quem VOCÊ escolher possa acessar o bot.

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
-   **IDs de Usuários Autorizados do Telegram** (opcional, separados por vírgula).

#### 2. Estrutura de Arquivos
```text
CourseVision/
├── main.py            # Ponto de entrada para o bot
├── Dockerfile         # Definição do Contêiner
├── docker-compose.yml # Configuração do Serviço
├── requirements.txt   # Dependências Python
├── .env.example       # Exemplo de variáveis de ambiente
├── core/
│   ├── config.py      # Configurações
│   ├── database.py    # Interações com o banco de dados
│   ├── handlers.py    # Manipuladores de comandos do bot Telegram
│   ├── i18n.py        # Configuração de internacionalização
│   ├── main.py        # Lógica central do bot
│   ├── parsing.py     # Lógica de análise de visão do Gemini
│   └── responses.json # Mensagens de resposta do bot
└── data/
    └── database.db    # Armazenamento SQLite (Gerado Automaticamente)
```

### ▶️ Início Rápido

1.  Crie o arquivo `.env` na raiz do projeto:

    ```bash
    TELEGRAM_TOKEN=seu_token_do_bot
    AUTHORIZED_USER_ID=seu_id_de_usuario_do_telegram
    TELEGRAM_USERS_IDS=ids_dos_usuarios_autorizados (opcional, separados por vírgula)
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

### 💡 Notas

-   **Análise Inteligente:** O bot usa a Saída Estruturada do Gemini para extrair dados tabulares de imagens. As informações de dia e data são atribuídas deterministicamente após a extração, e o upload de um novo horário substitui automaticamente o horário da semana atual.
-   **Fallback de Modelo:** Se o modelo principal (por exemplo, Gemini 2.0 Flash) ficar sem cota, ele tenta automaticamente outros modelos disponíveis.
-   **Alertas de Exame:** As notificações são enviadas 24h antes e no dia do exame.
-   **Segurança:** `AUTHORIZED_USER_ID` e `TELEGRAM_USERS_IDS` restringem a interação apenas às contas do Telegram que você escolher.

### 📚 Próximos Aprimoramentos (To-Dos)

-   **Gerenciamento Aprimorado de Exames:** Implementar a capacidade de adicionar e gerenciar datas de exames, incluindo lembretes personalizáveis (por exemplo, um dia antes e imediatamente antes do exame).
-   **Controle de Presença:** Desenvolver funcionalidades para rastrear a presença em aulas e registrar as ausências.
-   **Lembretes Configuráveis para Aulas Regulares:** Permitir que os usuários configurem lembretes para aulas regulares (por exemplo, 15 minutos antes do início da aula).
-   **Edição Manual de Horários:** Habilitar os usuários a adicionar, remover ou modificar manualmente aulas individuais em seus horários.
-   **Horários Multissemanais e Recorrentes:** Estender o sistema para suportar a análise e o gerenciamento de horários que abrangem múltiplas semanas, e implementar funcionalidades para horários recorrentes em semestres ou anos acadêmicos.
-   **Preferências e Personalização do Usuário:** Introduzir configurações específicas do usuário para horários de lembretes, idioma padrão e outras opções personalizadas.
