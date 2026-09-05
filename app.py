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

# Custom Styling
st.markdown("""
<style>
    .main { background-color: #0b0f19; color: #f3f4f6; }
    .stChatMessage { border-radius: 12px; margin-bottom: 12px; }
</style>
""", unsafe_allow_html=True)

# Direct HTTPS call to Gemini REST API (zero SDK deprecation issues)
def query_gemini(api_key, prompt, model_name="gemini-1.5-flash"):
    if not api_key:
        return None, "No API key provided."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key.strip()}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 800
        }
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            text = res_json["candidates"][0]["content"]["parts"][0]["text"]
            return text, None
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_msg)
            return None, err_json.get("error", {}).get("message", str(e))
        except Exception:
            return None, f"HTTP Error {e.code}: {e.reason}"
    except Exception as e:
        return None, str(e)

# Master Cases Database with Benchmark Model Answers
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

# Sidebar
st.sidebar.title("🎯 MICA Studio")
st.sidebar.caption("Executive Placement Interview Simulator")

secret_key = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else ""
api_key = st.sidebar.text_input("Gemini API Key", value=secret_key, type="password", help="Enter free API key from Google AI Studio (aistudio.google.com).")

if api_key:
    st.sidebar.success("⚡ Live AI Active")
else:
    st.sidebar.warning("⚠️ Enter API key to activate live cross-examination")

st.sidebar.markdown("---")
st.sidebar.subheader("Case Repository")

for cid, cdata in CASES.items():
    s_obj = st.session_state.sessions_db.get(cid)
    status_str = "Not Started"
    if s_obj:
        status_str = "Completed" if s_obj["completed"] else f"Turn {s_obj['current_turn']}/5"
    
    col_btn, col_stat = st.sidebar.columns(2)
    with col_btn:
        if st.sidebar.button(f"{cdata['company']}", key=f"btn_{cid}", use_container_width=True):
            st.session_state.current_case_id = cid
            st.rerun()
    with col_stat:
        st.caption(status_str)

current_case = CASES[st.session_state.current_case_id]
active_session = get_or_create_case_session(st.session_state.current_case_id)

# Main Screen Header
st.title(f"{current_case['company']}")
st.caption(f"**Role:** {current_case['role']} | **Sector:** {current_case['sector']}")
st.info(current_case["context"])

with st.expander("👥 View 4-Member Interview Panel", expanded=False):
    cols = st.columns(4)
    for idx, p in enumerate(current_case["panelists"]):
        with cols[idx]:
            st.markdown(f"**{p['name']}**")
            st.caption(f"*{p['role']}*")
            st.write(p["focus"])

# Interview Floor
