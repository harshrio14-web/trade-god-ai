import streamlit as st
import yfinance as yf
import pandas as pd
# Manual calculation of indicators to avoid dependency issues
from groq import Groq
from duckduckgo_search import DDGS
import requests
import datetime

# --- Page Config ---
st.set_page_config(page_title="God-Tier Stock & Nifty Analysis", layout="wide")

# --- Sidebar for API Keys ---
with st.sidebar:
    st.header("🔑 API Configurations")
    groq_api_key = st.text_input("Groq API Key", type="password")
    telegram_bot_token = st.text_input("Telegram Bot Token", type="password")
    telegram_chat_id = st.text_input("Telegram Chat ID")
    
    st.info("Note: No data is stored. This dashboard uses the Groq Llama3-70b model.")

# --- Agent 1: Technical Analyst ---
def get_technical_analysis(ticker):
    try:
        data = yf.download(ticker, period="1y", interval="1d")
        if data.empty:
            return None, "Ticker not found or no data available."
        
        # Calculate RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # Calculate MACD
        exp1 = data['Close'].ewm(span=12, adjust=False).mean()
        exp2 = data['Close'].ewm(span=26, adjust=False).mean()
        data['MACD'] = exp1 - exp2
        data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()
        
        # Calculate EMA 50
        data['EMA_50'] = data['Close'].ewm(span=50, adjust=False).mean()
        
        latest = data.iloc[-1]
        
        rsi_val = latest['RSI']
        macd_val = latest['MACD']
        macd_signal = latest['Signal_Line']
        ema_50 = latest['EMA_50']
        current_price = latest['Close']
        
        # Trend Determination
        trend = "Neutral"
        if current_price > ema_50 and macd_val > macd_signal and rsi_val > 50:
            trend = "Bullish"
        elif current_price < ema_50 and macd_val < macd_signal and rsi_val < 50:
            trend = "Bearish"
            
        # Convert to float to avoid pandas Series issues
        cp_val = float(current_price.iloc[0]) if isinstance(current_price, pd.Series) else float(current_price)
        rsi_v = float(rsi_val.iloc[0]) if isinstance(rsi_val, pd.Series) else float(rsi_val)
        macd_v = float(macd_val.iloc[0]) if isinstance(macd_val, pd.Series) else float(macd_val)
        macd_s = float(macd_signal.iloc[0]) if isinstance(macd_signal, pd.Series) else float(macd_signal)
        ema_v = float(ema_50.iloc[0]) if isinstance(ema_50, pd.Series) else float(ema_50)

        tech_summary = {
            "current_price": round(cp_val, 2),
            "rsi": round(rsi_v, 2),
            "macd": round(macd_v, 4),
            "macd_signal": round(macd_s, 4),
            "ema_50": round(ema_v, 2),
            "trend": trend,
            "data": data
        }
        return tech_summary, None
    except Exception as e:
        return None, str(e)

# --- Agent 2: Sentiment Spy ---
def get_sentiment_analysis(ticker):
    try:
        with DDGS() as ddgs:
            # Search for news and reddit mentions
            query = f"{ticker} stock news reddit sentiment"
            results = list(ddgs.text(query, max_results=5))
            
            if not results:
                return "No recent news or sentiment found.", "Neutral"
            
            news_snippets = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
            return news_snippets, "Analysis Pending"
    except Exception as e:
        return f"Error fetching sentiment: {str(e)}", "Error"

