# 🚀 GramSevak AI - Deployment Guide

## ✅ Pre-Deployment Checklist

- [x] Code is complete and tested
- [x] Documentation is clean (3 essential files)
- [x] No API keys in code
- [x] .gitignore is configured
- [x] All features working

---

## 📦 Step 1: Push to GitHub

### 1.1 Create .env.example file

```bash
# Create example environment file
cat > backend/.env.example << 'EOF'
# GROQ API Configuration
GROQ_API_KEY=your_groq_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Rate Limiting
RATE_LIMIT_MAX=20
RATE_LIMIT_WINDOW=60

# Admin Token
ADMIN_TOKEN=your_admin_token_here
EOF
```

### 1.2 Initialize Git (if not already done)

```bash
git init
git add .
git commit -m "Initial commit: GramSevak AI - Complete implementation"
```

### 1.3 Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `gramsevak-ai`
3. Description: "AI assistant for rural India - Optimized for 2G/3G networks"
4. Public or Private: **Public** (recommended for portfolio)
5. Don't initialize with README (we already have one)

### 1.4 Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/gramsevak-ai.git
git branch -M main
git push -u origin main
```

---

## 🌐 Step 2: Deploy Backend

### Option A: Railway (Recommended - Free Tier)

**Why Railway?**
- ✅ Free tier available
- ✅ Easy deployment
- ✅ Automatic HTTPS
- ✅ Environment variables support

**Steps:**

1. **Sign up**: https://railway.app
2. **New Project** → Deploy from GitHub
3. **Select repository**: gramsevak-ai
4. **Root directory**: `/backend`
5. **Add environment variables**:
   ```
   GROQ_API_KEY=your_actual_key
   ADMIN_TOKEN=gramsevak_admin_2024
   ```
6. **Deploy** - Railway will auto-detect FastAPI
7. **Get URL**: `https://your-app.railway.app`

### Option B: Render (Free Tier)

**Steps:**

1. **Sign up**: https://render.com
2. **New Web Service** → Connect GitHub
3. **Settings**:
   - Name: `gramsevak-ai-backend`
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. **Environment Variables**:
   ```
   GROQ_API_KEY=your_actual_key
   ADMIN_TOKEN=gramsevak_admin_2024
   ```
5. **Deploy** - Get URL: `https://gramsevak-ai-backend.onrender.com`

### Option C: Fly.io (Free Tier)

**Steps:**

1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Login: `fly auth login`
3. Create `backend/fly.toml`:
   ```toml
   app = "gramsevak-ai"
   
   [build]
   
   [env]
   PORT = "8000"
   
   [[services]]
   http_checks = []
   internal_port = 8000
   processes = ["app"]
   protocol = "tcp"
   
   [[services.ports]]
   force_https = true
   handlers = ["http"]
   port = 80
   
   [[services.ports]]
   handlers = ["tls", "http"]
   port = 443
   ```
4. Deploy: `fly launch` (in backend directory)
5. Set secrets: `fly secrets set GROQ_API_KEY=your_key`

### Option D: Vercel (Serverless)

**Steps:**

1. Install Vercel CLI: `npm i -g vercel`
2. Create `backend/vercel.json`:
   ```json
   {
     "builds": [
       {
         "src": "main.py",
         "use": "@vercel/python"
       }
     ],
     "routes": [
       {
         "src": "/(.*)",
         "dest": "main.py"
       }
     ]
   }
   ```
3. Deploy: `vercel --prod` (in backend directory)
4. Add environment variables in Vercel dashboard

---

## 🎨 Step 3: Deploy Frontend

### Option A: Netlify (Recommended - Free)

**Why Netlify?**
- ✅ Free tier with custom domain
- ✅ Automatic HTTPS
- ✅ CDN included
- ✅ Easy deployment

**Steps:**

1. **Sign up**: https://netlify.com
2. **New site from Git** → Select repository
3. **Build settings**:
   - Base directory: `frontend`
   - Build command: (leave empty)
   - Publish directory: `.` (current directory)
