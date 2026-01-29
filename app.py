import streamlit as st
import yfinance as yf
import pandas as pd
from groq import Groq
import requests

st.set_page_config(page_title="God-Tier Trade AI", layout="wide")
st.title("🚀 God-Tier Trade AI")

# --- SECRETS CHECK ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("❌ Secrets missing! Add GROQ_API_KEY in Streamlit Settings.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- MANUAL RSI CALCULATION (No Library Needed) ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_data(ticker):
    try:
        # Download data (1 year for safety)
        df = yf.download(ticker, period="1y", interval="1d")
        
        if df.empty:
            return None, "Invalid Ticker or No Data Found"
        
        # Fixing Multi-index Issue (Very Important for Nifty)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Calculate RSI manually
        df['RSI'] = calculate_rsi(df['Close'])
        
        # Clean data
        df = df.dropna()
        
        if len(df) < 1:
            return None, "Data exists but calculation failed. Try another ticker."
            
        latest_price = float(df['Close'].iloc[-1])
        latest_rsi = float(df['RSI'].iloc[-1])
        
        return {"price": latest_price, "rsi": latest_rsi}, None
    except Exception as e:
        return None, str(e)

# --- UI ---
ticker_input = st.text_input("Enter Ticker (e.g., ^NSEI, RELIANCE.NS)", "^NSEI")

if st.button("Analyze Now"):
    with st.spinner("Decoding Market Secrets..."):
        res, err = get_data(ticker_input)
        
        if err:
            st.error(f"⚠️ Error: {err}")
        else:
            c1, c2 = st.columns(2)
            c1.metric("Live Price", f"₹{res['price']:.2f}")
            c2.metric("RSI (14)", f"{res['rsi']:.2f}")
            
            try:
                p = f"Stock: {ticker_input}, Price: {res['price']}, RSI: {res['rsi']}. Verdict: BUY_CALL, BUY_PUT, or WAIT? Short reason."
                chat = client.chat.completions.create(
                    messages=[{"role": "user", "content": p}],
                    model="llama3-70b-8192"
                )
                verdict = chat.choices[0].message.content
                st.success(f"🤖 AI Verdict: {verdict}")
                
                # Telegram Alert
                if "TELEGRAM_BOT_TOKEN" in st.secrets:
                    t_url = f"https://api.telegram.org/bot{st.secrets['TELEGRAM_BOT_TOKEN']}/sendMessage"
                    t_data = {"chat_id": st.secrets["TELEGRAM_CHAT_ID"], "text": f"🚨 {ticker_input}: {verdict}"}
                    requests.post(t_url, data=t_data)
                    st.toast("Sent to Telegram!")
            except Exception as e:
                st.error(f"🤖 AI Error: {str(e)}")
