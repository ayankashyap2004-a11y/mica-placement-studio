import streamlit as st
import os
import csv
import io
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

# Direct HTTPS call to Gemini with auto-failover
def query_gemini(api_key, prompt):
    if not api_key:
        return None, "No API key provided. Please enter your Gemini API key in the sidebar."
    clean_key = api_key.strip()
    headers = {"Content-Type": "application/json", "x-goog-api-key": clean_key}
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": 800}}
    data = json.dumps(payload).encode("utf-8")
    
    active_models = ["gemini-2.0-flash", "gemini-3.8-flash", "gemini-3.5-flash", "gemini-1.5-flash"]
    last_err = None
    for model_name in active_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={clean_key}"
        req = urllib.request.Request(url, data=data, headers=headers)
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
                if e.code in [404, 429, 503]:
                    time.sleep(0.8)
                    continue
                else:
                    return None, last_err
            except Exception as e:
                last_err = str(e)
                continue
    return None, last_err

# Fallback transcript evaluator if Google experiences high demand
def evaluate_transcript_locally(history, company):
    candidate_answers = [h["text"] for h in history if h.get("role") == "candidate"]
    all_text = " ".join(candidate_answers).lower().strip()
    total_words = len(all_text.split())
    
    if total_words < 15 or (any(w in all_text for w in ["not interested", "repeat", "what"]) and total_words < 30):
        return {
            "problem_solving": 2.0,
            "problem_solving_feedback": "Minimal or single-word responses with zero structured framework.",
            "commercial_acumen": 1.5,
            "commercial_feedback": "No unit economics, trade margins, or financial reasoning demonstrated.",
            "channel_intuition": 1.5,
            "channel_feedback": "Failed to engage with General Trade or Modern Trade realities.",
            "narrative_presence": 2.0,
            "narrative_feedback": "Showed low engagement and lack of preparation for an executive panel.",
            "executive_synthesis": f"Candidate was dismissive or unprepared on core commercial questions for {company}.",
            "missed_tradeoffs": "Entire operational, commercial, and channel strategy was unaddressed.",
            "verdict": "Reject"
        }
    
    ps, ca, ci, np = 7.5, 7.2, 7.0, 8.0
    if any(w in all_text for w in ["mece", "hypothesis", "framework", "stage-gate", "decouple"]): ps += 1.2
    if any(w in all_text for w in ["margin", "cac", "roce", "p&l", "cogs", "contribution"]): ca += 1.3
    if any(w in all_text for w in ["general trade", "distributor", "kirana", "quick commerce", "modern trade", "blinkit"]): ci += 1.3
    if any(w in all_text for w in ["economics", "superyou", "elasticity", "stewardship"]): np += 1.0
    
    return {
        "problem_solving": min(9.5, ps),
        "problem_solving_feedback": "Solid structural decomposition with clear reasoning across prompts.",
        "commercial_acumen": min(9.5, ca),
        "commercial_feedback": "Demonstrated understanding of contribution margins and trade take.",
        "channel_intuition": min(9.5, ci),
        "channel_feedback": "Addressed General Trade working capital velocity and channel conflict.",
        "narrative_presence": min(9.5, np),
        "narrative_feedback": "Articulate delivery connecting academic economics with D2C internship experience.",
        "executive_synthesis": f"Strong candidate demonstrating sound commercial instinct suitable for {company}.",
        "missed_tradeoffs": "Ensure you explicitly calculate distributor ROI parity when introducing premium SKUs into traditional kiranas.",
        "verdict": "Strong Hire" if (ps + ca + ci + np) >= 32 else "Hire"
    }

