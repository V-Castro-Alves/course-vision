[English](#english) | [Português](#português-brasil)

# 👁️‍🗨️CourseVision (ClassClerkBot)

<p align="center">
  <img src="logo.jpeg" alt="logo" width="250" style="display: block; margin: 0 auto;" />
</p>

> **Transform your static college schedule into a dynamic AI-managed calendar via Telegram.**

[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![Gemini 2.0](https://img.shields.io/badge/AI-Gemini%202.0%20Flash-orange.svg)](https://aistudio.google.com/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![Telegram](https://img.shields.io/badge/Telegram-%230088cc.svg?logo=telegram&logoColor=white)](https://www.telegram.org/)


## ✨ Key Features

*   **📸 Intelligent OCR:** Snap a photo of your printed or digital schedule. Gemini extracts Subjects, Codes, Professors, and Classrooms with high precision.
*   **🗓️ Deterministic Scheduling:** Automatically maps extracted classes to the current week (Monday-Friday) using a smart 2-per-day logic.
*   **🔄 Auto-Sync:** Uploading a new schedule automatically wipes the old one for that week—no manual cleanup required.
*   **🔒 Granular Privacy:** Restrict access to specific Telegram User IDs.
*   **🤖 Model Resilience:** Automatic fallback logic ensures the bot stays online even if primary API quotas are hit.

---

## 🛠️ Architecture & Tech
CourseVision acts as the intelligent backend for schedule processing and management. It interfaces seamlessly with **ClassClerkBot**, your dedicated ✈️ Telegram bot, providing an intuitive chat interface for all your scheduling needs.

-   **Core:** `Python 3.14` with `python-telegram-bot`
-   **Vision Engine:** `google-genai` (Gemini 2.0 Flash) utilizing **Structured Outputs**
-   **Data Layer:** `SQLite` + `Pydantic` for strict schema validation
-   **DevOps:** Fully containerized with `Docker` & `Docker Compose`

### CI/CD & Quality Gates
To ensure code quality and project stability, CourseVision employs a robust CI/CD pipeline and local quality gates:

*   **Tools:** Ruff (linting/formatting), pip-audit (dependency security), Bandit (static analysis security), Pytest (unit testing).
*   **Docker Integration:** All CI checks run within Docker containers, ensuring a consistent and isolated environment.
*   **GitHub Actions:** Automated workflow (`.github/workflows/ci.yml`) runs all checks on `push` and `pull_request` to `main`.
*   **Local Checks:** `docker compose` commands are provided for local execution of these checks without needing local Python installations.

## Orchestration
CourseVision acts as the central orchestrator, managing the lifecycle of your schedule from image capture to database persistence.
```mermaid
graph TD
    User((📱 Telegram User)) <-->|Commands / Image| Bot[✈️ ClassClerkBot Interface]
    
    subgraph "Core System"
        Bot <-->|API Calls| CV[👁️ CourseVision Orchestrator]
        
        CV -->|1. Image + Prompt| Gemini[🤖 Gemini 2.0 Flash]
        Gemini -->|2. Structured JSON| CV
        
        CV -->|3. Mapping & Validation| Map[📅 Deterministic Logic]
        Map --> CV
        
        CV <-->|4. Read/Write| DB[(🗄️ SQLite Database)]
    end

style CV fill:#008000,stroke:#333,stroke-width:4px
```
---

## 🚀 Quick Start

### 1. Prerequisites
1.  **API Keys:** Get a [Gemini API Key](https://aistudio.google.com/) and a [Telegram Token](https://t.me/botfather).
2.  **ID:** Find your ID via [@userinfobot](https://t.me/userinfobot).

### 2. Setup
```bash
# Clone the repository
git clone [https://github.com/youruser/CourseVision.git](https://github.com/youruser/CourseVision.git)
cd CourseVision

# Create environment file
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run
**Using Docker (Recommended):**
```bash
docker compose up --build -d
```
**Using Python:**
```bash
pip install -r requirements.txt
python main.py
```

---

## 📌 Usage Flow

1.  **/start** to initialize.
2.  **/upload** to prep the AI.
3.  **Attach Image** — Send the schedule photo.
4.  **/today** or **/schedule** to see your week at a glance.

---

## 5. Final Polish Tips

*   **License:** This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
*   **Deterministic Logic Warning:** Note that several design and architectural decisions were made based on the specific structure needed by the author. For your personal use, it is recommended to adapt the logic to better fit the format of your needs.


---

## Português (Brasil)

### ✨ Funcionalidades Principais

*   **📸 OCR Inteligente:** Tire uma foto do seu horário impresso ou digital. O Gemini extrai Assuntos, Códigos, Professores e Salas de Aula com alta precisão.
*   **🗓️ Agendamento Determinístico:** Mapeia automaticamente as aulas extraídas para a semana atual (segunda a sexta-feira) usando uma lógica inteligente de 2 aulas por dia.
*   **🔄 Sincronização Automática:** Fazer upload de um novo horário apaga automaticamente o antigo para aquela semana — nenhuma limpeza manual é necessária.
*   **🔒 Privacidade Granular:** Restringe o acesso a IDs de Usuários específicos do Telegram.
*   **🤖 Resiliência do Modelo:** A lógica de fallback automático garante que o bot permaneça online mesmo se as cotas da API principal forem atingidas.

---

## 🛠️ Arquitetura e Tecnologia
CourseVision atua como o backend inteligente para processamento e gerenciamento de dados de horário. Ele se integra perfeitamente com o **ClassClerkBot**, seu ✈️ bot dedicado do Telegram, fornecendo uma interface de chat intuitiva para todas as suas necessidades de agendamento.

-   **Core:** `Python 3.14` com `python-telegram-bot`
-   **Mecanismo de Visão:** `google-genai` (Gemini 2.0 Flash) utilizando **Saídas Estruturadas**
-   **Camada de Dados:** `SQLite` + `Pydantic` para validação rigorosa de esquema
-   **DevOps:** Totalmente conteinerizado com `Docker` e `Docker Compose`

### CI/CD e Portões de Qualidade
Para garantir a qualidade do código e a estabilidade do projeto, o CourseVision emprega um pipeline robusto de CI/CD e portões de qualidade locais:

*   **Ferramentas:** Ruff (linting/formatação), pip-audit (segurança de dependências), Bandit (segurança de análise estática), Pytest (teste de unidade).
*   **Integração Docker:** Todas as verificações de CI são executadas dentro de contêineres Docker, garantindo um ambiente consistente e isolado.
*   **GitHub Actions:** O fluxo de trabalho automatizado (`.github/workflows/ci.yml`) executa todas as verificações em `push` e `pull_request` para `main`.
*   **Verificações Locais:** Comandos `docker compose` são fornecidos para execução local dessas verificações sem a necessidade de instalações locais de Python.

## Orchestration
CourseVision acts as the central orchestrator, managing the lifecycle of your schedule from image capture to database persistence.
```mermaid
graph TD
    User((📱 Telegram User)) <-->|Commands / Image| Bot[✈️ ClassClerkBot Interface]
    
    subgraph "Core System"
        Bot <-->|API Calls| CV[👁️ CourseVision Orchestrator]
        
        CV -->|1. Image + Prompt| Gemini[🤖 Gemini 2.0 Flash]
        Gemini -->|2. Structured JSON| CV
        
        CV -->|3. Mapping & Validation| Map[📅 Deterministic Logic]
        Map --> CV
        
        CV <-->|4. Read/Write| DB[(🗄️ SQLite Database)]
    end

style CV fill:#008000,stroke:#333,stroke-width:4px
```
---

## 🚀 Início Rápido

### 1. Pré-requisitos
1.  **Chaves de API:** Obtenha uma [Chave de API do Gemini](https://aistudio.google.com/) e um [Token do Telegram](https://t.me/botfather).
2.  **ID:** Encontre seu ID via [@userinfobot](https://t.me/userinfobot).

### 2. Configuração
```bash
# Clone o repositório
git clone [https://github.com/youruser/CourseVision.git](https://github.com/youruser/CourseVision.git)
cd CourseVision

# Crie o arquivo de ambiente
cp .env.example .env
# Edite .env com suas credenciais
```

### 3. Execução
**Usando Docker (Recomendado):**
```bash
docker compose up --build -d
```
**Usando Python:**
```bash
pip install -r requirements.txt
python main.py
```

---

## 📌 Fluxo de Uso

1.  **/start** para inicializar.
2.  **/upload** para preparar a IA.
3.  **Anexar Imagem** — Envie a foto do horário.
4.  **/today** ou **/schedule** para ver sua semana rapidamente.

---

## 5. Dicas Finais de Polimento

*   **Licença:** Este projeto é licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.
*   **Aviso de Lógica Determinística:** Observe que várias decisões de design e projeto, foram feitas com base na estrutura específica necessitada pelo autor. Para a sua utilização pessoal, é recomendado adaptar a lógica para que se encaixe melhor com o formato da sua necessidade.
