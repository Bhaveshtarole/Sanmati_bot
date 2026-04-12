# 🎓 Sanmati Admission Bot

An AI-powered WhatsApp chatbot for **Sanmati Engineering College, Washim** that automates admission counseling, lead management, and student engagement via the Meta WhatsApp Cloud API.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)
![WhatsApp](https://img.shields.io/badge/WhatsApp-Cloud%20API-25D366?logo=whatsapp)
![License](https://img.shields.io/badge/License-Private-red)

---

## ✨ Features

### 🤖 AI-Powered Counseling
- Real **LLM-based** AI counselor (via OpenRouter) — not rule-based
- **Conversation memory** — remembers last 10 messages for context
- Answers any question about admissions, fees, placements, eligibility naturally

### 🌐 Multi-Language Support
- **Language selection** on first contact (English / Hindi / Marathi)
- All static messages localized in 3 languages
- AI responds in **Hinglish** (Hindi + English) or **Marathlish** (Marathi + English) naturally

### 📋 Interactive Menu System
- **3-level interactive menu** — no AI calls needed for browsing
  - Category → Branch → Detailed Info
- Programs covered: **B.E. (5 branches) | ITI (5 trades) | Nursing (3 programs)**
- Course details include seats, duration, HOD name, contact number

### 📊 Smart Lead Scoring
- Automatic **0-10 lead scoring** based on:
  - High-intent keywords (fees, admission, seats)
  - Message engagement (count + session time)
  - Course-specific interest
- Hot lead detection for priority follow-up

### 📢 Broadcast Tool
- Send **WhatsApp template messages** to student lists
- Rate-limited batch sending (100/hour)
- Supports CSV and Excel files

### 📱 Read Receipts
- Instant **blue tick** (mark-as-read) on incoming messages
- Makes the bot feel responsive before AI processes

---

## 🏗️ Architecture

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   WhatsApp   │──────▶│   FastAPI    │──────▶│   Database   │
│  Cloud API   │◀──────│   Backend    │       │  SQLite/PG   │
└──────────────┘       └──────┬───────┘       └──────────────┘
                              │
                       ┌──────▼───────┐
                       │  OpenRouter  │
                       │   (LLM AI)  │
                       └──────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| **Backend** | Python 3.10+, FastAPI |
| **AI Engine** | OpenRouter API (StepFun Step-3.5-Flash) |
| **WhatsApp** | Meta WhatsApp Cloud API v21.0 |
| **Database** | SQLAlchemy (SQLite for dev, PostgreSQL for prod) |
| **HTTP Client** | httpx (async) |
| **Broadcast** | Pandas + rate-limited batch sending |

---

## 📁 Project Structure

```
sanmati-bot/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py             # Environment config
│   ├── database.py           # SQLAlchemy setup
│   ├── models.py             # Student, Interaction, LeadNote models
│   ├── schemas.py            # Pydantic schemas
│   ├── routers/
│   │   └── webhook.py        # WhatsApp webhook + menu logic + localization
│   ├── services/
│   │   ├── gemini.py         # AI response generation (OpenRouter)
│   │   ├── whatsapp.py       # WhatsApp API (send text, buttons, lists, docs)
│   │   └── lead_detector.py  # Hot lead keyword detection
│   └── utils/
│       └── helpers.py        # Message extraction from webhook payload
├── static/
│   ├── campus.jpg            # Campus image for welcome header
│   └── brochure.pdf          # College brochure (not in repo)
├── tests/
│   └── test_lead_detector.py # 31 tests
├── broadcast.py              # CLI broadcast tool
├── knowledge.txt             # AI knowledge base
├── requirements.txt
└── .env.example
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/Bhaveshtarole/Sanmati_bot.git
cd Sanmati_bot
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

Required environment variables:

| Variable | Description |
|---|---|
| `WHATSAPP_TOKEN` | Meta WhatsApp API access token |
| `WHATSAPP_PHONE_NUMBER_ID` | Your WhatsApp phone number ID |
| `WEBHOOK_VERIFY_TOKEN` | Custom token for webhook verification |
| `OPENROUTER_API_KEY` | OpenRouter API key for AI responses |
| `DATABASE_URL` | Database URL (default: `sqlite:///sanmati.db`) |

### 3. Run the Bot

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Expose Webhook (Development)

```bash
# Using Cloudflare Tunnel
cloudflared tunnel --url http://localhost:8000
```

Set the tunnel URL as your webhook in Meta Business Manager:
```
https://your-tunnel-url/webhook
```

---

## 📡 Webhook Flow

```
Student sends "Hi" on WhatsApp
    │
    ▼
Meta sends POST /webhook
    │
    ▼
Is language set? ──NO──▶ Send language picker [EN] [HI] [MR]
    │
   YES
    │
    ▼
Is it a greeting? ──YES──▶ Send welcome menu with buttons
    │
    NO
    │
    ▼
Is it a menu button? ──YES──▶ Send static response (no AI)
    │
    NO
    │
    ▼
Free text ──▶ AI with conversation memory ──▶ Reply in student's language
```

---

## 📢 Broadcasting

Send template messages to a list of students:

```bash
python broadcast.py --file students.csv --template admission_open_2025 --batch-size 50
```

CSV format:
```csv
phone,language
918010716238,en
919876543210,hi
```

---

## 🧪 Testing

```bash
python -m pytest tests/ -v
```

All **31 tests** covering lead detection, keyword matching, and edge cases.

---

## 🌍 Supported Languages

| Language | Code | Style |
|---|---|---|
| English | `en` | Standard English |
| Hindi | `hi` | Hinglish (Hindi + English mix) |
| Marathi | `mr` | Marathlish (Marathi + English mix) |

---

## 📞 Programs Offered

### Engineering (B.E.) — 4 Years
| Branch | Seats | HOD |
|---|---|---|
| Computer Science (CSE) | 60 | Prof. S.R. Tayade |
| Electrical Engineering | 60 | Prof. Nayanish Ambhore |
| Mechanical Engineering | 60 | Prof. Swapnil Kurhekar |
| Civil Engineering | 60 | Prof. Kunal Ghadge |
| AI & Data Science (AI&DS) | 60 | Prof. M.G. Jaiswal |

### ITI Trades
Fitter, Electrician, Welder, Turner, COPA

### Nursing
B.Sc Nursing, GNM, ANM

---

## 🚢 Deployment

**Recommended:** Railway (backend) + Supabase (database)

```bash
# Procfile
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set environment variables in Railway dashboard and update the webhook URL in Meta Business Manager.

---

## 📄 License

Private — Sanmati Engineering College, Washim.

---

## 👨‍💻 Author

**Bhavesh Tarole**  
[GitHub](https://github.com/Bhaveshtarole)
