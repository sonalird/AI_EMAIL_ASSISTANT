# Api keys
Create a .env file and add:

OPENAI_API_KEY=your_key_here

# Multi-agent Email Assistant (LangGraph)

This project implements a six-agent workflow with LangGraph:
- Input Parsing Agent
- Intent Detection Agent
- Tone Stylist Agent
- Draft Writer Agent
- Personalization Agent
- Review & Validator Agent
- Routing & Memory Agent

## Setup
1. Create venv and activate (macOS):
   - python3 -m venv .venv
   - source .venv/bin/activate
2. Install deps:
   - pip install -r requirements.txt
3. Optional: create `.env` from `.env.example` and set `SIGNATURE` or API keys.

## Run
python -m src.main "Subject: Follow-up\nTo: Alex\nRequirements: friendly, concise\nFollowing up on last week meeting."