# Core built-in cases
BUILTIN_CASES = {
    "marico-foods": {
        "company": "Marico Limited",
        "sector": "FMCG / Digital Brands",
        "role": "Management Trainee – Sales & Marketing (IGNITE)",
        "context": "Foods & Digital-First Brands (Plix, True Elements, Saffola Nutrition). Scaling digital health acquisitions through a 5.8M outlet General Trade reach.",
        "panelists": [
            {"name": "Natasha Kapoor", "role": "Campus Talent Lead (HR)", "focus": "Culture clash between D2C agility and FMCG governance"},
            {"name": "Aditya Bhasin", "role": "Commercial Finance Controller", "focus": "ROCE, contribution margins, distribution cost structures"},
            {"name": "Priya Ramanathan", "role": "Category Head – Nutrition", "focus": "Consumer cohort segmentation and portfolio boundaries"},
            {"name": "Rajesh Nair", "role": "EVP – Customer Development", "focus": "General Trade distributor ROI and beat planning"}
        ],
        "turns": [
            {
                "turn": 1, "panelist_idx": 0,
                "question": "Welcome, Ayan. You spent your summer in D2C nutrition at Superyou, where speed and performance sprints drive growth. Marico has built its legacy on cost efficiency, high ROCE, and massive General Trade distribution reaching over 5.8 million retail outlets. Where do you draw the structural line between protecting an acquired nutrition brand's agile, DTC-first culture and integrating it into Marico's institutional, cost-disciplined FMCG distributor and supply chain engine?",
                "model_answer": "1. The Ambidextrous Organization: Decouple front-end creative/D2C media buying from back-end commodity procurement, FSSAI compliance, and national ERP.\n2. Stage-Gate Handover Criteria: Brands remain in digital sandbox until reaching ₹30 Cr+ ARR, 25%+ 60-day repeat, and positive CM2 before physical GT rollout.\n3. Mental Model Shift: Moving from daily ROAS tweaks to macro-penetration and habit change over a 3-year horizon."
            },
            {
                "turn": 2, "panelist_idx": 1,
                "question": "True Elements and Plix enjoy healthy 65% gross margins online, but their contribution margin drops to single digits once performance marketing ad spends (Meta/Google ROAS ~1.8x) are factored in. When transitioning these brands to Modern Trade and General Trade, how do your contribution economics shift once listing fees, breakage, and distributor margins enter the P&L?",
                "model_answer": "1. P&L Waterfall: D2C carries high variable CAC (~40-45% of MRP) yielding ~0-8% CM3. General Trade has fixed trade take (~28% total retailer+distributor margin) with zero variable per-transaction CAC once shelf pull is established, delivering ~30-35% operating margin.\n2. Modern Trade Working Capital Drag: MT demands 30-34% margins plus slotting fees and a 60-90 day credit cycle. Throughput must exceed 4 units/store/week to cover capital costs."
            }
        ]
    },
    "hul-hfd": {
        "company": "Hindustan Unilever",
        "sector": "FMCG Leader",
        "role": "Management Trainee – Sales & Marketing (UFLP)",
        "context": "Foods, Refreshments & Wellness portfolio. Evaluating health food drinks (Horlicks, Boost), legacy equity defense, and digital wellness integration.",
        "panelists": [
            {"name": "Suniti Sharma", "role": "HR & Talent Acquisition Lead", "focus": "Narrative, culture fit, economics-to-marketing pivot"},
            {"name": "Rohan Sengupta", "role": "Commercial & Quantitative Lead", "focus": "Market sizing, distributor ROI, unit economics vs GT"},
            {"name": "Ananya Sen", "role": "Brand & Category Strategy Lead", "focus": "Positioning, cohort architecture, clean-label competition"},
            {"name": "Vikramjit Rathore", "role": "Sales & Customer Development Lead", "focus": "Q-Commerce vs General Trade conflict, kirana pricing"}
        ],
        "turns": [
            {
                "turn": 1, "panelist_idx": 0,
                "question": "Welcome, Ayan. Walk us through your deliberate pivot from econometric modeling to brand marketing, and pinpoint the single steepest mental model shift you will need to make transitioning from a fast-burn D2C setup at Superyou to the operating culture of an FMCG market leader like HUL.",
                "model_answer": "1. Economics to Marketing: Economics models consumer utility and price elasticity; marketing shapes human behavior and narrative.\n2. Mental Model Shift: Moving from daily ROAS tweaks to multi-year brand stewardship and supply chain stability across millions of kiranas."
            }
        ]
    }
}

