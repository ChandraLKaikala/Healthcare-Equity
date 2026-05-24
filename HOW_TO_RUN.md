# How to Run

## One-Line Start Command

```bash
streamlit run dashboard/app.py
```

Then open your browser to **`http://localhost:8501`**

---

## Full Setup (First Time Only)

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Step 1: Install Dependencies
```bash
cd C:\Users\lokes\Downloads\Equity_Bias_Detection
pip install -r requirements.txt
```

### Step 2: Configure Environment (Optional)
```bash
# Copy the template
copy .env.example .env

# Edit .env and add credentials (if you have them)
# ANTHROPIC_API_KEY=sk-ant-...
# DATABRICKS_... (if using your own Databricks instance)
```

If you skip this, the dashboard will work with demo data.

### Step 3: Run Dashboard
```bash
streamlit run dashboard/app.py
```

Browser opens automatically to `http://localhost:8501`

---

## To Stop the Dashboard
Press `Ctrl+C` in the terminal where you ran the command.

---

## If Something Goes Wrong

**Port already in use?**
```bash
streamlit run dashboard/app.py --server.port 8502
```

**Missing dependencies?**
```bash
pip install -r requirements.txt --upgrade
```

**Clear cache:**
```bash
streamlit cache clear
```

---

## Next Time You Want to Run It

Just use the one-line command:
```bash
streamlit run dashboard/app.py
```

No setup needed!

---

For more details, see [DETAILED_GUIDE.md](DETAILED_GUIDE.md)
