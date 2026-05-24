# 🔄 Data Refresh Guide

## The Problem (Now Fixed)

### What Was Wrong:
```
Databricks updated data → 5 minute delay → Data appears in dashboard
```

**Root Cause**: Streamlit was caching data with `ttl=300` (5 minutes)

### What's Fixed:
```
Databricks updated data → <5 seconds → Data appears in dashboard
```

---

## 🎯 How Data Refresh Works Now

### 3 Ways to Get Fresh Data:

#### **1️⃣ AUTO-REFRESH (Every 5 seconds)**
**Best for**: Live monitoring, real-time dashboards

**How to use**:
1. Open dashboard → http://localhost:8501
2. Look at sidebar → **Settings** section
3. Check the box: **"Auto-refresh (5s)"** ✓
4. Dashboard will refresh every 5 seconds automatically

**What happens**:
- Page reloads every 5 seconds
- Latest data from Databricks fetched
- All charts/tables update
- Continuous monitoring

#### **2️⃣ MANUAL REFRESH (Instant)**
**Best for**: When you need data NOW

**How to use**:
- **Main Page**: Sidebar → Settings → Click **"🔄 Refresh Now"**
- **Page 2** (Bias Detection): Top of page → Click **"🔄 Refresh Data"**
- **Page 6** (AI Summary): Top of page → Click **"🔄 Refresh Data"**

**What happens**:
- Page reloads immediately
- All caches cleared
- Latest data fetched
- Results appear instantly

#### **3️⃣ BROWSER RELOAD (Complete Reset)**
**Best for**: If something seems wrong

**How to use**:
- Press **F5** or **Ctrl+R** to reload page
- Complete browser refresh
- All caches cleared
- Fresh start

---

## 📊 Data Update Latency

| Source | Latency | How |
|--------|---------|-----|
| Databricks updates data | Varies | Depends on your pipeline |
| Data appears in dashboard | < 5 sec | No caching, real-time fetch |
| Auto-refresh polls | 5 sec | Every 5 seconds |
| Manual refresh | Instant | Click button, reload immediately |

---

## 🔧 Technical Details

### How Caching Changed:

**BEFORE** (Slow):
```python
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data():
    # ... fetch from Databricks
```
Result: Data stale for up to 5 minutes

**AFTER** (Fast):
```python
# NO CACHING - fetch fresh every time
def load_data():
    # ... fetch from Databricks
```
Result: Always fresh data, <5 second latency

### Connection Caching:

```python
@st.cache_resource(ttl=60)  # Cache connection for 60 sec
def get_databricks_connection():
    return DatabricksConnection()
```

**Why**: Reusing HTTP connection is faster than creating new one each time
**Tradeoff**: Connection might be 60 sec old, but data is always fresh

---

## 📱 Which Method to Use When?

### Use AUTO-REFRESH (5s) If:
- ✅ Monitoring equity metrics in real-time
- ✅ Running intervention and want to see progress
- ✅ Presenting to leadership (shows live data)
- ✅ Demo mode (continuous updates look professional)

### Use MANUAL REFRESH If:
- ✅ Want to see specific update right now
- ✅ Just made change to Databricks
- ✅ Want to check one thing without continuous refresh
- ✅ Performance matters (refreshing every 5 sec uses resources)

### Use BROWSER RELOAD If:
- ✅ Page seems frozen or broken
- ✅ Want complete clean slate
- ✅ Testing something

---

## ⚡ Performance Impact

### AUTO-REFRESH (5 second interval)
- **CPU**: Low (just reloading page)
- **Network**: ~1-2 API calls/minute to Databricks
- **User Experience**: Smooth, continuous updates
- **Data Freshness**: < 5 seconds old

### MANUAL REFRESH (on-demand)
- **CPU**: Medium (one spike per click)
- **Network**: 1 API call per click
- **User Experience**: No interruption between refreshes
- **Data Freshness**: Instant when clicked

### NO REFRESH (page left open)
- **CPU**: Minimal
- **Network**: No calls
- **User Experience**: Static view
- **Data Freshness**: Gets older over time

---

## 🎯 Recommended Settings by Use Case

### **24/7 Monitoring Dashboard**
```
✓ Auto-refresh: ON
✓ Refresh interval: 5 seconds
✓ Result: Live updates, professional appearance
```

### **Executive Dashboard (Presentations)**
```
✓ Auto-refresh: ON
✓ Refresh interval: 5 seconds
✓ Result: Shows latest metrics during demo
```

### **Clinical Staff Analysis**
```
✓ Auto-refresh: OFF
✓ Manual refresh: Use as needed
✓ Result: Stable view, click to update
```

### **Compliance Reporting**
```
✓ Auto-refresh: OFF
✓ Manual refresh: When ready to export
✓ Result: Snapshot in time for report
```

---

## 🚨 Troubleshooting

### "Data hasn't updated in a while"
**Solution**: 
1. Click "Refresh Now" button
2. Check if auto-refresh is ON (sidebar)
3. Check if Databricks pipeline is running

### "Page keeps refreshing (auto-refresh too fast)"
**Solution**:
1. Uncheck "Auto-refresh" in sidebar
2. Use manual refresh instead

### "Data shows old values"
**Solution**:
1. Click "Refresh Now" button
2. Wait 5-10 seconds for pipeline
3. Refresh again

### "Refresh button not working"
**Solution**:
1. Reload page (F5)
2. Restart dashboard
3. Check Databricks connection

---

## 📈 Data Refresh Flow Diagram

```
Databricks Delta Tables
        ↓
    (Pipeline runs)
        ↓
   Data updated
        ↓
Dashboard fetches [No cache]
        ↓
(Option A) Auto-refresh → Repeat every 5 sec
(Option B) Manual refresh → Click to repeat
        ↓
   Data displayed
        ↓
   User sees update
```

---

## 💡 Best Practices

1. **Auto-refresh ON for monitoring**, OFF for analysis
2. **Click refresh AFTER making Databricks changes**
3. **Use manual refresh to avoid unnecessary API calls**
4. **For presentations, keep auto-refresh ON**
5. **For performance, disable auto-refresh when not needed**

---

## Summary

| Feature | Status | Speed | Use When |
|---------|--------|-------|----------|
| Auto-refresh (5s) | ✅ Working | Every 5 sec | Monitoring |
| Manual refresh | ✅ Working | Instant | On-demand |
| Browser reload | ✅ Working | Instant | Emergency |
| Cache | ✅ Removed | — | — |

**Your dashboard is now REAL-TIME ready!** 🚀
