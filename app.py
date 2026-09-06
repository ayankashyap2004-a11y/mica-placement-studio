import streamlit as st
import os
import json
import urllib.request
import urllib.error

st.set_page_config(
    page_title="MICA Placement Studio | Final Interview Simulator",
    page_icon="🎯",
    layout="wide"
)

# ==========================================
# OPTION TO HARDCODE YOUR API KEY HERE:
# Paste your 39-character key between the quotes if you want it always connected.
# Example: HARDCODED_API_KEY = "AIzaSy..."
# ==========================================


# Custom Styling
st.markdown("""
<style>
    .main { background-color: #0b0f19; color: #f3f4f6; }
    .stChatMessage { border-radius: 12px; margin-bottom: 12px; }
</style>
""", unsafe_allow_html=True)

# Bulletproof HTTPS call testing both v1 (GA) and v1beta (Beta) with all active models
def query_gemini(api_key, prompt):
    if not api_key:
        return None, "No API key provided."
    
    clean_key = api_key.strip()
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": clean_key
    }
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 800
        }
    }
    data = json.dumps(payload).encode("utf-8")
    
    # Sequence testing both GA (v1) and Beta (v1beta) across standard models
    attempts = [
        ("v1beta", "gemini-2.0-flash"),
        ("v1", "gemini-2.0-flash"),
        ("v1beta", "gemini-2.5-flash"),
        ("v1", "gemini-1.5-flash"),
        ("v1beta", "gemini-1.5-flash"),
        ("v1", "gemini-1.5-pro"),
        ("v1beta", "gemini-pro")
    ]
    
    last_err = None
    for api_ver, model_name in attempts:
        url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model_name}:generateContent?key={clean_key}"
        req = urllib.request.Request(url, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                res_json = json.loads(response.read().decode("utf-8"))
                text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                st.session_state.connected_model = f"{api_ver}/{model_name}"
                return text, None
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8")
            try:
                err_json = json.loads(err_msg)
                last_err = err_json.get("error", {}).get("message", str(e))
            except Exception:
                last_err = f"HTTP Error {e.code}: {e.reason}"
            if e.code == 404:
                continue
            else:
                return None, last_err
        except Exception as e:
            last_err = str(e)
            continue
            
    return None, last_err

# Master Cases Database
CASES = {
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
                "turn": 1,
                "panelist_idx": 0,
                "question": "Welcome, Ayan. You spent your summer in D2C nutrition at Superyou, where speed and performance sprints drive growth. Marico has built its legacy on cost efficiency, high ROCE, and massive General Trade distribution reaching over 5.8 million retail outlets. Where do you draw the structural line between protecting an acquired nutrition brand's agile, DTC-first culture and integrating it into Marico's institutional, cost-disciplined FMCG distributor and supply chain engine?",
                "model_answer": "1. The Ambidextrous Organization: Decouple front-end creative/D2C media buying from back-end commodity procurement, FSSAI compliance, and national ERP.\n2. Stage-Gate Handover Criteria: Brands remain in digital sandbox until reaching ₹30 Cr+ ARR, 25%+ 60-day repeat, and positive CM2 before physical GT rollout.\n3. Mental Model Shift: Moving from daily ROAS tweaks to macro-penetration and habit change over a 3-year horizon."
            },
            {
                "turn": 2,
                "panelist_idx": 1,
                "question": "True Elements and Plix enjoy healthy 65% gross margins online, but their contribution margin drops to single digits once performance marketing ad spends (Meta/Google ROAS ~1.8x) are factored in. When transitioning these brands to Modern Trade and General Trade, how do your contribution economics shift once listing fees, breakage, and distributor margins enter the P&L?",
                "model_answer": "1. P&L Waterfall: D2C carries high variable CAC (~40-45% of MRP) yielding ~0-8% CM3. General Trade has fixed trade take (~28% total retailer+distributor margin) with zero variable per-transaction CAC once shelf pull is established, delivering ~30-35% operating margin.\n2. Modern Trade Working Capital Drag: MT demands 30-34% margins plus slotting fees and a 60-90 day credit cycle. Throughput must exceed 4 units/store/week to cover capital costs."
            },
            {
                "turn": 3,
                "panelist_idx": 2,
                "question": "Saffola Fittify occupies the health/wellness space, while True Elements owns clean breakfast and Plix owns plant nutrition. How do you design consumer cohort targeting so that these three brands do not cannibalize each other's digital and retail shelf space?",
                "model_answer": "1. 3-Way Brand Matrix: Saffola Fittify (32-48 yr mass-affluent family health; ₹200-350; Supermarkets/GT), True Elements (24-35 yr urban clean breakfast; ₹350-550; Q-Commerce/MT), Plix (18-28 yr youth lifestyle/beauty; ₹600-1200; D2C/Nykaa/Chemists).\n2. Channel & Pack Isolation: Negative cross-bidding on search ads; bulk jars for D2C/MT and single-serve impulse pouches for Q-Comm/GT."
            },
            {
                "turn": 4,
                "panelist_idx": 3,
                "question": "Traditional FMCG stockists refuse to stock slow-moving premium health mix SKUs because the inventory turns are under 2.5 per month compared to 8.0 turns for Parachute. How do you incentivize the sales force and trade partners to carry this portfolio?",
                "model_answer": "1. Distributor ROI Parity: Parachute turns 8x/mo @ 5% margin = 40% monthly capital return. At 2.5 turns/mo, stockist needs 11% trade margin + 21-day credit terms + 90-day buyback guarantee.\n2. Gold Store Beat Strategy: Restrict distribution to top 5% high-throughput urban grocers and modern pharmacies (~65,000 outlets nationally) rather than blanket dumping.\n3. Sales Rep Incentives: Pay sales force commissions exclusively on verified retailer secondary replenishment, not primary stock dumping."
            },
            {
                "turn": 5,
                "panelist_idx": 0,
                "question": "Final turn: Walk us through how your BSc in Economics directly influences how you evaluate price elasticity when Marico passes on commodity cost inflation to the mass consumer.",
                "model_answer": "1. Kinked Demand Curves around Coinage Barriers: Demand elasticity spikes from -0.6 to -2.8 when crossing mental coin thresholds (₹5, ₹10, ₹20).\n2. Asymmetric Pass-Through: De-gram (shrinkflate) low unit packs (₹5 & ₹10) by 7-9% to maintain nominal price for daily-wage earners; pass on nominal price increases to larger family packs where affluent buyers exhibit low elasticity.\n3. Consumer Surplus Framing: Announce functional or packaging improvements concurrently to shift the perceived utility curve outward."
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
                "turn": 1,
                "panelist_idx": 0,
                "question": "Welcome, Ayan. Walk us through your deliberate pivot from econometric modeling to brand marketing, and pinpoint the single steepest mental model shift you will need to make transitioning from a fast-burn D2C setup at Superyou to the operating culture of an FMCG market leader like HUL.",
                "model_answer": "1. Economics to Marketing: Economics models consumer utility and price elasticity; marketing shapes human behavior and narrative.\n2. Mental Model Shift: Moving from daily ROAS tweaks to multi-year brand stewardship and supply chain stability across millions of kiranas."
            },
            {
                "turn": 2,
                "panelist_idx": 1,
                "question": "Size the annual market for premium adult protein drinks in Tier-1 metros, and walk through how you would reconcile a 60% gross margin D2C unit economic structure with a General Trade distributor model that demands 18-20% system margins.",
                "model_answer": "1. Market Sizing: ~5M SEC A/B Tier-1 households x 8% category penetration = 400,000 consuming households. At ₹1,000/month = ₹480 Cr annual TAM.\n2. Margin Reconciliation: D2C 60% GM is eroded by 40% CAC. In GT, 20% trade margins replace variable CAC, delivering higher net operating margin per unit."
            },
            {
                "turn": 3,
                "panelist_idx": 2,
                "question": "If we launch an aggressive 'zero-refined-sugar, clean-protein' sub-brand under Horlicks, how do you prevent consumer confusion and cannibalization of our core mass-market SKUs that still drive 80% of our category operating profits?",
                "model_answer": "1. Endorsed Sub-Brand: Launch as 'Horlicks Plus Active' with distinct matte packaging and 2.5x higher price tier.\n2. Channel Separation: Sell clean-protein exclusively on Q-Commerce, D2C, and Modern Trade in 400g tubs (₹650+), keeping core Horlicks anchored in 500g pouches and sachets in GT."
            },
            {
                "turn": 4,
                "panelist_idx": 3,
                "question": "Quick commerce players like Blinkit and Zepto are discounting our top-selling 500g jars by 18%, triggering severe protests from General Trade wholesalers and kiranas. What concrete channel strategy and pack-architecture changes would you implement?",
                "model_answer": "1. Channel-Exclusive Pack Architecture: Keep 500g refill pouch exclusive to GT; create distinct 400g 'Easy-Pour Bottle' for Q-Commerce to prevent barcode-to-barcode price matching.\n2. Minimum Advertised Price (MAP): Tie platform trade allowances to strict MAP price adherence."
            },
            {
                "turn": 5,
                "panelist_idx": 1,
                "question": "Raw input costs have surged by 220 basis points. The CFO wants an immediate 5% price hike across the board. The Brand Director insists on absorbing the hit to defend market share against D2C challengers. What is your balanced P&L recommendation?",
                "model_answer": "1. Bifurcated Pricing: Absorb 100 bps on core mass SKUs via factory yield optimization and de-gramming sachets by 4-5%; implement 6-7% price hike on premium/adult extensions where demand is inelastic."
            }
        ]
    }
}

