# TLCIT Engine: Dual Integration Build (FastAPI + QuantConnect + Backtrader + Alerts + Storage + Google Chat)
# Re-trigger deploy after enabling API
# Trigger deploy now

# --- FastAPI Core ---
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Literal, Optional
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import requests
import yfinance as yf

app = FastAPI()

# Google Sheets Setup (for live portfolio storage)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("gcloud_credentials.json", scope)
gs_client = gspread.authorize(credentials)
sheet = gs_client.open("TLCIT_Portfolio").sheet1

# Signal Request Model
class SignalRequest(BaseModel):
    ticker: str
    timeframe: Literal["daily", "weekly", "hourly"]
    trigger: str
    quantity: Optional[float] = 0.0

# Simulated Portfolio (In-Memory)
portfolio = {}

# Google Chat Webhook (set this in your environment or secrets manager)
CHAT_WEBHOOK_URL = os.getenv("GOOGLE_CHAT_WEBHOOK")

def send_google_chat_message(message: str):
    if CHAT_WEBHOOK_URL:
        requests.post(CHAT_WEBHOOK_URL, json={"
