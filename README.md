#  Groupify

> Groupify is a platform which solves the  tedious task of doing the SWOT analysis of your project as well your idea.It also  let you analyse your coding style along with telling you how much ahead  you are as compared to another developers.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)
![Solara](https://img.shields.io/badge/Solara-Reactive_UI-6366f1)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-336791?logo=postgresql&logoColor=white)
![AI](https://img.shields.io/badge/AI-Ollama_%7C_CrewAI-ff6b6b)

---

##  Features

| Feature | Description |
|---|---|
|  **Premium Home Page** | Landing page with highly creative glassmorphism flashcards, glowing orbs, and grid overlays |
|  **Member Management** | Full CRUD for members with domain assignment. Dynamic themed UI that changes per skill domain |
| **Idea Refiner** | Patent-level gap analysis, novelty scoring (0-100), and technical refinement options |
|  **Repo Judge** | Submit any GitHub repo URL and our AI performs deep codebase analysis and delivers a hackathon style verdict with mentor feedback |
|  **Multi Domain** | Comprehensive support for Web/App Dev, ML, AI, Cloud, and Cybersecurity across all features |


```mermaid
graph TD
    %% Styling for High Contrast Neon
    classDef frontend fill:#1e1b4b,stroke:#0ea5e9,stroke-width:4px,color:#fff,rx:15,ry:15;
    classDef backend fill:#1e1b4b,stroke:#8b5cf6,stroke-width:4px,color:#fff,rx:15,ry:15;
    classDef ai fill:#1e1b4b,stroke:#ec4899,stroke-width:4px,color:#fff,rx:15,ry:15;
    classDef db fill:#1e1b4b,stroke:#10b981,stroke-width:4px,color:#fff,rx:15,ry:15;
    classDef cloud fill:#1e1b4b,stroke:#f59e0b,stroke-width:4px,color:#fff,rx:15,ry:15;

    subgraph UserZone [" User Interface"]
        UI[" <b>Reactive Frontend</b><br/>(Solara / Python)"]:::frontend
    end

    subgraph ServiceZone [" Backend Logic"]
        API["<b>FastAPI Layer</b><br/>(Endpoints)"]:::backend
        Biz[" <b>Core Services</b><br/>(Business Logic)"]:::backend
    end

    subgraph IntelligenceZone [" AI Multi-Model"]
        Ollama[" <b>Local LLM</b><br/>(Ollama)"]:::ai
        Gemini[" <b>Cloud AI</b><br/>(Gemini 2.0)"]:::ai
    end

    subgraph DataZone ["Persistent Storage"]
        PG["<b>PostgreSQL</b><br/>(Main DB)"]:::db
        SQL[" <b>SQLite</b><br/>(Fallback)"]:::db
    end

    %% Flow Connections with Neon Styling
    UI ==>|Secure API Calls| API
    API --> Biz
    Biz ==>|Query/Store| PG
    PG -.->|Failover| SQL
    Biz ==>|Prompt| Ollama
    Biz -.->|Fallback| Gemini

    %% Link Styling
    linkStyle 0,2,4 stroke:#0ea5e9,stroke-width:3px;
    linkStyle 1,3,5 stroke:#8b5cf6,stroke-width:3px;
```

---

## Feature Workflow

```mermaid
sequenceDiagram
    autonumber
    
    %% Premium Participants
    participant U as  User
    participant S as  Solara UI
    participant F as  FastAPI
    participant A as  AI Engine
    participant D as  Database

    Note over U,D:  End-to-End Premium Assessment Flow 

    U->>+S: Start Assessment (Select Domains)
    S->>+F: Initialize Session Request
    F->>+A: Craft AI Intro Persona
    A-->>-F: Personalized Opening
    F->>+D: Log Active Session
    D-->>-F: Session Stored
    F-->>-S: Session ID + AI Greeting
    S-->>-U: Show Dynamic Chat Interface

    rect rgb(30, 27, 75)
        Note right of U: Interactive Real-Time Loop
        U->>+S: Send Response / Question
        S->>+F: Process Message
        F->>+A: Analyze Context & Generate
        A-->>-F: Intelligent Agent Reply
        F->>+D: Update Transcript
        D-->>-F: Saved
        F-->>-S: Agent Text
        S-->>-U: Smooth UI Update
    end

    U->>+S: Complete Evaluation
    S->>+F: Request Final Scoring
    F->>+A: Deep Multi-Domain Analysis
    A-->>-F: Structured KPI Data (JSON)
    F->>+D: Mark Scored & Save Results
    D-->>-F: Confirmed
    F-->>-S: Final Report
    S-->>-U: 🎉 Display Astonishing Scorecard
```



##  Project Structure

```
group_maker/
├── backend/
│   └── app/
│       ├── main.py                
│       ├── models.py               
│       ├── schemas.py             
│       ├── crud.py                
│       ├── database.py            
│       ├── routers/
│       │   ├── members.py        
│       │   ├── assessment.py      
│       │   ├── repo_judge.py      
│       │   ├── project_suggest.py 
│       │   └── idea_validator.py 
│       └── services/              
│           └── llm_factory.py     
├── solara_app/
│   ├── app.py                     
│   ├── assets/
│   │   └── custom.css             
│   └── pages/
│       ├── home.py               
│       ├── members.py             
│       ├── assessment.py          
│       ├── project_suggest.py    
│       ├── repo_judge.py           
│       └── idea_refiner.py       
├── requirements.txt
├── render.yaml                
└── .env                       
```

---

##  Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI, SQLAlchemy, Pydantic |
| **Database** | PostgreSQL (Supabase)  auto fallback to SQLite |
| **Frontend** | Solara (Python native reactive UI) |
| **AI / LLM** | **Hybrid Model Factory** (Gemini 2.0 Flash via OpenRouter  Ollama Local) |
| **Agents** | CrewAI, LangChain |
| **Deployment** | Render.com (Blueprint via `render.yaml`) |

---

##  Getting Started (Local)

### 1. Clone & install

```bash
git clone https://github.com/keshavmishra27/group_maker.git
cd group_maker
python -m venv venv
venv\Scripts\activate #for windows
source venv/bin/activate #for linux/mac
pip install -r requirements.txt 
```

### 2. Configure environment

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://<user>:<password>@<host>:5432/<db>
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_BASE_URL=http://localhost:11434
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=google/gemini-2.0-flash-001
API_URL=http://localhost:8000
```

> **Tip:** Omit `DATABASE_URL` to auto-fallback to local SQLite (`group_maker.db`).

### 3. Pull the Ollama model

Make sure [Ollama](https://ollama.com/) is installed and running:

```bash
ollama pull qwen2.5:3b
```

### 4. Start the backend

```bash
uvicorn backend.app.main:app --reload --port 8000
```

- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`

### 5. Start the frontend

```bash
solara run solara_app/app.py
```

- UI: `http://localhost:8765`

---

##  API Endpoints

### Members

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/members/` | List all members (optional `?domain_id=`) |
| `GET` | `/members/domains` | List all domains |
| `GET` | `/members/by-domain` | Members grouped by domain |
| `POST` | `/members/` | Create a member with domain assignments |
| `POST` | `/members/bulk` | Bulk create members |
| `PUT` | `/members/{id}` | Update a member |
| `DELETE` | `/members/{id}` | Delete a member |

### Assessment

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/assess/start` | Start a new AI assessment session |
| `POST` | `/assess/chat` | Send a student message, get AI reply |
| `POST` | `/assess/score/{id}` | End session & get CrewAI generated scores |
| `GET` | `/assess/domains` | List available assessment domains |

### Repo Judge

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/repo-judge/analyze` | Submit a GitHub repo for AI evaluation |


### Project Suggestion

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/project-suggest/suggest` | Get AI generated project ideas for multiple domains |
| `GET` | `/project-suggest/health` | Project suggestion health check |
| `POST` | `/idea-validator/check` | Check idea similarity vs current market |
| `POST` | `/idea-validator/refine` | Get patent level refinement & novelty scoring |


**Services deployed:**
- **`group-maker-api`** → FastAPI backend
- **`group-maker-ui`** → Solara frontend

**Required env vars (set in Render dashboard):**

| Variable | Service | Description |
|---|---|---|
| `DATABASE_URL` | API | PostgreSQL connection string |
| `OPENAI_API_KEY` | API | For AI features (if using OpenAI) |
| `VAPI_API_KEY` | API | Vapi calling agent key (optional) |
| `API_URL` | UI | Points to deployed backend URL |

---

##  Database Models

| Model | Description |
|---|---|
| **`Member`** | Name, category (senior/intermediate/junior), linked domains |
| **`Domain`** | Skill domain (e.g. Web Dev, ML, Cybersecurity) |
| **`MemberDomain`** | Many to many join table |
| **`AssessmentSession`** | Student name, domains tested, chat transcript, scores, status |
