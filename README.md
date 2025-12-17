# Nokk.AI QC Bot - v1.0

A multi-project, brand-aware AI Quality Control (QC) bot for Basecamp, built with Flask, Groq. This bot automates comment analysis and brand-specific responses across multiple Basecamp projects, with easy deployment on Render and local development support.

---

## Features

- **Multi-Project Support:** Handles multiple Basecamp projects, each with its own brand context.
- **AI-Powered:** Uses Groq for advanced comment analysis and response generation.
- **Webhook Automation:** Single webhook endpoint for all projects, with easy setup via script.
- **Image Processing:** Supports image-based QC using Pillow and HuggingFace.
- **Easy Deployment:** Ready for Render.com deployment (see `render.yaml`), with local development support.
- **Secure:** Uses `.env` for all secrets and API keys.

---

## Folder Structure

```
qc/
├── Procfile
├── qcbot.py           # Main Flask app (API, AI logic, brand context)
├── webhook.py         # Script to register webhooks for all projects
├── requirements.txt   # Python dependencies
├── render.yaml        # Render.com deployment config
├── .env               # Environment variables (not committed)
├── qc_images/         # Brand-specific image folders
│   └── ...
└── ...
```

---

## Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/qc-bot.git
cd qc-bot
```

### 2. Install Python Dependencies

It is recommended to use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `.env` and fill in your credentials:

```
CLIENT_ID=your_basecamp_client_id
CLIENT_SECRET=your_basecamp_client_secret
REFRESH_TOKEN=your_basecamp_refresh_token
ACCOUNT_ID=your_basecamp_account_id
GROQ_API_KEY=your_groq_api_key
FLASK_ENV=production
FLASK_DEBUG=False
PORT=10000
HOST=0.0.0.0
```

> **Note:** Never commit your `.env` file. It is already in `.gitignore`.

### 4. Run Locally

```bash
python qcbot.py
```

Or with Gunicorn (recommended for production):

```bash
gunicorn qcbot:app
```

The app will run on the port specified in `.env` (default: 10000).

---

## Webhook Setup (Basecamp)

To connect Basecamp projects to your bot, use the provided `webhook.py` script. This script registers a webhook for each project, pointing to your bot's `/webhook/basecamp` endpoint.

### 1. Start Your Server (with public URL)

- For local development, use [ngrok](https://ngrok.com/) to expose your local server:
  ```bash
  ngrok http 10000
  ```
- For production, deploy to Render.com (see below).

### 2. Register Webhooks

```bash
python webhook.py https://your-ngrok-or-production-url
```

- The script will prompt you to delete old webhooks if needed.
- It will register a webhook for each project listed in `webhook.py`.

---

## Deployment (Render.com)

1. Push your code to GitHub.
2. Create a new **Web Service** on [Render.com](https://render.com/):
   - Connect your repo.
   - Set the build command: `pip install -r requirements.txt`
   - Set the start command: `gunicorn qcbot:app`
   - Add environment variables as per your `.env` file.
   - Use the provided `render.yaml` for configuration.
3. Deploy!

---

## API Endpoints

- `POST /webhook/basecamp` – Receives Basecamp comment events.
- (Add more endpoints as you expand functionality)

---

## Image QC

- Place brand-specific images in `qc_images/<brand_name>/`.
- The bot uses these for image-based QC tasks.

---

## Technologies Used

- **Python 3.11**
- **Flask** – Web framework
- **Groq** – AI language model API
- **HuggingFace Hub** – For image and text inference
- **Pillow** – Image processing
- **Gunicorn** – Production WSGI server
- **Render.com** – Cloud deployment

---





## Credits

- Maintained by Varun Shetty

---


