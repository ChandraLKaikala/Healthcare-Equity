# 🚀 Quick Start Guide - Healthcare Equity Dashboard

## ✅ Status: PRODUCTION READY

Your dashboard is **fully tested** and **ready to use**. Here's everything you need to know.

---

## 🌐 ACCESSING THE DASHBOARD

### Start Dashboard
```bash
cd C:\Users\lokes\Downloads\Equity_Bias_Detection
python -m streamlit run dashboard/app.py
```

### Open in Browser
```
http://localhost:8501
```

**Note**: Dashboard starts at port 8501 (NOT 8020 - that was the OAuth issue, now FIXED)

---

## 📊 THE 5 PAGES

### PAGE 1: 📊 Executive Summary
**What**: High-level equity metrics and KPIs  
**Who**: Hospital leadership, C-suite executives  
**Key Metrics**:
- Total patients analyzed
- Total decisions tracked
- Overall approval rate
- Number of scenarios with disparities

**Time to load**: ~2 seconds

---

### PAGE 2: 🔍 Bias Detection Analysis ⭐ RECOMMENDED START HERE

**What**: Deep-dive into specific bias scenarios  
**Who**: Clinical staff, quality teams, compliance officers  

#### How to Use:
1. **Select Scenario**: Choose which treatment/procedure to analyze
   - Cardiac Catheterization
   - Pain Management
   - Mental Health Referral
   - Hospital Admission

2. **Choose Demographic**: Analyze by Race or Gender

3. **Set Min Sample Size**: Filter out small groups
   - Default: 100 (good balance)
   - 30-50: Very sensitive (can show noise)
   - 1000+: Very conservative (only strong signals)

4. **Auto-Refresh**: Toggle to update every 5 seconds (for live monitoring)

#### What You'll See:
- **Forest Plot**: Visual comparison of odds ratios
- **Statistical Summary**: 
  - DIR (Disparate Impact Ratio) - is it < 0.80?
  - Severity level
  - Sample size
- **Data Table**: Approval rates by group
- **📖 Plain Language Summary**: SCROLL TO BOTTOM for doctor-friendly explanation
- **Download Button**: Export summary for clinical meetings

#### Example Interpretation:
```
Finding: Cardiac catheterization disparities by race
DIR = 0.62 (Status: VIOLATION)
Meaning: Black patients get this procedure 40% less often than White patients
with identical clinical need.

Action: Requires immediate intervention within 30 days.
```

---

### PAGE 3: 💡 Interventions
**What**: Recommended bias reduction strategies  
**Who**: Quality improvement teams  
**Shows**:
- Intervention recommendations
- Current status of each intervention
- Effectiveness tracking
- Provider accountability scores

---

### PAGE 4: 📈 Outcome Tracking
**What**: Provider performance and outcome metrics  
**Who**: Clinical leadership, compliance teams  
**Shows**:
- Trends in disparities over time
- Readmission equity (gaps between groups)
- Mortality equity (deaths by demographic)
- Provider accountability scores

---

### PAGE 5: 📋 Regulatory Reports
**What**: Generate reports for regulatory bodies  
**Who**: Compliance officers, hospital leadership  

#### Regulatory Frameworks:
- **CMS** (Medicare/Medicaid compliance)
- **Joint Commission** (accreditation)
- **OCR** (Office for Civil Rights - Section 1557)
- **NCQA** (HEDIS equity measures)

#### Export Options:
- **📄 PDF Report**: Full report with findings (opens in Adobe Reader)
- **📊 Excel Export**: Data + findings (opens in Excel)
- **📧 Email**: Send to stakeholders (coming soon)

---

## 🎯 TYPICAL USE CASES

### 1. Hospital Leadership Monthly Check-In
1. Go to **Page 1** (Executive Summary)
2. Review KPI cards
3. If disparities found → Go to **Page 2**
4. Select scenario with highest DIR
5. Share **Plain Language Summary** with clinical team
6. Download **PDF Report** for board meeting

**Time**: 5 minutes

### 2. Quality Improvement Team Deep Dive
1. Go to **Page 2** (Bias Detection)
2. Select scenario of interest
3. Try different demographic dimensions (race vs gender)
4. Adjust min sample size to find robust findings
5. Review **Plain Language Summary** at bottom
6. Go to **Page 3** for intervention recommendations
7. Track on **Page 4**

**Time**: 15-20 minutes

### 3. Compliance Officer Report Generation
1. Go to **Page 5** (Regulatory Reports)
2. Select regulatory framework (CMS/JC/OCR/NCQA)
3. Select reporting period and facility
4. Click "Generate Report"
5. Download as **PDF** or **Excel**
6. Send to regulatory body

**Time**: 5 minutes

### 4. Continuous Monitoring
1. Go to **Page 2**
2. Toggle **Auto-Refresh ON**
3. Leave running on wall display
4. Dashboard updates every 5 seconds

---

## 📖 UNDERSTANDING THE STATISTICS

### Disparate Impact Ratio (DIR)
```
DIR = Lowest approval rate ÷ Highest approval rate

Example:
- Black patients: 40% approval
- White patients: 60% approval
- DIR = 40 ÷ 60 = 0.67 (VIOLATION - below 0.80 threshold)
```