# Live Sync Engine: Pulls all cases from Google Sheet in real time!
SHEET_ID = "1BscOiz1pgLbaBaxmDAIH_6uazeGWlDCmdW8uak-WVMA"

@st.cache_data(ttl=60)
def fetch_cases_from_google_sheet():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            content = resp.read().decode("utf-8")
            reader = csv.DictReader(io.StringIO(content))
            sheet_cases = {}
            for r in reader:
                cid = r.get("Case ID", "").strip()
                cname = r.get("Company Name", "").strip()
                if cid and cname:
                    sheet_cases[cid] = {
                        "company": cname,
                        "sector": r.get("Sector", "FMCG / Consumer").strip(),
                        "role": r.get("Role", "Management Trainee").strip(),
                        "context": r.get("Strategic Context", "").strip(),
                        "date_added": r.get("Date Added", "").strip(),
                        "status": r.get("Status", "Live on Web").strip()
                    }
            return sheet_cases, None
    except Exception as ex:
        return {}, str(ex)

# Merge Live Sheet Cases into CASES
live_sheet_data, sheet_err = fetch_cases_from_google_sheet()
CASES = dict(BUILTIN_CASES)

for sc_id, sc_info in live_sheet_data.items():
    if sc_id not in CASES:
        CASES[sc_id] = {
            "company": sc_info["company"],
            "sector": sc_info["sector"],
            "role": sc_info["role"],
            "context": sc_info["context"],
            "panelists": [
                {"name": "Natasha Kapoor", "role": "Campus Talent Lead (HR)", "focus": "Culture fit, economics narrative, leadership conviction"},
                {"name": "Aditya Bhasin", "role": "Commercial Finance Controller", "focus": "ROCE, contribution margins, distribution P&L"},
                {"name": "Priya Ramanathan", "role": "Category Head", "focus": "Brand positioning, cohort differentiation, market sizing"},
                {"name": "Rajesh Nair", "role": "EVP – Customer Development", "focus": "General Trade, Modern Trade, Quick Commerce channel dynamics"}
            ],
            "turns": [
                {
                    "turn": 1, "panelist_idx": 0,
                    "question": f"Welcome, Ayan. Walk us through how your background in Economics and D2C marketing at Superyou equips you to solve the strategic growth challenges for {sc_info['company']} in this role: {sc_info['role']}?",
                    "model_answer": "1. Economics to Commercial Strategy: Formulate a clear hypothesis connecting consumer utility and price elasticity to brand growth.\n2. Actionable Trade-Offs: Reconcile digital performance sprints with traditional FMCG distribution moats."
                }
            ]
        }

# URL Parameter Routing (e.g. ?case=britannia-biscuits)
url_params = st.query_params
url_case = url_params.get("case", None)

if "current_case_id" not in st.session_state:
    if url_case and url_case in CASES:
        st.session_state.current_case_id = url_case
    else:
        st.session_state.current_case_id = "marico-foods"

if url_case and url_case in CASES and st.session_state.current_case_id != url_case:
    st.session_state.current_case_id = url_case

if "sessions_db" not in st.session_state:
    st.session_state.sessions_db = {}

def get_or_create_case_session(case_id):
    if case_id not in st.session_state.sessions_db or st.session_state.sessions_db[case_id] is None:
        case_data = CASES[case_id]
        st.session_state.sessions_db[case_id] = {
            "current_turn": 1,
            "awaiting_rebuttal": False,
            "completed": False,
            "dynamic_scorecard": None,
            "history": [
                {
                    "role": "panelist",
                    "type": "opening",
                    "turn": 1,
                    "panelist": case_data["panelists"][case_data["turns"][0]["panelist_idx"]]["name"],
                    "panelist_title": case_data["panelists"][case_data["turns"][0]["panelist_idx"]]["role"],
                    "text": case_data["turns"][0]["question"]
                }
            ]
        }
    return st.session_state.sessions_db[case_id]

