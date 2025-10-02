import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
import sqlite3
import hashlib
import re
from bs4 import BeautifulSoup
import time

# Page configuration
st.set_page_config(
    page_title="KrishiMitra Maharashtra - AI-Powered Agriculture",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Anthropic client
@st.cache_resource
def get_anthropic_client():
    try:
        from anthropic import Anthropic
        
        # Try both locations for the API key
        api_key = None
        try:
            # First try root level
            api_key = st.secrets["ANTHROPIC_API_KEY"]
        except KeyError:
            try:
                # Then try under api_keys section
                api_key = st.secrets["api_keys"]["ANTHROPIC_API_KEY"]
            except KeyError:
                st.error("Could not find ANTHROPIC_API_KEY in secrets. Check your secrets configuration.")
                return None
        
        if api_key:
            return Anthropic(api_key=api_key)
        else:
            st.error("ANTHROPIC_API_KEY is empty")
            return None
            
    except ImportError:
        st.error("anthropic package not installed. Check requirements.txt and redeploy.")
        return None
    except Exception as e:
        st.error(f"Error initializing AI: {str(e)}")
        return None

# Custom CSS with improved styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.8rem;
        font-weight: bold;
        color: #2E7D32;
        text-align: center;
        padding: 1.5rem;
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        border-radius: 15px;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #558B2F;
        font-weight: bold;
        margin-top: 1.5rem;
        border-bottom: 3px solid #4CAF50;
        padding-bottom: 0.5rem;
    }
    .info-card {
        background-color: #F1F8E9;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 6px solid #4CAF50;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .price-card {
        background-color: #E8F5E9;
        padding: 1.2rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        transition: transform 0.2s;
    }
    .price-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.12);
    }
    .fertilizer-card {
        background-color: #FFF3E0;
        padding: 1.2rem;
        border-radius: 10px;
        border-left: 5px solid #FF9800;
        margin: 0.8rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    }
    .ai-card {
        background-color: #E3F2FD;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 6px solid #2196F3;
        margin: 1rem 0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }
    .notification-card {
        background-color: #F3E5F5;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #9C27B0;
        margin: 0.5rem 0;
    }
    .marketplace-card {
        background-color: #FFF8E1;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 6px solid #FFA000;
        margin: 1rem 0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }
    .bid-card {
        background-color: #E1F5FE;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #0288D1;
        margin: 0.5rem 0;
    }
    .ceda-attribution {
        background-color: #E8EAF6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 5px solid #3F51B5;
        margin: 0.8rem 0;
        font-size: 0.95em;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        animation: fadeIn 0.3s;
    }
    .user-message {
        background-color: #E3F2FD;
        border-left: 4px solid #2196F3;
    }
    .assistant-message {
        background-color: #F1F8E9;
        border-left: 4px solid #4CAF50;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    </style>
    """, unsafe_allow_html=True)

# ====================
# CEDA INTEGRATION (Original)
# ====================

CEDA_BASE_URL = "https://ceda.ashoka.edu.in"

CEDA_COMMODITY_MAP = {
    "Rice": ["rice", "paddy", "basmati"],
    "Wheat": ["wheat"],
    "Cotton": ["cotton"],
    "Maize": ["maize", "corn"],
    "Tomato": ["tomato"],
    "Potato": ["potato"],
    "Onion": ["onion"],
    "Soybean": ["soybean", "soya"],
    "Groundnut": ["groundnut", "peanut"],
    "Pomegranate": ["pomegranate"],
    "Chilli": ["chilli", "chili", "green chilli"],
    "Sugarcane": ["sugarcane", "sugar cane"]
}

def fetch_ceda_prices(commodity, state="Maharashtra", district=None):
    """Fetch agricultural prices from CEDA Ashoka University"""
    try:
        time.sleep(2)
        headers = {
            'User-Agent': 'KrishiMitra/1.0 (Educational; Non-commercial; Agricultural Price Research)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        commodity_keywords = CEDA_COMMODITY_MAP.get(commodity, [commodity.lower()])
        search_url = f"{CEDA_BASE_URL}/data/agricultural-prices"
        response = requests.get(search_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            price_data = []
            tables = soup.find_all('table', class_=['price-table', 'data-table'])
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        item_name = cols[0].get_text(strip=True).lower()
                        if any(keyword in item_name for keyword in commodity_keywords):
                            try:
                                price_data.append({
                                    'commodity': cols[0].get_text(strip=True),
                                    'market': cols[1].get_text(strip=True) if len(cols) > 1 else 'N/A',
                                    'price': cols[2].get_text(strip=True) if len(cols) > 2 else 'N/A',
                                    'date': cols[3].get_text(strip=True) if len(cols) > 3 else 'N/A',
                                    'source': 'CEDA Ashoka University'
                                })
                            except:
                                continue
            if price_data:
                df = pd.DataFrame(price_data)
                return df, "✅ Data retrieved from CEDA Ashoka University"
            else:
                return None, f"No price data found for {commodity} at CEDA"
        elif response.status_code == 404:
            return None, "CEDA endpoint not found. Service may have been updated."
        elif response.status_code == 403:
            return None, "Access restricted. Please verify CEDA's terms of use."
        else:
            return None, f"HTTP {response.status_code} from CEDA"
    except requests.Timeout:
        return None, "Request timeout. CEDA server may be slow or unavailable."
    except requests.ConnectionError:
        return None, "Connection error. Please check internet connectivity."
    except Exception as e:
        return None, f"Error accessing CEDA: {str(e)}"

def get_ceda_attribution():
    """Return proper CEDA attribution text"""
    return """
    📊 **Data Source:** Centre for Economic Data and Analysis (CEDA), Ashoka University
    
    CEDA provides economic data for research and non-commercial use. 
    Learn more: https://ceda.ashoka.edu.in
    
    ⚖️ **Usage Compliance:**
    - Non-commercial educational use
    - Proper attribution provided
    - Rate-limited respectful access
    """

# ====================
# MAHARASHTRA LOCATIONS (Original - all 36 districts)
# ====================
MAHARASHTRA_LOCATIONS = {
    "Pune": {
        "tehsils": {
            "Pune City": ["Shivajinagar", "Kothrud", "Hadapsar", "Yerawada", "Aundh"],
            "Haveli": ["Phursungi", "Manjri", "Uruli Kanchan", "Wagholi"],
            "Mulshi": ["Paud", "Pirangut", "Lavale", "Mulshi"],
            "Maval": ["Talegaon", "Vadgaon Maval", "Kamshet", "Lonavala"],
            "Bhor": ["Bhor", "Nasrapur", "Velhe", "Yavat"],
            "Purandhar": ["Saswad", "Jejuri", "Pargaon", "Narayanpur"],
            "Baramati": ["Baramati", "Morgaon", "Bhigwan", "Kurkumbh"],
            "Indapur": ["Indapur", "Bhigwan", "Akluj", "Nimgaon"],
            "Daund": ["Daund", "Kurkundi", "Yevat", "Patas"],
            "Shirur": ["Shirur", "Shikrapur", "Kendal", "Pabal"],
            "Khed": ["Rajgurunagar", "Chakan", "Manchar", "Kusgaon"],
            "Junnar": ["Junnar", "Narayangaon", "Otur", "Alephata"],
            "Ambegaon": ["Ghodegaon", "Manchar", "Bhigwan", "Pargaon"]
        }
    },
    "Mumbai Suburban": {
        "tehsils": {
            "Kurla": ["Kurla East", "Kurla West", "Chunabhatti", "Tilak Nagar"],
            "Andheri": ["Andheri East", "Andheri West", "Jogeshwari", "Vile Parle"],
            "Borivali": ["Borivali East", "Borivali West", "Kandivali", "Malad"]
        }
    },
    "Nagpur": {
        "tehsils": {
            "Nagpur Urban": ["Dharampeth", "Sadar", "Hingna", "Nandanvan"],
            "Nagpur Rural": ["Kalmeshwar", "Kamptee", "Ramtek", "Parseoni"],
            "Umred": ["Umred", "Khapa", "Bhiwapur", "Kuhi"],
            "Kalameshwar": ["Kalameshwar", "Mouza", "Parseoni", "Savner"]
        }
    },
    "Nashik": {
        "tehsils": {
            "Nashik": ["Nashik Road", "Panchavati", "Satpur", "Deolali"],
            "Igatpuri": ["Igatpuri", "Ghoti", "Dindori", "Trimbakeshwar"],
            "Sinnar": ["Sinnar", "Malegaon", "Nandgaon", "Chandwad"],
            "Niphad": ["Niphad", "Dindori", "Malegaon", "Vani"]
        }
    },
    "Thane": {
        "tehsils": {
            "Thane": ["Naupada", "Kopri", "Vartak Nagar", "Wagle Estate"],
            "Kalyan": ["Kalyan East", "Kalyan West", "Dombivli East", "Dombivli West"],
            "Bhiwandi": ["Bhiwandi", "Kalyan", "Nizampur", "Anjur"],
            "Shahapur": ["Shahapur", "Asangaon", "Atgaon", "Vashind"]
        }
    },
    "Aurangabad": {"tehsils": {"Aurangabad": ["Aurangabad City", "Paithan", "Gangapur"]}},
    "Solapur": {"tehsils": {"Solapur North": ["Solapur City", "Akluj", "Barshi"]}},
    "Kolhapur": {"tehsils": {"Kolhapur": ["Kolhapur City", "Karveer", "Panhala"]}},
    "Ahmednagar": {"tehsils": {"Ahmednagar": ["Ahmednagar City", "Nagar", "Sangamner"]}},
    "Satara": {"tehsils": {"Satara": ["Satara City", "Karad", "Koregaon"]}},
    "Sangli": {"tehsils": {"Sangli": ["Sangli City", "Miraj", "Tasgaon"]}},
    "Ratnagiri": {"tehsils": {"Ratnagiri": ["Ratnagiri City", "Mandangad", "Dapoli"]}},
    "Sindhudurg": {"tehsils": {"Sindhudurg": ["Sindhudurg City", "Malwan", "Kudal"]}},
    "Amravati": {"tehsils": {"Amravati": ["Amravati City", "Morshi", "Daryapur"]}},
    "Akola": {"tehsils": {"Akola": ["Akola City", "Barshitakli", "Akot"]}},
    "Washim": {"tehsils": {"Washim": ["Washim City", "Karanja", "Malegaon"]}},
    "Buldhana": {"tehsils": {"Buldhana": ["Buldhana City", "Malkapur", "Chikhli"]}},
    "Yavatmal": {"tehsils": {"Yavatmal": ["Yavatmal City", "Pusad", "Darwha"]}},
    "Wardha": {"tehsils": {"Wardha": ["Wardha City", "Hinganghat", "Arvi"]}},
    "Chandrapur": {"tehsils": {"Chandrapur": ["Chandrapur City", "Warora", "Ballarpur"]}},
    "Gadchiroli": {"tehsils": {"Gadchiroli": ["Gadchiroli City", "Dhanora", "Chamorshi"]}},
    "Gondia": {"tehsils": {"Gondia": ["Gondia City", "Tirora", "Goregaon"]}},
    "Bhandara": {"tehsils": {"Bhandara": ["Bhandara City", "Tumsar", "Pauni"]}},
    "Jalgaon": {"tehsils": {"Jalgaon": ["Jalgaon City", "Bhusawal", "Amalner"]}},
    "Dhule": {"tehsils": {"Dhule": ["Dhule City", "Sakri", "Shirpur"]}},
    "Nandurbar": {"tehsils": {"Nandurbar": ["Nandurbar City", "Shahada", "Taloda"]}},
    "Osmanabad": {"tehsils": {"Osmanabad": ["Osmanabad City", "Tuljapur", "Bhum"]}},
    "Latur": {"tehsils": {"Latur": ["Latur City", "Nilanga", "Ausa"]}},
    "Beed": {"tehsils": {"Beed": ["Beed City", "Ambajogai", "Parli"]}},
    "Parbhani": {"tehsils": {"Parbhani": ["Parbhani City", "Purna", "Pathri"]}},
    "Jalna": {"tehsils": {"Jalna": ["Jalna City", "Bhokardan", "Ambad"]}},
    "Hingoli": {"tehsils": {"Hingoli": ["Hingoli City", "Kalamnuri", "Sengaon"]}},
    "Nanded": {"tehsils": {"Nanded": ["Nanded City", "Kinwat", "Hadgaon"]}},
    "Palghar": {"tehsils": {"Palghar": ["Palghar City", "Vasai", "Virar"]}},
    "Raigad": {"tehsils": {"Raigad": ["Alibag", "Panvel", "Karjat"]}}
}

# Initialize session state
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'location_data' not in st.session_state:
    st.session_state.location_data = {'district': None, 'tehsil': None, 'village': None}
if 'notifications_enabled' not in st.session_state:
    st.session_state.notifications_enabled = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = "🏠 Dashboard"
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# ====================
# ENHANCED CROP DATABASE with detailed practices
# ====================
CROP_DATABASE = {
    "Rice": {
        "seed_rate_kg_per_acre": "10-12",
        "spacing": "20cm x 15cm",
        "water_requirement": "485-607 mm",
        "duration_days": "120-150",
        "expected_yield_tons": "1.6-2.4",
        "best_season": "Kharif (June-October)",
        "soil_type": "Clay loam, silt loam",
        "market_price_range": "₹2000-2800/quintal",
        "detailed_practices": {
            "land_preparation": [
                "First plowing: Deep plowing to 20-25 cm depth after monsoon onset",
                "Puddle the field 2-3 times with 5 cm water standing",
                "Level the field properly for uniform water distribution",
                "Create 30 cm height bunds to retain water",
                "Apply decomposed FYM 2 weeks before transplanting"
            ],
            "nursery_management": [
                "Seed treatment: Soak seeds in water for 24 hours, incubate for 48 hours",
                "Prepare raised nursery bed of 1m width, 10m length, 15cm height",
                "Apply 2 kg Urea, 4 kg SSP per 100 sq.m nursery",
                "Sow pre-germinated seeds @ 20-25 kg per hectare",
                "Maintain 2-3 cm water in nursery after 3 days of sowing"
            ],
            "transplanting": [
                "Transplant 21-25 days old seedlings (3-4 leaf stage)",
                "Plant 2-3 seedlings per hill at 20x15 cm spacing",
                "Transplant at shallow depth (2-3 cm) for better tillering",
                "Complete transplanting within 3-4 weeks for uniform maturity",
                "Replant missing hills within 7 days"
            ],
            "water_management": [
                "Maintain 5 cm water up to flowering stage",
                "Drain water at panicle initiation for 3-4 days (increases tillers)",
                "Keep field saturated (no standing water) during flowering",
                "Drain field 10 days before harvesting",
                "Total water requirement: 120-150 cm over crop duration"
            ],
            "weed_management": [
                "First hand weeding at 20-25 days after transplanting",
                "Second hand weeding at 40-45 days after transplanting",
                "Use cono weeder for mechanical weeding (reduces labor by 50%)",
                "Pre-emergence herbicide: Butachlor @ 2 liters/acre within 3 days",
                "Post-emergence: 2,4-D @ 500ml/acre at 25-30 days"
            ],
            "pest_disease_control": [
                "Stem borer: Use pheromone traps @ 5/acre from 30 DAT",
                "Leaf folder: Spray Cartap hydrochloride @ 1.5g/liter",
                "Brown plant hopper: Use Imidacloprid @ 0.5ml/liter at early stage",
                "Blast disease: Apply Tricyclazole 75% WP @ 60g/acre at boot leaf stage",
                "Sheath blight: Spray Hexaconazole @ 2ml/liter at tillering"
            ],
            "harvesting": [
                "Harvest when 80-85% of grains turn golden yellow",
                "Moisture content should be 20-22% at harvest",
                "Cut panicles 15-20 cm below the ear head",
                "Complete harvesting within 7-10 days after maturity",
                "Thresh within 2-3 days to prevent grain damage"
            ]
        },
        "chemical_fertilizers": {
            "urea_kg": "65",
            "dap_kg": "50",
            "mop_kg": "20",
            "total_npk": "48:24:16 kg/acre",
            "application_schedule": [
                "Basal: 50% N + 100% P + 100% K at transplanting",
                "First top dressing: 25% N at tillering (21-25 days)",
                "Second top dressing: 25% N at panicle initiation (40-45 days)"
            ]
        },
        "organic_fertilizers": {
            "fym_tons": "4-5",
            "vermicompost_kg": "500-600",
            "neem_cake_kg": "100",
            "green_manure": "Dhaincha or Sunhemp - 8-10 kg/acre",
            "biofertilizers": "Azospirillum + PSB @ 2 kg each per acre",
            "application_schedule": [
                "FYM: Apply 2-3 weeks before transplanting",
                "Vermicompost: Mix in soil at final land preparation",
                "Neem cake: Apply at transplanting as basal",
                "Biofertilizers: Mix with seeds or apply to roots"
            ]
        },
        "methods": [
            "System of Rice Intensification (SRI): Transplant 8-12 day old seedlings, one per hill, with 25x25cm spacing. Use rotary weeder. Can increase yield by 30-50%",
            "Direct Seeded Rice (DSR): Drill seeds at 8-10 kg/acre, reduces water usage by 30%, labor saving method"
        ],
        "tips": [
            "Maintain 2-5 cm water level during vegetative stage",
            "Apply zinc sulfate at 10 kg/acre to prevent zinc deficiency",
            "Use pheromone traps for stem borer management"
        ]
    },
    "Wheat": {
        "seed_rate_kg_per_acre": "40-50",
        "spacing": "20-23cm row spacing",
        "water_requirement": "182-263 mm",
        "duration_days": "110-130",
        "expected_yield_tons": "1.6-2.0",
        "best_season": "Rabi (November-March)",
        "soil_type": "Loam to clay loam",
        "market_price_range": "₹2000-2400/quintal",
        "detailed_practices": {
            "land_preparation": [
                "Deep plowing with soil turning plough to 20-25 cm",
                "Two cross harrowings followed by planking for fine tilth",
                "Level field properly for uniform irrigation",
                "Incorporate crop residues 20-25 days before sowing",
                "Apply well-decomposed FYM @ 10 tons/acre 3-4 weeks before sowing"
            ],
            "sowing": [
                "Sow within first fortnight of November for optimal yields",
                "Use seed drill for uniform depth (4-5 cm) and spacing",
                "Row to row spacing: 20-23 cm for normal varieties",
                "Seed treatment: Vitavax @ 2.5g/kg or Thiram @ 3g/kg seeds",
                "Ensure proper seed-soil contact by light roller/plank"
            ],
            "irrigation": [
                "First irrigation: Crown Root Initiation stage (20-25 days)",
                "Second: Late tillering/early jointing (40-45 days)",
                "Third: Late jointing stage (60-65 days)",
                "Fourth: Flowering stage (80-85 days)",
                "Fifth: Milk stage (100-105 days)",
                "Sixth: Dough stage (115-120 days) - if needed"
            ],
            "nutrient_management": [
                "Basal dose: Apply entire P, K and 50% N before sowing",
                "First top dressing: 25% N at CRI (20-25 DAS)",
                "Second top dressing: 25% N at late jointing (60-65 DAS)",
                "Apply Zinc sulphate @ 10 kg/acre if deficiency observed",
                "Spray Iron @ 5g/liter if yellowing appears"
            ]
        },
        "chemical_fertilizers": {
            "urea_kg": "87",
            "dap_kg": "65",
            "mop_kg": "17",
            "total_npk": "48:24:16 kg/acre",
            "application_schedule": [
                "Basal: 50% N + 100% P + 100% K at sowing",
                "First top dressing: 25% N at CRI (21 days)",
                "Second top dressing: 25% N at tillering (45 days)"
            ]
        },
        "organic_fertilizers": {
            "fym_tons": "4-5",
            "vermicompost_kg": "500-600",
            "neem_cake_kg": "80-100",
            "compost_tons": "2-3",
            "biofertilizers": "Azotobacter + PSB @ 2 kg each per acre",
            "application_schedule": [
                "FYM: Apply 3-4 weeks before sowing",
                "Vermicompost: Mix during final plowing",
                "Neem cake: Apply as basal at sowing"
            ]
        },
        "methods": [
            "Zero tillage: Direct seeding with specialized drill, saves fuel and time",
            "Raised bed planting: 20-30% water savings, better drainage"
        ],
        "tips": [
            "Sow within first fortnight of November for optimal yields",
            "Apply first irrigation at Crown Root Initiation (21 days)"
        ]
    },
    "Cotton": {
        "seed_rate_kg_per_acre": "5-6",
        "spacing": "90cm x 60cm",
        "water_requirement": "283-526 mm",
        "duration_days": "150-180",
        "expected_yield_tons": "0.8-1.2",
        "best_season": "Kharif (May-June sowing)",
        "soil_type": "Deep black cotton soil",
        "market_price_range": "₹5500-7000/quintal",
        "detailed_practices": {
            "pre_sowing": [
                "Deep summer plowing to 30 cm depth for moisture conservation",
                "Two harrowing and leveling for proper seed bed",
                "Ridge and furrow method recommended for better drainage",
                "Seed treatment: Imidacloprid @ 5g/kg for sucking pests",
                "Apply Trichoderma enriched FYM @ 5 tons/acre"
            ],
            "sowing_planting": [
                "Sow during May 15 to June 15 with pre-monsoon shower",
                "Plant 2 seeds per hill at 4-5 cm depth",
                "Spacing: 90 cm x 60 cm (normal), 90 cm x 30 cm (HDPS)",
                "Gap filling within 10 days of emergence",
                "Thinning at 15-20 days, keep one healthy plant per hill"
            ],
            "water_irrigation": [
                "First irrigation: After 3-4 weeks if no rain (establishment)",
                "Critical stages: Square formation, flowering, boll development",
                "Maintain soil moisture at 70-80% field capacity",
                "Avoid water stress during flowering (40-80 days)",
                "Drip irrigation: 50% water saving with better efficiency"
            ],
            "intercultural_operations": [
                "First hoeing and earthing up at 25-30 days",
                "Second hoeing at 50-60 days",
                "Remove suckers and bottom branches touching ground",
                "Install bird perches @ 10/acre for natural pest control",
                "Topping: Remove terminal bud at 100-120 days for better boll setting"
            ],
            "pest_management": [
                "Pheromone traps: 5-6 traps/acre from 30 days",
                "Yellow sticky traps @ 10-12/acre for whitefly monitoring",
                "Pink bollworm: Release Trichogramma cards @ 5 cards/acre",
                "Whitefly: Spray Spiromesifen @ 1.5ml/liter if ETL reached",
                "Bt cotton: Provides 90% protection against bollworms"
            ]
        },
        "chemical_fertilizers": {
            "urea_kg": "87",
            "dap_kg": "65",
            "mop_kg": "25",
            "total_npk": "48:24:24 kg/acre",
            "application_schedule": [
                "Basal: 25% N + 100% P + 50% K at sowing",
                "First: 25% N + 50% K at square formation (30-35 days)",
                "Second: 25% N at flowering (60-65 days)",
                "Third: 25% N at boll development (90-95 days)"
            ]
        },
        "organic_fertilizers": {
            "fym_tons": "5-6",
            "vermicompost_kg": "800-1000",
            "neem_cake_kg": "120-150",
            "compost_tons": "3-4",
            "biofertilizers": "Azospirillum + PSB + KSB @ 2 kg each",
            "application_schedule": [
                "FYM: Apply 4-5 weeks before sowing",
                "Vermicompost: Apply at sowing in furrows"
            ]
        },
        "methods": [
            "High Density Planting: 90cm x 30cm spacing, 15-25% yield increase",
            "Bt cotton hybrids reduce insecticide use by 50%"
        ],
        "tips": [
            "Deep plowing to 25-30cm improves root development",
            "Install pheromone traps @ 5 traps/acre for monitoring"
        ]
    },
    # Add more crops with detailed practices following the same pattern
    "Tomato": {
        "seed_rate_kg_per_acre": "80-100 grams",
        "spacing": "60cm x 45cm",
        "water_requirement": "243-324 mm",
        "duration_days": "65-90",
        "expected_yield_tons": "20-28",
        "best_season": "Kharif, Rabi & Summer",
        "soil_type": "Well-drained sandy loam",
        "market_price_range": "₹800-2500/quintal",
        "detailed_practices": {
            "nursery": [
                "Raise seedlings in pro-trays or raised beds (15-20 cm height)",
                "Seed rate: 100-150 grams for one acre transplanting",
                "Treat seeds with Trichoderma @ 4g/kg or Captan @ 2g/kg",
                "Seedling ready in 25-30 days (4-5 true leaves)",
                "Harden seedlings by reducing water 5 days before transplanting"
            ],
            "transplanting": [
                "Transplant in evening hours to reduce transplant shock",
                "Make pits of 30x30x30 cm at recommended spacing",
                "Apply FYM/compost @ 1 kg per pit before planting",
                "Water immediately after transplanting",
                "Provide shade for 2-3 days using leaves or shade net"
            ],
            "staking_pruning": [
                "Provide bamboo/wooden stakes at 15-20 days (1.5-2m height)",
                "Tie plants loosely with soft cloth strips as they grow",
                "Remove lower leaves touching soil to prevent disease",
                "Remove side shoots (suckers) weekly for determinate varieties",
                "For indeterminate: Keep 1-2 main stems, remove all side shoots"
            ],
            "irrigation_mulching": [
                "Light irrigation immediately after transplanting",
                "Daily irrigation for first week, then alternate days",
                "Critical stages: Flowering and fruit development",
                "Drip irrigation: Best method, saves 40-50% water",
                "Plastic mulching: Black film reduces weeds, conserves moisture"
            ]
        },
        "chemical_fertilizers": {
            "urea_kg": "108",
            "dap_kg": "109",
            "mop_kg": "33",
            "total_npk": "60:40:40 kg/acre",
            "application_schedule": [
                "Basal: 50% N + 100% P + 50% K at transplanting",
                "30 days: 25% N + 25% K",
                "60 days: 25% N + 25% K"
            ]
        },
        "organic_fertilizers": {
            "fym_tons": "6-8",
            "vermicompost_kg": "800-1000",
            "neem_cake_kg": "100-120",
            "biofertilizers": "Azotobacter + PSB @ 2 kg each",
            "application_schedule": [
                "FYM: Mix 2-3 weeks before transplanting",
                "Vermicompost: Apply in pits at transplanting"
            ]
        },
        "methods": [
            "Polyhouse: Year-round production, 121-162 tons/acre yield",
            "Drip + mulch: 50% water saving, better quality"
        ],
        "tips": [
            "Transplant 30-35 day old seedlings in evening",
            "Apply calcium and boron sprays to prevent cracking"
        ]
    },
    "Onion": {
        "seed_rate_kg_per_acre": "3-4",
        "spacing": "15cm x 10cm",
        "water_requirement": "182-283 mm",
        "duration_days": "120-150",
        "expected_yield_tons": "10-16",
        "best_season": "Kharif, Late Kharif, Rabi",
        "soil_type": "Well-drained loamy soil",
        "market_price_range": "₹1000-3500/quintal",
        "chemical_fertilizers": {
            "urea_kg": "72",
            "dap_kg": "54",
            "mop_kg": "17",
            "total_npk": "40:20:20 kg/acre",
            "application_schedule": [
                "Basal: 50% N + 100% P + 50% K at transplanting",
                "30 days: 25% N + 25% K",
                "60 days: 25% N + 25% K"
            ]
        },
        "organic_fertilizers": {
            "fym_tons": "4-5",
            "vermicompost_kg": "600-800",
            "neem_cake_kg": "80-100",
            "biofertilizers": "Azospirillum + PSB @ 2 kg each"
        },
        "methods": ["Raised bed: 15-20% yield increase", "Drip irrigation: 40% water saving"],
        "tips": ["Transplant 45-50 day seedlings", "Apply sulfur for better pungency"]
    }
}

# Other databases (keeping originals)
SEASONAL_CALENDAR = {
    "Kharif": {
        "description": "Monsoon crops sown with monsoon, harvested at end",
        "sowing_period": "June - August",
        "harvesting_period": "September - November",
        "characteristics": ["Warm weather required", "Depends on monsoon", "Temperature: 25-35°C"],
        "crops": {
            "Rice": {"sowing": "June-July", "harvesting": "Oct-Nov", "duration": "120-150 days"},
            "Cotton": {"sowing": "May-June", "harvesting": "Oct-Jan", "duration": "150-180 days"}
        }
    },
    "Rabi": {
        "description": "Winter crops sown in winter, harvested in spring",
        "sowing_period": "October - December",
        "harvesting_period": "March - May",
        "characteristics": ["Cool weather for growth", "Needs irrigation", "Temperature: 10-25°C"],
        "crops": {
            "Wheat": {"sowing": "Oct-Nov", "harvesting": "Mar-Apr", "duration": "110-130 days"}
        }
    },
    "Zaid": {
        "description": "Summer crops between Rabi and Kharif",
        "sowing_period": "March - May",
        "harvesting_period": "June - August",
        "characteristics": ["Short duration", "Irrigation required", "Temperature: 25-40°C"],
        "crops": {}
    }
}

DISEASE_DATABASE = {
    "Rice": [
        {"name": "Blast Disease", "symptoms": "Leaf spots, neck blast", "control": "Tricyclazole 75% WP @ 60g/acre"},
        {"name": "Brown Plant Hopper", "symptoms": "Yellowing, hopper burn", "control": "Imidacloprid @ 20ml/acre"}
    ],
    "Wheat": [
        {"name": "Yellow Rust", "symptoms": "Yellow pustules in rows", "control": "Propiconazole @ 100ml/acre"}
    ],
    "Cotton": [
        {"name": "Pink Bollworm", "symptoms": "Bored bolls", "control": "Pheromone traps @ 5/acre"}
    ]
}

GOVERNMENT_SCHEMES = {
    "PM-KISAN": {
        "name": "PM Kisan Samman Nidhi",
        "benefit": "₹6000/year in 3 installments",
        "eligibility": "All landholding farmers",
        "website": "https://pmkisan.gov.in/",
        "helpline": "011-24300606"
    },
    "PMFBY": {
        "name": "Pradhan Mantri Fasal Bima Yojana",
        "benefit": "Crop insurance at 2% (Kharif), 1.5% (Rabi)",
        "eligibility": "All farmers",
        "website": "https://pmfby.gov.in/",
        "helpline": "1800-180-1551"
    }
}

# ====================
# AI HELPER FUNCTIONS
# ====================

def get_ai_response(user_message, context=""):
    """Get AI response from Claude"""
    client = get_anthropic_client()
    if not client:
        return "🤖 AI Assistant is not configured. Please add ANTHROPIC_API_KEY to secrets."
    
    try:
        user_data = st.session_state.get('user_data', {})
        location = f"{user_data.get('village', 'Unknown')}, {user_data.get('tehsil', 'Unknown')}, {user_data.get('district', 'Maharashtra')}"
        
        system_prompt = f"""You are KrishiMitra AI, an expert agricultural advisor for Maharashtra farmers. 
        
Current farmer context:
- Location: {location}
- Farm size: {user_data.get('farm_size', 'Unknown')} acres

You provide:
1. Practical farming advice specific to Maharashtra
2. Crop recommendations based on location and season
3. Pest and disease management guidance
4. Market insights and pricing trends
5. Government scheme information

Always be:
- Concise and practical
- Supportive and encouraging
- Specific to Indian/Maharashtra agriculture
- Use simple language with Marathi terms where helpful

{context}"""
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        return message.content[0].text
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

def get_crop_recommendation_ai(district, tehsil, season, soil_type="", budget="medium"):
    """Get AI-powered crop recommendation"""
    client = get_anthropic_client()
    if not client:
        return "AI recommendations unavailable. Please configure ANTHROPIC_API_KEY."
    
    try:
        prompt = f"""As an agricultural expert, recommend the best 3 crops for:
        
Location: {tehsil}, {district}, Maharashtra
Season: {season}
Soil Type: {soil_type if soil_type else 'General Maharashtra soil'}
Budget: {budget}

Provide:
1. Top 3 crop recommendations with reasons
2. Expected yield and profit potential
3. Key success factors for each crop
4. Water and input requirements

Keep response practical and specific to this location."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return message.content[0].text
    except Exception as e:
        return f"Error getting recommendations: {str(e)}"

def analyze_disease_ai(crop, symptoms):
    """AI-powered disease diagnosis"""
    client = get_anthropic_client()
    if not client:
        return "AI disease diagnosis unavailable."
    
    try:
        prompt = f"""As a plant pathologist, diagnose this issue:

Crop: {crop}
Symptoms observed: {symptoms}

Provide:
1. Most likely disease/pest (with confidence level)
2. Detailed symptoms to confirm
3. Treatment recommendations (organic and chemical)
4. Prevention measures
5. Expected recovery time

Be specific and actionable."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return message.content[0].text
    except Exception as e:
        return f"Error in diagnosis: {str(e)}"

# ====================
# DATABASE FUNCTIONS (Original)
# ====================

def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect('krishimitra.db', check_same_thread=False)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  full_name TEXT NOT NULL,
                  mobile TEXT NOT NULL,
                  email TEXT,
                  district TEXT,
                  tehsil TEXT,
                  village TEXT,
                  farm_size_acres REAL,
                  user_type TEXT DEFAULT 'Farmer',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS activities
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  activity_type TEXT,
                  crop_name TEXT,
                  area_acres REAL,
                  activity_data TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS notifications
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  notification_type TEXT,
                  message TEXT,
                  status TEXT DEFAULT 'pending',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  sent_at TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS marketplace_listings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  seller_id INTEGER,
                  crop_name TEXT,
                  quantity REAL,
                  unit TEXT,
                  price_per_unit REAL,
                  quality_grade TEXT,
                  location TEXT,
                  description TEXT,
                  status TEXT DEFAULT 'Active',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(seller_id) REFERENCES users(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS bids
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  listing_id INTEGER,
                  buyer_id INTEGER,
                  bid_amount REAL,
                  bid_quantity REAL,
                  buyer_name TEXT,
                  buyer_phone TEXT,
                  message TEXT,
                  status TEXT DEFAULT 'Pending',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(listing_id) REFERENCES marketplace_listings(id),
                  FOREIGN KEY(buyer_id) REFERENCES users(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS manual_market_prices
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  district TEXT,
                  market_name TEXT,
                  commodity TEXT,
                  min_price REAL,
                  max_price REAL,
                  modal_price REAL,
                  arrival_quantity TEXT,
                  price_date DATE,
                  updated_by INTEGER,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(updated_by) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password, full_name, mobile, email, district, tehsil, village, farm_size, user_type='Farmer'):
    try:
        conn = sqlite3.connect('krishimitra.db')
        c = conn.cursor()
        password_hash = hash_password(password)
        c.execute('''INSERT INTO users (username, password_hash, full_name, mobile, email, 
                     district, tehsil, village, farm_size_acres, user_type)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (username, password_hash, full_name, mobile, email, district, tehsil, village, farm_size, user_type))
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        return True, user_id
    except sqlite3.IntegrityError:
        return False, "Username already exists"
    except Exception as e:
        return False, str(e)

def authenticate_user(username, password):
    conn = sqlite3.connect('krishimitra.db')
    c = conn.cursor()
    password_hash = hash_password(password)
    c.execute('''SELECT id, username, full_name, mobile, email, district, tehsil, village, farm_size_acres, user_type
                 FROM users WHERE username=? AND password_hash=?''',
              (username, password_hash))
    user = c.fetchone()
    conn.close()
    if user:
        return {
            'id': user[0], 'username': user[1], 'full_name': user[2],
            'mobile': user[3], 'email': user[4], 'district': user[5],
            'tehsil': user[6], 'village': user[7], 'farm_size': user[8],
            'user_type': user[9]
        }
    return None

def log_activity(user_id, activity_type, crop_name, area_acres, activity_data):
    try:
        conn = sqlite3.connect('krishimitra.db')
        c = conn.cursor()
        c.execute('''INSERT INTO activities (user_id, activity_type, crop_name, area_acres, activity_data)
                     VALUES (?, ?, ?, ?, ?)''',
                  (user_id, activity_type, crop_name, area_acres, json.dumps(activity_data)))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Error logging activity: {e}")

def get_user_activities(user_id, limit=10):
    conn = sqlite3.connect('krishimitra.db')
    c = conn.cursor()
    c.execute('''SELECT activity_type, crop_name, area_acres, activity_data, created_at
                 FROM activities WHERE user_id=?
                 ORDER BY created_at DESC LIMIT ?''',
              (user_id, limit))
    activities = c.fetchall()
    conn.close()
    return activities

def create_notification(user_id, notification_type, message):
    conn = sqlite3.connect('krishimitra.db')
    c = conn.cursor()
    c.execute('''INSERT INTO notifications (user_id, notification_type, message)
                 VALUES (?, ?, ?)''',
              (user_id, notification_type, message))
    conn.commit()
    conn.close()

def get_manual_prices(commodity=None, district=None, days=30):
    conn = sqlite3.connect('krishimitra.db')
    c = conn.cursor()
    query = '''SELECT district, market_name, commodity, min_price, max_price, modal_price, 
               arrival_quantity, price_date, updated_at 
               FROM manual_market_prices 
               WHERE price_date >= date('now', '-' || ? || ' days')'''
    params = [days]
    if commodity:
        query += " AND commodity = ?"
        params.append(commodity)
    if district:
        query += " AND district = ?"
        params.append(district)
    query += " ORDER BY price_date DESC"
    c.execute(query, params)
    results = c.fetchall()
    conn.close()
    if results:
        return pd.DataFrame(results, columns=['district', 'market', 'commodity', 'min_price', 
                                               'max_price', 'modal_price', 'arrival_quantity', 
                                               'price_date', 'updated_at'])
    return None

def add_manual_price(district, market_name, commodity, min_price, max_price, modal_price, 
                     arrival_quantity, price_date, updated_by):
    conn = sqlite3.connect('krishimitra.db')
    c = conn.cursor()
    c.execute('''INSERT INTO manual_market_prices 
                 (district, market_name, commodity, min_price, max_price, modal_price, 
                  arrival_quantity, price_date, updated_by)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (district, market_name, commodity, min_price, max_price, modal_price, 
               arrival_quantity, price_date, updated_by))
    conn.commit()
    conn.close()

def get_nearest_mandis(district):
    mandis = {
        "Pune": ["Pune Market Yard", "Baramati APMC", "Daund APMC"],
        "Nagpur": ["Nagpur Cotton Market", "Kamptee APMC"],
        "Nashik": ["Nashik APMC", "Lasalgaon APMC"],
        "Mumbai Suburban": ["Vashi APMC", "Turbhe Market"]
    }
    return mandis.get(district, ["Contact District Agriculture Office"])

# ====================
# MAIN APPLICATION
# ====================

def main():
    init_database()
    st.markdown('<div class="main-header">🌾 KrishiMitra Maharashtra - AI Powered</div>', unsafe_allow_html=True)
    st.markdown("### संपूर्ण कृषी व्यवस्थापन प्रणाली | Complete Agriculture Management System with AI")
    
    if st.session_state.user_data is None:
        show_auth_page()
    else:
        show_main_app()

def show_auth_page():
    """Authentication page"""
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        st.markdown("### Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True, type="primary")
            
            if submitted:
                if username and password:
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state.user_data = user
                        st.session_state.location_data = {
                            'district': user['district'],
                            'tehsil': user['tehsil'],
                            'village': user['village']
                        }
                        st.success(f"Welcome {user['full_name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
                else:
                    st.warning("Please fill all fields")
    
    with tab2:
        st.markdown("### Create Account")
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_username = st.text_input("Username*")
                new_password = st.text_input("Password* (min 6 chars)", type="password")
                full_name = st.text_input("Full Name*")
                mobile = st.text_input("Mobile* (10 digits)")
            with col2:
                email = st.text_input("Email")
                user_type = st.selectbox("I am a", ["Farmer", "Buyer/Trader"])
                farm_size = st.number_input("Farm Size (Acres)", min_value=0.1, value=1.0, step=0.5)
            
            st.markdown("### 📍 Location Details")
            col1, col2, col3 = st.columns(3)
            with col1:
                district = st.selectbox("District*", ["Select"] + list(MAHARASHTRA_LOCATIONS.keys()))
            with col2:
                if district != "Select":
                    tehsils = list(MAHARASHTRA_LOCATIONS[district]["tehsils"].keys())
                    tehsil = st.selectbox("Tehsil*", ["Select"] + tehsils)
                else:
                    tehsil = st.selectbox("Tehsil*", ["First select district"], disabled=True)
            with col3:
                if district != "Select" and tehsil != "Select" and tehsil != "First select district":
                    villages = MAHARASHTRA_LOCATIONS[district]["tehsils"][tehsil]
                    village = st.selectbox("Village*", ["Select"] + villages)
                else:
                    village = st.selectbox("Village*", ["First select tehsil"], disabled=True)
            
            submitted = st.form_submit_button("Register", use_container_width=True, type="primary")
            
            if submitted:
                if not all([new_username, new_password, full_name, mobile]):
                    st.error("Please fill all required fields")
                elif district == "Select" or tehsil == "Select" or village == "Select":
                    st.error("Please select location details")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                elif not mobile.isdigit() or len(mobile) != 10:
                    st.error("Please enter valid 10-digit mobile")
                else:
                    success, result = create_user(new_username, new_password, full_name, mobile, 
                                                 email, district, tehsil, village, farm_size, user_type)
                    if success:
                        st.success("✅ Account created! Please login")
                        st.balloons()
                    else:
                        st.error(f"Error: {result}")

def show_main_app():
    """Main app with fixed navigation"""
    user = st.session_state.user_data
    
    with st.sidebar:
        st.markdown(f"### 👤 {user['full_name']}")
        st.markdown(f"**📍 {user['village']}, {user['tehsil']}**")
        st.markdown(f"**🌾 Farm: {user['farm_size']} acres**")
        st.markdown("---")
        
        # Define pages based on user type
        if user.get('user_type') == 'Farmer':
            pages = [
                "🏠 Dashboard",
                "🤖 AI Assistant", 
                "🌱 Seed Calculator",
                "📊 Market Prices",
                "🎯 Best Practices",
                "💰 Profit Calculator",
                "📚 Crop Knowledge",
                "🦠 Disease Diagnosis",
                "🛒 Marketplace",
                "🛍️ My Listings",
                "📱 Notifications",
                "📊 My Activity"
            ]
        else:
            pages = [
                "🏠 Dashboard",
                "🤖 AI Assistant",
                "🛒 Marketplace",
                "💼 My Bids",
                "📊 Market Prices",
                "📱 Notifications"
            ]
        
        # Navigation with proper state management
        st.markdown("### 🧭 Navigation")
        for page in pages:
            if st.button(page, key=f"nav_{page}", use_container_width=True, 
                        type="primary" if st.session_state.current_page == page else "secondary"):
                st.session_state.current_page = page
                st.rerun()
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user_data = None
            st.session_state.current_page = "🏠 Dashboard"
            st.rerun()
    
    # Page routing
    page = st.session_state.current_page
    
    try:
        if page == "🏠 Dashboard":
            show_dashboard()
        elif page == "🤖 AI Assistant":
            show_ai_assistant()
        elif page == "🌱 Seed Calculator":
            show_seed_fertilizer_calculator()
        elif page == "📊 Market Prices":
            show_live_market_prices()
        elif page == "🎯 Best Practices":
            show_best_practices_enhanced()
        elif page == "💰 Profit Calculator":
            show_profit_calculator()
        elif page == "📚 Crop Knowledge":
            show_knowledge_base()
        elif page == "🦠 Disease Diagnosis":
            show_ai_disease_diagnosis()
        elif page == "🛒 Marketplace":
            show_marketplace()
        elif page == "🛍️ My Listings":
            show_my_listings()
        elif page == "💼 My Bids":
            show_my_bids()
        elif page == "📱 Notifications":
            show_notifications()
        elif page == "📊 My Activity":
            show_activity_history()
        else:
            show_dashboard()
    except Exception as e:
        st.error(f"Error: {str(e)}")
        if st.button("🔄 Refresh"):
            st.rerun()

# ====================
# PAGE FUNCTIONS
# ====================

def show_dashboard():
    """Enhanced Dashboard"""
    user = st.session_state.user_data
    st.markdown(f"### 🏠 Welcome, {user['full_name']}!")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Your Farm", f"{user['farm_size']} acres", "🌾")
    with col2:
        activities = get_user_activities(user['id'], limit=1000)
        st.metric("Activities", len(activities), "📊")
    with col3:
        st.metric("District", user['district'], "📍")
    with col4:
        conn = sqlite3.connect('krishimitra.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM marketplace_listings WHERE seller_id=? AND status='Active'", (user['id'],))
        listings = c.fetchone()[0]
        conn.close()
        st.metric("Listings", listings, "🛒")
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🤖 Ask AI", use_container_width=True):
            st.session_state.current_page = "🤖 AI Assistant"
            st.rerun()
    with col2:
        if st.button("🌱 Calculate Seeds", use_container_width=True):
            st.session_state.current_page = "🌱 Seed Calculator"
            st.rerun()
    with col3:
        if st.button("📊 Check Prices", use_container_width=True):
            st.session_state.current_page = "📊 Market Prices"
            st.rerun()
    with col4:
        if st.button("🛒 Marketplace", use_container_width=True):
            st.session_state.current_page = "🛒 Marketplace"
            st.rerun()
    
    # Recent activities
    st.markdown("### 📈 Recent Activities")
    recent = get_user_activities(user['id'], limit=5)
    if recent:
        for act in recent:
            st.markdown(f"- **{act[0]}**: {act[1]} ({act[2]} acres) - {act[4]}")
    else:
        st.info("No activities yet")

def show_ai_assistant():
    """AI Chat Assistant"""
    st.markdown("### 🤖 AI Agricultural Assistant")
    st.markdown("Ask me anything about farming, crops, market prices, or government schemes!")
    
    client = get_anthropic_client()
    if not client:
        st.warning("⚠️ AI Assistant requires ANTHROPIC_API_KEY in secrets. Demo responses will be limited.")
    
    # Chat interface
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f'<div class="chat-message user-message">👤 <strong>You:</strong> {message["content"]}</div>', 
                       unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message assistant-message">🤖 <strong>KrishiMitra AI:</strong> {message["content"]}</div>', 
                       unsafe_allow_html=True)
    
    # Quick action buttons
    st.markdown("### 🚀 Quick Questions")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🌾 Best crops for my location", use_container_width=True):
            user = st.session_state.user_data
            question = f"What are the best crops for {user['tehsil']}, {user['district']}?"
            with st.spinner("Thinking..."):
                response = get_ai_response(question)
                st.session_state.chat_history.append({"role": "user", "content": question})
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()
    with col2:
        if st.button("💰 Current market trends", use_container_width=True):
            question = "What are the current agricultural market trends in Maharashtra?"
            with st.spinner("Analyzing..."):
                response = get_ai_response(question)
                st.session_state.chat_history.append({"role": "user", "content": question})
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()
    with col3:
        if st.button("🛡️ Government schemes", use_container_width=True):
            question = "What government schemes are available for farmers?"
            with st.spinner("Searching..."):
                response = get_ai_response(question)
                st.session_state.chat_history.append({"role": "user", "content": question})
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()
    
    # Chat input
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area("Your question:", placeholder="E.g., What is the best time to plant cotton?", height=100)
        submitted = st.form_submit_button("Send 📤", use_container_width=True, type="primary")
        
        if submitted and user_input:
            with st.spinner("Getting answer..."):
                response = get_ai_response(user_input)
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()
    
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()

def show_ai_disease_diagnosis():
    """AI Disease Diagnosis"""
    st.markdown("### 🦠 AI Disease & Pest Diagnosis")
    st.markdown("Describe symptoms and get instant diagnosis with treatment recommendations")
    
    col1, col2 = st.columns(2)
    with col1:
        crop_name = st.selectbox("Select Crop", list(CROP_DATABASE.keys()))
    with col2:
        st.info("💡 Be specific about symptoms for accurate diagnosis")
    
    symptoms = st.text_area(
        "Describe the symptoms you're seeing:",
        placeholder="E.g., Yellow spots on leaves, wilting stems, holes in leaves...",
        height=150
    )
    
    if st.button("🔍 Diagnose", type="primary", use_container_width=True):
        if symptoms:
            with st.spinner("Analyzing symptoms..."):
                diagnosis = analyze_disease_ai(crop_name, symptoms)
                st.markdown('<div class="ai-card">', unsafe_allow_html=True)
                st.markdown("### 🔬 AI Diagnosis")
                st.markdown(diagnosis)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Log activity
                user = st.session_state.user_data
                log_activity(user['id'], "Disease Diagnosis", crop_name, 0, {"symptoms": symptoms})
        else:
            st.warning("Please describe the symptoms")

def show_best_practices_enhanced():
    """Enhanced Best Practices with detailed information"""
    st.markdown("### 🎯 Comprehensive Farming Best Practices")
    
    crop_name = st.selectbox("Select Crop for Detailed Guide", list(CROP_DATABASE.keys()))
    crop = CROP_DATABASE[crop_name]
    
    st.markdown(f"# 🌾 Complete Guide: {crop_name}")
    
    # Basic info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Expected Yield", f"{crop['expected_yield_tons']} tons/acre")
        st.metric("Duration", f"{crop['duration_days']} days")
    with col2:
        st.metric("Market Price", crop['market_price_range'])
        st.metric("Best Season", crop['best_season'])
    with col3:
        st.metric("Water Need", crop['water_requirement'])
        st.metric("Soil Type", crop['soil_type'])
    
    st.markdown("---")
    
    # Detailed practices if available
    if 'detailed_practices' in crop:
        practices = crop['detailed_practices']
        
        tabs = st.tabs(list(practices.keys()))
        
        for idx, (practice_name, steps) in enumerate(practices.items()):
            with tabs[idx]:
                st.markdown(f"### {practice_name.replace('_', ' ').title()}")
                for step_idx, step in enumerate(steps, 1):
                    st.markdown(f"**Step {step_idx}:** {step}")
                st.markdown("---")
    
    # Fertilizer recommendations
    st.markdown("## 🧪 Fertilizer Recommendations")
    tab1, tab2 = st.tabs(["Chemical Fertilizers", "Organic Fertilizers"])
    
    with tab1:
        chem = crop['chemical_fertilizers']
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Urea", f"{chem['urea_kg']} kg/acre")
        with col2:
            st.metric("DAP", f"{chem['dap_kg']} kg/acre")
        with col3:
            st.metric("MOP", f"{chem['mop_kg']} kg/acre")
        
        st.markdown("### Application Schedule")
        for schedule in chem['application_schedule']:
            st.success(f"✓ {schedule}")
    
    with tab2:
        org = crop['organic_fertilizers']
        st.markdown(f"**FYM:** {org.get('fym_tons', 'N/A')} tons/acre")
        st.markdown(f"**Vermicompost:** {org.get('vermicompost_kg', 'N/A')} kg/acre")
        if 'neem_cake_kg' in org:
            st.markdown(f"**Neem Cake:** {org['neem_cake_kg']} kg/acre")
        if 'biofertilizers' in org:
            st.markdown(f"**Biofertilizers:** {org['biofertilizers']}")
    
    # Expert tips
    st.markdown("## 💡 Expert Tips")
    for tip in crop.get('tips', []):
        st.info(f"💡 {tip}")
    
    # AI recommendations
    st.markdown("---")
    if st.button("🤖 Get AI-Powered Recommendations", use_container_width=True):
        user = st.session_state.user_data
        with st.spinner("Getting personalized recommendations..."):
            recommendations = get_ai_response(
                f"Give me specific recommendations for growing {crop_name} in {user['tehsil']}, {user['district']}"
            )
            st.markdown('<div class="ai-card">', unsafe_allow_html=True)
            st.markdown("### 🤖 AI Recommendations")
            st.markdown(recommendations)
            st.markdown('</div>', unsafe_allow_html=True)

def show_seed_fertilizer_calculator():
    """Seed & Fertilizer Calculator"""
    st.markdown("### 🌱 Seed & Fertilizer Calculator")
    
    user = st.session_state.user_data
    
    col1, col2 = st.columns(2)
    with col1:
        crop = st.selectbox("Select Crop", list(CROP_DATABASE.keys()))
        area = st.number_input("Area (Acres)", min_value=0.1, value=1.0, step=0.1)
    with col2:
        method = st.selectbox("Method", ["Standard", "High Density", "SRI/SCI"])
        fert_type = st.radio("Fertilizer Type", ["Chemical", "Organic", "Both"])
    
    if st.button("Calculate 📊", type="primary"):
        crop_info = CROP_DATABASE[crop]
        
        # Calculate seeds
        seed_rate = crop_info["seed_rate_kg_per_acre"]
        try:
            if "-" in seed_rate:
                low, high = map(float, seed_rate.split("-"))
                avg_seed = (low + high) / 2
            else:
                avg_seed = float(seed_rate.split()[0])
        except:
            avg_seed = 10
        
        if "High" in method:
            avg_seed *= 1.2
        elif "SRI" in method:
            avg_seed *= 0.8
        
        total_seeds = avg_seed * area
        
        # Results
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Seed Rate", seed_rate)
        with col2:
            st.metric("Total Seeds", f"{total_seeds:.1f} kg")
        with col3:
            yield_tons = float(crop_info["expected_yield_tons"].split("-")[-1]) * area
            st.metric("Expected Yield", f"{yield_tons:.1f} tons")
        
        # Fertilizers
        if fert_type in ["Chemical", "Both"]:
            st.markdown("### 🧪 Chemical Fertilizers")
            chem = crop_info["chemical_fertilizers"]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Urea", f"{float(chem['urea_kg']) * area:.1f} kg")
            with col2:
                st.metric("DAP", f"{float(chem['dap_kg']) * area:.1f} kg")
            with col3:
                st.metric("MOP", f"{float(chem['mop_kg']) * area:.1f} kg")
        
        if fert_type in ["Organic", "Both"]:
            st.markdown("### 🌱 Organic Fertilizers")
            org = crop_info["organic_fertilizers"]
            fym = org['fym_tons'].split('-')[-1]
            st.write(f"**FYM:** {float(fym) * area:.1f} tons")
            if 'vermicompost_kg' in org:
                vermi = org['vermicompost_kg'].split('-')[-1]
                st.write(f"**Vermicompost:** {float(vermi) * area:.0f} kg")
        
        log_activity(user['id'], "Seed Calculation", crop, area, {"method": method})

def show_live_market_prices():
    """Market Prices"""
    st.markdown("### 📊 Market Prices")
    user = st.session_state.user_data
    
    commodity = st.selectbox("Select Commodity", list(CROP_DATABASE.keys()))
    
    manual_data = get_manual_prices(commodity=commodity, district=user['district'])
    
    if manual_data is not None:
        st.success(f"✅ Price data for {commodity}")
        latest = manual_data.iloc[0]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Min Price", f"₹{latest['min_price']:,.0f}")
        with col2:
            st.metric("Max Price", f"₹{latest['max_price']:,.0f}")
        with col3:
            st.metric("Modal Price", f"₹{latest['modal_price']:,.0f}")
        
        st.dataframe(manual_data, use_container_width=True)
    else:
        crop_info = CROP_DATABASE[commodity]
        st.info(f"Expected price: {crop_info['market_price_range']}")
        
        mandis = get_nearest_mandis(user['district'])
        st.markdown("### 🏪 Nearest Markets")
        for mandi in mandis:
            st.markdown(f"- 📍 {mandi}")

def show_profit_calculator():
    """Profit Calculator"""
    st.markdown("### 💰 Profit & ROI Calculator")
    user = st.session_state.user_data
    
    col1, col2 = st.columns(2)
    with col1:
        crop = st.selectbox("Crop", list(CROP_DATABASE.keys()))
        area = st.number_input("Area (Acres)", min_value=0.1, value=1.0)
        st.markdown("### Costs")
        seed_cost = st.number_input("Seeds (₹)", value=5000)
        fert_cost = st.number_input("Fertilizers (₹)", value=8000)
        pest_cost = st.number_input("Pesticides (₹)", value=3000)
        labor = st.number_input("Labor (₹)", value=15000)
        other = st.number_input("Other (₹)", value=2000)
    
    with col2:
        crop_info = CROP_DATABASE[crop]
        yield_tons = float(crop_info["expected_yield_tons"].split("-")[-1])
        expected_yield = st.slider("Expected Yield (tons/acre)", 
                                   yield_tons * 0.5, yield_tons * 1.5, yield_tons)
        price_str = crop_info["market_price_range"].replace("₹", "").split("-")
        avg_price = sum([float(p.split("/")[0]) for p in price_str]) / len(price_str)
        selling_price = st.number_input("Selling Price (₹/quintal)", value=int(avg_price))
        
        total_quintals = expected_yield * area * 10
        revenue = total_quintals * selling_price
        st.metric("Revenue", f"₹{revenue:,.0f}")
    
    if st.button("Calculate Profit 💰", type="primary"):
        total_cost = seed_cost + fert_cost + pest_cost + labor + other
        profit = revenue - total_cost
        roi = (profit / total_cost * 100) if total_cost > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Cost", f"₹{total_cost:,.0f}")
        with col2:
            st.metric("Net Profit", f"₹{profit:,.0f}")
        with col3:
            st.metric("ROI", f"{roi:.1f}%")
        
        if profit > 0:
            st.success(f"✅ Profitable! ROI: {roi:.1f}%")
        else:
            st.error("⚠️ Loss projected")
        
        log_activity(user['id'], "Profit Calculation", crop, area, 
                    {"cost": total_cost, "profit": profit})

def show_knowledge_base():
    """Knowledge Base"""
    st.markdown("### 📚 Crop Knowledge Base")
    
    search = st.text_input("🔍 Search crops...")
    
    for crop_name, crop in CROP_DATABASE.items():
        if search and search.lower() not in crop_name.lower():
            continue
        
        with st.expander(f"🌱 {crop_name}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Duration:** {crop['duration_days']} days")
                st.write(f"**Yield:** {crop['expected_yield_tons']} tons/acre")
                st.write(f"**Season:** {crop['best_season']}")
            with col2:
                st.write(f"**Soil:** {crop['soil_type']}")
                st.write(f"**Price:** {crop['market_price_range']}")

def show_marketplace():
    """Marketplace"""
    st.markdown("### 🛒 Agricultural Marketplace")
    user = st.session_state.user_data
    
    col1, col2 = st.columns(2)
    with col1:
        filter_crop = st.selectbox("Filter Crop", ["All"] + list(CROP_DATABASE.keys()))
    with col2:
        filter_district = st.selectbox("Filter District", ["All"] + list(MAHARASHTRA_LOCATIONS.keys()))
    
    conn = sqlite3.connect('krishimitra.db')
    c = conn.cursor()
    query = """SELECT ml.*, u.full_name, u.mobile, u.district 
               FROM marketplace_listings ml 
               JOIN users u ON ml.seller_id = u.id 
               WHERE ml.status = 'Active'"""
    params = []
    if filter_crop != "All":
        query += " AND ml.crop_name = ?"
        params.append(filter_crop)
    if filter_district != "All":
        query += " AND ml.location = ?"
        params.append(filter_district)
    query += " ORDER BY ml.created_at DESC"
    
    c.execute(query, params)
    listings = c.fetchall()
    conn.close()
    
    if listings:
        st.success(f"✅ {len(listings)} listings found")
        for listing in listings:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"""
                **🌾 {listing[2]}** - {listing[3]} {listing[4]}
                
                💰 Price: ₹{listing[5]:,.0f} per {listing[4]}
                
                📍 Location: {listing[13]}
                
                👤 Seller: {listing[11]} ({listing[12]})
                """)
            with col2:
                if st.button(f"Place Bid", key=f"bid_{listing[0]}"):
                    st.info("Bid functionality - Place your bid here")
            st.markdown("---")
    else:
        st.info("No listings available")

def show_my_listings():
    """My Listings"""
    st.markdown("### 🛍️ My Listings")
    user = st.session_state.user_data
    
    tab1, tab2 = st.tabs(["My Listings", "Create New"])
    
    with tab1:
        conn = sqlite3.connect('krishimitra.db')
        c = conn.cursor()
        c.execute("SELECT * FROM marketplace_listings WHERE seller_id=?", (user['id'],))
        listings = c.fetchall()
        conn.close()
        
        if listings:
            for listing in listings:
                st.markdown(f"**{listing[2]}** - {listing[3]} {listing[4]} @ ₹{listing[5]}")
                st.markdown("---")
        else:
            st.info("No listings yet")
    
    with tab2:
        with st.form("new_listing"):
            crop = st.selectbox("Crop", list(CROP_DATABASE.keys()))
            quantity = st.number_input("Quantity", min_value=0.1)
            unit = st.selectbox("Unit", ["Quintal", "Kg", "Tonnes"])
            price = st.number_input("Price per Unit (₹)", min_value=1.0)
            
            if st.form_submit_button("Create Listing", use_container_width=True):
                conn = sqlite3.connect('krishimitra.db')
                c = conn.cursor()
                c.execute("""INSERT INTO marketplace_listings 
                            (seller_id, crop_name, quantity, unit, price_per_unit, location, status)
                            VALUES (?, ?, ?, ?, ?, ?, 'Active')""",
                         (user['id'], crop, quantity, unit, price, user['district']))
                conn.commit()
                conn.close()
                st.success("✅ Listing created!")
                st.rerun()

def show_my_bids():
    """My Bids"""
    st.markdown("### 💼 My Bids")
    user = st.session_state.user_data
    
    conn = sqlite3.connect('krishimitra.db')
    c = conn.cursor()
    c.execute("""SELECT b.*, ml.crop_name FROM bids b
                 JOIN marketplace_listings ml ON b.listing_id = ml.id
                 WHERE b.buyer_id = ?""", (user['id'],))
    bids = c.fetchall()
    conn.close()
    
    if bids:
        for bid in bids:
            st.markdown(f"**{bid[10]}** - ₹{bid[3]} - Status: {bid[8]}")
            st.markdown("---")
    else:
        st.info("No bids placed yet")

def show_notifications():
    """Notifications"""
    st.markdown("### 📱 Notifications")
    user = st.session_state.user_data
    
    conn = sqlite3.connect('krishimitra.db')
    c = conn.cursor()
    c.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC", (user['id'],))
    notifications = c.fetchall()
    conn.close()
    
    if notifications:
        for notif in notifications:
            st.info(f"{notif[2]}: {notif[3]}")
            st.caption(f"Date: {notif[5]}")
            st.markdown("---")
    else:
        st.info("No notifications")

def show_activity_history():
    """Activity History"""
    st.markdown("### 📊 Activity History")
    user = st.session_state.user_data
    
    activities = get_user_activities(user['id'], limit=50)
    
    if activities:
        df = pd.DataFrame(activities, columns=['Activity', 'Crop', 'Area', 'Data', 'Date'])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No activities yet")

if __name__ == "__main__":
    main()