# SamXpress Fleet Management Demo

A small Flask app for a Manchester student delivery operation. The dashboard covers incoming requests, driver and vehicle allocation, delivery status, and a lightweight run summary. Records are stored in `data.json`, so no database service is used for this demo implementation.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. Demo sign-in: `dispatch` / `samxpress123`.