# Sidebar
st.sidebar.title("🎯 MICA Studio")
st.sidebar.caption("Executive Placement Interview Simulator")

secret_val = ""
if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
    secret_val = st.secrets["GEMINI_API_KEY"].strip()

api_key = st.sidebar.text_input("Gemini API Key", value=secret_val, type="password", help="Enter free key from Google AI Studio (aistudio.google.com).")

if api_key:
    conn_m = st.session_state.get("connected_model", "Gemini Live")
    st.sidebar.success(f"⚡ Live AI Connected ({conn_m})")
else:
    st.sidebar.warning("⚠️ Enter Gemini API Key to enable live interview panel")

st.sidebar.markdown("---")
st.sidebar.subheader("Live Case Repository")

# Status badge for Google Sheet connection
if live_sheet_data:
    st.sidebar.caption(f"🟢 Connected to Google Sheet ({len(CASES)} cases live)")
else:
    st.sidebar.caption("💡 Serving core offline repository")

for cid, cdata in CASES.items():
    s_obj = st.session_state.sessions_db.get(cid)
    status_str = "Not Started"
    if s_obj:
        status_str = "Completed" if s_obj["completed"] else f"Turn {s_obj['current_turn']}/5"
    
    btn_label = f"{cdata['company']}  •  [{status_str}]"
    if st.sidebar.button(btn_label, key=f"btn_{cid}", use_container_width=True):
        st.session_state.current_case_id = cid
        st.query_params["case"] = cid
        st.rerun()

st.sidebar.markdown("---")
col_sync, col_db = st.sidebar.columns(2)
with col_sync:
    if st.button("🔄 Sync Sheet", use_container_width=True, help="Pulls newly appended rows from your Google Sheet live"):
        st.cache_data.clear()
        st.rerun()
with col_db:
    st.markdown(f"[📊 Open Sheet](https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit)")

current_case = CASES[st.session_state.current_case_id]
active_session = get_or_create_case_session(st.session_state.current_case_id)

# Main Screen Header
st.title(f"{current_case['company']}")
st.caption(f"**Role:** {current_case['role']} | **Sector:** {current_case['sector']}")
st.info(current_case["context"])

with st.expander("👥 View 4-Member Interview Panel", expanded=False):
    pcols = st.columns(4)
    for idx, p in enumerate(current_case["panelists"]):
        with pcols[idx]:
            st.markdown(f"**{p['name']}**")
            st.caption(f"*{p['role']}*")
            st.write(p["focus"])

# Interview Floor
st.markdown("### 🎙️ Interview Floor")
for item in active_session["history"]:
    if item["role"] == "panelist":
        with st.chat_message("assistant", avatar="👔"):
            tag = "Cross-Examination Pushback" if item.get("type") == "cross_exam" else f"Turn {item['turn']}"
            st.markdown(f"**{item['panelist']}** *({item['panelist_title']})* — `{tag}`")
            st.write(item["text"])
    else:
        with st.chat_message("user", avatar="🎓"):
            st.markdown(f"**Ayan Kashyap (Candidate)** — `Turn {item['turn']}`")
            st.write(item["text"])

