import streamlit as st
import os
import json
import time
import urllib.request
import urllib.error

st.set_page_config(
    page_title="MICA Placement Studio | Final Interview Simulator",
    page_icon="🎯",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .main { background-color: #0b0f19; color: #f3f4f6; }
    .stChatMessage { border-radius: 12px; margin-bottom: 12px; }
</style>
""", unsafe_allow_html=True)

# Direct HTTPS call targeting active Google production models with auto-failover on 503 / 429 high demand
def query_gemini(api_key, prompt):
    if not api_key:
        return None, "No API key provided. Please enter your Gemini API key in the sidebar."
    
    clean_key = api_key.strip()
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": clean_key
    }
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 800
        }
    }
    data = json.dumps(payload).encode("utf-8")
    
    # Priority order: Highly stable production models with multi-model failover
    active_models = [
        "gemini-2.0-flash",
        "gemini-3.8-flash",
        "gemini-3.5-flash",
        "gemini-1.5-flash"
    ]
    
    last_err = None
    for model_name in active_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={clean_key}"
        req = urllib.request.Request(url, data=data, headers=headers)
        
        # Up to 2 retries per model if Google servers experience high demand spikes (503 / 429)
        for attempt in range(2):
            try:
                with urllib.request.urlopen(req, timeout=20) as response:
                    res_json = json.loads(response.read().decode("utf-8"))
                    text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                    st.session_state.connected_model = model_name
                    return text, None
            except urllib.error.HTTPError as e:
                err_msg = e.read().decode("utf-8")
                try:
                    err_json = json.loads(err_msg)
                    last_err = err_json.get("error", {}).get("message", str(e))
                except Exception:
                    last_err = f"HTTP Error {e.code}: {e.reason}"
                
                # If model not found (404), rate limited (429), or high demand (503), failover to next model
                if e.code in [404, 429, 503]:
                    time.sleep(0.8)
                    continue
                else:
                    return None, last_err
            except Exception as e:
                last_err = str(e)
                continue
            
    return None, last_err

# Comprehensive in-app transcript evaluator if Google experiences high demand
def evaluate_transcript_locally(history, company):
    candidate_answers = [h["text"] for h in history if h.get("role") == "candidate"]
    all_text = " ".join(candidate_answers).lower().strip()
    words = all_text.split()
    total_words = len(words)
    
    if total_words < 15 or (any(w in all_text for w in ["not interested", "repeat", "what"]) and total_words < 30):
        return {
            "problem_solving": 2.0,
            "problem_solving_feedback": "Candidate provided dismissive or single-word responses with zero structured framework.",
            "commercial_acumen": 1.5,
            "commercial_feedback": "No unit economics
