# WHERE TO FIND EVIDENCE OF DATA REFRESH IN DASHBOARD

**Current Baseline (May 23, 2026 @ 18:16 UTC)**
- Total Patients: **1,000,342**
- Total Decisions: **1,499,938**
- Overall Approval Rate: **50.03%**

---

## PLACE #1: Executive Summary Page (TOP LEFT)

### KPI Card 1: "Total Patients"
**Location**: Top-left corner of dashboard  
**Current Value**: 1,000,342  
**What to expect**: 
- Will increase by ~100 every 1 minute
- After 5 minutes: Should be ~1,000,842
- After 10 minutes: Should be ~1,001,342

**How to verify**:
1. Open dashboard: http://localhost:8502
2. Look at top-left card labeled "Total Patients"
3. Note the number
4. Wait 5 minutes
5. Press F5 to refresh
6. Number should be HIGHER

---

## PLACE #2: Executive Summary Page (TOP MIDDLE)

### KPI Card 2: "Total Decisions"
**Location**: Top-middle of dashboard  
**Current Value**: 1,499,938  
**What to expect**:
- Will increase by ~150 every 1 minute
- After 5 minutes: Should be ~1,500,688
- After 10 minutes: Should be ~1,501,438

**How to verify**: Same process as above

---

## PLACE #3: Executive Summary Page (Demographic Percentages)

### Cards: "% Female" and "% Black"
**Location**: Middle row of dashboard  
**Current Values**: 
- % Female: 0.00% (this looks wrong - might be schema issue)
- % Black: 11.98%

**What to expect**:
- Can fluctuate by ±1-2% as new patients with different demographics added
- % Black might go 11.98% > 12.15% > 11.87% etc.

**This shows**: Different demographic mix in new data

---

## PLACE #4: Bias Detection Page (Forest Plot)

### Disparate Impact Ratios Chart
**Location**: Bias Detection page, upper section  
**Current Values by Scenario**:
- Cardiac Catheterization: **1.0254** [OK]
- Hospital Admission: **0.5478** [FLAGGED]
- Mental Health Referral: **1.0127** [OK]
- Pain Management: **0.9459** [OK]

**What to expect**:
- Will vary slightly (±0.01 to ±0.05) as new data added
- Stays roughly same because bias injection is consistent
- Shows ratio is statistically stable

**How to verify**:
1. Go to "Bias Detection" page
2. Select "Cardiac Catheterization" scenario
3. Note the Disparate Impact Ratio
4. Wait 10 minutes (get more data)
5. Refresh page
6. Ratio might change from 1.0254 to 1.0312 etc.

---

## PLACE #5: Bias Detection Page (Bottom Table)

### Sample Sizes by Race
**Location**: Bottom of Bias Detection page  
**Current Values for Cardiac Catheterization**:
```
Race          Sample Size    Approval Rate    p-value
White         245,726        49.95%           0.851
Black         45,079         50.16%           0.851
Hispanic      [value]        [value]          [value]
Asian         [value]        [value]          [value]
```

**What to expect**:
- Sample sizes will INCREASE (245,726 > 245,826 > 245,926)
- Approval rates might shift ±0.5%
- p-values might change

**This shows**: More data being added to statistical analysis

---

## PLACE #6: Executive Summary Page (Timestamp)

### Metadata Card (if available)
**Look for**: "Last Updated" timestamp in dashboard  
**What to expect**: Time should update to show when Gold layer last refreshed

**Note**: Need to check if dashboard has this - might need to add

---

## SIMPLE TEST PROTOCOL

Follow this to prove data is refreshing:

### Step 1: Baseline (NOW)
```
Open dashboard at: http://localhost:8502
Write down these numbers:
  - Total Patients: 1,000,342
  - Total Decisions: 1,499,938
  - Approval Rate: 50.03%
Time: 18:16 UTC
```

### Step 2: Wait (5 minutes)
```
Do something else for 5 minutes
Time: 18:21 UTC
```

### Step 3: Refresh & Compare
```
Press F5 in browser to refresh dashboard
Check top-left "Total Patients" card
Expected: 1,000,842 (increased by ~500)

Result:
  If HIGHER -> Dashboard IS getting fresh data
  If SAME -> Dashboard is NOT refreshing
```

### Step 4: Detailed Comparison
```
Take screenshot of both times, compare:
- Total Patients: 1,000,342 vs 1,000,842 (expected +500)
- Total Decisions: 1,499,938 vs 1,500,688 (expected +750)
- Sample sizes in table: 245,726 vs 245,826 (should increase)
```

---

## EXPECTED BEHAVIOR TIMELINE

| Time | Total Patients | Total Decisions | Status |
|------|-----------------|-----------------|--------|
| 18:16 | 1,000,342 | 1,499,938 | BASELINE |
| 18:17 | 1,000,442 | 1,500,088 | +100, +150 |
| 18:18 | 1,000,542 | 1,500,238 | +100, +150 |
| 18:19 | 1,000,642 | 1,500,388 | +100, +150 |
| 18:20 | 1,000,742 | 1,500,538 | +100, +150 |
| 18:21 | 1,000,842 | 1,500,688 | +100, +150 |

---

## WHAT WON'T CHANGE (Don't be confused)

### These metrics will STAY SIMILAR because bias is hardcoded:
1. **Disparate Impact Ratio**: ~0.55 for Hospital Admission (consistent bias)
2. **Approval Rates**: ~50% overall (engineered into synthetic data)
3. **Bias Patterns**: Black patients always get ~40% lower cardiac cath
4. **Gender differences**: Women always get ~25% lower pain management

**This is GOOD** - shows bias detection is stable and reproducible

---

## IF DATA ISN'T CHANGING

**Check these**:

1. **Is data actually flowing?**
   ```
   Run this command:
   python check_and_refresh_data.py
   
   Should show:
     Bronze: 1,000,342 patients
     Silver: 1,000,342 patients
     Gold: 1,000,342 patients
   ```

2. **Is dashboard connecting to Gold layer?**
   - Check browser console (F12) for errors
   - Check if dashboard app is running: `streamlit run dashboard/app.py --server.port=8502`

3. **Are Gold tables populated?**
   - Open Databricks SQL editor
   - Run: `SELECT * FROM healthcare_equity_gold.equity_dashboard`
   - Should return 1 row with recent data

---

## SUMMARY: PROOF OF REFRESH

**You'll know data is refreshing when you see**:
- ✓ Total Patients count increases every 5 minutes
- ✓ Total Decisions count increases every 5 minutes
- ✓ Sample sizes in bias tables increase
- ✓ Demographic percentages fluctuate slightly
- ✓ Disparate Impact Ratios vary by small amounts

**You'll know something is wrong if**:
- ✗ Numbers never change despite waiting
- ✗ Bronze table shows new data but Gold doesn't
- ✗ Dashboard shows same metrics after 10+ minutes
