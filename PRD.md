# Product Requirements Document (PRD)
## Sanmati Admission Bot — WhatsApp AI Counselor

| Field | Value |
|---|---|
| **Product Name** | Sanmati Admission Bot |
| **Version** | 2.0.1 |
| **Author** | Bhavesh Tarole |
| **Date** | April 2026 |
| **Status** | Active Development |
| **Client** | Sanmati Engineering College, Washim, Maharashtra |

---

## 1. Executive Summary

The Sanmati Admission Bot is an AI-powered WhatsApp chatbot that automates the admission counseling process for Sanmati Engineering College, Washim. It replaces manual phone calls and walk-in inquiries with a 24/7 intelligent assistant that handles student questions, provides course information, captures leads, and broadcasts admission updates — all through WhatsApp.

### Problem Statement

- **Manual counseling** doesn't scale — counselors can handle ~20 calls/day
- **Students expect instant responses** — 70% of inquiries happen outside office hours
- **Lead management** is manual — no tracking of student interest or follow-ups
- **Multi-language gap** — rural Maharashtra students prefer Hindi/Marathi communication

### Solution

An always-on WhatsApp bot that:
- Answers unlimited student queries 24/7 using AI
- Communicates in English, Hindi, and Marathi
- Automatically scores and prioritizes leads
- Broadcasts admission announcements at scale
- Costs 76% less than competing SaaS solutions

---

## 2. Target Users

### Primary Users
| User | Description | Needs |
|---|---|---|
| **Prospective Students** | 12th pass students from Maharashtra, looking for engineering/ITI/nursing admissions | Instant answers about courses, fees, eligibility, placements |
| **Parents** | Parents researching colleges for their children | College credibility, fee structure, placement records, hostel facilities |

### Secondary Users
| User | Description | Needs |
|---|---|---|
| **Admission Office** | College admission staff managing inquiries | Lead tracking, broadcast tools, hot lead alerts |
| **Faculty/HODs** | Department heads assigned to follow up on interested students | Student contact info, course interest data |

---

## 3. User Journey

### New Student Flow
```
1. Student discovers bot (QR code / ad / word-of-mouth)
2. Sends first message on WhatsApp
3. Bot asks: "Select your language" [English] [Hindi] [Marathi]
4. Student picks a language → Saved permanently
5. Bot shows welcome menu with campus image:
   [🎓 Courses] [🏫 Campus & Fees] [📥 Brochure]
6. Student taps "Courses" → Category menu:
   [⚙️ Engineering] [🏥 Nursing] [🔧 ITI]
7. Student taps "Engineering" → Branch list:
   [CSE] [Electrical] [Mechanical] [Civil] [AI&DS]
8. Student taps "CSE" → Detailed info + follow-up:
   [💰 Fees] [📄 Admission] [📞 Request Call]
9. Student asks free-text questions → AI answers in chosen language
10. Bot scores the lead (0-10) based on engagement + intent
```

### Returning Student Flow
```
1. Student sends any message
2. Bot recognizes student (by phone number)
3. Language already set → Responds in saved language
4. Greeting → Welcome menu (in their language)
5. Free text → AI with full conversation memory
```

---

## 4. Functional Requirements

### 4.1 Language Selection (P0 — Must Have)
| ID | Requirement | Status |
|---|---|---|
| L-01 | Show language picker on first contact | ✅ Done |
| L-02 | Support English, Hindi, Marathi | ✅ Done |
| L-03 | Persist language choice per student | ✅ Done |
| L-04 | All static messages localized in 3 languages | ✅ Done |
| L-05 | AI responds in Hinglish/Marathlish (not pure Hindi/Marathi) | ✅ Done |

