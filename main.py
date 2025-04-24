# TLCIT Engine: Dual Integration Build (FastAPI + QuantConnect + Backtrader + Alerts + Storage + Google Chat)
# 🔁 Re-trigger deploy after enabling Cloud Resource Manager API

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
        requests.post(CHAT_WEBHOOK_URL, json={"text": message})

# Gold Price Scraper
def get_live_gold_price():
    try:
        gold_data = yf.download("GC=F", period="1d", interval="1m")
        if not gold_data.empty:
            return gold_data["Close"].iloc[-1]
    except Exception as e:
        print("Error fetching gold price:", e)
    return 0

@app.get("/")
def read_root():
    return {"message": "TLCIT is live 🚀"}

@app.get("/score")
def get_score():
    return {
        "ticker": "NEM",
        "conviction_score": 9.8,
        "reason": "Post-earnings momentum, gold divergence, TLCIT v9.8 global signal"
    }

@app.post("/signal")
def generate_signal(req: SignalRequest):
    ticker = req.ticker.upper()
    trigger = req.trigger.lower()
    if ticker == "NEM" and trigger == "breakout":
        msg = f"📈 TLCIT Signal: BUY {ticker} on {trigger.upper()} trigger"
        send_google_chat_message(msg)
        return {
            "action": "BUY",
            "conviction": 9.8,
            "reason": "Breakout + gold correlation + earnings beat"
        }
    return {"action": "HOLD", "reason": "No current signal"}

@app.post("/buy")
def buy_stock(req: SignalRequest):
    portfolio[req.ticker.upper()] = portfolio.get(req.ticker.upper(), 0) + req.quantity
    sheet.append_row([datetime.datetime.now().isoformat(), req.ticker.upper(), "BUY", req.quantity])
    msg = f"✅ TRADE EXECUTED: Bought {req.quantity} of {req.ticker.upper()}"
    send_google_chat_message(msg)
    return {"status": "success", "portfolio": portfolio}

@app.post("/sell")
def sell_stock(req: SignalRequest):
    ticker = req.ticker.upper()
    if ticker in portfolio:
        portfolio[ticker] = max(0, portfolio[ticker] - req.quantity)
    sheet.append_row([datetime.datetime.now().isoformat(), ticker, "SELL", req.quantity])
    msg = f"🔻 TRADE EXECUTED: Sold {req.quantity} of {ticker}"
    send_google_chat_message(msg)
    return {"status": "success", "portfolio": portfolio}

@app.get("/portfolio")
def get_portfolio():
    return portfolio

# --- Backtrader Integration (RSI + Gold Divergence Logic) ---
import backtrader as bt
from datetime import datetime
Re-trigger deploy after enabling API

class TLCITStrategy(bt.Strategy):
    def __init__(self):
        self.sma = bt.indicators.SimpleMovingAverage(self.data, period=15)
        self.rsi = bt.indicators.RSI(self.data.close, period=14)

    def next(self):
        gold_price = get_live_gold_price()
        nem_price = self.data.close[0]
        gold_threshold = 3200

        if gold_price > gold_threshold and nem_price < self.sma[0] and self.rsi[0] < 50:
            self.buy()
        elif self.rsi[0] > 70:
            self.sell()

cerebro = bt.Cerebro()
cerebro.addstrategy(TLCITStrategy)
data = bt.feeds.YahooFinanceData(dataname='NEM', fromdate=datetime(2024, 1, 1), todate=datetime(2025, 1, 1))
cerebro.adddata(data)
cerebro.run()
cerebro.plot()

# --- QuantConnect Lean Algorithm (Gold Divergence + RSI) ---
class TLCITAlgorithm(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2024, 1, 1)
        self.SetEndDate(2025, 1, 1)
        self.SetCash(100000)
        self.nem = self.AddEquity("NEM", Resolution.Daily).Symbol
        self.sma = self.SMA(self.nem, 15, Resolution.Daily)
        self.rsi = self.RSI(self.nem, 14, MovingAverageType.Simple, Resolution.Daily)

    def OnData(self, data):
        if not self.sma.IsReady or not self.rsi.IsReady:
            return

        price = self.Securities[self.nem].Price
        gold_price = 3293  # Replace with external feed integration in full version
        gold_threshold = 3200

        if gold_price > gold_threshold and price < self.sma.Current.Value and self.rsi.Current.Value < 50:
            self.SetHoldings(self.nem, 1)
        elif self.rsi.Current.Value > 70:
            self.Liquidate(self.nem)

# --- Optional Daily Alert Scheduler ---
# Use Google Cloud Scheduler or cron job to call /signal or /portfolio endpoints
# Alerts are now pushed to Google Chat if webhook is configured
