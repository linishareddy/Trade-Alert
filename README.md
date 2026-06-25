#  SentinelAI

A full-stack, AI-powered algorithmic trading platform that ingests signals from Discord, parses them, validates them against real-time technical indicators (EMA/VWAP), automatically executes them via Alpaca/Webull, and provides an intelligent dashboard and AI Chatbot to monitor your portfolio.

---

##  Key Features

- **📡 Discord Signal Ingestion:** A self-bot integration that listens to specific Discord channels and captures trade alerts in real-time.
- **🧠 Smart Parsing & Validation:** Uses intelligent parsing to extract ticker, action, and price points. Trades are then passed through a rigorous validation gate checking real-time EMA (9, 13, 21) and VWAP indicators before execution.
- **⚡ Auto-Execution Broker:** Direct integration with Alpaca and Webull to seamlessly execute paper or live trades via bracket orders (with Take Profit and Stop Loss).
- **🤖 AI Chat Assistant (SentinelAI):** An LLM-powered chatbot running on Groq (Llama 3) that translates natural language into SQL. You can chat with your database to ask questions like *"What are my active trades?"* or *"Did I enter any positions today?"*
- **💻 Modern Next.js Dashboard:** A sleek, responsive dashboard built with Next.js, Tailwind CSS, and React Query to monitor signals, active trades, and interact with the AI assistant.

---

## 🛠️ Tech Stack

**Backend:**
- Python 3.12, FastAPI
- PostgreSQL, SQLAlchemy (asyncpg)
- Groq LLMs (Llama 3), Discord.py
- Alpaca API / Webull API

**Frontend:**
- Next.js 14 (App Router), React
- Tailwind CSS, Lucide Icons
- React Query, React Markdown

---

## 📂 Project Structure

```text
Trade-Alert/
├── backend/                  # FastAPI Backend
│   ├── agents/               # AI Agents (Discord ingestion, parsing, chatting)
│   ├── db/                   # SQLAlchemy Models and DB Configuration
│   ├── frontend/             # Next.js Dashboard & Chat UI
│   ├── routers/              # API Endpoints (v1)
│   ├── services/             # Validation and Trade Execution Services
│   ├── scripts/              # Utilities (Schema generation, etc.)
│   └── main.py               # Application Entry Point
```

---

## ⚙️ Setup & Installation

### 1. Prerequisites
- **Python 3.12+**
- **Node.js 18+**
- **PostgreSQL Database**
- API Keys for **Discord**, **Groq**, and **Alpaca**

### 2. Backend Setup

Open a terminal and navigate to the backend directory:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory with your credentials (see `.env.example` if available):
```env
# Database
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tradealert

# Integrations
DISCORD_USER_TOKEN=your_discord_token
DISCORD_TARGET_CHANNEL_IDS=your_channel_id
GROQ_API_KEY=your_groq_api_key
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret

# Trading Config
EXECUTION_ENABLED=true
EMA_VWAP_ENABLED=false
```

Start the backend server (this also starts the Discord bot and background agents):
```bash
python main.py
```
*The backend API will run on http://localhost:8000*

### 3. Frontend Setup

Open a new terminal and navigate to the frontend directory:
```bash
cd backend/frontend
npm install
```

Start the Next.js development server:
```bash
npm run dev
```
*The frontend dashboard will run on http://localhost:3000*

---

## 💬 Using the AI ChatBot (SentinelAI)

Once the application is running, open [http://localhost:3000/chat](http://localhost:3000/chat). 

You can interact with your trading database using natural language. Try asking:
- *"Show me my active trades"*
- *"What's my best performing ticker?"*
- *"Did I enter any positions today?"*

SentinelAI will intelligently map your question to the correct database tables, execute the SQL query safely, and present the data directly in the chat interface.

---

## ⚠️ Disclaimer

**This software is for educational and research purposes only.** Do not use this software to trade with real money without extensive testing and paper trading. You are fully responsible for your own trading decisions and any financial losses incurred.
