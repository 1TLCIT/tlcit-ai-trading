import os
import datetime
import requests
import yfinance as yf
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Literal, Field
import google.auth.transport.requests
import google.oauth2.id_token

app = FastAPI()

# --- Security: only allow calls with a valid OIDC token ---
bearer = HTTPBearer(auto_error=False)

def verify_token(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    if creds is None:
        raise HTTPException(status_code=401, detail="Authorization required")
    audience = os.environ.get("OIDC_AUDIENCE")
    request = google.auth.transport.requests.Request()
    try:
        google.oauth2.id_token.verify_token(creds.credentials, request, audience=audience)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    return True

# --- Google Chat webhook for alerts ---
CHAT_WEBHOOK_URL = os.getenv("GOOGLE_CHAT_WEBHOOK")
def send_google_chat(message: str):
    if CHAT_WEBHOOK_URL:
        requests.post(CHAT_WEBHOOK_URL, json={"text": message})

# --- Request model ---
class SignalRequest(BaseModel):
    ticker: str = Field(..., description="Ticker symbol")
    timeframe: Literal["daily", "weekly", "hourly"] = "daily"
    trigger: str
    quantity: float = 0.0

# --- In-memory portfolio (replace with a real DB if you like) ---
portfolio = {}

# --- Health check ---
@app.get("/", tags=["health"])
async def health():
    return {"status": "OK"}

# --- Manual endpoints (protected) ---
@app.get("/score", dependencies=[Depends(verify_token)], tags=["signals"])
async def get_score():
    return {"ticker": "NEM", "conviction_score": 9.8, "reason": "Post-earnings momentum"}

@app.post("/signal", dependencies=[Depends(verify_token)], tags=["signals"])
async def generate_signal(req: SignalRequest):
    t = req.ticker.upper()
    if t == "NEM" and req.trigger.lower() == "breakout":
        send_google_chat(f"📈 TLCIT Signal: BUY {t}")
        return {"action": "BUY", "conviction": 9.8, "reason": "Breakout + gold correlation"}
    return {"action": "HOLD", "reason": "No signal"}

@app.post("/buy", dependencies=[Depends(verify_token)], tags=["trades"])
async def buy_stock(req: SignalRequest):
    s = req.ticker.upper()
    portfolio[s] = portfolio.get(s, 0) + req.quantity
    send_google_chat(f"✅ TRADE EXECUTED: Bought {req.quantity} of {s}")
    return {"status": "success", "portfolio": portfolio}

@app.post("/sell", dependencies=[Depends(verify_token)], tags=["trades"])
async def sell_stock(req: SignalRequest):
    s = req.ticker.upper()
    portfolio[s] = max(0, portfolio.get(s, 0) - req.quantity)
    send_google_chat(f"🔻 TRADE EXECUTED: Sold {req.quantity} of {s}")
    return {"status": "success", "portfolio": portfolio}

# --- Step 4: Automated scan endpoint (/scan) ---
@app.post("/scan", dependencies=[Depends(verify_token)], tags=["automation"])
async def scan_all():
    # Read tickers from env var, default to just NEM
    tickers = os.getenv("TICKERS", "NEM").split(",")
    summary = {}
    for t in tickers:
        t = t.strip()
        req = SignalRequest(ticker=t, timeframe="daily", trigger="breakout", quantity=1)
        res = await generate_signal(req)
        if res.get("action") == "BUY":
            await buy_stock(req)
            summary[t] = "bought"
        else:
            summary[t] = res.get("action")
    return {"scanned": summary}

# --- Uvicorn entrypoint ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)