4. **Update API URL** in `frontend/app.js`:
   ```javascript
   const API_BASE_URL = 'https://your-backend-url.railway.app';
   ```
5. **Deploy** - Get URL: `https://gramsevak-ai.netlify.app`

### Option B: Vercel (Free)

**Steps:**

1. **Sign up**: https://vercel.com
2. **Import Project** → Select repository
3. **Root Directory**: `frontend`
4. **Framework Preset**: Other
5. **Update API URL** in `frontend/app.js`
6. **Deploy** - Get URL: `https://gramsevak-ai.vercel.app`

### Option C: GitHub Pages (Free)

**Steps:**

1. Update `frontend/app.js` with backend URL
2. Go to repository Settings → Pages
3. Source: Deploy from branch `main`
4. Folder: `/frontend`
5. Save - Get URL: `https://username.github.io/gramsevak-ai`

### Option D: Cloudflare Pages (Free)

**Steps:**

1. **Sign up**: https://pages.cloudflare.com
2. **Create project** → Connect GitHub
3. **Build settings**:
   - Build command: (none)
   - Build output directory: `frontend`
4. **Deploy** - Get URL: `https://gramsevak-ai.pages.dev`

---

## 🔧 Step 4: Update Frontend with Backend URL

After deploying backend, update the frontend:

```javascript
// frontend/app.js (line ~2)
const API_BASE_URL = 'https://your-backend-url.railway.app';

// frontend/stats-dashboard.html (line ~242)
const API_URL = 'https://your-backend-url.railway.app';
```

Then redeploy frontend.

---

## 🔒 Step 5: Security Configuration

### 5.1 Update CORS in Backend

```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://gramsevak-ai.netlify.app",  # Your frontend URL
        "http://localhost:3000",  # Local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5.2 Change Admin Token

```bash
# In your deployment platform, set:
ADMIN_TOKEN=your_secure_random_token_here
```

Generate secure token:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 5.3 Enable Rate Limiting

Already configured! 20 requests per minute per IP.

---

## 📊 Step 6: Monitor Deployment

### Backend Health Check

```bash
curl https://your-backend-url.railway.app/health
```

Expected response:
```json
{
  "status": "ok",
  "schemes_loaded": 128,
  "timestamp": 1234567890.123
}
```

### Frontend Check

1. Open: `https://gramsevak-ai.netlify.app`
2. Ask: "पीएम किसान योजना क्या है?"
3. Verify response appears
4. Check network tab: Response should be <2KB

### Analytics Dashboard

1. Open: `https://gramsevak-ai.netlify.app/stats-dashboard.html`
2. Add token: `?token=your_admin_token`
3. Verify metrics display

---

## 🎯 Step 7: Custom Domain (Optional)

### For Frontend (Netlify)

1. Buy domain (Namecheap, GoDaddy, etc.)
2. Netlify → Domain settings → Add custom domain
3. Update DNS records as instructed
4. Wait for SSL certificate (automatic)

### For Backend (Railway)

1. Railway → Settings → Domains
2. Add custom domain: `api.yourdomain.com`
3. Update DNS: CNAME to Railway URL
4. SSL automatic

---

## 📱 Step 8: PWA Installation

After deployment, users can install as app:

**On Mobile:**
1. Open in Chrome/Safari
2. Tap "Add to Home Screen"
3. App installs with icon

**On Desktop:**
1. Open in Chrome
2. Click install icon in address bar
3. App installs

---

## 🧪 Step 9: Testing Checklist

### Backend Tests

```bash
# Health check
curl https://your-backend.railway.app/health

# Query test
curl -X POST https://your-backend.railway.app/query \
  -H "Content-Type: application/json" \
  -d '{"text": "पीएम किसान योजना क्या है?"}'

# Rate limiting test (send 25 requests)
for i in {1..25}; do
  curl -X POST https://your-backend.railway.app/query \
    -H "Content-Type: application/json" \
    -d '{"text": "test"}' &
done

# Analytics test
curl https://your-backend.railway.app/analytics?token=your_token
```

### Frontend Tests