# Session State Persistence
if "current_case_id" not in st.session_state:
    st.session_state.current_case_id = "marico-foods"

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

# Resolve API Key Priority: 1) Hardcoded, 2) Streamlit Secrets, 3) Sidebar Input
resolved_key = HARDCODED_API_KEY.strip()
if not resolved_key and hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
    resolved_key = st.secrets["GEMINI_API_KEY"].strip()

# Sidebar
st.sidebar.title("🎯 MICA Studio")
st.sidebar.caption("Executive Placement Interview Simulator")

if resolved_key:
    api_key = resolved_key
    connected_info = st.session_state.get("connected_model", "Connected")
    st.sidebar.success(f"⚡ Live AI Active ({connected_info})")
else:
    api_key = st.sidebar.text_input("Gemini API Key", type="password", help="Enter key from Google AI Studio (aistudio.google.com).")
    if api_key:
        st.sidebar.success("⚡ Key Entered")
    else:
        st.sidebar.warning("⚠️ Enter key or hardcode in app.py")

st.sidebar.markdown("---")
st.sidebar.subheader("Case Repository")

for cid, cdata in CASES.items():
    s_obj = st.session_state.sessions_db.get(cid)
    status_str = "Not Started"
    if s_obj:
        status_str = "Completed" if s_obj["completed"] else f"Turn {s_obj['current_turn']}/5"
    
    if st.sidebar.button(f"{cdata['company']}  •  [{status_str}]", key=f"btn_{cid}", use_container_width=True):
        st.session_state.current_case_id = cid
        st.rerun()

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
                # Stage A: Generate live cross-examination
                turn_data = current_case["turns"][cur_turn - 1]
                panelist_data = current_case["panelists"][turn_data["panelist_idx"]]
                
                cross_exam_done = False
                if api_key:
                    with st.spinner(f"{panelist_data['name']} is evaluating your response..."):
                        prompt = f"""You are roleplaying as {panelist_data['name']}, {panelist_data['role']} at {current_case['company']} on a strict MICA final placement interview panel for candidate Ayan Kashyap (BSc Economics, Superyou D2C growth internship).
Category Context: {current_case['context']}
The Question Asked: "{turn_data['question']}"
Candidate's Exact Response: "{ans_clean}"

Task:
1. Identify the most critical flaw, unaddressed commercial reality, or weak assumption in the candidate's answer (e.g. if they say 'what?' or give a vague answer, call them out immediately; if they give numbers, challenge the margin or ROI; if theoretical, challenge implementation).
2. Deliver a sharp, aggressive in-character cross-examination follow-up in 2 to 3 sentences. Address him as Ayan.
Do NOT reveal the model answer. Challenge him directly now:"""

                        reply, err = query_gemini(api_key, prompt)
                        if reply and not err:
                            active_session["history"].append({
                                "role": "panelist",
                                "type": "cross_exam",
                                "turn": cur_turn,
                                "panelist": panelist_data["name"],
                                "panelist_title": panelist_data["role"],
                                "text": reply
                            })
                            active_session["awaiting_rebuttal"] = True
                            cross_exam_done = True
                        elif err:
                            st.error(f"Google Gemini Error: {err}")

                if not cross_exam_done:
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

            else:
                # Stage B: Candidate gave rebuttal, advance to next turn!
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
    st.subheader("📊 Dynamic Placement Scorecard")

    # Action Buttons
    col_eval_btn, col_rst_btn = st.columns(2)
    with col_eval_btn:
        trigger_eval = st.button("📊 Calculate / Refresh AI Scorecard", type="primary", use_container_width=True)
    with col_rst_btn:
        if st.button("↺ Restart This Case", use_container_width=True):
            st.session_state.sessions_db[st.session_state.current_case_id] = None
            get_or_create_case_session(st.session_state.current_case_id)
            st.rerun()

    # Trigger Evaluation
    if trigger_eval or (active_session["dynamic_scorecard"] is None and api_key):
        with st.spinner("Panel is deliberating and scoring your actual answers..."):
            transcript = ""
            for h in active_session["history"]:
                speaker = h.get("panelist", "Ayan Kashyap (Candidate)")
                transcript += f"[{speaker}]: {h['text']}\n\n"

            eval_prompt = f"""You are the senior MICA placement interview panel evaluating candidate Ayan Kashyap for an FMCG/D2C Management Trainee role at {current_case['company']}.
Here is the verbatim transcript of the candidate's actual answers during the interview:
{transcript}

Analyze the candidate's performance rigorously and realistically based strictly on what they said above. If the candidate gave poor, short (e.g. 'what?'), or unprepared answers, assign realistic low scores (e.g. 1.0 - 4.0). If they provided structured, nuanced answers, assign appropriate scores (e.g. 7.0 - 9.5).

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
            eval_res, err = query_gemini(api_key, eval_prompt)
            if err:
                st.error(f"Google Gemini API Error: {err}")
            elif eval_res:
                try:
                    clean_json = eval_res.strip().replace("```json", "").replace("```", "")
                    active_session["dynamic_scorecard"] = json.loads(clean_json)
                except Exception as ex:
                    st.error(f"Failed to parse scorecard JSON: {ex}")

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
    else:
        st.info("Click 'Calculate / Refresh AI Scorecard' above to evaluate this session with your Gemini API key.")

    # Benchmark Model Answers
    st.markdown("### 📘 Turn-by-Turn Benchmark Model Answers")
    for t in current_case["turns"]:
        p_name = current_case["panelists"][t["panelist_idx"]]["name"]
        p_role = current_case["panelists"][t["panelist_idx"]]["role"]
        with st.expander(f"Turn {t['turn']} Benchmark | {p_name} ({p_role})", expanded=False):
            st.markdown(f"**Question:** *\"{t['question']}\"*")
            st.markdown(f"**Benchmark Model Answer:**\n{t['model_answer']}")
