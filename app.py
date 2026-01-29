import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from groq import Groq
import requests

# Page Config
st.set_page_config(page_title="God-Tier Trade AI", layout="wide")
st.title("🚀 God-Tier Trade AI")

# --- SECRETS CHECK ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("❌ Secrets missing! Go to Settings > Secrets and add GROQ_API_KEY.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- CORE LOGIC ---
def get_data(ticker):
    try:
        # Download at least 3 months to get a proper RSI calculation
        data = yf.download(ticker, period="3mo", interval="1d")
        if data.empty:
            return None, "Invalid Ticker or No Data Found"
        
        # Calculate RSI and Clean Data
        data['RSI'] = ta.rsi(data['Close'], length=14)
        
        # ERROR FIX: Remove any rows with None/NaN values
        data = data.dropna()
        
        if data.empty:
            return None, "Not enough data to calculate indicators."
        
        # Get latest values safely
        latest_price = float(data['Close'].iloc[-1])
        latest_rsi = float(data['RSI'].iloc[-1])
        
        return {"price": latest_price, "rsi": latest_rsi}, None
    except Exception as e:
        return None, str(e)

# --- UI INTERFACE ---
ticker_input = st.text_input("Enter Ticker (e.g., ^NSEI, RELIANCE.NS)", "^NSEI")

if st.button("Analyze Now"):
    with st.spinner("Analyzing market patterns..."):
        res, err = get_data(ticker_input)
        
        if err:
            st.error(f"⚠️ Error: {err}")
        else:
            # Show Metrics
            c1, c2 = st.columns(2)
            c1.metric("Live Price", f"₹{res['price']:.2f}")
            c2.metric("RSI (14)", f"{res['rsi']:.2f}")
            
            # AI BRAIN VERDICT
            try:
                p = f"Stock: {ticker_input}, Price: {res['price']}, RSI: {res['rsi']}. Verdict: BUY_CALL, BUY_PUT, or WAIT? Short reason."
                chat = client.chat.completions.create(
                    messages=[{"role": "user", "content": p}],
                    model="llama3-70b-8192"
                )
                verdict = chat.choices[0].message.content
                st.success(f"🤖 AI Verdict: {verdict}")
                
                # Telegram Notification (Optional check)
                if "TELEGRAM_BOT_TOKEN" in st.secrets:
                    t_url = f"https://api.telegram.org/bot{st.secrets['TELEGRAM_BOT_TOKEN']}/sendMessage"
                    t_data = {"chat_id": st.secrets["TELEGRAM_CHAT_ID"], "text": f"🔥 Trade Alert: {ticker_input}\n{verdict}"}
                    requests.post(t_url, data=t_data)
                    st.toast("Alert sent to Telegram!")
            except Exception as e:
                st.error(f"🤖 AI Brain Error: {str(e)}")