**The 80% Rule**: If DIR < 0.80, it's evidence of disparate impact (legal/compliance issue)

### Severity Classification
| DIR | Severity | Action Required |
|-----|----------|-----------------|
| < 0.70 | SEVERE/CRITICAL | Immediate intervention (30 days) |
| 0.70-0.80 | MODERATE | Intervention needed (90 days) |
| ≥ 0.80 | OK | Monitor and track |

### Odds Ratio (Forest Plot)
- **OR = 1.0** (on dashed line) = Equal rates
- **OR < 1.0** = Disadvantaged group
- **OR > 1.0** = Advantaged group
- **Wider CI bars** = Less certain result (small sample)
- **Narrow CI bars** = More certain result (large sample)

---

## ✅ WHAT'S WORKING

- ✅ All 5 pages load without errors
- ✅ Database connection stable (1M+ patients, 1.5M+ decisions)
- ✅ Filters working (scenario, demographic, sample size)
- ✅ Statistics calculated correctly (DIR, odds ratios)
- ✅ Charts rendering properly
- ✅ PDF export generates real files
- ✅ Excel export generates real files
- ✅ Auto-refresh functional
- ✅ Doctor-friendly summaries available
- ✅ Dark theme consistent across pages
- ✅ **NO OAUTH POPUPS** ✅

---

## ⚠️ KNOWN LIMITATIONS

1. **Date Range Filter**: Not implemented (database lacks date columns)
   - Workaround: All data shown is current/recent
   
2. **Real-time Updates**: Dashboard reflects data at query time
   - Workaround: Use auto-refresh toggle

3. **Email Export**: Available as button but not yet integrated
   - Workaround: Download PDF/Excel and send manually

---

## 🐛 IF SOMETHING BREAKS

### "Error loading data: ..."
- **Fix**: Reduce Min Sample Size to 30-50
- **Reason**: Some scenarios have small demographic groups

### "No data found ..."
- **Fix**: Change scenario or demographic
- **Reason**: Specific demographic + scenario might have low volume

### Charts not showing
- **Fix**: Refresh browser (Ctrl+R)
- **Reason**: Streamlit caching issue

### Dashboard very slow
- **Fix**: Close other browser tabs
- **Reason**: 1.5M decision records require processing time

---

## 📞 KEY CONTACTS

**For System Issues**:
- Check `FINAL_VERIFICATION_REPORT.md` for system status
- See `ISSUES_FOUND_AND_FIXED.md` for troubleshooting

**For Clinical Questions**:
- Review "Plain Language Summary" on Page 2
- Consult your quality improvement team

---

## 📚 DOCUMENTATION

In same folder as dashboard:

1. **FINAL_VERIFICATION_REPORT.md** - Complete system health check
2. **ISSUES_FOUND_AND_FIXED.md** - Log of all 12 issues found & fixed
3. **QUICK_START_GUIDE.md** - This file
4. **README.md** - Project overview

---

## 🎓 INTERPRETING RESULTS

### If You Find a Disparity (DIR < 0.80)

**The Question**: Why are certain groups receiving treatment at different rates?

**The Investigation** (ROI Decision Support Framework):
1. **Review Cases**: Look at 5-10 actual patient records
   - Are lower-rate group patients actually sicker?
   - Are they being evaluated differently?
   - Is there a referral bottleneck?

2. **Identify Root Cause**:
   - Explicit bias? (Conscious discrimination)
   - Implicit bias? (Unconscious stereotyping)
   - Structural? (System prevents access)
   - Data artifact? (Coding/documentation differences)

3. **Choose Intervention**:
   - **If bias**: Bias training, decision alerts, peer learning
   - **If structural**: Remove barriers (transportation, insurance approval, language)
   - **If algorithm**: Retrain on diverse population

4. **Monitor Impact**: 
   - Re-check DIR monthly
   - Goal: Improve DIR from 0.62 → 0.85+

---

## ✨ PRO TIPS

1. **Best Time to Check**: Monthly at quality meetings
2. **Share With**: Clinical staff (not just IT)
3. **Use Page 2 Summary**: Copy-paste into clinical emails
4. **Export PDF**: Use for board/regulatory meetings
5. **Auto-Refresh**: Run during code rounds for live monitoring
6. **Multiple Scenarios**: Compare which scenario is worst → prioritize

---

## 🎯 SUCCESS METRICS

- ✅ Disparities identified (Page 2)
- ✅ Interventions recommended (Page 3)
- ✅ Disparities reduce over time (Page 4)
- ✅ DIR improves from 0.6x to 0.85+

**Example Victory**: 
- Month 1: Cardiac cath DIR = 0.62 (Black patients 40% denied)
- Month 3: Cardiac cath DIR = 0.78 (gap reduced to 22%)
- Month 6: Cardiac cath DIR = 0.88 (equitable)

---

## 🚀 READY?

```bash
# Start dashboard
python -m streamlit run dashboard/app.py

# Open browser
http://localhost:8501

# Go to Page 2: Bias Detection
# Select a scenario
# Scroll to bottom for doctor-friendly summary
```

**That's it!** Your healthcare equity dashboard is ready to detect and reduce bias.

---

**Built with ❤️ for health equity**  
**Because bias kills people.**
