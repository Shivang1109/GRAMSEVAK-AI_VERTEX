# 🔧 Troubleshooting Guide

## Issue: Getting fallback message on every query

### Symptoms
You see this message on every query:
```
क्षमा करें, मुझे इस प्रश्न का उत्तर नहीं मिला। कृपया 1800-180-1551 पर संपर्क करें।
```

### Root Cause
This is likely a browser cache or service worker issue, NOT a backend problem.

### Solution Steps

#### Step 1: Clear Browser Cache (Recommended)

**On Desktop (Chrome/Edge):**
1. Open https://gramsevak-ai.netlify.app
2. Press `F12` to open DevTools
3. Go to "Application" tab
4. Click "Clear storage" on the left
5. Check all boxes
6. Click "Clear site data"
7. Close DevTools
8. Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)

**On Mobile:**
1. Go to browser settings
2. Find "Site settings" or "Privacy"
3. Clear cache for gramsevak-ai.netlify.app
4. Restart browser

#### Step 2: Unregister Service Worker

1. Open https://gramsevak-ai.netlify.app
2. Press `F12` → "Application" tab
3. Click "Service Workers" on the left
4. Click "Unregister" next to the service worker
5. Refresh the page

#### Step 3: Test Backend Directly

Open this URL in a new tab to verify backend is working:
```
https://gramsevak-ai-vertex-2.onrender.com/health
```

You should see:
```json
{"status":"ok","schemes_loaded":128}
```

#### Step 4: Test API Directly

Open browser console (`F12` → Console) and run:

```javascript
fetch('https://gramsevak-ai-vertex-2.onrender.com/query', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({text: 'पीएम किसान योजना क्या है?'})
})
.then(r => r.json())
.then(d => console.log(d))
```

You should see a proper response with `summary` field containing the answer.

#### Step 5: Incognito/Private Mode

1. Open browser in Incognito/Private mode
2. Visit https://gramsevak-ai.netlify.app
3. Try a query
4. If it works here, the issue is browser cache

### Quick Fix: Force Refresh

Try this keyboard shortcut:
- **Windows/Linux:** `Ctrl + Shift + R`
- **Mac:** `Cmd + Shift + R`

This bypasses all caches and loads fresh content.

---

## Other Common Issues

### Issue: Voice input not working

**Solution:**
1. Check microphone permissions in browser
2. Use HTTPS (required for Web Speech API)
3. Try Chrome/Edge (best support for Hindi)

### Issue: Offline mode not working

**Solution:**
1. Load the app once while online
2. Service worker needs to cache assets first
3. Check DevTools → Application → Service Workers (should show "activated")

### Issue: Slow response time

**Possible causes:**
1. Render free tier cold start (first request after 15 min idle takes ~30 seconds)
2. Network connectivity
3. LLM API rate limits

**Solution:**
- Wait 30 seconds for first query after idle period
- Subsequent queries will be fast (<1 second)

### Issue: Analytics dashboard not loading

**Solution:**
1. Check URL: https://gramsevak-ai.netlify.app/stats-dashboard.html
2. Verify admin token is correct in the code
3. Check browser console for errors

---

## Verification Checklist

Run these tests to verify everything is working:

### Backend Health
```bash
curl https://gramsevak-ai-vertex-2.onrender.com/health
```
Expected: `{"status":"ok","schemes_loaded":128}`

### Query Test
```bash
curl -X POST https://gramsevak-ai-vertex-2.onrender.com/query \
  -H "Content-Type: application/json" \
  -d '{"text": "पीएम किसान योजना क्या है?"}'
```
Expected: JSON with proper `summary` field

### Frontend Loading
1. Visit https://gramsevak-ai.netlify.app
2. Check browser console (F12) for errors
3. Network tab should show successful API calls

---

## Still Having Issues?

### Check Backend Logs
If you have access to Render dashboard:
1. Go to https://dashboard.render.com
2. Select your service
3. Check "Logs" tab for errors

### Check Frontend Console
1. Open https://gramsevak-ai.netlify.app
2. Press F12 → Console tab
3. Look for red error messages
4. Share screenshot if asking for help

### Contact Support
If none of the above works:
1. Take screenshots of:
   - Browser console errors
   - Network tab showing failed requests
   - The actual error message
2. Check GitHub Issues: https://github.com/Shivang1109/GRAMSEVAK-AI_VERTEX/issues
3. Create a new issue with details

---

## Prevention

To avoid cache issues in future:

1. **Version your service worker:**
   - Update version number in `sw.js` when making changes
   - This forces browser to reload

2. **Add cache busting:**
   - Add `?v=1.0.0` to script URLs
   - Increment version on updates

3. **Test in incognito:**
   - Always test major changes in incognito mode first
   - Ensures you're seeing fresh content

---

## Quick Command Reference

```bash
# Test backend health
curl https://gramsevak-ai-vertex-2.onrender.com/health

# Test query
curl -X POST https://gramsevak-ai-vertex-2.onrender.com/query \
  -H "Content-Type: application/json" \
  -d '{"text": "मनरेगा में कितने दिन काम मिलता है?"}'

# Check if site is up
curl -I https://gramsevak-ai.netlify.app

# Test CORS
curl -X POST https://gramsevak-ai-vertex-2.onrender.com/query \
  -H "Content-Type: application/json" \
  -H "Origin: https://gramsevak-ai.netlify.app" \
  -d '{"text": "test"}'
```
