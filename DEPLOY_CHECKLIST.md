# 🚀 Quick Deployment Checklist

## ✅ Pre-Deployment (5 minutes)

- [ ] Review code - all features working locally
- [ ] Check .gitignore - no sensitive data
- [ ] Create .env from .env.example
- [ ] Test backend: `uvicorn main:app --reload`
- [ ] Test frontend: Open `index.html` in browser

## 📦 GitHub Push (2 minutes)

```bash
# If not initialized
git init
git add .
git commit -m "Initial commit: GramSevak AI v1.0.0"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/gramsevak-ai.git
git branch -M main
git push -u origin main
```

## 🌐 Backend Deployment (10 minutes)

### Railway (Recommended)
1. [ ] Sign up: https://railway.app
2. [ ] New Project → Deploy from GitHub
3. [ ] Select `gramsevak-ai` repo
4. [ ] Root directory: `/backend`
5. [ ] Add environment variables:
   - `GROQ_API_KEY=your_key`
   - `ADMIN_TOKEN=your_token`
6. [ ] Deploy & copy URL

### Alternative: Render
1. [ ] Sign up: https://render.com
2. [ ] New Web Service → Connect GitHub
3. [ ] Build: `pip install -r requirements.txt`
4. [ ] Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. [ ] Add environment variables
6. [ ] Deploy & copy URL

## 🎨 Frontend Deployment (5 minutes)

### Netlify (Recommended)
1. [ ] Sign up: https://netlify.com
2. [ ] New site from Git → Select repo
3. [ ] Base directory: `frontend`
4. [ ] Publish directory: `.`
5. [ ] Deploy

### Update API URL
1. [ ] Edit `frontend/app.js` line 2:
   ```javascript
   const API_BASE_URL = 'https://your-backend.railway.app';
   ```
2. [ ] Edit `frontend/stats-dashboard.html` line 242:
   ```javascript
   const API_URL = 'https://your-backend.railway.app';
   ```
3. [ ] Commit & push changes
4. [ ] Netlify auto-deploys

## 🧪 Testing (5 minutes)

### Backend
- [ ] Health: `curl https://your-backend.railway.app/health`
- [ ] Query: Test with Postman or curl
- [ ] Analytics: Open with token

### Frontend
- [ ] Homepage loads
- [ ] Submit query - response appears
- [ ] Feedback buttons work
- [ ] Analytics dashboard loads
- [ ] PWA installs on mobile

## 📊 Post-Deployment (5 minutes)

- [ ] Update README with live URLs
- [ ] Add badges to README
- [ ] Create GitHub release (v1.0.0)
- [ ] Share on LinkedIn/Twitter
- [ ] Submit to hackathon (if applicable)

## 🎉 Done!

**Total Time**: ~30 minutes
**Cost**: $0 (free tiers)

Your GramSevak AI is now live! 🌾🇮🇳

---

## 📞 Quick Links

- **Deployment Guide**: See `DEPLOYMENT_GUIDE.md` for detailed instructions
- **Documentation**: See `README.md` and `QUICKSTART.md`
- **Support**: Check logs in Railway/Netlify dashboard

## 🐛 Common Issues

**CORS Error**: Update `allow_origins` in `backend/main.py`
**502 Error**: Check backend logs, ensure PORT is set
**API Not Found**: Verify API_BASE_URL in frontend files

---

**Ready?** Start with GitHub push, then deploy backend, then frontend! 🚀