### 4.2 Interactive Menu System (P0 — Must Have)
| ID | Requirement | Status |
|---|---|---|
| M-01 | 3-level drill-down: Category → Branch → Details | ✅ Done |
| M-02 | Engineering: CSE, EE, ME, CE, AI&DS | ✅ Done |
| M-03 | ITI: Fitter, Electrician, COPA | ✅ Done |
| M-04 | Nursing: B.Sc, GNM, ANM | ✅ Done |
| M-05 | Branch details: seats, duration, HOD, phone | ✅ Done |
| M-06 | Follow-up buttons after branch info: Fees / Admission / Call | ✅ Done |
| M-07 | Campus highlights with brochure CTA | ✅ Done |
| M-08 | Brochure PDF delivery | ✅ Done |
| M-09 | Text shortcuts: "1" = Courses, "2" = Campus, "3" = Brochure | ✅ Done |

### 4.3 AI Counselor (P0 — Must Have)
| ID | Requirement | Status |
|---|---|---|
| A-01 | Free-text question answering via LLM | ✅ Done |
| A-02 | Knowledge base context (knowledge.txt) | ✅ Done |
| A-03 | Conversation memory (last 10 messages) | ✅ Done |
| A-04 | Language-aware responses | ✅ Done |
| A-05 | Personalized with student name | ✅ Done |
| A-06 | College-specific system prompt | ✅ Done |

### 4.4 Lead Management (P0 — Must Have)
| ID | Requirement | Status |
|---|---|---|
| D-01 | Auto-capture: phone, name, source | ✅ Done |
| D-02 | Track course interest per student | ✅ Done |
| D-03 | Lead scoring (0-10) | ✅ Done |
| D-04 | Hot lead detection (score ≥ 7) | ✅ Done |
| D-05 | Session time tracking | ✅ Done |
| D-06 | Message count tracking | ✅ Done |
| D-07 | Interaction logging (inbound + outbound) | ✅ Done |

### 4.5 Broadcasting (P1 — Important)
| ID | Requirement | Status |
|---|---|---|
| B-01 | Send template messages from CSV/Excel | ✅ Done |
| B-02 | Rate-limited batch sending | ✅ Done |
| B-03 | Success/failure logging | ✅ Done |
| B-04 | CLI interface | ✅ Done |