# --- Agent 3: The God Brain (LLM Logic) ---
def get_god_brain_verdict(api_key, tech_data, sentiment_data, ticker):
    if not api_key:
        return "Please provide Groq API Key", "N/A"
    
    client = Groq(api_key=api_key)
    
    prompt = f"""
    Act as a 'God-Tier' Financial Analyst. Analyze the following data for ticker: {ticker}
    
    TECHNICAL DATA:
    - Current Price: {tech_data['current_price']}
    - RSI: {tech_data['rsi']}
    - MACD: {tech_data['macd']} (Signal: {tech_data['macd_signal']})
    - 50-Day EMA: {tech_data['ema_50']}
    - Calculated Trend: {tech_data['trend']}
    
    SENTIMENT DATA (News/Reddit):
    {sentiment_data}
    
    Your Task:
    1. Evaluate the synergy between Technicals and Sentiment.
    2. Determine a clear trade signal: BUY CALL, BUY PUT, or NO TRADE.
    3. Provide a brief 2-sentence justification.
    
    Return the response in this EXACT format:
    SIGNAL: [SIGNAL_HERE]
    JUSTIFICATION: [JUSTIFICATION_HERE]
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        response = completion.choices[0].message.content
        return response
    except Exception as e:
        return f"LLM Error: {str(e)}"

# --- Telegram Alert Function ---
def send_telegram_alert(token, chat_id, message):
    if not token or not chat_id:
        return False, "Telegram credentials missing."
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return True, "Alert sent successfully!"
        else:
            return False, f"Failed to send alert: {response.text}"
    except Exception as e:
        return False, str(e)

# --- Main Dashboard UI ---
st.title("🚀 God-Tier Stock & Nifty Analysis Dashboard")
st.markdown("---")

ticker = st.text_input("Enter Ticker (e.g., ^NSEI, RELIANCE.NS, TSLA, BTC-USD)", value="^NSEI").upper()

if st.button("Analyze Now"):
    if not groq_api_key:
        st.error("Please enter your Groq API Key in the sidebar.")
    else:
        with st.spinner(f"Analyzing {ticker}..."):
            # 1. Technical Analysis
            tech_data, error = get_technical_analysis(ticker)
            
            if error:
                st.error(error)
            else:
                # 2. Sentiment Analysis
                sentiment_text, _ = get_sentiment_analysis(ticker)
                
                # 3. God Brain Verdict
                verdict = get_god_brain_verdict(groq_api_key, tech_data, sentiment_text, ticker)
                
                # --- Display Results ---
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader("📊 Technical Indicators")
                    st.metric("Live Price", f"{tech_data['current_price']}")
                    st.metric("RSI (14)", f"{tech_data['rsi']}")
                    st.metric("50-Day EMA", f"{tech_data['ema_50']}")
                    st.write(f"**Trend:** {tech_data['trend']}")
                    
                    # Chart
                    st.line_chart(tech_data['data']['Close'])
                
                with col2:
                    st.subheader("🕵️ Sentiment Spy")
                    st.info(sentiment_text[:1000] + "..." if len(sentiment_text) > 1000 else sentiment_text)
                
                st.markdown("---")
                st.subheader("🧠 The God Brain Verdict")
                
                # Parse Signal for Styling
                signal_color = "white"
                if "BUY CALL" in verdict.upper():
                    signal_color = "#00FF00" # Green
                elif "BUY PUT" in verdict.upper():
                    signal_color = "#FF0000" # Red
                
                st.markdown(f"""
                <div style="padding:20px; border-radius:10px; border: 2px solid {signal_color}; background-color: rgba(0,0,0,0.1);">
                    <h2 style="color:{signal_color}; text-align:center;">{verdict.split('JUSTIFICATION:')[0].replace('SIGNAL:', '').strip()}</h2>
                    <p style="font-size:1.2em;">{verdict.split('JUSTIFICATION:')[1].strip() if 'JUSTIFICATION:' in verdict else ''}</p>
                </div>
                """, unsafe_allow_index=True)
                
                # Store verdict in session state for alert
                st.session_state['last_verdict'] = f"Ticker: {ticker}\n{verdict}"

# --- Alert Section ---
st.markdown("---")
if 'last_verdict' in st.session_state:
    if st.button("📢 Send Alert to Telegram"):
        success, msg = send_telegram_alert(telegram_bot_token, telegram_chat_id, st.session_state['last_verdict'])
        if success:
            st.success(msg)
        else:
            st.error(msg)
else:
    st.write("Run an analysis first to enable alerts.")
