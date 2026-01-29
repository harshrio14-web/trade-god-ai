# Version 2.0 - Fixed API and Error
import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from duckduckgo_search import DDGS
from groq import Groq
import requests

# --- PAGE CONFIG ---
st.set_page_config(page_title="God-Tier Trade AI", layout="wide")

# --- SIDEBAR: API KEYS ---
st.sidebar.title("🔑 API Keys & Settings")
GROQ_API_KEY = st.sidebar.text_input("Groq API Key", type="password")
TELEGRAM_BOT_TOKEN = st.sidebar.text_input("Telegram Bot Token", type="password")
TELEGRAM_CHAT_ID = st.sidebar.text_input("Telegram Chat ID")

# --- FUNCTIONS ---

def get_technical_analysis(ticker):
    """
    Fetches data and calculates technical indicators safely.
    Fixes the 'Identically-labeled Series' error by using .iloc[-1] for final values.
    """
    try:
        # 1. Fetch Data
        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")
        
        if df.empty:
            return None, "No Data Found"
        
        # 2. Calculate Indicators (RSI, EMA, MACD)
        # Using pandas_ta to add columns directly
        df.ta.rsi(length=14, append=True)
        df.ta.ema(length=50, append=True)
        df.ta.macd(append=True)
        
        # 3. Get the LATEST Row (Aaj ka data)
        # Isse 'Series' error nahi aayega kyunki hum sirf last value utha rahe hain
        latest = df.iloc[-1]
        
        # Safe extraction of values
        close_price = latest['Close']
        rsi = latest['RSI_14']
        ema_50 = latest['EMA_50']
        macd = latest['MACD_12_26_9']
        macd_signal = latest['MACDs_12_26_9']
        
        # 4. Generate Technical Signal
        signal = "NEUTRAL"
        score = 0
        
        # RSI Logic
        if rsi < 30: score += 1      # Oversold (Buy signal)
        elif rsi > 70: score -= 1    # Overbought (Sell signal)
        
        # EMA Logic (Trend)
        if close_price > ema_50: score += 1
        else: score -= 1
        
        # MACD Logic
        if macd > macd_signal: score += 1
        else: score -= 1
        
        if score >= 2: signal = "BULLISH (BUY CALL)"
        elif score <= -2: signal = "BEARISH (BUY PUT)"
        
        return {
            "current_price": close_price,
            "rsi": rsi,
            "trend": "Up" if close_price > ema_50 else "Down",
            "signal": signal
        }, None

    except Exception as e:
        return None, str(e)

def get_sentiment(ticker):
    """Gets news and sentiment using DuckDuckGo"""
    try:
        with DDGS() as ddgs:
            # Using clean keywords for better results
            keywords = f"{ticker} stock news market sentiment"
            results = list(ddgs.text(keywords, max_results=5))
            
            if not results:
                return "No news found."
                
            summary = " ".join([r['body'] for r in results])
            return summary[:2000] # Limit text for LLM
    except Exception as e:
        return f"Error fetching news: {e}"

def get_god_verdict(ticker, tech_data, news_summary):
    """Sends everything to Groq AI for the final decision"""
    if not GROQ_API_KEY:
        return "Please enter Groq API Key in sidebar."
    
    client = Groq(api_key=GROQ_API_KEY)
    
    prompt = f"""
    Act as a Hedge Fund Manager. Analyze this data for {ticker}:
    
    1. TECHNICALS:
    - Price: {tech_data['current_price']}
    - RSI: {tech_data['rsi']} (Over 70=Overbought, Under 30=Oversold)
    - Trend: {tech_data['trend']}
    - Algo Signal: {tech_data['signal']}
    
    2. NEWS SENTIMENT:
    {news_summary}
    
    DECISION:
    Based on both technicals and news, give a ONE WORD Verdict: "BUY_CALL", "BUY_PUT", or "WAIT".
    Then give a 1-line reason why.
    """
    
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-70b-8192",
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"AI Error: {e}"

def send_telegram_alert(message):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        try:
            requests.post(url, data=data)
            return True
        except:
            return False
    return False

# --- MAIN UI ---
st.title("🚀 God-Tier Stock & Nifty AI")

ticker = st.text_input("Enter Ticker (e.g., ^NSEI, RELIANCE.NS, TATAMOTORS.NS)", value="^NSEI")

if st.button("Analyze Now"):
    with st.spinner('Asking the Market Gods...'):
        
        # 1. Technical Analysis
        tech_data, error = get_technical_analysis(ticker)
        
        if error:
            st.error(f"Error: {error}")
        else:
            # Display Metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Price", f"₹{tech_data['current_price']:.2f}")
            col2.metric("RSI", f"{tech_data['rsi']:.2f}")
            col3.metric("Trend", tech_data['trend'])
            
            # 2. Sentiment Analysis
            st.subheader("🕵️ Sentiment Spy")
            news_summary = get_sentiment(ticker)
            st.info(news_summary[:500] + "...")
            
            # 3. God Verdict
            st.subheader("⚡ God Brain Verdict")
            verdict = get_god_verdict(ticker, tech_data, news_summary)
            st.success(verdict)
            
            # 4. Notification
            if "BUY" in verdict.upper():
                msg = f"🚨 TRADE ALERT: {ticker}\nVerdict: {verdict}\nPrice: {tech_data['current_price']}"
                if send_telegram_alert(msg):
                    st.toast("Telegram Alert Sent! 📲")
