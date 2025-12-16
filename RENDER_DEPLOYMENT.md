# Render Deployment Guide for QC Bot

## Prerequisites
- GitHub account with your code pushed
- Render account (render.com)
- API credentials prepared (CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN, ACCOUNT_ID, GROQ_API_KEY)

## Step 1: Push Code to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files (will exclude .env due to .gitignore)
git add .

# Commit
git commit -m "Initial commit: Basecamp QC Bot with Render deployment config"

# Push to GitHub (replace USERNAME and REPO with your details)
git remote add origin https://github.com/USERNAME/REPO.git
git branch -M main
git push -u origin main
```

## Step 2: Create Render Account and Connect GitHub

1. Go to [render.com](https://render.com)
2. Sign up / Log in
3. Go to Dashboard → Connect GitHub account
4. Authorize Render to access your repositories
5. Select your repository

## Step 3: Create a New Web Service

1. Click "New +" → "Web Service"
2. Select your repository
3. Fill in the following:
   - **Name**: `qcbot` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn qcbot:app`
   - **Plan**: Free (or paid if you prefer)

## Step 4: Add Environment Variables

Before deploying, add all required environment variables:

1. In Render service settings, go to **Environment Variables**
2. Add each variable from `.env.example`:
   - `CLIENT_ID`
   - `CLIENT_SECRET`
   - `REFRESH_TOKEN`
   - `ACCOUNT_ID`
   - `GROQ_API_KEY`
   - `FLASK_ENV` = `production`
   - `FLASK_DEBUG` = `False`
   - `PORT` = `10000` (Render default)

## Step 5: Deploy

1. Click "Create Web Service"
2. Render will automatically build and deploy
3. View logs in the Render dashboard
4. Get your service URL (e.g., `https://qcbot-abc123.onrender.com`)

## Step 6: Update Webhook URL

Run your webhook setup script with the new Render URL:

```bash
python webhook.py https://qcbot-abc123.onrender.com
```

## Step 7: Test the Deployment

- Add a comment in any Basecamp project to trigger the webhook
- Check Render logs to see if the bot is processing correctly

## Troubleshooting

### Build Fails
- Check that `requirements.txt` is in the root directory
- Ensure all dependencies are listed

### Runtime Errors
- View logs in Render dashboard
- Check that all environment variables are set correctly

### Bot Not Responding
- Verify webhook URL is correct in Basecamp
- Check that GROQ_API_KEY is valid
- Ensure Basecamp credentials are correct

## Local Testing Before Deployment

```bash
# Create virtual environment
python -m venv venv

# Activate venv (Windows)
venv\Scripts\activate

# Or activate venv (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your credentials
cp .env.example .env
# Edit .env with your actual credentials

# Run locally
flask run
```

## Notes

- Free tier on Render has limitations (auto-sleeps after inactivity)
- For production, upgrade to a paid plan
- Use environment variables, never commit secrets
- Keep your refresh tokens secure
