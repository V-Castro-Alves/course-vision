# 🗺️ CourseVision Roadmap

> This roadmap tracks the evolution of CourseVision from a working prototype into a robust, extensible, and community-friendly project. Items are organized by status across all four areas: **New Features**, **Technical Improvements**, **UX / Bot Experience**, and **Docs & Community**.

---

## ✅ Done

> What's already shipped and working.

### New Features
- [x] OCR-based schedule extraction via Gemini 2.0 Flash
- [x] Deterministic weekly mapping (Monday–Friday, 2 classes/day logic)
- [x] Auto-sync: uploading a new schedule replaces the old week's data automatically
- [x] Granular access control via Telegram User ID allowlist
- [x] `/today` and `/schedule` commands for quick week overview
- [x] `/upload` flow for image-based schedule ingestion

### Technical Improvements
- [x] Structured outputs with Pydantic schema validation
- [x] SQLite persistence layer
- [x] Automatic model fallback when primary API quota is hit
- [x] Full Docker & Docker Compose containerization

### UX / Bot Experience
- [x] `/start` initialization command
- [x] Single-image upload flow via Telegram attachment

### Docs & Community
- [x] Bilingual README (English + Português)
- [x] Quick Start guide with Docker and Python paths
- [x] MIT License

---

## 🔄 In Progress

> Actively being worked on or planned for the immediate next cycle.

### New Features
- [ ] **Change /upload command behavior**: Make so that the user can send a photo without needing to type `/upload` first. The bot will automatically detect that a photo has been sent and will ask if it should be processed.

### Technical Improvements
- [ ] Improve OCR prompt engineering for edge-case schedule formats
- [ ] Add structured logging (replace raw `print` statements)
- [ ] Write unit tests for the scheduling/mapping logic
- [ ] Add a `.env.example` with all required variables documented

### UX / Bot Experience
- [ ] Better error messages when OCR extraction fails or returns partial data
- [ ] Confirmation message after `/upload` showing what was extracted (subject count, days covered)

### Docs & Community
- [ ] Add `CONTRIBUTING.md` with contribution guidelines
- [ ] Document the deterministic scheduling logic so others can adapt it

---

## 📋 Planned

> Validated ideas queued for future development.

### New Features
- [ ] `/remind` command — set a Telegram reminder X minutes before a class
- [ ] Export schedule to `.ics` / Google Calendar format
- [ ] **Visual Schedule Generation**: Use a library like Pillow to generate a clean, color-coded .png calendar of the week and send it back to the user after /upload.

### Technical Improvements
- [ ] Replace SQLite with a proper DB (PostgreSQL) for multi-user scalability
- [ ] Add CI/CD pipeline (GitHub Actions) for linting and tests
- [ ] Implement retry logic with exponential backoff on API failures
- [ ] Abstract the AI provider layer to make swapping models easier
- [ ] **Input Validation**: In handlers.py, when a user sends a photo, add a check for file size. Large 4K images might hit Telegram's download limits or Gemini's token limits unnecessarily
- [ ] **Pydantic strictness**: In ClassRow model (referenced in GEMINI.md), add Field(description=...). This acts as "prompt engineering" inside the code, telling the AI exactly what to look for

### UX / Bot Experience
- [ ] Inline keyboard buttons for common commands (no need to type `/today`)
- [ ] Weekly digest message sent automatically on Monday morning
- [ ] Support for sending schedule as a formatted image/PDF response

### Docs & Community
- [ ] Architecture diagram showing bot ↔ backend ↔ Gemini flow
- [ ] Video walkthrough / GIF demo for the README
- [ ] `CHANGELOG.md` to track releases
- [ ] GitHub issue templates (bug report, feature request)
- [ ] Publish to Docker Hub for one-command deployment
- [ ] **Visual Architecture Diagram**: Use a Mermaid.js diagram in README
- [ ] **Detailed .env.example**: Ensure the README explains that ALLOWED_TELEGRAM_IDS should be a comma-separated list
- [ ] **"Troubleshooting" Section**: Add a section in the README about how to handle "hallucinations." Advise users to take photos with high contrast and no glare

---

## 💡 Ideas / Backlog

> Speculative or longer-horizon ideas — not yet committed.

- Web dashboard as an alternative to the Telegram interface
- Support for photo-to-schedule from WhatsApp (via Twilio or similar)
- Natural language queries: *"When do I have Math this week?"*

---

*Want to contribute? Check out [`CONTRIBUTING.md`](CONTRIBUTING.md) (coming soon) or open an issue!*
