# 🎓 Sanmati Admission Bot — Backend API

An AI-powered **WhatsApp admission chatbot + counselor dashboard REST API** for **Sanmati Engineering College, Washim**.

Built with **FastAPI + SQLAlchemy + SQLite**, deployable on **Railway**.

![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)
![WhatsApp](https://img.shields.io/badge/WhatsApp-Cloud%20API-25D366?logo=whatsapp)
![Railway](https://img.shields.io/badge/Deploy-Railway-8B5CF6?logo=railway)

---

## ✨ What This Does

### 🤖 WhatsApp Bot
- AI-powered admission counselor via Meta WhatsApp Cloud API
- **Multi-language** (English / Hindi / Marathi) selection on first contact
- **3-level interactive menu** (Category → Branch → Details) — zero AI calls for menu browsing
- Free-text questions answered by **Gemini / OpenRouter LLM** with conversation memory
- **Brochure PDF** delivery, campus info, fee structure, placement data
- **Lead scoring** (0–10) based on engagement & high-intent keywords

### 📊 Counselor Dashboard REST API *(New)*
A full REST API consumed by the React frontend dashboard:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/stats` | Dashboard stats + chart data |
| GET | `/api/students` | Filter/search/paginate student leads |
| GET | `/api/students/{id}` | Student detail + chat transcript + notes |
| POST | `/api/students` | Create student manually |
| POST | `/api/students/bulk` | Bulk import from CSV/Excel |
| PUT | `/api/students/{id}` | Edit student details |
| DELETE | `/api/students/{id}` | Delete student |
| PUT | `/api/students/{id}/status` | Update lead status |
| POST | `/api/students/{id}/notes` | Add counselor note |
| GET | `/api/students/export` | Download all students as CSV |
| GET | `/api/campaigns` | List campaign history |
| POST | `/api/campaigns` | Create campaign |

---

## 🏗️ Architecture

```
┌─────────────────────────┐     HTTP/REST      ┌────────────────────────┐
│   React Dashboard        │ ◄────────────────► │   FastAPI Backend       │
│   (Vercel)               │   /api/*           │   (Railway)             │
└─────────────────────────┘                    │                         │
                                               │  SQLAlchemy ORM         │
┌─────────────────────────┐                    │  SQLite (dev)           │
│   WhatsApp Cloud API     │ ◄────────────────► │  PostgreSQL (prod)      │
│   (Meta)                 │   /webhook         │                         │
└─────────────────────────┘                    └────────────────────────┘
                                                           │
                                               ┌───────────▼────────────┐
                                               │  Gemini / OpenRouter   │
                                               │  (LLM AI)              │
                                               └────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | Python 3.12, FastAPI 0.115 |
| **ORM / Database** | SQLAlchemy 2.0, SQLite (dev) / PostgreSQL (prod) |
| **AI Engine** | Google Gemini API, OpenRouter (fallback) |
| **WhatsApp** | Meta WhatsApp Cloud API v21.0 |
| **Deployment** | Railway (`railway.toml`) |
| **HTTP Client** | httpx (async) |

---

## 📁 Project Structure

```
Sanmati_bot/
├── app/
│   ├── main.py               # FastAPI entry point + CORS + router registration
│   ├── config.py             # Environment variable settings
│   ├── database.py           # SQLAlchemy engine + session factory
│   ├── models.py             # Student, Interaction, LeadNote, User, Campaign
│   ├── schemas.py            # Pydantic schemas (webhook + dashboard API)
│   ├── routers/
│   │   ├── webhook.py        # WhatsApp webhook handler (bot logic + menus)
│   │   └── dashboard.py      # Dashboard REST API (12 endpoints)  ← NEW
│   ├── services/
│   │   ├── gemini.py         # AI response generation
│   │   ├── whatsapp.py       # WhatsApp API helpers
│   │   └── lead_detector.py  # Hot lead keyword detection
│   └── utils/
│       └── helpers.py        # Webhook payload extraction
├── static/
│   ├── campus.jpg            # Campus image for welcome message header
│   └── brochure.pdf          # College brochure PDF
├── tests/
│   └── test_lead_detector.py
├── broadcast.py              # CLI broadcast tool
├── knowledge.txt             # College knowledge base for AI
├── railway.toml              # Railway deployment config               ← NEW
├── requirements.txt
└── .env.example              # Environment variable template
```

---

## 🚀 Quick Start (Local)

### 1. Clone & Install

```bash
git clone https://github.com/Bhaveshtarole/Sanmati_bot.git
cd Sanmati_bot
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
copy .env.example .env       # Windows
# cp .env.example .env       # Mac/Linux
```

Edit `.env` with your credentials:

| Variable | Description |
|---|---|
| `WHATSAPP_TOKEN` | Meta WhatsApp API access token |
| `WHATSAPP_PHONE_NUMBER_ID` | Your WhatsApp phone number ID |
| `WEBHOOK_VERIFY_TOKEN` | Custom token for webhook verification |
| `GEMINI_API_KEY` | Google Gemini API key |
| `OPENROUTER_API_KEY` | OpenRouter API key (fallback AI) |
| `DATABASE_URL` | Default: `sqlite:///sanmati.db` |
| `ALLOWED_ORIGINS` | CORS origins. Use `*` for local dev, Vercel URL for prod |

### 3. Run

```bash
python -m uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
```

- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

### 4. Expose Webhook (Development)

```bash
cloudflared tunnel --url http://localhost:8000
```

Set the tunnel URL as your webhook in Meta Business Manager:
```
https://your-tunnel-url/webhook
```

---

## 🌐 CORS Configuration

CORS is driven by the `ALLOWED_ORIGINS` environment variable:

| Environment | Value |
|---|---|
| Local dev | `ALLOWED_ORIGINS=*` (default, allows all) |
| Production | `ALLOWED_ORIGINS=https://your-app.vercel.app` |

---

## 🚢 Deploy to Railway

1. Push this repo to GitHub
2. Connect repo to Railway — it auto-detects `railway.toml`
3. Set environment variables in Railway dashboard (see `.env.example`)
4. Set `ALLOWED_ORIGINS` to your Vercel frontend URL
5. Add **Railway PostgreSQL** plugin and set `DATABASE_URL`
6. Update your Meta WhatsApp webhook URL to the Railway domain

```toml
# railway.toml (already included)
[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```

---

## 📡 WhatsApp Bot Flow

```
Student sends "Hi"
    │
    ▼
Language not set? ──YES──▶ Send picker [English] [Hindi] [Marathi]
    │
   NO
    │
    ▼
Greeting word? ──YES──▶ Send welcome menu with 3 buttons
    │
   NO
    │
    ▼
Menu button? ──YES──▶ Static response (no AI call, no cost)
    │
   NO
    │
    ▼
Free text ──▶ Gemini AI + conversation memory ──▶ Reply in student language
```

---

## 📊 Data Models

### Student
```
id, name, phone, course_interest, lead_score (0–10), is_hot_lead,
lead_status (new/in_progress/visit_scheduled/admitted/not_interested),
source, message_count, first_contact, last_active, created_at
```

### Interaction
```
id, student_id (FK), message_direction (inbound/outbound),
message_body, message_type, timestamp
```

### LeadNote
```
id, student_id (FK), user_id (FK), note_text, created_at
```

### Campaign *(New)*
```
id, message, recipient_group, recipient_count, sent_at
```

---

## 🧪 Testing

```bash
python -m pytest tests/ -v
```

---

## 📞 Programs Offered

**Engineering (B.E.):** CSE, Electrical, Mechanical, Civil, AI & Data Science  
**ITI Trades:** Fitter, Electrician, Welder, Turner, COPA  
**Nursing:** B.Sc Nursing, GNM, ANM

---

## 🤝 Partner Repos

| Repo | Description |
|---|---|
| **This repo** | FastAPI backend + WhatsApp bot |
| [sanmati-admissions-hub](https://github.com/yogeshbhange8/sanmati-admissions-hub) | React counselor dashboard (frontend) |

---

## 👨‍💻 Authors

**Bhavesh Tarole** — [GitHub](https://github.com/Bhaveshtarole)  
**Yogesh Bhange** — [GitHub](https://github.com/yogeshbhange8)

---

*Private — Sanmati Engineering College, Washim.*
