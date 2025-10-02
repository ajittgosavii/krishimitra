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
        
        api_key = None
        try:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
        except KeyError:
            try:
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

# Custom CSS
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
    .ai-card {
        background-color: #E3F2FD;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 6px solid #2196F3;
        margin: 1rem 0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }
    .alert-card {
        background-color: #FFF3E0;
        padding: 1.2rem;
        border-radius: 10px;
        border-left: 5px solid #FF9800;
        margin: 0.8rem 0;
    }
    .success-card {
        background-color: #E8F5E9;
        padding: 1.2rem;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        margin: 0.8rem 0;
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
    </style>
    """, unsafe_allow_html=True)

# CEDA Integration
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
                return df, "Data retrieved from CEDA Ashoka University"
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

# Maharashtra Locations
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
}

# Initialize session state
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'location_data' not in st.session_state:
    st.session_state.location_data = {'district': None, 'tehsil': None, 'village': None}
if 'notifications_enabled' not in st.session_state:
    st.session_state.notifications_enabled = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'price_alerts' not in st.session_state:
    st.session_state.price_alerts = []
if 'crop_tracking' not in st.session_state:
    st.session_state.crop_tracking = []

# Crop Database
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
        "critical_growth_stages": [
            {"stage": "Germination", "days": "0-10", "water_need": "High", "nutrients": "Minimal"},
            {"stage": "Tillering", "days": "15-40", "water_need": "Medium", "nutrients": "High N"},
            {"stage": "Panicle Initiation", "days": "45-65", "water_need": "Critical", "nutrients": "Balanced NPK"},
            {"stage": "Flowering", "days": "70-90", "water_need": "High", "nutrients": "Low N, High K"},
            {"stage": "Grain Filling", "days": "95-120", "water_need": "Medium", "nutrients": "K only"}
        ],
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
        },
        "common_pests": ["Stem Borer", "Brown Plant Hopper", "Leaf Folder"],
        "common_diseases": ["Blast Disease", "Sheath Blight", "Bacterial Leaf Blight"]
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
        "critical_growth_stages": [
            {"stage": "Crown Root Initiation", "days": "20-25", "water_need": "Critical", "nutrients": "High N"},
            {"stage": "Tillering", "days": "30-50", "water_need": "Medium", "nutrients": "High N"},
            {"stage": "Jointing", "days": "60-70", "water_need": "High", "nutrients": "Balanced NPK"},
            {"stage": "Flowering", "days": "80-85", "water_need": "Critical", "nutrients": "Low N, High K"},
            {"stage": "Grain Filling", "days": "95-110", "water_need": "Medium", "nutrients": "K only"}
        ],
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
            "biofertilizers": "Azotobacter + PSB @ 2 kg each per acre",
        },
        "common_pests": ["Aphids", "Termites"],
        "common_diseases": ["Yellow Rust", "Brown Rust", "Powdery Mildew"]
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
        "critical_growth_stages": [
            {"stage": "Germination", "days": "0-15", "water_need": "High", "nutrients": "Minimal"},
            {"stage": "Square Formation", "days": "40-60", "water_need": "Critical", "nutrients": "High N"},
            {"stage": "Flowering", "days": "70-100", "water_need": "Critical", "nutrients": "Balanced NPK"},
            {"stage": "Boll Development", "days": "105-140", "water_need": "High", "nutrients": "High K"},
            {"stage": "Boll Opening", "days": "145-180", "water_need": "Low", "nutrients": "Minimal"}
        ],
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
            "biofertilizers": "Azospirillum + PSB + KSB @ 2 kg each",
        },
        "common_pests": ["Pink Bollworm", "Whitefly", "Aphids"],
        "common_diseases": ["Wilt", "Root Rot", "Leaf Spot"]
    },
    "Tomato": {
        "seed_rate_kg_per_acre": "80-100 grams",
        "spacing": "60cm x 45cm",
        "water_requirement": "243-324 mm",
        "duration_days": "65-90",
        "expected_yield_tons": "20-28",
        "best_season": "Kharif, Rabi & Summer",
        "soil_type": "Well-drained sandy loam",
        "market_price_range": "₹800-2500/quintal",
        "critical_growth_stages": [
            {"stage": "Transplanting", "days": "0-10", "water_need": "High", "nutrients": "Minimal"},
            {"stage": "Vegetative Growth", "days": "15-35", "water_need": "Medium", "nutrients": "High N"},
            {"stage": "Flowering", "days": "40-55", "water_need": "Critical", "nutrients": "Balanced NPK + Ca"},
            {"stage": "Fruit Setting", "days": "60-75", "water_need": "High", "nutrients": "High K + Ca"},
            {"stage": "Fruit Development", "days": "80-90", "water_need": "Medium", "nutrients": "High K"}
        ],
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
        },
        "common_pests": ["Fruit Borer", "Whitefly", "Leaf Miner"],
        "common_diseases": ["Early Blight", "Late Blight", "Wilt", "Leaf Curl Virus"]
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
        "critical_growth_stages": [
            {"stage": "Transplanting", "days": "0-10", "water_need": "High", "nutrients": "Minimal"},
            {"stage": "Vegetative Growth", "days": "15-50", "water_need": "Medium", "nutrients": "High N"},
            {"stage": "Bulb Initiation", "days": "60-90", "water_need": "Critical", "nutrients": "Balanced NPK"},
            {"stage": "Bulb Development", "days": "100-130", "water_need": "Medium", "nutrients": "High K"},
            {"stage": "Maturity", "days": "140-150", "water_need": "Stop", "nutrients": "None"}
        ],
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
        "common_pests": ["Thrips", "Onion Maggot"],
        "common_diseases": ["Purple Blotch", "Stemphylium Blight", "Basal Rot"]
    }
}

# Database Functions
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
    
    c.execute('''CREATE TABLE IF NOT EXISTS crop_tracking
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  crop_name TEXT,
                  area_acres REAL,
                  sowing_date DATE,
                  expected_harvest_date DATE,
                  current_stage TEXT,
                  days_after_sowing INTEGER,
                  health_status TEXT,
                  notes TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS price_alerts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  commodity TEXT,
                  target_price REAL,
                  alert_type TEXT,
                  status TEXT DEFAULT 'Active',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS irrigation_schedule
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  crop_name TEXT,
                  schedule_date DATE,
                  water_amount REAL,
                  completed BOOLEAN DEFAULT 0,
                  notes TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS yield_predictions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  crop_name TEXT,
                  area_acres REAL,
                  predicted_yield REAL,
                  confidence_level TEXT,
                  factors TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
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
        "Pune": ["Pune Market Yard", "Baramati APMC", "Daund APMC", "Indapur APMC", "Shirur APMC"],
        "Nagpur": ["Nagpur Cotton Market", "Kamptee APMC", "Umred APMC", "Hinganghat APMC"],
        "Nashik": ["Nashik APMC", "Lasalgaon APMC", "Sinnar APMC", "Niphad APMC"],
        "Mumbai Suburban": ["Vashi APMC", "Turbhe Market", "Kalyan APMC"],
        "Thane": ["Kalyan APMC", "Bhiwandi Market", "Thane Market"],
        "Aurangabad": ["Aurangabad APMC", "Paithan Market", "Gangapur Market"],
        "Solapur": ["Solapur APMC", "Barshi Market", "Pandharpur APMC"],
        "Kolhapur": ["Kolhapur APMC", "Ichalkaranji Market", "Kagal APMC"],
        "Ahmednagar": ["Ahmednagar APMC", "Sangamner Market", "Rahuri Market"],
        "Satara": ["Satara APMC", "Karad Market", "Phaltan APMC"],
        "Sangli": ["Sangli APMC", "Miraj Market", "Tasgaon APMC"]
    }
    return mandis.get(district, ["Contact District Agriculture Office", "Visit nearest APMC"])

# AI Helper Functions
def get_ai_response(user_message, context=""):
    """Get AI response from Claude"""
    client = get_anthropic_client()
    if not client:
        return "AI Assistant is not configured. Please add ANTHROPIC_API_KEY to secrets."
    
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
6. Yield optimization strategies
7. Water and soil management

Always be:
- Concise and practical
- Supportive and encouraging
- Specific to Indian/Maharashtra agriculture
- Data-driven with actionable advice

{context}"""
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        return message.content[0].text
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

# Main Application
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
    tab1, tab2 = st.tabs(["Login", "Register"])
    
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
            
            st.markdown("### Location Details")
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
                        st.success("Account created! Please login")
                        st.balloons()
                    else:
                        st.error(f"Error: {result}")

def show_main_app():
    """Main app with navigation"""
    user = st.session_state.user_data
    
    with st.sidebar:
        st.markdown(f"### {user['full_name']}")
        st.markdown(f"**{user['village']}, {user['tehsil']}**")
        st.markdown(f"**Farm: {user['farm_size']} acres**")
        st.markdown("---")
        
        # Define pages based on user type
        if user.get('user_type') == 'Farmer':
            pages = [
                "Dashboard",
                "AI Assistant", 
                "Crop Growth Tracker",
                "Smart Irrigation Planner",
                "Soil Health Analyzer",
                "Yield Predictor",
                "Seed Calculator",
                "Market Prices",
                "Price Alert System",
                "Best Time to Sell",
                "Complete Crop Guide",
                "Profit Calculator",
                "Disease Diagnosis",
                "My Activity"
            ]
        else:
            pages = [
                "Dashboard",
                "AI Assistant",
                "Market Prices",
                "Price Alert System"
            ]
        
        st.markdown("### Navigation")
        for page in pages:
            if st.button(page, key=f"nav_{page}", use_container_width=True, 
                        type="primary" if st.session_state.current_page == page else "secondary"):
                st.session_state.current_page = page
                st.rerun()
        
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            st.session_state.user_data = None
            st.session_state.current_page = "Dashboard"
            st.rerun()
    
    # Page routing
    page = st.session_state.current_page
    
    try:
        if page == "Dashboard":
            show_dashboard()
        elif page == "AI Assistant":
            show_ai_assistant()
        elif page == "Crop Growth Tracker":
            show_crop_growth_tracker()
        elif page == "Smart Irrigation Planner":
            show_smart_irrigation_planner()
        elif page == "Soil Health Analyzer":
            show_soil_health_analyzer()
        elif page == "Yield Predictor":
            show_yield_predictor()
        elif page == "Seed Calculator":
            show_seed_fertilizer_calculator()
        elif page == "Market Prices":
            show_live_market_prices()
        elif page == "Price Alert System":
            show_price_alert_system()
        elif page == "Best Time to Sell":
            show_best_time_to_sell()
        elif page == "Complete Crop Guide":
            show_complete_crop_guide()
        elif page == "Profit Calculator":
            show_profit_calculator()
        elif page == "Disease Diagnosis":
            show_ai_disease_diagnosis()
        elif page == "My Activity":
            show_activity_history()
        else:
            show_dashboard()
    except Exception as e:
        st.error(f"Error: {str(e)}")
        if st.button("Refresh"):
            st.rerun()

# Page Functions
def show_dashboard():
    """Enhanced Dashboard"""
    user = st.session_state.user_data
    st.markdown(f"### Welcome, {user['full_name']}!")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Your Farm", f"{user['farm_size']} acres")
    with col2:
        activities = get_user_activities(user['id'], limit=1000)
        st.metric("Activities", len(activities))
    with col3:
        conn = sqlite3.connect('krishimitra.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM crop_tracking WHERE user_id=?", (user['id'],))
        crop_count = c.fetchone()[0]
        conn.close()
        st.metric("Active Crops", crop_count)
    with col4:
        st.metric("Location", f"{user['district']}")
    
    # Quick actions
    st.markdown("### Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("AI Assistant", use_container_width=True):
            st.session_state.current_page = "AI Assistant"
            st.rerun()
    with col2:
        if st.button("Track Crops", use_container_width=True):
            st.session_state.current_page = "Crop Growth Tracker"
            st.rerun()
    with col3:
        if st.button("Check Prices", use_container_width=True):
            st.session_state.current_page = "Market Prices"
            st.rerun()
    with col4:
        if st.button("Predict Yield", use_container_width=True):
            st.session_state.current_page = "Yield Predictor"
            st.rerun()
    
    # Active crop tracking summary
    st.markdown("### Active Crop Status")
    conn = sqlite3.connect('krishimitra.db')
    c = conn.cursor()
    c.execute('''SELECT crop_name, area_acres, days_after_sowing, current_stage, health_status 
                 FROM crop_tracking WHERE user_id=? ORDER BY sowing_date DESC LIMIT 5''', (user['id'],))
    crops = c.fetchall()
    conn.close()
    
    if crops:
        for crop in crops:
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**{crop[0]}** - {crop[1]} acres")
            with col2:
                st.write(f"Day {crop[2]} - {crop[3]}")
            with col3:
                if crop[4] == "Healthy":
                    st.success("Healthy")
                elif crop[4] == "Attention":
                    st.warning("Attention")
                else:
                    st.error("Critical")
    else:
        st.info("No active crops. Start tracking your crops for better yield management!")
    
    # Recent activities
    st.markdown("### Recent Activities")
    recent = get_user_activities(user['id'], limit=5)
    if recent:
        for act in recent:
            st.markdown(f"- **{act[0]}**: {act[1]} ({act[2]} acres) - {act[4]}")
    else:
        st.info("No activities yet. Start using the tools!")

def show_ai_assistant():
    """AI Chat Assistant"""
    st.markdown("### AI Agricultural Assistant")
    st.markdown("Ask me anything about farming, crops, market prices, or government schemes!")
    
    client = get_anthropic_client()
    if not client:
        st.warning("AI Assistant requires ANTHROPIC_API_KEY in secrets.")
    
    # Chat interface
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {message["content"]}</div>', 
                       unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message assistant-message"><strong>KrishiMitra AI:</strong> {message["content"]}</div>', 
                       unsafe_allow_html=True)
    
    # Quick action buttons
    st.markdown("### Quick Questions")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Best crops for my location", use_container_width=True):
            user = st.session_state.user_data
            question = f"What are the best crops for {user['tehsil']}, {user['district']} this season?"
            with st.spinner("Thinking..."):
                response = get_ai_response(question)
                st.session_state.chat_history.append({"role": "user", "content": question})
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()
    with col2:
        if st.button("Current market trends", use_container_width=True):
            question = "What are the current agricultural market trends in Maharashtra?"
            with st.spinner("Analyzing..."):
                response = get_ai_response(question)
                st.session_state.chat_history.append({"role": "user", "content": question})
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()
    with col3:
        if st.button("Yield improvement tips", use_container_width=True):
            question = "What are the top 5 ways to increase crop yields in Maharashtra?"
            with st.spinner("Searching..."):
                response = get_ai_response(question)
                st.session_state.chat_history.append({"role": "user", "content": question})
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()
    
    # Chat input
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area("Your question:", placeholder="E.g., How can I increase my rice yield?", height=100)
        submitted = st.form_submit_button("Send", use_container_width=True, type="primary")
        
        if submitted and user_input:
            with st.spinner("Getting answer..."):
                response = get_ai_response(user_input)
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()
    
    if st.session_state.chat_history:
        if st.button("Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()

def show_crop_growth_tracker():
    """Crop Growth Tracking System"""
    st.markdown("### Crop Growth Tracker")
    st.markdown("Monitor your crops day-by-day for optimal yield")
    
    user = st.session_state.user_data
    
    tab1, tab2, tab3 = st.tabs(["Active Crops", "Add New Crop", "Growth Insights"])
    
    with tab1:
        conn = sqlite3.connect('krishimitra.db')
        c = conn.cursor()
        c.execute('''SELECT id, crop_name, area_acres, sowing_date, days_after_sowing, 
                     current_stage, health_status, notes 
                     FROM crop_tracking WHERE user_id=? ORDER BY sowing_date DESC''', (user['id'],))
        crops = c.fetchall()
        conn.close()
        
        if crops:
            for crop in crops:
                with st.expander(f"{crop[1]} - {crop[2]} acres (Day {crop[4]})"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Current Stage", crop[5])
                        st.metric("Days After Sowing", crop[4])
                    with col2:
                        st.metric("Health Status", crop[6])
                        st.metric("Sowing Date", crop[3])
                    with col3:
                        crop_info = CROP_DATABASE.get(crop[1], {})
                        duration = crop_info.get("duration_days", "120-150")
                        max_days = int(duration.split("-")[-1])
                        progress = (crop[4] / max_days) * 100
                        st.metric("Progress", f"{progress:.1f}%")
                    
                    if crop[7]:
                        st.info(f"Notes: {crop[7]}")
                    
                    # Show current stage requirements
                    if crop[1] in CROP_DATABASE and "critical_growth_stages" in CROP_DATABASE[crop[1]]:
                        stages = CROP_DATABASE[crop[1]]["critical_growth_stages"]
                        current_stage = None
                        for stage in stages:
                            day_range = stage["days"].split("-")
                            start = int(day_range[0])
                            end = int(day_range[-1])
                            if start <= crop[4] <= end:
                                current_stage = stage
                                break
                        
                        if current_stage:
                            st.markdown("#### Current Stage Requirements")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Water Need:** {current_stage['water_need']}")
                            with col2:
                                st.write(f"**Nutrients:** {current_stage['nutrients']}")
                    
                    # AI recommendations for this stage
                    if st.button(f"Get AI Recommendations for {crop[1]}", key=f"ai_{crop[0]}"):
                        with st.spinner("Getting stage-specific recommendations..."):
                            prompt = f"""Provide specific care recommendations for {crop[1]} at day {crop[4]}:
                            
                            Current details:
                            - Stage: {crop[5]}
                            - Health: {crop[6]}
                            - Location: {user['tehsil']}, {user['district']}
                            
                            Provide:
                            1. Critical actions needed now
                            2. Irrigation schedule for next 7 days
                            3. Nutrient application timing
                            4. Pest/disease watch points
                            5. Expected challenges in next growth stage
                            """
                            response = get_ai_response(prompt)
                            st.markdown('<div class="ai-card">', unsafe_allow_html=True)
                            st.markdown(response)
                            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No crops being tracked. Add your first crop below!")
    
    with tab2:
        st.markdown("### Add New Crop to Track")
        with st.form("add_crop_tracking"):
            col1, col2 = st.columns(2)
            with col1:
                crop_name = st.selectbox("Crop", list(CROP_DATABASE.keys()))
                area = st.number_input("Area (Acres)", min_value=0.1, value=1.0)
            with col2:
                sowing_date = st.date_input("Sowing Date", value=datetime.now())
                health_status = st.selectbox("Current Health", ["Healthy", "Attention", "Critical"])
            
            notes = st.text_area("Notes", placeholder="Any observations...")
            
            submitted = st.form_submit_button("Start Tracking", use_container_width=True, type="primary")
            
            if submitted:
                days_after_sowing = (datetime.now().date() - sowing_date).days
                crop_info = CROP_DATABASE[crop_name]
                duration = crop_info.get("duration_days", "120-150")
                max_days = int(duration.split("-")[-1])
                expected_harvest = sowing_date + timedelta(days=max_days)
                
                # Determine current stage
                current_stage = "Germination"
                if "critical_growth_stages" in crop_info:
                    for stage in crop_info["critical_growth_stages"]:
                        day_range = stage["days"].split("-")
                        start = int(day_range[0])
                        end = int(day_range[-1])
                        if start <= days_after_sowing <= end:
                            current_stage = stage["stage"]
                            break
                
                conn = sqlite3.connect('krishimitra.db')
                c = conn.cursor()
                c.execute('''INSERT INTO crop_tracking 
                            (user_id, crop_name, area_acres, sowing_date, expected_harvest_date,
                             current_stage, days_after_sowing, health_status, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                         (user['id'], crop_name, area, sowing_date, expected_harvest, 
                          current_stage, days_after_sowing, health_status, notes))
                conn.commit()
                conn.close()
                
                st.success(f"Started tracking {crop_name}!")
                log_activity(user['id'], "Crop Tracking Started", crop_name, area, 
                            {"sowing_date": str(sowing_date)})
                st.rerun()
    
    with tab3:
        st.markdown("### Growth Insights & Analytics")
        
        conn = sqlite3.connect('krishimitra.db')
        c = conn.cursor()
        c.execute('''SELECT crop_name, COUNT(*), AVG(area_acres) 
                     FROM crop_tracking WHERE user_id=? GROUP BY crop_name''', (user['id'],))
        summary = c.fetchall()
        conn.close()
        
        if summary:
            df = pd.DataFrame(summary, columns=['Crop', 'Times Grown', 'Avg Area'])
            
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(df, x='Crop', y='Times Grown', title="Crop History")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = px.pie(df, values='Avg Area', names='Crop', title="Area Distribution")
                st.plotly_chart(fig, use_container_width=True)

def show_smart_irrigation_planner():
    """AI-powered irrigation scheduling"""
    st.markdown("### Smart Irrigation Planner")
    st.markdown("Get AI-powered irrigation schedule based on crop stage and conditions")
    
    user = st.session_state.user_data
    
    col1, col2 = st.columns(2)
    with col1:
        crop = st.selectbox("Current Crop", list(CROP_DATABASE.keys()))
        days_after_sowing = st.number_input("Days After Sowing/Transplanting", 1, 200, 30)
        area = st.number_input("Area (Acres)", 0.1, 100.0, 1.0)
    
    with col2:
        irrigation_type = st.selectbox("Irrigation Method", 
                                       ["Drip", "Sprinkler", "Flood", "Furrow"])
        soil_type = st.selectbox("Soil Type", 
                                 ["Clay", "Loam", "Sandy", "Sandy Loam", "Clay Loam"])
        recent_rainfall = st.number_input("Recent Rainfall (mm in last 7 days)", 0.0, 200.0, 0.0)
    
    if st.button("Generate Irrigation Schedule", type="primary", use_container_width=True):
        with st.spinner("Creating personalized irrigation schedule..."):
            crop_info = CROP_DATABASE[crop]
            
            # Determine current stage
            current_stage = "Vegetative"
            water_need = "Medium"
            if "critical_growth_stages" in crop_info:
                for stage in crop_info["critical_growth_stages"]:
                    day_range = stage["days"].split("-")
                    start = int(day_range[0])
                    end = int(day_range[-1])
                    if start <= days_after_sowing <= end:
                        current_stage = stage["stage"]
                        water_need = stage["water_need"]
                        break
            
            prompt = f"""Create a detailed 7-day irrigation schedule:
            
            Farm Details:
            - Location: {user['tehsil']}, {user['district']}, Maharashtra
            - Crop: {crop} (Day {days_after_sowing})
            - Current Stage: {current_stage}
            - Area: {area} acres
            - Irrigation Method: {irrigation_type}
            - Soil Type: {soil_type}
            - Recent Rainfall: {recent_rainfall} mm
            - Water Need Level: {water_need}
            
            Provide:
            1. Day-by-day irrigation schedule (next 7 days)
            2. Water quantity per irrigation (in liters or mm)
            3. Best time of day for irrigation
            4. Signs to watch for under/over watering
            5. Water savings tips for {irrigation_type} system
            6. Expected water consumption for the week
            
            Consider the crop stage and recent rainfall in recommendations."""
            
            response = get_ai_response(prompt)
            
            st.markdown('<div class="ai-card">', unsafe_allow_html=True)
            st.markdown("### Your Personalized Irrigation Schedule")
            st.markdown(f"**Current Stage:** {current_stage} | **Water Need:** {water_need}")
            st.markdown("---")
            st.markdown(response)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Save to database
            conn = sqlite3.connect('krishimitra.db')
            c = conn.cursor()
            for day in range(7):
                schedule_date = datetime.now().date() + timedelta(days=day)
                c.execute('''INSERT INTO irrigation_schedule 
                            (user_id, crop_name, schedule_date, notes)
                            VALUES (?, ?, ?, ?)''',
                         (user['id'], crop, schedule_date, "AI Generated Schedule"))
            conn.commit()
            conn.close()
            
            log_activity(user['id'], "Irrigation Schedule Created", crop, area, 
                        {"stage": current_stage, "irrigation": irrigation_type})
    
    # Show upcoming irrigation schedule
    st.markdown("### Upcoming Irrigation Tasks")
    conn = sqlite3.connect('krishimitra.db')
    c = conn.cursor()
    c.execute('''SELECT crop_name, schedule_date, completed, notes 
                 FROM irrigation_schedule 
                 WHERE user_id=? AND schedule_date >= date('now')
                 ORDER BY schedule_date LIMIT 7''', (user['id'],))
    schedules = c.fetchall()
    conn.close()
    
    if schedules:
        for sched in schedules:
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**{sched[0]}**")
            with col2:
                st.write(f"{sched[1]}")
            with col3:
                if sched[2]:
                    st.success("Done")
                else:
                    st.warning("Pending")
    else:
        st.info("No irrigation schedule set. Generate one above!")

def show_soil_health_analyzer():
    """AI Soil Health Analysis & Recommendations"""
    st.markdown("### Soil Health Analyzer")
    st.markdown("Get AI-powered soil analysis and amendment recommendations")
    
    user = st.session_state.user_data
    
    col1, col2 = st.columns(2)
    with col1:
        crop = st.selectbox("Crop to Plant", list(CROP_DATABASE.keys()))
        nitrogen = st.slider("Nitrogen (N) %", 0.0, 2.0, 0.5, 0.1)
        phosphorus = st.slider("Phosphorus (P) %", 0.0, 1.0, 0.3, 0.1)
        potassium = st.slider("Potassium (K) %", 0.0, 2.0, 0.4, 0.1)
    
    with col2:
        ph = st.slider("Soil pH", 4.0, 9.0, 6.5, 0.1)
        organic_matter = st.slider("Organic Matter %", 0.0, 5.0, 1.5, 0.1)
        moisture = st.slider("Moisture Level %", 0.0, 100.0, 50.0, 5.0)
        soil_texture = st.selectbox("Soil Texture", 
                                    ["Sandy", "Loamy", "Clay", "Sandy Loam", "Clay Loam"])
    
    st.markdown("### Optional: Upload Soil Test Report")
    uploaded_file = st.file_uploader("Upload PDF/Image of soil test", type=['pdf', 'jpg', 'png'])
    
    if st.button("Analyze Soil & Get Recommendations", type="primary", use_container_width=True):
        with st.spinner("Analyzing soil health..."):
            crop_info = CROP_DATABASE[crop]
            
            prompt = f"""As a soil scientist, provide comprehensive soil analysis for {crop} cultivation:
            
            Current Soil Parameters:
            - Nitrogen (N): {nitrogen}%
            - Phosphorus (P): {phosphorus}%
            - Potassium (K): {potassium}%
            - pH: {ph}
            - Organic Matter: {organic_matter}%
            - Moisture: {moisture}%
            - Texture: {soil_texture}
            
            Location: {user['tehsil']}, {user['district']}, Maharashtra
            Crop Requirements: {crop_info.get('soil_type', 'General')}
            
            Provide detailed analysis:
            1. Overall soil health rating (1-10 with explanation)
            2. Specific deficiencies or excesses identified
            3. Critical amendments needed:
               - Product names (both organic and chemical)
               - Exact quantities per acre
               - Application timing
               - Expected cost (in INR)
            4. Expected yield impact (% increase) if recommendations followed
            5. Timeline for soil improvement (short-term and long-term)
            6. Organic vs chemical correction comparison
            7. Maintenance plan for optimal soil health
            8. Impact on neighboring crops/future rotations
            
            Be specific with local Maharashtra product names and realistic prices."""
            
            response = get_ai_response(prompt)
            
            st.markdown('<div class="ai-card">', unsafe_allow_html=True)
            st.markdown("### Comprehensive Soil Analysis Report")
            st.markdown(response)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Visual representation
            st.markdown("### Soil Nutrient Levels")
            
            # NPK comparison
            ideal_npk = {
                "Nitrogen": 1.5,
                "Phosphorus": 0.5,
                "Potassium": 1.0
            }
            current_npk = {
                "Nitrogen": nitrogen,
                "Phosphorus": phosphorus,
                "Potassium": potassium
            }
            
            df_npk = pd.DataFrame({
                "Nutrient": ["Nitrogen", "Phosphorus", "Potassium"],
                "Current": [nitrogen, phosphorus, potassium],
                "Ideal Range": [1.5, 0.5, 1.0]
            })
            
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Current', x=df_npk['Nutrient'], y=df_npk['Current']))
            fig.add_trace(go.Bar(name='Ideal', x=df_npk['Nutrient'], y=df_npk['Ideal Range']))
            fig.update_layout(title="NPK Levels Comparison", barmode='group')
            st.plotly_chart(fig, use_container_width=True)
            
            # pH indicator
            col1, col2, col3 = st.columns(3)
            with col1:
                if ph < 6.0:
                    st.error(f"pH {ph} - Too Acidic")
                elif ph > 7.5:
                    st.error(f"pH {ph} - Too Alkaline")
                else:
                    st.success(f"pH {ph} - Optimal")
            
            with col2:
                if organic_matter < 1.0:
                    st.error(f"OM {organic_matter}% - Very Low")
                elif organic_matter < 2.0:
                    st.warning(f"OM {organic_matter}% - Low")
                else:
                    st.success(f"OM {organic_matter}% - Good")
            
            with col3:
                if moisture < 30:
                    st.error(f"Moisture {moisture}% - Too Dry")
                elif moisture > 70:
                    st.error(f"Moisture {moisture}% - Too Wet")
                else:
                    st.success(f"Moisture {moisture}% - Optimal")
            
            log_activity(user['id'], "Soil Analysis", crop, 0, 
                        {"ph": ph, "N": nitrogen, "P": phosphorus, "K": potassium})

def show_yield_predictor():
    """AI-based yield prediction"""
    st.markdown("### Yield Predictor")
    st.markdown("Predict your harvest yield with AI-powered analysis")
    
    user = st.session_state.user_data
    
    col1, col2 = st.columns(2)
    with col1:
        crop = st.selectbox("Crop", list(CROP_DATABASE.keys()))
        area = st.number_input("Area (Acres)", min_value=0.1, value=1.0)
        days_after_sowing = st.number_input("Days After Sowing", 1, 200, 60)
        
        soil_quality = st.select_slider("Soil Quality", 
                                        options=["Poor", "Below Average", "Average", "Good", "Excellent"],
                                        value="Average")
    
    with col2:
        irrigation_quality = st.select_slider("Irrigation Adequacy",
                                              options=["Insufficient", "Below Adequate", "Adequate", "Good", "Excellent"],
                                              value="Adequate")
        
        pest_disease_control = st.select_slider("Pest/Disease Control",
                                                options=["Poor", "Below Average", "Average", "Good", "Excellent"],
                                                value="Average")
        
        weather_conditions = st.select_slider("Weather Conditions This Season",
                                             options=["Very Unfavorable", "Unfavorable", "Normal", "Favorable", "Very Favorable"],
                                             value="Normal")
        
        fertilizer_application = st.select_slider("Fertilizer Application",
                                                 options=["Insufficient", "Below Recommended", "As Recommended", "Above Recommended", "Excessive"],
                                                 value="As Recommended")
    
    if st.button("Predict Yield", type="primary", use_container_width=True):
        with st.spinner("Analyzing factors and predicting yield..."):
            crop_info = CROP_DATABASE[crop]
            base_yield = crop_info.get("expected_yield_tons", "1.0-1.5")
            
            prompt = f"""As an agricultural data scientist, predict the yield for this farm:
            
            Crop Details:
            - Crop: {crop}
            - Area: {area} acres
            - Days After Sowing: {days_after_sowing}
            - Base Expected Yield: {base_yield} tons/acre
            - Location: {user['tehsil']}, {user['district']}, Maharashtra
            
            Current Conditions:
            - Soil Quality: {soil_quality}
            - Irrigation: {irrigation_quality}
            - Pest/Disease Control: {pest_disease_control}
            - Weather: {weather_conditions}
            - Fertilizer Application: {fertilizer_application}
            
            Provide:
            1. Predicted yield (in tons and quintals)
            2. Confidence level (High/Medium/Low) with reasoning
            3. Yield range (best case - worst case)
            4. Key factors positively impacting yield
            5. Key factors negatively impacting yield
            6. Critical interventions needed NOW to improve yield
            7. Expected yield if all recommendations followed
            8. Comparison with district average yield
            9. Financial projection (estimated revenue at current market rates)
            
            Be realistic and data-driven. Use Maharashtra-specific benchmarks."""
            
            response = get_ai_response(prompt)
            
            st.markdown('<div class="success-card">', unsafe_allow_html=True)
            st.markdown("### Yield Prediction Report")
            st.markdown(response)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Visual yield comparison
            yield_range = base_yield.split("-")
            min_yield = float(yield_range[0])
            max_yield = float(yield_range[-1])
            
            # Calculate adjustment factor based on inputs
            quality_scores = {
                "Poor": 0.6, "Below Average": 0.8, "Average": 1.0, 
                "Good": 1.15, "Excellent": 1.3,
                "Insufficient": 0.7, "Below Adequate": 0.85, "Adequate": 1.0,
                "Below Recommended": 0.9, "As Recommended": 1.0, "Above Recommended": 1.05, "Excessive": 0.95,
                "Very Unfavorable": 0.6, "Unfavorable": 0.8, "Normal": 1.0, "Favorable": 1.15, "Very Favorable": 1.3
            }
            
            adjustment = (
                quality_scores.get(soil_quality, 1.0) * 0.25 +
                quality_scores.get(irrigation_quality, 1.0) * 0.25 +
                quality_scores.get(pest_disease_control, 1.0) * 0.2 +
                quality_scores.get(weather_conditions, 1.0) * 0.2 +
                quality_scores.get(fertilizer_application, 1.0) * 0.1
            )
            
            predicted_yield = ((min_yield + max_yield) / 2) * adjustment * area
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Predicted Yield", f"{predicted_yield:.2f} tons")
            with col2:
                st.metric("Per Acre", f"{predicted_yield/area:.2f} tons")
            with col3:
                confidence = "High" if 0.9 <= adjustment <= 1.2 else "Medium" if 0.7 <= adjustment <= 1.4 else "Low"
                st.metric("Confidence", confidence)
            
            # Yield factors chart
            factors_df = pd.DataFrame({
                "Factor": ["Soil", "Irrigation", "Pest Control", "Weather", "Fertilizer"],
                "Impact Score": [
                    quality_scores.get(soil_quality, 1.0),
                    quality_scores.get(irrigation_quality, 1.0),
                    quality_scores.get(pest_disease_control, 1.0),
                    quality_scores.get(weather_conditions, 1.0),
                    quality_scores.get(fertilizer_application, 1.0)
                ]
            })
            
            fig = px.bar(factors_df, x="Factor", y="Impact Score", 
                        title="Yield Impact Factors (1.0 = Average)",
                        color="Impact Score",
                        color_continuous_scale=["red", "yellow", "green"])
            st.plotly_chart(fig, use_container_width=True)
            
            # Save prediction
            conn = sqlite3.connect('krishimitra.db')
            c = conn.cursor()
            c.execute('''INSERT INTO yield_predictions 
                        (user_id, crop_name, area_acres, predicted_yield, confidence_level, factors)
                        VALUES (?, ?, ?, ?, ?, ?)''',
                     (user['id'], crop, area, predicted_yield, confidence, 
                      json.dumps({
                          "soil": soil_quality, "irrigation": irrigation_quality,
                          "pest_control": pest_disease_control, "weather": weather_conditions,
                          "fertilizer": fertilizer_application
                      })))
            conn.commit()
            conn.close()
            
            log_activity(user['id'], "Yield Prediction", crop, area, 
                        {"predicted_yield": predicted_yield, "confidence": confidence})

def show_price_alert_system():
    """Price alert system for farmers"""
    st.markdown("### Price Alert System")
    st.markdown("Get notified when crop prices reach your target")
    
    user = st.session_state.user_data
    
    tab1, tab2 = st.tabs(["Active Alerts", "Create Alert"])
    
    with tab1:
        st.markdown("### Your Active Price Alerts")
        
        conn = sqlite3.connect('krishimitra.db')
        c = conn.cursor()
        c.execute('''SELECT id, commodity, target_price, alert_type, status, created_at 
                     FROM price_alerts WHERE user_id=? ORDER BY created_at DESC''', (user['id'],))
        alerts = c.fetchall()
        conn.close()
        
        if alerts:
            for alert in alerts:
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                with col1:
                    st.write(f"**{alert[1]}**")
                with col2:
                    st.write(f"Target: ₹{alert[2]:,.0f}/quintal")
                with col3:
                    alert_type_display = "Above" if alert[3] == "above" else "Below"
                    st.write(f"Alert When: {alert_type_display}")
                with col4:
                    if alert[4] == "Active":
                        st.success("Active")
                    else:
                        st.info("Inactive")
                st.markdown("---")
        else:
            st.info("No price alerts set. Create your first alert below!")
    
    with tab2:
        st.markdown("### Create New Price Alert")
        
        with st.form("create_alert"):
            col1, col2 = st.columns(2)
            
            with col1:
                commodity = st.selectbox("Commodity", list(CROP_DATABASE.keys()))
                crop_info = CROP_DATABASE[commodity]
                price_range = crop_info.get("market_price_range", "₹1000-2000")
                
                st.info(f"Current typical range: {price_range}")
            
            with col2:
                target_price = st.number_input("Target Price (₹/quintal)", 
                                              min_value=100, value=2000, step=100)
                alert_type = st.radio("Alert When Price Goes", ["Above", "Below"])
            
            notification_method = st.multiselect("Notification Method",
                                                ["SMS", "In-App", "Email"],
                                                default=["In-App"])
            
            submitted = st.form_submit_button("Create Alert", use_container_width=True, type="primary")
            
            if submitted:
                conn = sqlite3.connect('krishimitra.db')
                c = conn.cursor()
                c.execute('''INSERT INTO price_alerts 
                            (user_id, commodity, target_price, alert_type, status)
                            VALUES (?, ?, ?, ?, 'Active')''',
                         (user['id'], commodity, target_price, alert_type.lower()))
                conn.commit()
                conn.close()
                
                st.success(f"Alert created! You'll be notified when {commodity} price goes {alert_type.lower()} ₹{target_price}")
                log_activity(user['id'], "Price Alert Created", commodity, 0, 
                            {"target_price": target_price, "type": alert_type})
                st.rerun()
        
        # Show AI price trend analysis
        st.markdown("### AI Price Trend Analysis")
        if st.button("Analyze Market Trends", use_container_width=True):
            with st.spinner("Analyzing market trends..."):
                prompt = f"""Analyze current agricultural market trends for Maharashtra:
                
                Provide insights on:
                1. Current price trends for major crops (Rice, Wheat, Cotton, Tomato, Onion)
                2. Expected price movements in next 30-60 days
                3. Factors influencing prices (supply, demand, exports, government policy)
                4. Best crops to sell now vs hold
                5. Seasonal price patterns farmers should know
                6. Tips for getting best prices at mandis
                
                Be specific to Maharashtra markets and current season."""
                
                response = get_ai_response(prompt)
                st.markdown('<div class="ai-card">', unsafe_allow_html=True)
                st.markdown("### Market Trends & Insights")
                st.markdown(response)
                st.markdown('</div>', unsafe_allow_html=True)

def show_best_time_to_sell():
    """AI-powered best time to sell predictor"""
    st.markdown("### Best Time to Sell Predictor")
    st.markdown("Get AI recommendations on optimal selling time for maximum profit")
    
    user = st.session_state.user_data
    
    col1, col2 = st.columns(2)
    with col1:
        crop = st.selectbox("Crop to Sell", list(CROP_DATABASE.keys()))
        quantity = st.number_input("Quantity Available (Quintals)", min_value=1.0, value=10.0)
        quality_grade = st.select_slider("Quality Grade",
                                         options=["Below Standard", "Standard", "Good", "Premium", "Super Premium"],
                                         value="Good")
    
    with col2:
        harvest_date = st.date_input("Harvest/Ready Date", value=datetime.now())
        storage_capacity = st.selectbox("Storage Availability",
                                       ["No storage", "Limited (1 month)", "Moderate (3 months)", 
                                        "Good (6 months)", "Excellent (1 year+)"])
        urgency = st.select_slider("Selling Urgency",
                                   options=["No rush", "Can wait 2-3 months", "Prefer within month", 
                                           "Need to sell soon", "Urgent"],
                                   value="Can wait 2-3 months")
    
    if st.button("Get Selling Strategy", type="primary", use_container_width=True):
        with st.spinner("Analyzing market conditions and creating selling strategy..."):
            crop_info = CROP_DATABASE[crop]
            current_price_range = crop_info.get("market_price_range", "₹2000")
            
            prompt = f"""As an agricultural market expert, provide comprehensive selling strategy:
            
            Crop Details:
            - Crop: {crop}
            - Quantity: {quantity} quintals
            - Quality: {quality_grade}
            - Harvest/Ready Date: {harvest_date}
            - Current Market Range: {current_price_range}
            - Location: {user['tehsil']}, {user['district']}, Maharashtra
            
            Farmer's Situation:
            - Storage: {storage_capacity}
            - Urgency: {urgency}
            
            Provide detailed analysis:
            1. IMMEDIATE RECOMMENDATION: Sell now vs wait? (Clear yes/no with reasoning)
            2. Optimal selling timeline:
               - Best case scenario
               - Good scenario
               - Acceptable scenario
            3. Expected price trends for next 3-6 months with reasoning
            4. Price targets to aim for (realistic based on quality and market)
            5. Specific APMC mandis in Maharashtra with best rates for this crop
            6. Storage vs immediate sale cost-benefit analysis
            7. Risk factors to consider (market glut, weather, government policies)
            8. Alternative selling channels (FPOs, contract farming, direct buyers)
            9. Negotiation tips for getting best prices
            10. Documentation and quality certification recommendations
            
            Consider:
            - Current season and supply situation
            - Upcoming festivals/events affecting demand
            - Export opportunities if any
            - Government procurement prices
            
            Be specific, actionable, and realistic about Maharashtra market conditions."""
            
            response = get_ai_response(prompt)
            
            st.markdown('<div class="success-card">', unsafe_allow_html=True)
            st.markdown("### Your Personalized Selling Strategy")
            st.markdown(response)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Additional insights
            st.markdown("### Quick Insights")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### Storage Cost Analysis")
                monthly_storage_cost = quantity * 10  # Approximate ₹10/quintal/month
                st.write(f"Estimated storage cost: ₹{monthly_storage_cost}/month")
                st.write(f"3-month storage: ₹{monthly_storage_cost * 3}")
                st.write(f"6-month storage: ₹{monthly_storage_cost * 6}")
            
            with col2:
                st.markdown("#### Price Improvement Needed")
                st.write("To justify 3-month storage:")
                st.write(f"Need: ₹{(monthly_storage_cost * 3) / quantity:.0f}/quintal increase")
                st.write("")
                st.write("To justify 6-month storage:")
                st.write(f"Need: ₹{(monthly_storage_cost * 6) / quantity:.0f}/quintal increase")
            
            with col3:
                st.markdown("#### Quality Premium")
                base_multipliers = {
                    "Below Standard": 0.8,
                    "Standard": 1.0,
                    "Good": 1.15,
                    "Premium": 1.3,
                    "Super Premium": 1.5
                }
                multiplier = base_multipliers.get(quality_grade, 1.0)
                st.write(f"Your quality grade: {quality_grade}")
                st.write(f"Expected premium: {(multiplier - 1) * 100:.0f}%")
            
            # Market comparison
            st.markdown("### Nearby Market Comparison")
            st.info(f"""
            **Top Markets for {crop} in {user['district']}:**
            
            1. Check rates at your nearest APMC mandi
            2. Compare with neighboring district rates
            3. Consider transportation costs
            4. Look for bulk buyer direct deals
            5. Explore FPO/cooperative options
            
            💡 Tip: Prices vary by 10-20% between mandis. Worth checking multiple options!
            """)
            
            log_activity(user['id'], "Selling Strategy", crop, 0, 
                        {"quantity": quantity, "quality": quality_grade})

def show_seed_fertilizer_calculator():
    """Seed & Fertilizer Calculator"""
    st.markdown("### Seed & Fertilizer Calculator")
    
    user = st.session_state.user_data
    
    col1, col2 = st.columns(2)
    with col1:
        crop = st.selectbox("Select Crop", list(CROP_DATABASE.keys()))
        area = st.number_input("Area (Acres)", min_value=0.1, value=1.0, step=0.1)
    with col2:
        method = st.selectbox("Method", ["Standard", "High Density", "SRI/SCI"])
        fert_type = st.radio("Fertilizer Type", ["Chemical", "Organic", "Both"])
    
    if st.button("Calculate", type="primary"):
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
            st.markdown("### Chemical Fertilizers")
            chem = crop_info["chemical_fertilizers"]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Urea", f"{float(chem['urea_kg']) * area:.1f} kg")
            with col2:
                st.metric("DAP", f"{float(chem['dap_kg']) * area:.1f} kg")
            with col3:
                st.metric("MOP", f"{float(chem['mop_kg']) * area:.1f} kg")
            
            st.markdown("#### Application Schedule")
            for schedule in chem['application_schedule']:
                st.success(f"✓ {schedule}")
        
        if fert_type in ["Organic", "Both"]:
            st.markdown("### Organic Fertilizers")
            org = crop_info["organic_fertilizers"]
            fym = org['fym_tons'].split('-')[-1]
            st.write(f"**FYM:** {float(fym) * area:.1f} tons")
            if 'vermicompost_kg' in org:
                vermi = org['vermicompost_kg'].split('-')[-1]
                st.write(f"**Vermicompost:** {float(vermi) * area:.0f} kg")
        
        log_activity(user['id'], "Seed Calculation", crop, area, {"method": method})

def show_live_market_prices():
    """Live Market Prices with CEDA Integration"""
    st.markdown("### Live Market Prices")
    user = st.session_state.user_data
    
    tab1, tab2, tab3 = st.tabs(["Real-Time Prices", "Price Trends", "Add Manual Price"])
    
    with tab1:
        st.markdown("### Check Real-Time Market Prices")
        
        col1, col2 = st.columns(2)
        with col1:
            commodity = st.selectbox("Select Commodity", list(CROP_DATABASE.keys()))
        with col2:
            district = st.selectbox("District", ["Maharashtra", user['district']], index=1)
        
        if st.button("Fetch Latest Prices from CEDA", type="primary", use_container_width=True):
            with st.spinner("Fetching real-time prices from CEDA Ashoka University..."):
                # Fetch from CEDA
                ceda_df, ceda_status = fetch_ceda_prices(commodity, district)
                
                if ceda_df is not None:
                    st.success(ceda_status)
                    
                    # Display CEDA data
                    st.markdown("#### CEDA Market Data")
                    st.dataframe(ceda_df, use_container_width=True)
                    
                    # Show statistics
                    if 'price' in ceda_df.columns:
                        try:
                            prices = pd.to_numeric(ceda_df['price'].str.replace('[^\d.]', '', regex=True), errors='coerce')
                            prices = prices.dropna()
                            
                            if len(prices) > 0:
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Average Price", f"₹{prices.mean():.0f}/quintal")
                                with col2:
                                    st.metric("Min Price", f"₹{prices.min():.0f}/quintal")
                                with col3:
                                    st.metric("Max Price", f"₹{prices.max():.0f}/quintal")
                                
                                # Price distribution chart
                                fig = px.histogram(prices, nbins=10, 
                                                 title=f"{commodity} Price Distribution",
                                                 labels={'value': 'Price (₹/quintal)', 'count': 'Frequency'})
                                st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.info("Price analysis not available")
                    
                    # CEDA Attribution
                    st.markdown('<div class="info-card">', unsafe_allow_html=True)
                    st.markdown("""
                    **Data Source:** Centre for Economic Data and Analysis (CEDA), Ashoka University
                    
                    CEDA provides economic data for research and non-commercial use. 
                    Learn more: https://ceda.ashoka.edu.in
                    
                    **Usage Compliance:**
                    - Non-commercial educational use
                    - Proper attribution provided
                    - Rate-limited respectful access
                    """)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.warning(ceda_status)
                    st.info("Showing typical price range from database")
        
        # Show database prices
        st.markdown("### Manual Market Prices (User Contributed)")
        manual_df = get_manual_prices(commodity=commodity, district=user['district'], days=30)
        
        if manual_df is not None:
            st.dataframe(manual_df, use_container_width=True)
            
            # Show latest price
            if len(manual_df) > 0:
                latest = manual_df.iloc[0]
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Latest Min Price", f"₹{latest['min_price']:,.0f}")
                with col2:
                    st.metric("Latest Max Price", f"₹{latest['max_price']:,.0f}")
                with col3:
                    st.metric("Latest Modal Price", f"₹{latest['modal_price']:,.0f}")
        else:
            # Show expected price from database
            crop_info = CROP_DATABASE[commodity]
            st.info(f"Expected price range: {crop_info['market_price_range']}")
        
        # Nearest mandis
        st.markdown("### Nearest APMC Markets")
        mandis = get_nearest_mandis(user['district'])
        for mandi in mandis:
            st.markdown(f"- {mandi}")
        
        # AI Price Analysis
        if st.button("Get AI Price Analysis", use_container_width=True):
            with st.spinner("Analyzing prices..."):
                prompt = f"""Analyze current market situation for {commodity} in {user['district']}, Maharashtra:
                
                Provide:
                1. Current price trend (rising/falling/stable)
                2. Factors affecting current prices
                3. Short-term forecast (next 2-4 weeks)
                4. Best time to sell in current scenario
                5. Price negotiation tips for farmers
                
                Be specific and actionable."""
                
                response = get_ai_response(prompt)
                st.markdown('<div class="ai-card">', unsafe_allow_html=True)
                st.markdown("### AI Price Analysis")
                st.markdown(response)
                st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### Price Trends & History")
        
        commodity_trend = st.selectbox("Select Commodity for Trends", list(CROP_DATABASE.keys()), key="trend_commodity")
        
        # Get historical data
        trend_df = get_manual_prices(commodity=commodity_trend, district=user['district'], days=90)
        
        if trend_df is not None and len(trend_df) > 1:
            # Convert price_date to datetime
            trend_df['price_date'] = pd.to_datetime(trend_df['price_date'])
            trend_df = trend_df.sort_values('price_date')
            
            # Create line chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=trend_df['price_date'], y=trend_df['min_price'],
                                    mode='lines+markers', name='Min Price',
                                    line=dict(color='red', width=2)))
            fig.add_trace(go.Scatter(x=trend_df['price_date'], y=trend_df['modal_price'],
                                    mode='lines+markers', name='Modal Price',
                                    line=dict(color='green', width=3)))
            fig.add_trace(go.Scatter(x=trend_df['price_date'], y=trend_df['max_price'],
                                    mode='lines+markers', name='Max Price',
                                    line=dict(color='blue', width=2)))
            
            fig.update_layout(title=f"{commodity_trend} Price Trends (Last 90 Days)",
                            xaxis_title="Date",
                            yaxis_title="Price (₹/quintal)",
                            hovermode='x unified')
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Price statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_modal = trend_df['modal_price'].mean()
                st.metric("Average Modal Price", f"₹{avg_modal:,.0f}")
            with col2:
                price_change = trend_df['modal_price'].iloc[-1] - trend_df['modal_price'].iloc[0]
                st.metric("Price Change", f"₹{price_change:,.0f}", 
                         delta=f"{(price_change/trend_df['modal_price'].iloc[0]*100):.1f}%")
            with col3:
                volatility = trend_df['modal_price'].std()
                st.metric("Price Volatility", f"₹{volatility:,.0f}")
        else:
            st.info("Not enough historical data for trends. Add manual prices to see trends.")
    
    with tab3:
        st.markdown("### Add Manual Market Price")
        st.info("Help the community by adding latest prices from your local mandi")
        
        with st.form("add_manual_price"):
            col1, col2 = st.columns(2)
            
            with col1:
                price_district = st.selectbox("District", list(MAHARASHTRA_LOCATIONS.keys()))
                mandis = get_nearest_mandis(price_district)
                market_name = st.selectbox("Market/Mandi", mandis)
                price_commodity = st.selectbox("Commodity", list(CROP_DATABASE.keys()))
            
            with col2:
                min_price = st.number_input("Minimum Price (₹/quintal)", min_value=0, value=1000, step=50)
                max_price = st.number_input("Maximum Price (₹/quintal)", min_value=0, value=1500, step=50)
                modal_price = st.number_input("Modal/Average Price (₹/quintal)", min_value=0, value=1250, step=50)
            
            arrival_quantity = st.text_input("Arrival Quantity (optional)", placeholder="e.g., 100 quintals")
            price_date = st.date_input("Price Date", value=datetime.now())
            
            submitted = st.form_submit_button("Add Price Data", use_container_width=True, type="primary")
            
            if submitted:
                if min_price > max_price:
                    st.error("Minimum price cannot be greater than maximum price")
                elif modal_price < min_price or modal_price > max_price:
                    st.error("Modal price should be between minimum and maximum price")
                else:
                    add_manual_price(
                        price_district, market_name, price_commodity,
                        min_price, max_price, modal_price,
                        arrival_quantity, price_date, user['id']
                    )
                    st.success("Price data added successfully! Thank you for contributing.")
                    log_activity(user['id'], "Price Data Added", price_commodity, 0,
                               {"market": market_name, "modal_price": modal_price})
                    st.rerun()

def show_complete_crop_guide():
    """Complete crop cultivation guide"""
    st.markdown("### Complete Crop Guide")
    
    crop_name = st.selectbox("Select Crop for Detailed Guide", list(CROP_DATABASE.keys()))
    crop = CROP_DATABASE[crop_name]
    
    st.markdown(f"# {crop_name}")
    
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
    
    # Detailed practices
    if 'detailed_practices' in crop:
        practices = crop['detailed_practices']
        
        tabs = st.tabs(list(practices.keys()))
        
        for idx, (practice_name, steps) in enumerate(practices.items()):
            with tabs[idx]:
                st.markdown(f"### {practice_name.replace('_', ' ').title()}")
                for step_idx, step in enumerate(steps, 1):
                    st.markdown(f"**Step {step_idx}:** {step}")
    
    # Growth stages
    if 'critical_growth_stages' in crop:
        st.markdown("## Critical Growth Stages")
        for stage in crop['critical_growth_stages']:
            with st.expander(f"{stage['stage']} - Days {stage['days']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Water Need:** {stage['water_need']}")
                with col2:
                    st.write(f"**Nutrients:** {stage['nutrients']}")

def show_profit_calculator():
    """Profit Calculator"""
    st.markdown("### Profit & ROI Calculator")
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
    
    if st.button("Calculate Profit", type="primary"):
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
            st.success(f"Profitable! ROI: {roi:.1f}%")
        else:
            st.error("Loss projected")
        
        log_activity(user['id'], "Profit Calculation", crop, area, 
                    {"cost": total_cost, "profit": profit})

def show_ai_disease_diagnosis():
    """AI Disease Diagnosis"""
    st.markdown("### AI Disease & Pest Diagnosis")
    
    col1, col2 = st.columns(2)
    with col1:
        crop_name = st.selectbox("Select Crop", list(CROP_DATABASE.keys()))
    with col2:
        st.info("Be specific about symptoms for accurate diagnosis")
    
    symptoms = st.text_area(
        "Describe the symptoms:",
        placeholder="E.g., Yellow spots on leaves, wilting stems...",
        height=150
    )
    
    if st.button("Diagnose", type="primary", use_container_width=True):
        if symptoms:
            with st.spinner("Analyzing symptoms..."):
                prompt = f"""As a plant pathologist, diagnose this issue:

Crop: {crop_name}
Symptoms: {symptoms}

Provide:
1. Most likely disease/pest (with confidence level)
2. Detailed symptoms to confirm
3. Treatment recommendations (organic and chemical)
4. Prevention measures
5. Expected recovery time

Be specific and actionable."""

                client = get_anthropic_client()
                if client:
                    response = get_ai_response(prompt)
                    st.markdown('<div class="ai-card">', unsafe_allow_html=True)
                    st.markdown("### AI Diagnosis")
                    st.markdown(response)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    log_activity(st.session_state.user_data['id'], "Disease Diagnosis", 
                               crop_name, 0, {"symptoms": symptoms})
        else:
            st.warning("Please describe the symptoms")

def show_activity_history():
    """Activity History"""
    st.markdown("### Activity History")
    user = st.session_state.user_data
    
    activities = get_user_activities(user['id'], limit=50)
    
    if activities:
        df = pd.DataFrame(activities, columns=['Activity', 'Crop', 'Area', 'Data', 'Date'])
        st.dataframe(df, use_container_width=True)
        
        # Activity summary
        st.markdown("### Activity Summary")
        activity_counts = df['Activity'].value_counts()
        fig = px.bar(x=activity_counts.index, y=activity_counts.values,
                    labels={'x': 'Activity Type', 'y': 'Count'},
                    title="Activity Distribution")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No activities yet")

if __name__ == "__main__":
    main()