# 🔧 Update Backend URL - Quick Guide

After deploying backend on Railway, follow these steps:

## Step 1: Get Your Railway Backend URL

From Railway dashboard, copy your backend URL. It will look like:
```
https://gramsevak-ai-production.up.railway.app
```

## Step 2: Update Frontend Files

### File 1: `frontend/app.js` (Line 4)

**Find:**
```javascript
const API_BASE_URL = 'http://localhost:8000';  // TODO: Update this
```

**Replace with:**
```javascript
const API_BASE_URL = 'https://your-railway-url.up.railway.app';
```

### File 2: `frontend/stats-dashboard.html` (Line 243)

**Find:**
```javascript
const API_URL = 'http://localhost:8000';  // TODO: Update this
```

**Replace with:**
```javascript
const API_URL = 'https://your-railway-url.up.railway.app';
```

## Step 3: Commit and Push

```bash
git add frontend/app.js frontend/stats-dashboard.html
git commit -m "Update backend URL for production"
git push origin main
```

## Step 4: Deploy Frontend on Netlify

Netlify will automatically redeploy with the new URL!

---

## Quick Replace Command

If you want to use command line (replace YOUR_URL with actual URL):

```bash
# For macOS/Linux
sed -i '' "s|http://localhost:8000|https://YOUR_URL.up.railway.app|g" frontend/app.js
sed -i '' "s|http://localhost:8000|https://YOUR_URL.up.railway.app|g" frontend/stats-dashboard.html

# For Linux (without '')
sed -i "s|http://localhost:8000|https://YOUR_URL.up.railway.app|g" frontend/app.js
sed -i "s|http://localhost:8000|https://YOUR_URL.up.railway.app|g" frontend/stats-dashboard.html

# Then commit
git add frontend/app.js frontend/stats-dashboard.html
git commit -m "Update backend URL for production"
git push origin main
```

---

**Note**: Make sure to update BOTH files before deploying frontend!
