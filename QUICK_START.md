# Quick Start Guide (3 Minutes)

## What This Is

A dashboard that detects unfair treatment patterns in healthcare and suggests how to fix them using AI.

## The 3 Steps

### 1. Install & Setup
```bash
cd C:\Users\lokes\Downloads\Equity_Bias_Detection
pip install -r requirements.txt
```

### 2. Configure (Optional)
```bash
# Copy the environment template
copy .env.example .env

# Add your Anthropic API key to .env (optional for AI features)
# ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Run
```bash
streamlit run dashboard/app.py
```

Your browser will open to `http://localhost:8501`

---

## What You'll See

**6 Pages**:
1. **Executive Dashboard** — Overview and key metrics
2. **Bias Detection** — Find disparities (e.g., "Black patients get treatment X 40% less")
3. **Interventions** — AI-generated solutions
4. **Provider Accountability** — Track performance
5. **Compliance Reports** — Download regulatory documents
6. **AI Summary** — Claude-powered strategic insights

---

## That's It!

Click around the dashboard and explore. No other setup needed.

For detailed information, see [DETAILED_GUIDE.md](DETAILED_GUIDE.md).