- [ ] Homepage loads
- [ ] Voice input works
- [ ] Query submission works
- [ ] Response displays correctly
- [ ] Feedback buttons work
- [ ] Explainability panel opens
- [ ] 2G mode toggle works
- [ ] Emergency button works
- [ ] Analytics dashboard loads
- [ ] Offline mode works (disable network)

---

## 📈 Step 10: Post-Deployment

### 1. Update README with Live URLs

```markdown
## 🌐 Live Demo

- **Frontend**: https://gramsevak-ai.netlify.app
- **Backend API**: https://gramsevak-ai.railway.app
- **Analytics**: https://gramsevak-ai.netlify.app/stats-dashboard.html
```

### 2. Add Badges to README

```markdown
![Status](https://img.shields.io/badge/status-live-success)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688)
![Frontend](https://img.shields.io/badge/frontend-PWA-blue)
![License](https://img.shields.io/badge/license-MIT-green)
```

### 3. Create GitHub Release

1. Go to Releases → Create new release
2. Tag: `v1.0.0`
3. Title: "GramSevak AI v1.0.0 - Initial Release"
4. Description: List all 23 features
5. Publish release

### 4. Share Your Project

- LinkedIn post with demo video
- Twitter/X thread with screenshots
- Dev.to article about the project
- Hackathon submission (if applicable)

---

## 🎓 Recommended Deployment Stack

**For Hackathon/Demo:**
```
Backend:  Railway (free, fast deployment)
Frontend: Netlify (free, custom domain)
Total:    $0/month
```

**For Production:**
```
Backend:  Railway Pro ($5/month) or AWS
Frontend: Netlify Pro ($19/month) or Cloudflare
Database: Add PostgreSQL for persistence
Total:    ~$25/month
```

---

## 🐛 Troubleshooting

### Backend Issues

**Problem**: 502 Bad Gateway
- **Solution**: Check logs, ensure PORT env variable is set

**Problem**: CORS errors
- **Solution**: Update allow_origins in main.py

**Problem**: Rate limiting too strict
- **Solution**: Increase RATE_LIMIT_MAX in environment

### Frontend Issues

**Problem**: API calls failing
- **Solution**: Check API_BASE_URL is correct

**Problem**: PWA not installing
- **Solution**: Ensure HTTPS is enabled

**Problem**: Voice input not working
- **Solution**: Requires HTTPS for Web Speech API

---

## 📊 Monitoring

### Backend Logs

**Railway**: Dashboard → Logs
**Render**: Dashboard → Logs
**Fly.io**: `fly logs`

### Analytics

Check `/analytics` endpoint regularly:
- Total queries
- Cache hit ratio
- User satisfaction
- Rate limit blocks

### Uptime Monitoring

Use free services:
- UptimeRobot: https://uptimerobot.com
- Pingdom: https://pingdom.com
- StatusCake: https://statuscake.com

---

## 🎉 Success Criteria

Your deployment is successful when:

- ✅ Backend health check returns 200
- ✅ Frontend loads without errors
- ✅ Queries return responses <2KB
- ✅ Response time <2 seconds
- ✅ Offline mode works
- ✅ PWA installs on mobile
- ✅ Analytics dashboard accessible
- ✅ Rate limiting prevents abuse
- ✅ Feedback system works
- ✅ All 23 features functional

---

## 📞 Support

If you encounter issues:

1. Check logs in deployment platform
2. Test locally first: `uvicorn main:app --reload`
3. Verify environment variables are set
4. Check CORS configuration
5. Test with curl commands above

---

## 🚀 Next Steps After Deployment

1. **Gather feedback** from real users
2. **Monitor analytics** for usage patterns
3. **Expand knowledge base** (128 → 400 entries)
4. **Add more features** based on user needs
5. **Optimize performance** based on metrics
6. **Scale infrastructure** as needed

---

**Ready to deploy?** Follow the steps above and your GramSevak AI will be live! 🎊

**Estimated deployment time**: 30-60 minutes
**Cost**: $0 (using free tiers)
**Difficulty**: Easy (step-by-step guide)

Good luck! 🌾🇮🇳
