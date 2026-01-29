import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from duckduckgo_search import DDGS
from groq import Groq
import requests

# Version 2.1 - Direct Secrets Integration
st.set_page_config(page_title="God-Tier Trade AI", layout="wide")

# --- FETCHING KEYS FROM STREAMLIT SECRETS ---
# Ab sidebar se baar-baar paste karne ki zaroorat nahi!
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    TELEGRAM_BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except:
    st.error("⚠️ Secrets not found! Please add GROQ_API_KEY in Streamlit Settings.")
    st.stop()

# --- FUNCTIONS (TECHNICAL & SENTIMENT) ---
def get_technical_analysis(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")
        if df.empty: return None, "No Data"
        
        df.ta.rsi(length=14, append=True)
        df.ta.ema(length=50, append=True)
        
        latest = df.iloc[-1]
        close_price = latest['Close']
        rsi = latest['RSI_14']
        ema_50 = latest['EMA_50']
        
        signal = "NEUTRAL"
        if rsi < 35 and close_price > ema_50: signal = "BULLISH (BUY CALL)"
        elif rsi > 65: signal = "BEARISH (BUY PUT)"
        
        return {"price": close_price, "rsi": rsi, "signal": signal}, None
    except Exception as e:
        return None, str(e)

def get_god_verdict(ticker, tech, news):
    client = Groq(api_key=GROQ_API_KEY)
    prompt = f"Analyze {ticker}: Price {tech['price']}, RSI {tech['rsi']}, Algo: {tech['signal']}. News: {news}. Give verdict: BUY_CALL, BUY_PUT, or WAIT with 1 reason."
    completion = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model="llama3-70b-8192")
    return completion.choices[0].message.content

# --- MAIN UI ---
st.title("🚀 God-Tier Trade AI")
ticker = st.text_input("Enter Ticker (e.g., ^NSEI, RELIANCE.NS)", "^NSEI")

if st.button("Analyze Now"):
    tech, err = get_technical_analysis(ticker)
    if err: st.error(err)
    else:
        st.metric("Price", f"₹{tech['price']:.2f}")
        verdict = get_god_verdict(ticker, tech, "Market is volatile")
        st.success(verdict)
        # Telegram Alert
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": f"Alert: {ticker} - {verdict}"})
