# Deployment Guide

## Option 1: Streamlit Cloud (Recommended - Free)

### Prerequisites
- GitHub account
- Streamlit Cloud account (sign up at [share.streamlit.io](https://share.streamlit.io))
- Google Gemini API key

### Steps

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: COREP Reporting Assistant"
   git branch -M main
   git remote add origin https://github.com/TANMAY4806w/corep-reporting-assistant.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select your repository: `TANMAY4806w/corep-reporting-assistant`
   - Set main file path: `src/app.py`
   - Click "Advanced settings"
   - Add secrets:
     ```toml
     GEMINI_API_KEY = "your_api_key_here"
     ```
   - Click "Deploy"

3. **Access Your App**
   - Your app will be available at: `https://tanmay4806w-corep-reporting-assistant.streamlit.app`

### Updating the Deployment

```bash
git add .
git commit -m "Update: description of changes"
git push
```

Streamlit Cloud will automatically redeploy when you push to GitHub.

---

## Option 2: Local Deployment

### For Development

```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Run Streamlit
streamlit run src/app.py
```

### For Production (Local Server)

```bash
streamlit run src/app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.headless true
```

---

## Option 3: Docker Deployment

### Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Build and Run

```bash
# Build image
docker build -t corep-assistant .

# Run container
docker run -p 8501:8501 \
  -e GEMINI_API_KEY=your_api_key_here \
  corep-assistant
```

---

## Environment Variables

### Required
- `GEMINI_API_KEY`: Your Google Gemini API key

### Optional
- `PORT`: Server port (default: 8501)

---

## Security Checklist

- [ ] Never commit `.env` file
- [ ] Use secrets management for API keys
- [ ] Enable HTTPS in production
- [ ] Set up authentication if needed
- [ ] Review CORS settings
- [ ] Enable rate limiting for API calls

---

## Troubleshooting

### Issue: "GEMINI_API_KEY not found"
**Solution**: Ensure your `.env` file exists locally or secrets are configured in Streamlit Cloud.

### Issue: "Module not found"
**Solution**: Install dependencies: `pip install -r requirements.txt`

### Issue: "Port already in use"
**Solution**: Change port: `streamlit run src/app.py --server.port 8502`

### Issue: Styling not applied
**Solution**: Clear Streamlit cache: `streamlit cache clear`

---

## Monitoring

### Streamlit Cloud
- View logs in the Streamlit Cloud dashboard
- Monitor app health and usage metrics
- Set up email alerts for errors

### Local Deployment
- Check terminal output for errors
- Monitor system resources (CPU, memory)
- Set up logging to file for production

---

## Performance Tips

1. **Cache API calls**: Use `@st.cache_data` for repeated queries
2. **Optimize schema loading**: Load once at startup
3. **Limit concurrent users**: Set appropriate resource limits
4. **Monitor API usage**: Track Gemini API quota

---

## Next Steps

After deployment:
1. Test with real scenarios
2. Gather user feedback
3. Monitor error logs
4. Plan feature enhancements
5. Consider additional COREP templates