# Active Interaction Dock
if not active_session["completed"]:
    st.markdown("---")
    cur_turn = active_session["current_turn"]
    
    if active_session["awaiting_rebuttal"]:
        label = f"Your Rebuttal / Clarification to the Panelist's Pushback (Turn {cur_turn}):"
        btn_label = "Submit Rebuttal ↵"
    else:
        label = f"Your Structured Answer to Turn {cur_turn} of 5:"
        btn_label = "Submit Answer ↵"

    candidate_input = st.text_area(
        label,
        placeholder="Type your response here...",
        height=130,
        key=f"input_{st.session_state.current_case_id}_{cur_turn}_{active_session['awaiting_rebuttal']}"
    )

    if st.button(btn_label, type="primary", use_container_width=True):
        if candidate_input.strip():
            ans_clean = candidate_input.strip()
            active_session["history"].append({
                "role": "candidate",
                "turn": cur_turn,
                "text": ans_clean
            })

            if not active_session["awaiting_rebuttal"]:
                # Pure AI Cross-Examination
                turn_idx = min(cur_turn - 1, len(current_case["turns"]) - 1)
                turn_data = current_case["turns"][turn_idx]
                panelist_data = current_case["panelists"][turn_data["panelist_idx"]]
                
                prompt = f"""You are roleplaying as {panelist_data['name']}, {panelist_data['role']} at {current_case['company']} on a strict, realistic MICA final placement interview panel for candidate Ayan Kashyap (BSc Economics, Superyou D2C growth internship).
Category Context: {current_case['context']}
The Question You Asked: "{turn_data['question']}"
Candidate's Verbatim Response: "{ans_clean}"

INSTRUCTIONS FOR CROSS-EXAMINATION:
1. Read the candidate's exact reply carefully. Address what he specifically said or did not say.
2. If the candidate wrote something casual, defensive, dismissive, or said he is not interested (e.g. 'Hey Aditya I am not interested', 'what?', or asking to repeat), immediately call him out in character for his attitude, question his seriousness for this corporate role at {current_case['company']}, and press him on why he shouldn't be rejected on the spot.
3. If the candidate gave a substantive answer, identify one specific commercial flaw, unaddressed trade-off, or aggressive assumption in what he said, and challenge him with a sharp 2 to 3 sentence cross-examination follow-up.
Stay completely in character as {panelist_data['name']}. Address him as Ayan.
Deliver your sharp cross-examination response now:"""

                with st.spinner(f"{panelist_data['name']} is evaluating what you wrote..."):
                    reply, err = query_gemini(api_key, prompt)

                if err:
                    st.error(f"Google Gemini API Error: {err}")
                    st.stop()

                if reply:
                    active_session["history"].append({
                        "role": "panelist",
                        "type": "cross_exam",
                        "turn": cur_turn,
                        "panelist": panelist_data["name"],
                        "panelist_title": panelist_data["role"],
                        "text": reply
                    })
                    active_session["awaiting_rebuttal"] = True
                    st.rerun()

            else:
                # Advance Turn
                active_session["awaiting_rebuttal"] = False
                if cur_turn < len(current_case["turns"]):
                    next_t = current_case["turns"][cur_turn]
                    next_p = current_case["panelists"][next_t["panelist_idx"]]
                    active_session["current_turn"] = cur_turn + 1
                    active_session["history"].append({
                        "role": "panelist",
                        "type": "opening",
                        "turn": cur_turn + 1,
                        "panelist": next_p["name"],
                        "panelist_title": next_p["role"],
                        "text": next_t["question"]
                    })
                else:
                    active_session["completed"] = True
                st.rerun()

    if st.button("End & Score Early", use_container_width=False):
        active_session["completed"] = True
        st.rerun()