### 4.6 Read Receipts (P1 — Important)
| ID | Requirement | Status |
|---|---|---|
| R-01 | Mark incoming messages as read (blue ticks) | ✅ Done |
| R-02 | Non-blocking (doesn't slow down response) | ✅ Done |

### 4.7 Admin Dashboard (P2 — Planned)
| ID | Requirement | Status |
|---|---|---|
| W-01 | Web dashboard to view all leads | ⏳ Planned |
| W-02 | Filter leads by score, course, status | ⏳ Planned |
| W-03 | Analytics: conversion rates, response times | ⏳ Planned |
| W-04 | Faculty assignment for hot leads | ⏳ Planned |
| W-05 | Broadcast management from UI | ⏳ Planned |

---

## 5. Non-Functional Requirements

### 5.1 Performance
| Requirement | Target |
|---|---|
| Webhook response time | < 2 seconds (static menus) |
| AI response time | < 10 seconds (including LLM call) |
| Concurrent students | 100+ simultaneous |
| Database capacity | 50,000+ students |

### 5.2 Reliability
| Requirement | Target |
|---|---|
| Uptime | 99.9% (Railway deployment) |
| Message delivery | 99%+ (WhatsApp API SLA) |
| Data persistence | All interactions logged |
| Error handling | Graceful fallbacks for API failures |

### 5.3 Security
| Requirement | Implementation |
|---|---|
| Secrets management | Environment variables (.env) |
| API authentication | Bearer token (WhatsApp) |
| Dashboard auth | JWT-based (planned) |
| Database | No PII in logs |

### 5.4 Scalability
| Scale | Infrastructure |
|---|---|
| 0-5K students | SQLite + single process |
| 5K-50K students | PostgreSQL (Supabase) + 4 workers |
| 50K+ students | PostgreSQL + load balancer + Redis cache |

---

## 6. Technical Architecture

### System Components
```
┌─────────────────────────────────────────────────────────┐
│                    PRODUCTION SETUP                       │
│                                                           │
│  ┌──────────┐    ┌───────────┐    ┌──────────────────┐  │
│  │  Meta WA  │◄──►│  FastAPI   │◄──►│  Supabase (PG)  │  │
│  │  Cloud    │    │  Backend   │    │  Database        │  │
│  │  API      │    └─────┬─────┘    └──────────────────┘  │
│  └──────────┘          │                                  │
│                   ┌─────▼─────┐    ┌──────────────────┐  │
│                   │ OpenRouter │    │  Vercel          │  │
│                   │ (LLM AI)  │    │  (Dashboard UI)  │  │
│                   └───────────┘    └──────────────────┘  │
│                                                           │
│  Hosted on: Railway (~₹600/mo)                           │
└─────────────────────────────────────────────────────────┘
```

### Data Models
```
Student
├── id, phone, name
├── language (en/hi/mr)
├── course_interest
├── lead_score (0-10)
├── is_hot_lead
├── message_count
├── total_session_minutes
├── first_contact, last_active
└── assigned_faculty_id

Interaction
├── id, student_id
├── message_direction (inbound/outbound)
├── message_body
├── message_type (text/interactive/document)
└── timestamp

LeadNote
├── id, student_id, author_id
├── note_text
└── created_at
```

---

## 7. Competitive Positioning

| Feature | AiSensy (₹1.5K/mo) | Wati (₹2.5K/mo) | QuickReply (₹8K/mo) | **Our Bot (₹600/mo)** |
|---|---|---|---|---|
| AI responses | Rule-based | Rule-based | Limited AI | ✅ Full LLM |
| Conversation memory | ❌ | ❌ | ❌ | ✅ 10-msg context |
| Multi-language AI | Templates only | Templates only | ❌ | ✅ Dynamic |
| Lead scoring | ❌ | Basic | ✅ | ✅ Auto 0-10 |
| Code ownership | ❌ | ❌ | ❌ | ✅ 100% owned |
| Annual cost | ₹18,000 | ₹30,000 | ₹96,000 | **₹7,200** |

---

## 8. Metrics & Success Criteria

| Metric | Target | How Measured |
|---|---|---|
| **Response rate** | 100% of messages get a reply | Interaction logs |
| **Avg response time** | < 5 seconds | Timestamp analysis |
| **Lead capture rate** | 80%+ of conversations capture course interest | `course_interest` field coverage |
| **Hot lead identification** | Auto-flag top 20% of engaged students | `is_hot_lead` = True |
| **Language adoption** | 40%+ students choose Hindi/Marathi | `language` field distribution |
| **Student satisfaction** | < 5% block rate | WhatsApp quality rating |

---

## 9. Roadmap

| Phase | Timeline | Features |
|---|---|---|
| **Phase 1** ✅ | March 2026 | Core bot, menu system, AI counselor |
| **Phase 2** ✅ | April 2026 | Multi-language, lead scoring, broadcast, read receipts |
| **Phase 3** ⏳ | May 2026 | Admin dashboard (React), Supabase migration, Railway deploy |
| **Phase 4** 📋 | June 2026 | Analytics, human handover, payment integration |
| **Phase 5** 📋 | July 2026 | Multi-college SaaS version |

---

## 10. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| WhatsApp account ban | 🔴 High — bot goes offline | Follow Meta policies strictly; no unsolicited broadcasts; include opt-out |
| OpenRouter API downtime | 🟡 Medium — AI stops working | Graceful fallback message with office phone number |
| Rate limiting by Meta | 🟡 Medium — messages delayed | Batch broadcasting with rate limits; start slow |
| Student data privacy | 🟡 Medium — legal risk | No PII in logs; secured database; .env for secrets |

---

*Last updated: April 12, 2026*
