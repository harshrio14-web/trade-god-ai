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
    st.error("❌ GROQ_API_KEY is missing in Streamlit Secrets! Check Settings > Secrets.")
    st.stop()

# Initialize Groq Client
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- CORE LOGIC ---
def get_data(ticker):
    try:
        # Download data
        data = yf.download(ticker, period="1mo", interval="1d")
        if data.empty:
            return None, "Invalid Ticker or No Data Found"
        
        # Calculate RSI using pandas_ta
        data['RSI'] = ta.rsi(data['Close'], length=14)
        
        # Get latest values
        latest_price = float(data['Close'].iloc[-1])
        latest_rsi = float(data['RSI'].iloc[-1])
        
        return {"price": latest_price, "rsi": latest_rsi}, None
    except Exception as e:
        return None, str(e)

# --- UI INTERFACE ---
ticker_input = st.text_input("Enter Ticker (e.g., ^NSEI, RELIANCE.NS)", "^NSEI")

if st.button("Analyze Now"):
    with st.spinner("Market Gods are thinking..."):
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
                
                # Telegram Notification
                if "TELEGRAM_BOT_TOKEN" in st.secrets:
                    t_url = f"https://api.telegram.org/bot{st.secrets['TELEGRAM_BOT_TOKEN']}/sendMessage"
                    t_data = {"chat_id": st.secrets["TELEGRAM_CHAT_ID"], "text": f"🔥 Trade Alert: {ticker_input}\n{verdict}"}
                    requests.post(t_url, data=t_data)
                    st.toast("Sent to Telegram!")
            except Exception as e:
                st.error(f"🤖 AI Brain Error: {str(e)}")