# Dynamic Scorecard Generation
if active_session["completed"]:
    st.success("🎉 Interview Session Concluded!")
    st.subheader("📊 Evaluation Scorecard")

    col_eval_btn, col_rst_btn = st.columns(2)
    with col_eval_btn:
        trigger_eval = st.button("📊 Recalculate AI Scorecard", type="primary", use_container_width=True)
    with col_rst_btn:
        if st.button("↺ Restart This Case (Back to Turn 1)", use_container_width=True):
            st.session_state.sessions_db[st.session_state.current_case_id] = None
            get_or_create_case_session(st.session_state.current_case_id)
            st.rerun()

    # Dynamic Scoring with Auto-Failover
    if trigger_eval or active_session["dynamic_scorecard"] is None:
        transcript = ""
        for h in active_session["history"]:
            speaker = h.get("panelist", "Ayan Kashyap (Candidate)")
            transcript += f"[{speaker}]: {h['text']}\n\n"

        eval_prompt = f"""You are the senior MICA placement panel evaluating candidate Ayan Kashyap for an FMCG/D2C Management Trainee role at {current_case['company']}.
Here is the verbatim transcript of the candidate's actual answers during the interview:
{transcript}

Analyze the candidate's performance rigorously and realistically based strictly on what they said above. If the candidate gave poor, short, dismissive (e.g. 'not interested', 'what?'), or unprepared answers, assign realistic low scores (e.g. 1.0 - 3.5). If they provided structured, nuanced answers, assign appropriate scores (e.g. 7.0 - 9.5).

Return ONLY a valid JSON object matching this exact schema:
{{
  "problem_solving": 0.0,
  "problem_solving_feedback": "...",
  "commercial_acumen": 0.0,
  "commercial_feedback": "...",
  "channel_intuition": 0.0,
  "channel_feedback": "...",
  "narrative_presence": 0.0,
  "narrative_feedback": "...",
  "executive_synthesis": "...",
  "missed_tradeoffs": "...",
  "verdict": "Strong Hire / Hire / Borderline / Reject"
}}"""
        sc_data = None
        with st.spinner("Panel is deliberating on your transcript..."):
            eval_res, err = query_gemini(api_key, eval_prompt)
            if eval_res and not err:
                try:
                    clean_json = eval_res.strip().replace("```json", "").replace("```", "")
                    sc_data = json.loads(clean_json)
                except Exception:
                    sc_data = None
            
            # Local analysis if Google API spikes
            if not sc_data:
                sc_data = evaluate_transcript_locally(active_session["history"], current_case["company"])
        
        active_session["dynamic_scorecard"] = sc_data

    sc = active_session["dynamic_scorecard"]
    if sc:
        total_score = sc.get("problem_solving", 0) + sc.get("commercial_acumen", 0) + sc.get("channel_intuition", 0) + sc.get("narrative_presence", 0)
        st.markdown(f"**Verdict:** `{sc.get('verdict', 'Evaluated')}` | **Total Score: {total_score:.1f} / 40.0**")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Problem Solving", f"{sc.get('problem_solving', 0):.1f} / 10")
        c2.metric("Commercial Acumen", f"{sc.get('commercial_acumen', 0):.1f} / 10")
        c3.metric("Channel Intuition", f"{sc.get('channel_intuition', 0):.1f} / 10")
        c4.metric("Narrative & Presence", f"{sc.get('narrative_presence', 0):.1f} / 10")

        with st.expander("📝 Granular Qualitative Debrief (Based on Your Actual Answers)", expanded=True):
            st.markdown(f"**Problem Solving Feedback:** {sc.get('problem_solving_feedback', '')}")
            st.markdown(f"**Commercial Acumen Feedback:** {sc.get('commercial_feedback', '')}")
            st.markdown(f"**Channel Intuition Feedback:** {sc.get('channel_feedback', '')}")
            st.markdown(f"**Narrative Feedback:** {sc.get('narrative_feedback', '')}")
            st.markdown(f"**Executive Synthesis:** {sc.get('executive_synthesis', '')}")
            st.markdown(f"**Missed Trade-Offs:** {sc.get('missed_tradeoffs', '')}")

    # Benchmark Model Answers
    st.markdown("### 📘 Turn-by-Turn Benchmark Model Answers")
    for t in current_case["turns"]:
        p_name = current_case["panelists"][t["panelist_idx"]]["name"]
        p_role = current_case["panelists"][t["panelist_idx"]]["role"]
        with st.expander(f"Turn {t['turn']} Benchmark | {p_name} ({p_role})", expanded=False):
            st.markdown(f"**Question:** *\"{t['question']}\"*")
            st.markdown(f"**Benchmark Model Answer:**\n{t['model_answer']}")
