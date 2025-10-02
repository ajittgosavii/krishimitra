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
    page_title="KrishiMitra Maharashtra - Complete System",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (keeping original)
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E7D32;
        text-align: center;
        padding: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #558B2F;
        font-weight: bold;
        margin-top: 1rem;
    }
    .info-card {
        background-color: #F1F8E9;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        margin: 1rem 0;
    }
    .price-card {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .fertilizer-card {
        background-color: #FFF3E0;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #FF9800;
        margin: 0.5rem 0;
    }
    .location-card {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2196F3;
        margin: 0.5rem 0;
    }
    .notification-card {
        background-color: #F3E5F5;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #9C27B0;
        margin: 0.5rem 0;
    }
    .marketplace-card {
        background-color: #FFF8E1;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #FFA000;
        margin: 1rem 0;
    }
    .bid-card {
        background-color: #E1F5FE;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #0288D1;
        margin: 0.5rem 0;
    }
    .ceda-attribution {
        background-color: #E8EAF6;
        padding: 0.8rem;
        border-radius: 5px;
        border-left: 4px solid #3F51B5;
        margin: 0.5rem 0;
        font-size: 0.9em;
    }
    </style>
    """, unsafe_allow_html=True)

# ====================
# CEDA INTEGRATION
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
    """
    Fetch agricultural prices from CEDA Ashoka University
    COMPLIANCE: Non-commercial use with proper attribution
    """
    try:
        time.sleep(2)  # Rate limiting
        
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
# MAHARASHTRA LOCATIONS (Original - keeping all 36 districts)
# ====================
MAHARASHTRA_LOCATIONS = {
    "Pune": {
        "tehsils": {
            "Pune City": ["Shivajinagar", "Kothrud", "Hadapsar", "Yerawada", "Aundh", "Deccan", "Parvati", "Warje", "Karve Nagar"],
            "Haveli": ["Phursungi", "Manjri", "Uruli Kanchan", "Wagholi", "Lohegaon", "Wadki", "Phursungi", "Handewadi"],
            "Mulshi": ["Paud", "Pirangut", "Lavale", "Mulshi", "Tamhini", "Panshet", "Varasgaon", "Pabe"],
            "Maval": ["Talegaon", "Vadgaon Maval", "Kamshet", "Lonavala", "Khandala", "Karla", "Bhaje"],
            "Bhor": ["Bhor", "Nasrapur", "Velhe", "Yavat", "Bhalgudi", "Nasrapur", "Morgaon"],
            "Purandhar": ["Saswad", "Jejuri", "Pargaon", "Narayanpur", "Rajewadi", "Dive", "Nimgaon"],
            "Baramati": ["Baramati", "Morgaon", "Bhigwan", "Kurkumbh", "Malshiras", "Supa", "Indapur"],
            "Indapur": ["Indapur", "Bhigwan", "Akluj", "Nimgaon", "Walchandnagar", "Kalas", "Morgaon"],
            "Daund": ["Daund", "Kurkundi", "Yevat", "Patas", "Supa", "Loni Kalbhor", "Ranjangaon"],
            "Shirur": ["Shirur", "Shikrapur", "Kendal", "Pabal", "Ranjangaon", "Talegaon Dhamdhere", "Nhavara"],
            "Khed": ["Rajgurunagar", "Chakan", "Manchar", "Kusgaon", "Kendal", "Alandi", "Talegaon Dabhade"],
            "Junnar": ["Junnar", "Narayangaon", "Otur", "Alephata", "Ghodegaon", "Manchar", "Rajur"],
            "Ambegaon": ["Ghodegaon", "Manchar", "Bhigwan", "Pargaon", "Kalamb", "Jambhul", "Khed"]
        }
    },
    "Mumbai Suburban": {
        "tehsils": {
            "Kurla": ["Kurla East", "Kurla West", "Chunabhatti", "Tilak Nagar", "Vidyavihar", "Ghatkopar"],
            "Andheri": ["Andheri East", "Andheri West", "Jogeshwari", "Vile Parle", "Santacruz", "Goregaon"],
            "Borivali": ["Borivali East", "Borivali West", "Kandivali", "Malad", "Dahisar", "Mira Road"]
        }
    },
    "Nagpur": {
        "tehsils": {
            "Nagpur Urban": ["Dharampeth", "Sadar", "Hingna", "Nandanvan", "Sitabuldi", "West Nagpur", "East Nagpur"],
            "Nagpur Rural": ["Kalmeshwar", "Kamptee", "Ramtek", "Parseoni", "Savner", "Katol", "Narkhed"],
            "Umred": ["Umred", "Khapa", "Bhiwapur", "Kuhi", "Mauda", "Dhamangaon"],
            "Kalameshwar": ["Kalameshwar", "Mouza", "Parseoni", "Savner", "Kalmeshwar Rural"],
            "Hingna": ["Hingna", "Khapa", "Mauda", "Narkhed", "Hingna Rural"],
            "Kamptee": ["Kamptee", "Nara", "Parseoni", "Katol", "Kamptee Cantt"],
            "Mouda": ["Mouda", "Saoner", "Ramtek", "Parseoni", "Mauda"],
            "Parseoni": ["Parseoni", "Kamptee", "Katol", "Ramtek", "Parseoni Rural"]
        }
    },
    "Nashik": {
        "tehsils": {
            "Nashik": ["Nashik Road", "Panchavati", "Satpur", "Deolali", "College Road", "Ashok Stambh", "Nashik MIDC"],
            "Igatpuri": ["Igatpuri", "Ghoti", "Dindori", "Trimbakeshwar", "Surgana", "Igatpuri Hill"],
            "Sinnar": ["Sinnar", "Malegaon", "Nandgaon", "Chandwad", "Dindori", "Sinnar MIDC"],
            "Niphad": ["Niphad", "Dindori", "Malegaon", "Vani", "Nandgaon", "Niphad Rural"],
            "Dindori": ["Dindori", "Peth", "Niphad", "Kalwan", "Surgana", "Dindori Forest"],
            "Trimbakeshwar": ["Trimbak", "Anjaneri", "Panchvati", "Igatpuri", "Trimbak Temple"],
            "Kalwan": ["Kalwan", "Deola", "Surgana", "Nandgaon", "Kalwan Rural"],
            "Deola": ["Deola", "Kalwan", "Chandwad", "Niphad", "Deola Station"],
            "Surgana": ["Surgana", "Kalwan", "Peth", "Dindori", "Surgana Tribal"],
            "Malegaon": ["Malegaon", "Nandgaon", "Sinnar", "Satana", "Malegaon Camp"],
            "Nandgaon": ["Nandgaon", "Chandwad", "Malegaon", "Yeola", "Nandgaon Station"]
        }
    },
    "Thane": {
        "tehsils": {
            "Thane": ["Naupada", "Kopri", "Vartak Nagar", "Wagle Estate", "Ghodbunder", "Majiwada", "Pokhran"],
            "Kalyan": ["Kalyan East", "Kalyan West", "Dombivli East", "Dombivli West", "Ulhasnagar", "Titwala"],
            "Bhiwandi": ["Bhiwandi", "Kalyan", "Nizampur", "Anjur", "Padgha", "Bhiwandi MIDC"],
            "Shahapur": ["Shahapur", "Asangaon", "Atgaon", "Vashind", "Tokawade", "Tisgaon"],
            "Dahanu": ["Dahanu", "Bordi", "Gholvad", "Zai", "Kasa", "Dahanu Beach"],
            "Vikramgad": ["Vikramgad", "Jawhar", "Mokhada", "Vada", "Vikramgad Fort"],
            "Palghar": ["Palghar", "Vasai", "Nalasopara", "Virar", "Boisar", "Manor"],
            "Vasai": ["Vasai East", "Vasai West", "Nalasopara East", "Nalasopara West", "Virar East", "Virar West"]
        }
    },
    "Aurangabad": {
        "tehsils": {
            "Aurangabad": ["Aurangabad City", "Paithan", "Gangapur", "Vaijapur", "Aurangabad Cantt"],
            "Kannad": ["Kannad", "Paithan", "Sillod", "Phulambri", "Kannad Station"],
            "Sillod": ["Sillod", "Kannad", "Vaijapur", "Soegaon", "Sillod Rural"],
            "Paithan": ["Paithan", "Aurangabad", "Gangapur", "Phulambri", "Paithan Dam"],
            "Gangapur": ["Gangapur", "Paithan", "Vaijapur", "Khultabad", "Gangapur Dam"],
            "Vaijapur": ["Vaijapur", "Gangapur", "Sillod", "Khultabad", "Vaijapur Station"]
        }
    },
    "Solapur": {
        "tehsils": {
            "Solapur North": ["Solapur City", "Akluj", "Barshi", "Karmala", "Solapur MIDC"],
            "Solapur South": ["Mohol", "Pandharpur", "Mangalwedha", "Sangole", "Solapur Station"],
            "Akkalkot": ["Akkalkot", "Solapur", "Mohol", "Malshiras", "Akkalkot Temple"],
            "Barshi": ["Barshi", "Karmala", "Solapur", "Pandharpur", "Barshi Town"],
            "Pandharpur": ["Pandharpur", "Mangalwedha", "Mohol", "Sangole", "Pandharpur Temple"]
        }
    },
    "Kolhapur": {
        "tehsils": {
            "Kolhapur": ["Kolhapur City", "Karveer", "Panhala", "Shahuwadi", "Kolhapur Palace"],
            "Panhala": ["Panhala", "Kolhapur", "Shahuwadi", "Bavda", "Panhala Fort"],
            "Kagal": ["Kagal", "Hatkanangle", "Shirol", "Bavda", "Kagal MIDC"],
            "Ichalkaranji": ["Ichalkaranji", "Hatkanangle", "Shirol", "Kagal", "Ichalkaranji Town"]
        }
    },
    "Ahmednagar": {
        "tehsils": {
            "Ahmednagar": ["Ahmednagar City", "Nagar", "Sangamner", "Rahuri", "Ahmednagar Cantt"],
            "Sangamner": ["Sangamner", "Akole", "Kopargaon", "Rahuri", "Sangamner Town"],
            "Kopargaon": ["Kopargaon", "Sangamner", "Shrirampur", "Rahata", "Shirdi"],
            "Rahuri": ["Rahuri", "Sangamner", "Nevasa", "Kopargaon", "Rahuri Factory"]
        }
    },
    "Satara": {
        "tehsils": {
            "Satara": ["Satara City", "Karad", "Koregaon", "Wai", "Satara Station"],
            "Karad": ["Karad", "Satara", "Patan", "Koregaon", "Karad Town"],
            "Wai": ["Wai", "Mahabaleshwar", "Panchgani", "Satara", "Wai Town"],
            "Mahabaleshwar": ["Mahabaleshwar", "Panchgani", "Wai", "Pratapgad", "Mahabaleshwar Hill"]
        }
    },
    "Sangli": {
        "tehsils": {
            "Sangli": ["Sangli City", "Miraj", "Tasgaon", "Jat", "Sangli MIDC"],
            "Miraj": ["Miraj", "Sangli", "Tasgaon", "Kavathemahankal", "Miraj Station"],
            "Islampur": ["Islampur", "Walwa", "Palus", "Khanapur", "Islampur Sugar"]
        }
    },
    "Ratnagiri": {
        "tehsils": {
            "Ratnagiri": ["Ratnagiri City", "Mandangad", "Dapoli", "Chiplun", "Ratnagiri Port"],
            "Dapoli": ["Dapoli", "Mandangad", "Khed", "Ratnagiri", "Dapoli Beach"],
            "Chiplun": ["Chiplun", "Khed", "Ratnagiri", "Guhagar", "Chiplun Station"]
        }
    },
    "Sindhudurg": {
        "tehsils": {
            "Sindhudurg": ["Sindhudurg City", "Malwan", "Kudal", "Vengurla", "Sindhudurg Fort"],
            "Kudal": ["Kudal", "Sawantwadi", "Vengurla", "Malwan", "Kudal Station"],
            "Malwan": ["Malwan", "Devgad", "Kankavli", "Sindhudurg", "Malwan Beach"]
        }
    },
    "Amravati": {
        "tehsils": {
            "Amravati": ["Amravati City", "Morshi", "Daryapur", "Chandurbazar", "Amravati Cantt"],
            "Morshi": ["Morshi", "Warud", "Chandurbazar", "Daryapur", "Morshi Town"]
        }
    },
    "Akola": {
        "tehsils": {
            "Akola": ["Akola City", "Barshitakli", "Akot", "Telhara", "Akola Station"],
            "Akot": ["Akot", "Akola", "Barshitakli", "Telhara", "Akot Town"]
        }
    },
    "Washim": {
        "tehsils": {
            "Washim": ["Washim City", "Karanja", "Malegaon", "Risod", "Washim Station"],
            "Karanja": ["Karanja", "Washim", "Malegaon", "Risod", "Karanja Lad"]
        }
    },
    "Buldhana": {
        "tehsils": {
            "Buldhana": ["Buldhana City", "Malkapur", "Chikhli", "Mehkar", "Buldhana Station"],
            "Malkapur": ["Malkapur", "Buldhana", "Chikhli", "Mehkar", "Malkapur Camp"]
        }
    },
    "Yavatmal": {
        "tehsils": {
            "Yavatmal": ["Yavatmal City", "Pusad", "Darwha", "Digras", "Yavatmal Station"],
            "Pusad": ["Pusad", "Yavatmal", "Darwha", "Digras", "Pusad Town"]
        }
    },
    "Wardha": {
        "tehsils": {
            "Wardha": ["Wardha City", "Hinganghat", "Arvi", "Deoli", "Wardha Station"],
            "Hinganghat": ["Hinganghat", "Wardha", "Arvi", "Deoli", "Hinganghat Town"]
        }
    },
    "Chandrapur": {
        "tehsils": {
            "Chandrapur": ["Chandrapur City", "Warora", "Ballarpur", "Brahmapuri", "Chandrapur Station"],
            "Warora": ["Warora", "Chandrapur", "Ballarpur", "Brahmapuri", "Warora Power"]
        }
    },
    "Gadchiroli": {
        "tehsils": {
            "Gadchiroli": ["Gadchiroli City", "Dhanora", "Chamorshi", "Armori", "Gadchiroli Forest"],
            "Dhanora": ["Dhanora", "Gadchiroli", "Chamorshi", "Armori", "Dhanora Tribal"]
        }
    },
    "Gondia": {
        "tehsils": {
            "Gondia": ["Gondia City", "Tirora", "Goregaon", "Salekasa", "Gondia Station"],
            "Tirora": ["Tirora", "Gondia", "Goregaon", "Salekasa", "Tirora Town"]
        }
    },
    "Bhandara": {
        "tehsils": {
            "Bhandara": ["Bhandara City", "Tumsar", "Pauni", "Mohadi", "Bhandara Station"],
            "Tumsar": ["Tumsar", "Bhandara", "Pauni", "Mohadi", "Tumsar Town"]
        }
    },
    "Jalgaon": {
        "tehsils": {
            "Jalgaon": ["Jalgaon City", "Bhusawal", "Amalner", "Chopda", "Jalgaon Station"],
            "Bhusawal": ["Bhusawal", "Jalgaon", "Amalner", "Chopda", "Bhusawal Junction"]
        }
    },
    "Dhule": {
        "tehsils": {
            "Dhule": ["Dhule City", "Sakri", "Shirpur", "Sindkheda", "Dhule Station"],
            "Shirpur": ["Shirpur", "Dhule", "Sakri", "Sindkheda", "Shirpur Gold"]
        }
    },
    "Nandurbar": {
        "tehsils": {
            "Nandurbar": ["Nandurbar City", "Shahada", "Taloda", "Akkalkuwa", "Nandurbar Station"],
            "Shahada": ["Shahada", "Nandurbar", "Taloda", "Akkalkuwa", "Shahada Town"]
        }
    },
    "Osmanabad": {
        "tehsils": {
            "Osmanabad": ["Osmanabad City", "Tuljapur", "Bhum", "Paranda", "Osmanabad Station"],
            "Tuljapur": ["Tuljapur", "Osmanabad", "Bhum", "Paranda", "Tuljapur Temple"]
        }
    },
    "Latur": {
        "tehsils": {
            "Latur": ["Latur City", "Nilanga", "Ausa", "Chakur", "Latur Station"],
            "Nilanga": ["Nilanga", "Latur", "Ausa", "Chakur", "Nilanga Town"]
        }
    },
    "Beed": {
        "tehsils": {
            "Beed": ["Beed City", "Ambajogai", "Parli", "Georai", "Beed Station"],
            "Ambajogai": ["Ambajogai", "Beed", "Parli", "Georai", "Ambajogai Town"]
        }
    },
    "Parbhani": {
        "tehsils": {
            "Parbhani": ["Parbhani City", "Purna", "Pathri", "Jintur", "Parbhani Station"],
            "Purna": ["Purna", "Parbhani", "Pathri", "Jintur", "Purna Town"]
        }
    },
    "Jalna": {
        "tehsils": {
            "Jalna": ["Jalna City", "Bhokardan", "Ambad", "Badnapur", "Jalna Station"],
            "Ambad": ["Ambad", "Jalna", "Bhokardan", "Badnapur", "Ambad Town"]
        }
    },
    "Hingoli": {
        "tehsils": {
            "Hingoli": ["Hingoli City", "Kalamnuri", "Sengaon", "Basmat", "Hingoli Station"],
            "Kalamnuri": ["Kalamnuri", "Hingoli", "Sengaon", "Basmat", "Kalamnuri Town"]
        }
    },
    "Nanded": {
        "tehsils": {
            "Nanded": ["Nanded City", "Kinwat", "Hadgaon", "Mukhed", "Nanded Station"],
            "Kinwat": ["Kinwat", "Nanded", "Hadgaon", "Mukhed", "Kinwat Town"]
        }
    },
    "Palghar": {
        "tehsils": {
            "Palghar": ["Palghar City", "Vasai", "Virar", "Boisar", "Manor", "Palghar Station"],
            "Vasai": ["Vasai East", "Vasai West", "Nalasopara", "Virar", "Vasai Road"]
        }
    },
    "Raigad": {
        "tehsils": {
            "Raigad": ["Alibag", "Panvel", "Karjat", "Khalapur", "Mangaon", "Pen"],
            "Panvel": ["Panvel", "New Panvel", "Kharghar", "Kamothe", "Kalamboli"]
        }
    }
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

# ====================
# CROP DATABASE (Original - all 12 crops)
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
        "chemical_fertilizers": {
            "urea_kg": "65",
            "dap_kg": "50",
            "mop_kg": "20",
            "total_npk": "48:24:16 kg/acre",
            "application_schedule": [
                "Basal: 50% N + 100% P + 100% K at sowing",
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
        "chemical_fertilizers": {
            "urea_kg": "87",
            "dap_kg": "65",
            "mop_kg": "25",
            "total_npk": "48:24:24 kg/acre",
            "application_schedule": [
                "Basal: 25% N + 100% P + 50% K at sowing",
                "First: 25% N + 50% K at square formation (30-35 days)"
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
    "Sugarcane": {
        "seed_rate_kg_per_acre": "12000-14000",
        "spacing": "90cm x 45cm",
        "water_requirement": "607-1012 mm",
        "duration_days": "300-365",
        "expected_yield_tons": "32-40",
        "best_season": "Feb-Mar (spring), Sep-Oct (autumn)",
        "soil_type": "Deep loam to clay loam",
        "market_price_range": "₹280-320/quintal",
        "chemical_fertilizers": {
            "urea_kg": "220",
            "dap_kg": "110",
            "mop_kg": "40",
            "total_npk": "101:40:40 kg/acre",
            "application_schedule": [
                "Basal: 25% N + 100% P + 50% K at planting",
                "30 days: 25% N + 50% K"
            ]
        },
        "organic_fertilizers": {
            "fym_tons": "8-10",
            "pressmud_tons": "3-4",
            "vermicompost_kg": "1000-1200",
            "biofertilizers": "Azospirillum + PSB + Trichoderma @ 2 kg each",
            "application_schedule": [
                "FYM + Pressmud: Apply in trenches before planting",
                "Vermicompost: Mix in trenches"
            ]
        },
        "methods": [
            "Trench planting: 30cm deep trenches, 20-25% higher yield",
            "Ring pit method: 75% less seed material, 40% water saving"
        ],
        "tips": [
            "Use healthy setts from 6-8 month old crop",
            "Treat setts with fungicide and insecticide"
        ]
    },
    "Maize": {
        "seed_rate_kg_per_acre": "8-10",
        "spacing": "60cm x 20cm",
        "water_requirement": "202-324 mm",
        "duration_days": "80-110",
        "expected_yield_tons": "2.4-3.2",
        "best_season": "Kharif & Rabi",
        "soil_type": "Well-drained loamy soil",
        "market_price_range": "₹1800-2200/quintal",
        "chemical_fertilizers": {
            "urea_kg": "87",
            "dap_kg": "65",
            "mop_kg": "17",
            "total_npk": "48:24:16 kg/acre",
            "application_schedule": [
                "Basal: 25% N + 100% P + 100% K at sowing",
                "First: 50% N at knee-high (25-30 days)"
            ]
        },
        "organic_fertilizers": {
            "fym_tons": "5-6",
            "vermicompost_kg": "600-800",
            "poultry_manure_kg": "400-500",
            "biofertilizers": "Azospirillum + PSB @ 2 kg each",
            "application_schedule": [
                "FYM/Poultry: Apply 2-3 weeks before sowing",
                "Vermicompost: Mix at final land preparation"
            ]
        },
        "methods": [
            "Hybrid seeds yield 30-40% more than composites",
            "Drip irrigation with fertigation increases efficiency by 40-60%"
        ],
        "tips": [
            "Apply 4-5 irrigations at critical stages",
            "Earthing up at 30-35 days prevents lodging"
        ]
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
        "chemical_fertilizers": {
            "urea_kg": "108",
            "dap_kg": "109",
            "mop_kg": "33",
            "total_npk": "60:40:40 kg/acre",
            "application_schedule": [
                "Basal: 50% N + 100% P + 50% K at transplanting",
                "30 days: 25% N + 25% K"
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
    "Potato": {
        "seed_rate_kg_per_acre": "800-1000",
        "spacing": "60cm x 20cm",
        "water_requirement": "202-283 mm",
        "duration_days": "90-120",
        "expected_yield_tons": "10-14",
        "best_season": "Rabi (October-November)",
        "soil_type": "Sandy loam with drainage",
        "market_price_range": "₹800-1500/quintal",
        "chemical_fertilizers": {
            "urea_kg": "87",
            "dap_kg": "87",
            "mop_kg": "33",
            "total_npk": "48:40:40 kg/acre",
            "application_schedule": [
                "Basal: 50% N + 100% P + 50% K at planting",
                "30 days: 25% N + 25% K at first earthing"
            ]
        },
        "organic_fertilizers": {
            "fym_tons": "6-8",
            "vermicompost_kg": "1000-1200",
            "neem_cake_kg": "100",
            "biofertilizers": "Azotobacter + PSB @ 2 kg each",
            "application_schedule": [
                "FYM: Apply 3-4 weeks before planting",
                "Vermicompost: Mix in furrows at planting"
            ]
        },
        "methods": [
            "Micro-tuber technology: 20-30% yield increase",
            "Ridge and furrow: Better drainage, easier harvest"
        ],
        "tips": [
            "Cut tubers with 2-3 eyes, cure 24-48 hours",
            "Earthing up 2-3 times prevents greening"
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
                "30 days: 25% N + 25% K"
            ]
        },
        "organic_fertilizers": {
            "fym_tons": "4-5",
            "vermicompost_kg": "600-800",
            "neem_cake_kg": "80-100",
            "biofertilizers": "Azospirillum + PSB @ 2 kg each",
            "application_schedule": [
                "FYM: Apply 3 weeks before transplanting",
                "Vermicompost: Mix in beds"
            ]
        },
        "methods": [
            "Raised bed: 15-20% yield increase",
            "Drip irrigation: 40% water saving"
        ],
        "tips": [
            "Transplant 45-50 day seedlings, 6-7mm thickness",
            "Apply sulfur for better pungency"
        ]
    },
    "Soybean": {
        "seed_rate_kg_per_acre": "30-32",
        "spacing": "45cm x 5cm",
        "water_requirement": "243-324 mm",
        "duration_days": "90-120",
        "expected_yield_tons": "0.6-0.8",
        "best_season": "Kharif (June-July)",
        "soil_type": "Well-drained loamy",
        "market_price_range": "₹3500-4500/quintal",
        "chemical_fertilizers": {
            "urea_kg": "22",
            "dap_kg": "54",
            "mop_kg": "17",
            "total_npk": "20:20:20 kg/acre",
            "application_schedule": [
                "Basal: 100% P + 100% K + 50% N at sowing",
                "Flowering: 50% N (30-35 days)"
            ]
        },
        "organic_fertilizers": {
            "fym_tons": "3-4",
            "vermicompost_kg": "400-500",
            "rhizobium": "200 gm per 10 kg seed",
            "biofertilizers": "Rhizobium + PSB @ 2 kg each",
            "application_schedule": [
                "FYM: Apply 2-3 weeks before sowing",
                "Rhizobium: Seed treatment mandatory"
            ]
        },
        "methods": [
            "Ridge and furrow for better drainage",
            "Seed inoculation with Rhizobium mandatory"
        ],
        "tips": [
            "Sow within first fortnight of June",
            "Rhizobium + fungicide seed treatment"
        ]
    },
    "Groundnut": {
        "seed_rate_kg_per_acre": "40-50",
        "spacing": "30cm x 10cm",
        "water_requirement": "202-283 mm",
        "duration_days": "120-140",
        "expected_yield_tons": "0.8-1.2",
        "best_season": "Kharif, Summer",
        "soil_type": "Sandy loam",
        "market_price_range": "₹5000-6000/quintal",
        "chemical_fertilizers": {
            "urea_kg": "22",
            "dap_kg": "43",
            "mop_kg": "13",
            "total_npk": "16:16:16 kg/acre",
            "application_schedule": [
                "Basal: 100% P + 100% K + 50% N",
                "30 days: 50% N"
            ]
        },
        "organic_fertilizers": {
            "fym_tons": "3-4",
            "gypsum_kg": "200",
            "vermicompost_kg": "400-500",
            "biofertilizers": "Rhizobium + PSB @ 2 kg each",
            "application_schedule": [
                "FYM: Apply 2-3 weeks before sowing",
                "Gypsum: Apply at flowering (35-40 days)"
            ]
        },
        "methods": [
            "Ridge and furrow improves pod filling",
            "Gypsum at flowering increases yield by 20%"
        ],
        "tips": [
            "Rhizobium + fungicide seed treatment",
            "Apply gypsum @ 200 kg/acre at flowering"
        ]
    },
    "Pomegranate": {
        "seed_rate_kg_per_acre": "445 plants",
        "spacing": "12ft x 9ft",
        "water_requirement": "810-1012 mm",
        "duration_days": "180-210",
        "expected_yield_tons": "6-8",
        "best_season": "Year-round with irrigation",
        "soil_type": "Well-drained loamy",
        "market_price_range": "₹4000-8000/quintal",
        "chemical_fertilizers": {
            "urea_kg": "200",
            "dap_kg": "150",
            "mop_kg": "100",
            "total_npk": "100:60:60 kg/acre/year",
            "application_schedule": [
                "Split in 4 doses",
                "Post-monsoon, flowering, fruit development, harvest"
            ]
        },
        "organic_fertilizers": {
            "fym_tons": "10-12",
            "vermicompost_kg": "1000-1200",
            "neem_cake_kg": "200",
            "biofertilizers": "Azotobacter + PSB @ 3 kg each",
            "application_schedule": [
                "FYM: Apply annually in two splits",
                "Vermicompost: Apply during flowering"
            ]
        },
        "methods": [
            "Drip irrigation with fertigation is standard",
            "Training and pruning for shape and yield"
        ],
        "tips": [
            "Maintain soil pH 6.5-7.5",
            "Regular pruning to maintain vigor"
        ]
    },
    "Chilli": {
        "seed_rate_kg_per_acre": "200-250 grams",
        "spacing": "60cm x 45cm",
        "water_requirement": "243-324 mm",
        "duration_days": "120-150",
        "expected_yield_tons": "2.4-3.2",
        "best_season": "Kharif & Rabi",
        "soil_type": "Well-drained loamy",
        "market_price_range": "₹8000-15000/quintal",
        "chemical_fertilizers": {
            "urea_kg": "108",
            "dap_kg": "87",
            "mop_kg": "33",
            "total_npk": "60:40:40 kg/acre",
            "application_schedule": [
                "Basal: 50% N + 100% P + 50% K",
                "30 days: 25% N + 25% K"
            ]
        },
        "organic_fertilizers": {
            "fym_tons": "6-8",
            "vermicompost_kg": "800-1000",
            "neem_cake_kg": "100-120",
            "biofertilizers": "Azotobacter + PSB @ 2 kg each",
            "application_schedule": [
                "FYM: Mix 2-3 weeks before transplanting",
                "Vermicompost: Apply in pits"
            ]
        },
        "methods": [
            "Raised bed planting for better drainage",
            "Drip irrigation + mulch: Water saving"
        ],
        "tips": [
            "Transplant 40-45 day old seedlings",
            "Provide stakes for support"
        ]
    }
}

# Original databases and data structures continue...
SEASONAL_CALENDAR = {
    "Kharif": {
        "description": "Monsoon crops sown with monsoon, harvested at end",
        "sowing_period": "June - August",
        "harvesting_period": "September - November",
        "characteristics": [
            "Warm weather and significant rainfall required",
            "Depends on monsoon rains",
            "Temperature: 25-35°C"
        ],
        "crops": {
            "Rice": {"sowing": "June-July", "harvesting": "Oct-Nov", "duration": "120-150 days"},
            "Cotton": {"sowing": "May-June", "harvesting": "Oct-Jan", "duration": "150-180 days"},
            "Soybean": {"sowing": "June-July", "harvesting": "Sep-Oct", "duration": "90-120 days"},
        }
    },
    "Rabi": {
        "description": "Winter crops sown in winter, harvested in spring",
        "sowing_period": "October - December",
        "harvesting_period": "March - May",
        "characteristics": [
            "Cool weather for growth, warm for ripening",
            "Needs irrigation",
            "Temperature: 10-25°C"
        ],
        "crops": {
            "Wheat": {"sowing": "Oct-Nov", "harvesting": "Mar-Apr", "duration": "110-130 days"},
            "Potato": {"sowing": "Oct-Nov", "harvesting": "Jan-Mar", "duration": "90-120 days"},
            "Onion": {"sowing": "Oct-Dec", "harvesting": "Mar-May", "duration": "120-150 days"},
        }
    },
    "Zaid": {
        "description": "Summer crops between Rabi and Kharif",
        "sowing_period": "March - May",
        "harvesting_period": "June - August",
        "characteristics": [
            "Short duration summer crops",
            "Irrigation throughout required",
            "Temperature: 25-40°C"
        ],
        "crops": {
            "Watermelon": {"sowing": "Feb-Mar", "harvesting": "May-Jun", "duration": "90-100 days"},
            "Cucumber": {"sowing": "Mar-Apr", "harvesting": "Jun-Jul", "duration": "60-70 days"},
        }
    }
}

DISEASE_DATABASE = {
    "Rice": [
        {"name": "Blast Disease", "symptoms": "Leaf spots, neck blast", "control": "Spray Tricyclazole 75% WP @ 60g/acre"},
        {"name": "Brown Plant Hopper", "symptoms": "Yellowing, hopper burn", "control": "Use Imidacloprid @ 20ml/acre"},
    ],
    "Wheat": [
        {"name": "Yellow Rust", "symptoms": "Yellow pustules in rows", "control": "Spray Propiconazole @ 100ml/acre"},
        {"name": "Aphids", "symptoms": "Sticky leaves, stunted growth", "control": "Use Dimethoate @ 200ml/acre"},
    ],
    "Cotton": [
        {"name": "Pink Bollworm", "symptoms": "Bored bolls, rosette flowers", "control": "Pheromone traps @ 5/acre"},
        {"name": "Whitefly", "symptoms": "Leaf yellowing, honeydew", "control": "Yellow sticky traps, Imidacloprid @ 40ml/acre"},
    ],
    "Tomato": [
        {"name": "Late Blight", "symptoms": "Brown water-soaked lesions", "control": "Mancozeb @ 400g/acre"},
        {"name": "Whitefly", "symptoms": "Yellowing, virus transmission", "control": "Yellow sticky traps @ 10/acre"},
    ],
    "Onion": [
        {"name": "Purple Blotch", "symptoms": "Purple spots on leaves", "control": "Mancozeb @ 400g/acre spray"},
        {"name": "Thrips", "symptoms": "Silver streaks on leaves", "control": "Fipronil @ 80ml/acre"},
    ]
}

GOVERNMENT_SCHEMES = {
    "PM-KISAN": {
        "name": "PM Kisan Samman Nidhi",
        "benefit": "₹6000/year in 3 installments",
        "eligibility": "All landholding farmers",
        "website": "https://pmkisan.gov.in/",
        "helpline": "011-24300606",
        "how_to_apply": "Visit pmkisan.gov.in, register with Aadhaar"
    },
    "PMFBY": {
        "name": "Pradhan Mantri Fasal Bima Yojana",
        "benefit": "Crop insurance at 2% (Kharif), 1.5% (Rabi)",
        "eligibility": "All farmers - landowners and tenants",
        "website": "https://pmfby.gov.in/",
        "helpline": "1800-180-1551",
        "how_to_apply": "Apply through banks or insurance companies"
    },
    "Soil Health Card": {
        "name": "Soil Health Card Scheme",
        "benefit": "Free soil testing every 2 years",
        "eligibility": "All farmers",
        "website": "https://soilhealth.dac.gov.in/",
        "helpline": "1800-180-1551",
        "how_to_apply": "Contact nearest Soil Testing Laboratory"
    },
    "KCC": {
        "name": "Kisan Credit Card",
        "benefit": "Easy credit at 4% interest",
        "eligibility": "Farmers with land records",
        "website": "Contact nearest bank",
        "helpline": "1800-180-1111",
        "how_to_apply": "Visit any bank with land documents"
    }
}

# Database functions (Original)
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
    
    c.execute('''CREATE TABLE IF NOT EXISTS transport_providers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  provider_name TEXT,
                  vehicle_type TEXT,
                  capacity TEXT,
                  rate_per_km REAL,
                  phone TEXT,
                  district TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS storage_facilities
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  facility_name TEXT,
                  storage_type TEXT,
                  capacity TEXT,
                  rate_per_quintal REAL,
                  location TEXT,
                  phone TEXT)''')
    
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
    query += " ORDER BY price_date DESC, updated_at DESC"
    c.execute(query, params)
    results = c.fetchall()
    conn.close()
    if results:
        return pd.DataFrame(results, columns=['district', 'market', 'commodity', 'min_price', 
                                               'max_price', 'modal_price', 'arrival_quantity', 
                                               'price_date', 'updated_at'])
    return None

def send_sms_notification(mobile, message):
    try:
        st.info(f"📱 SMS: {message[:50]}... to {mobile}")
        return True, "demo_message_id"
    except Exception as e:
        return False, str(e)

def send_whatsapp_notification(mobile, message):
    try:
        st.success(f"💬 WhatsApp: {message[:50]}... to {mobile}")
        return True, "demo_whatsapp_id"
    except Exception as e:
        return False, str(e)

AGMARKNET_COMMODITY_MAP = {
    "Rice": "Paddy(Dhan)(Common)",
    "Wheat": "Wheat",
    "Cotton": "Cotton",
    "Sugarcane": "Sugarcane",
    "Maize": "Maize",
    "Tomato": "Tomato",
    "Potato": "Potato",
    "Onion": "Onion",
    "Soybean": "Soyabean",
    "Groundnut": "Groundnut",
    "Pomegranate": "Pomegranate",
    "Chilli": "Green Chilli"
}

def fetch_agmarknet_prices(state, district, commodity):
    try:
        try:
            api_key = st.secrets["api_keys"]["data_gov_in"]
        except:
            return None, "API key not found in secrets"
        agmarknet_commodity = AGMARKNET_COMMODITY_MAP.get(commodity, commodity)
        url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
        params = {"api-key": api_key, "format": "json", "limit": 100}
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'records' in data and len(data['records']) > 0:
                df = pd.DataFrame(data['records'])
                filtered_df = df.copy()
                if 'commodity' in df.columns:
                    commodity_exact = filtered_df[filtered_df['commodity'] == agmarknet_commodity]
                    if len(commodity_exact) > 0:
                        filtered_df = commodity_exact
                    else:
                        commodity_partial = filtered_df[filtered_df['commodity'].str.contains(agmarknet_commodity, case=False, na=False)]
                        if len(commodity_partial) > 0:
                            filtered_df = commodity_partial
                if len(filtered_df) > 0:
                    if 'state' in filtered_df.columns:
                        state_filtered = filtered_df[filtered_df['state'].str.contains(state, case=False, na=False)]
                        if len(state_filtered) > 0:
                            filtered_df = state_filtered
                    if 'district' in filtered_df.columns:
                        district_filtered = filtered_df[filtered_df['district'].str.contains(district, case=False, na=False)]
                        if len(district_filtered) > 0:
                            filtered_df = district_filtered
                if len(filtered_df) > 0:
                    if 'arrival_date' in filtered_df.columns:
                        filtered_df = filtered_df.sort_values('arrival_date', ascending=False)
                    return filtered_df.head(20), f"Success: {len(filtered_df)} records found"
                else:
                    available_commodities = df['commodity'].unique()[:10] if 'commodity' in df.columns else []
                    return None, f"No match found. Available commodities in API: {', '.join(map(str, available_commodities))}"
            else:
                return None, "API has no data. The data.gov.in dataset may be empty or outdated."
        else:
            return None, f"HTTP {response.status_code}. API key may be invalid."
    except Exception as e:
        return None, f"Error: {str(e)}"

def fetch_weather_data(district, tehsil):
    try:
        try:
            api_key = st.secrets["api_keys"]["openweather"]
        except:
            api_key = "demo_key"
        location = f"{tehsil}, {district}, Maharashtra, India"
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": location, "appid": api_key, "units": "metric"}
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "temperature": data['main']['temp'],
                "humidity": data['main']['humidity'],
                "weather": data['weather'][0]['description'],
                "wind_speed": data['wind']['speed'],
                "pressure": data['main']['pressure']
            }
    except:
        pass
    return None

def get_nearest_mandis(district):
    mandis = {
        "Pune": ["Pune Market Yard", "Baramati APMC", "Daund APMC", "Junnar APMC", "Shirur APMC"],
        "Mumbai Suburban": ["Vashi APMC", "Turbhe Market", "Kalyan Market"],
        "Nagpur": ["Nagpur Cotton Market", "Kamptee APMC", "Katol Market", "Hingna APMC"],
        "Nashik": ["Nashik APMC", "Malegaon Market", "Sinnar APMC", "Lasalgaon APMC"],
        "Thane": ["Kalyan Market", "Bhiwandi APMC", "Palghar Market", "Dahanu APMC"],
        "Aurangabad": ["Aurangabad APMC", "Paithan Market", "Gangapur APMC"],
        "Solapur": ["Solapur APMC", "Pandharpur Market", "Barshi APMC"],
        "Kolhapur": ["Kolhapur APMC", "Kagal Market", "Ichalkaranji Market"],
        "Ahmednagar": ["Ahmednagar APMC", "Sangamner Market", "Kopargaon APMC"],
        "Satara": ["Satara APMC", "Karad Market", "Wai APMC"],
        "Sangli": ["Sangli APMC", "Miraj Market", "Islampur Market"],
        "Ratnagiri": ["Ratnagiri APMC", "Chiplun Market", "Dapoli APMC"],
        "Sindhudurg": ["Kudal APMC", "Malwan Market", "Vengurla Market"],
        "Amravati": ["Amravati Cotton Market", "Morshi APMC"],
        "Akola": ["Akola Cotton Market", "Akot APMC"],
        "Washim": ["Washim APMC", "Karanja Market"],
        "Buldhana": ["Buldhana Cotton Market", "Malkapur APMC"],
        "Yavatmal": ["Yavatmal Cotton Market", "Pusad APMC"],
        "Wardha": ["Wardha APMC", "Hinganghat Market"],
        "Chandrapur": ["Chandrapur APMC", "Warora Market"],
        "Gadchiroli": ["Gadchiroli APMC", "Dhanora Market"],
        "Gondia": ["Gondia APMC", "Tirora Market"],
        "Bhandara": ["Bhandara APMC", "Tumsar Market"],
        "Jalgaon": ["Jalgaon APMC", "Bhusawal Market"],
        "Dhule": ["Dhule APMC", "Shirpur Market"],
        "Nandurbar": ["Nandurbar APMC", "Shahada Market"],
        "Osmanabad": ["Osmanabad APMC", "Tuljapur Market"],
        "Latur": ["Latur APMC", "Nilanga Market"],
        "Beed": ["Beed APMC", "Ambajogai Market"],
        "Parbhani": ["Parbhani APMC", "Purna Market"],
        "Jalna": ["Jalna APMC", "Ambad Market"],
        "Hingoli": ["Hingoli APMC", "Kalamnuri Market"],
        "Nanded": ["Nanded APMC", "Kinwat Market"],
        "Palghar": ["Palghar APMC", "Vasai Market", "Virar Market"],
        "Raigad": ["Alibag APMC", "Panvel Market", "Karjat Market"]
    }
    return mandis.get(district, ["Contact District Agriculture Office"])

def generate_sample_prices(crop_name):
    import random
    dates = [datetime.now() - timedelta(days=x) for x in range(30, 0, -1)]
    base_price = random.randint(1500, 3500)
    prices = [base_price + random.randint(-300, 400) for _ in dates]
    return pd.DataFrame({'Date': dates, 'Price (₹/quintal)': prices})

# Main application
def main():
    init_database()
    st.markdown('<div class="main-header">🌾 KrishiMitra Maharashtra</div>', unsafe_allow_html=True)
    st.markdown("### संपूर्ण कृषी व्यवस्थापन प्रणाली | Complete Agriculture Management System")
    
    if st.session_state.user_data is None:
        show_auth_page()
    else:
        show_main_app()

def show_auth_page():
    """Authentication page - COMPLETE ORIGINAL"""
    tab1, tab2 = st.tabs(["🔐 Login / प्रवेश", "📝 Register / नोंदणी"])
    
    with tab1:
        st.markdown("### Login / प्रवेश करा")
        username = st.text_input("Username / वापरकर्ता नाव", key="login_user")
        password = st.text_input("Password / पासवर्ड", type="password", key="login_pass")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Login / प्रवेश", type="primary", use_container_width=True):
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
                        st.error("Invalid username or password")
                else:
                    st.warning("Please fill all fields")
    
    with tab2:
        st.markdown("### Create Account / नवीन खाते")
        col1, col2 = st.columns(2)
        with col1:
            new_username = st.text_input("Username", key="reg_user")
            new_password = st.text_input("Password (min 6 chars)", type="password", key="reg_pass")
            full_name = st.text_input("Full Name / पूर्ण नाव", key="reg_name")
            mobile = st.text_input("Mobile (10 digits)", key="reg_mobile")
        with col2:
            email = st.text_input("Email (Optional)", key="reg_email")
            user_type = st.selectbox("I am a / मी आहे", 
                                    ["Farmer / शेतकरी", "Buyer/Trader / खरेदीदार", "Transport Provider / वाहतूक"], 
                                    key="reg_type")
            farm_size = st.number_input("Farm Size (Acres)", min_value=0.1, value=1.0, step=0.5, key="reg_size")
        
        st.markdown("---")
        st.markdown("### 📍 Location Details / स्थान तपशील")
        col1, col2, col3 = st.columns(3)
        with col1:
            district = st.selectbox("District / जिल्हा", 
                                   ["Select District"] + list(MAHARASHTRA_LOCATIONS.keys()), 
                                   key="reg_dist")
        with col2:
            tehsil = None
            if district and district != "Select District":
                tehsils = list(MAHARASHTRA_LOCATIONS[district]["tehsils"].keys())
                tehsil = st.selectbox("Tehsil / तालुका", 
                                     ["Select Tehsil"] + tehsils, 
                                     key="reg_teh")
            else:
                st.selectbox("Tehsil / तालुका", ["First select district"], disabled=True, key="reg_teh_disabled")
        with col3:
            village = None
            if district and district != "Select District" and tehsil and tehsil != "Select Tehsil":
                villages = MAHARASHTRA_LOCATIONS[district]["tehsils"][tehsil]
                village = st.selectbox("Village / गाव", 
                                      ["Select Village"] + villages, 
                                      key="reg_vil")
            else:
                st.selectbox("Village / गाव", ["First select tehsil"], disabled=True, key="reg_vil_disabled")
        
        if st.button("Register / नोंदणी करा", type="primary", use_container_width=True, key="reg_submit_btn"):
            if not all([new_username, new_password, full_name, mobile]):
                st.error("Please fill all required fields")
            elif district == "Select District":
                st.error("Please select a district")
            elif not tehsil or tehsil == "Select Tehsil":
                st.error("Please select a tehsil")
            elif not village or village == "Select Village":
                st.error("Please select a village")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters")
            elif not mobile.isdigit() or len(mobile) != 10:
                st.error("Please enter valid 10-digit mobile number")
            else:
                user_type_clean = user_type.split("/")[0].strip()
                success, result = create_user(new_username, new_password, full_name, mobile, 
                                             email, district, tehsil, village, farm_size, user_type_clean)
                if success:
                    st.success("✅ Account created successfully! Please login")
                    st.balloons()
                else:
                    st.error(f"Error: {result}")

def show_main_app():
    """Main app with complete navigation"""
    user = st.session_state.user_data
    
    with st.sidebar:
        st.markdown(f"### 👤 {user['full_name']}")
        st.markdown(f"**📍 {user['village']}, {user['tehsil']}**")
        st.markdown(f"**🌾 Farm: {user['farm_size']} acres**")
        st.markdown(f"**👨‍🌾 Type: {user.get('user_type', 'Farmer')}**")
        st.markdown("---")
        
        st.markdown("### 🔔 Notifications")
        enable_sms = st.checkbox("SMS Alerts", value=st.session_state.notifications_enabled, key="sidebar_sms")
        enable_whatsapp = st.checkbox("WhatsApp Alerts", key="sidebar_whatsapp")
        if enable_sms or enable_whatsapp:
            st.session_state.notifications_enabled = True
            st.success("✅ Enabled")
        st.markdown("---")
        
        if user.get('user_type') == 'Farmer':
            pages = [
                "🏠 Dashboard", "🌱 Seed & Fertilizer", "📊 Market Prices",
                "🎯 Best Practices", "💰 Profit Calculator", "📚 Crop Knowledge",
                "📅 Seasonal Planner", "🌡️ Weather & Soil", "🛒 Marketplace",
                "🛍️ My Listings", "🚚 Transportation", "🏪 Storage Facilities",
                "🏛️ Govt Schemes", "🪙 Nearest Mandis", "🦠 Disease Guide",
                "📱 Notifications", "📊 My Activity"
            ]
        else:
            pages = [
                "🏠 Dashboard", "🛒 Marketplace", "💼 My Bids",
                "🚚 Transportation", "🏪 Storage Facilities",
                "📊 Market Prices", "📱 Notifications"
            ]
        
        if 'current_page' not in st.session_state or st.session_state.current_page not in pages:
            st.session_state.current_page = pages[0]
        
        current_index = pages.index(st.session_state.current_page) if st.session_state.current_page in pages else 0
        page = st.radio("Navigation", pages, index=current_index, key="main_navigation")
        
        if page != st.session_state.current_page:
            st.session_state.current_page = page
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True, key="sidebar_logout"):
            st.session_state.user_data = None
            st.session_state.current_page = "🏠 Dashboard"
            st.rerun()
    
    page = st.session_state.current_page
    
    try:
        if page == "🏠 Dashboard":
            show_dashboard()
        elif page == "🌱 Seed & Fertilizer":
            show_seed_fertilizer_calculator()
        elif page == "📊 Market Prices":
            show_live_market_prices()
        elif page == "🎯 Best Practices":
            show_best_practices()
        elif page == "💰 Profit Calculator":
            show_profit_calculator()
        elif page == "📚 Crop Knowledge":
            show_knowledge_base()
        elif page == "📅 Seasonal Planner":
            show_seasonal_planner()
        elif page == "🌡️ Weather & Soil":
            show_weather_soil()
        elif page == "🛒 Marketplace":
            show_marketplace()
        elif page == "🛍️ My Listings":
            show_my_listings()
        elif page == "💼 My Bids":
            show_my_bids()
        elif page == "🚚 Transportation":
            show_transportation()
        elif page == "🏪 Storage Facilities":
            show_storage_facilities()
        elif page == "🏛️ Govt Schemes":
            show_government_schemes_page()
        elif page == "🪙 Nearest Mandis":
            show_nearest_mandis()
        elif page == "🦠 Disease Guide":
            show_disease_guide()
        elif page == "📱 Notifications":
            show_notifications()
        elif page == "📊 My Activity":
            show_activity_history()
        else:
            show_dashboard()
    except Exception as e:
        st.error(f"Error loading page: {str(e)}")
        if st.button("🔄 Refresh", key="error_refresh"):
            st.rerun()

def show_dashboard():
    """Dashboard - COMPLETE ORIGINAL"""
    user = st.session_state.user_data
    st.markdown(f"### 🏠 Dashboard - Welcome {user['full_name']}!")
    
    current_month = datetime.now().month
    if current_month in [6, 7, 8]:
        st.success("🌧️ **Kharif Season Active** - Time for Rice, Cotton, Soybean!")
    elif current_month in [10, 11, 12, 1, 2]:
        st.success("❄️ **Rabi Season Active** - Time for Wheat, Onion, Potato!")
    else:
        st.info("☀️ **Zaid Season** - Summer vegetables with irrigation")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Your Farm", f"{user['farm_size']} acres")
    with col2:
        activities = get_user_activities(user['id'], limit=1000)
        st.metric("Activities", len(activities))
    with col3:
        st.metric("District", user['district'])
    with col4:
        conn = sqlite3.connect('krishimitra.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM marketplace_listings WHERE seller_id=? AND status='Active'", (user['id'],))
        listings = c.fetchone()[0]
        conn.close()
        st.metric("Active Listings", listings)
    
    st.markdown("### 📊 Recent Activities")
    recent = get_user_activities(user['id'], limit=5)
    if recent:
        for act in recent:
            st.markdown(f"- **{act[0]}**: {act[1]} ({act[2]} acres) - {act[4]}")
    else:
        st.info("No activities yet. Start using calculators!")
    
    st.markdown("### ⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🌱 Calculate Seeds", use_container_width=True, key="dash_btn_seeds"):
            st.session_state.current_page = "🌱 Seed & Fertilizer"
            st.rerun()
    with col2:
        if st.button("📊 Check Prices", use_container_width=True, key="dash_btn_prices"):
            st.session_state.current_page = "📊 Market Prices"
            st.rerun()
    with col3:
        if st.button("🛒 Browse Marketplace", use_container_width=True, key="dash_btn_market"):
            st.session_state.current_page = "🛒 Marketplace"
            st.rerun()
    with col4:
        if st.button("💰 Profit Calculator", use_container_width=True, key="dash_btn_profit"):
            st.session_state.current_page = "💰 Profit Calculator"
            st.rerun()
# This file contains the remaining functions for KrishiMitra
# Add these to the main file after show_dashboard()

def show_seed_fertilizer_calculator():
    """Seed & fertilizer calculator - COMPLETE ORIGINAL"""
    st.markdown("### 🌱 Seed & Fertilizer Calculator")
    st.markdown("### बी आणि खत मोजणी")
    
    user = st.session_state.user_data
    
    col1, col2 = st.columns(2)
    with col1:
        crop = st.selectbox("Select Crop / पीक निवडा", list(CROP_DATABASE.keys()), key="seed_calc_crop")
        area = st.number_input("Area (Acres) / क्षेत्र (एकर)", min_value=0.1, value=1.0, step=0.1, key="seed_calc_area")
    with col2:
        planting_method = st.selectbox("Method / पद्धत", ["Standard", "High Density", "SRI/SCI"], key="seed_calc_method")
        fert_type = st.radio("Fertilizer / खत", ["Chemical / रासायनिक", "Organic / सेंद्रिय", "Both / दोन्ही"], key="seed_calc_fert")
    
    if st.button("Calculate / मोजणी करा", type="primary", key="seed_calc_button"):
        crop_info = CROP_DATABASE[crop]
        log_activity(user['id'], "Seed Calculation", crop, area, {"method": planting_method, "fert": fert_type})
        
        seed_rate = crop_info["seed_rate_kg_per_acre"]
        try:
            if "-" in seed_rate:
                low, high = map(float, seed_rate.split("-"))
                avg_seed = (low + high) / 2
            else:
                avg_seed = float(seed_rate.split()[0])
        except:
            avg_seed = 100
        
        if "High Density" in planting_method:
            avg_seed *= 1.2
        elif "SRI" in planting_method or "SCI" in planting_method:
            avg_seed *= 0.8
        
        total_seeds = avg_seed * area
        
        st.markdown("---")
        st.markdown("### 📊 Results / परिणाम")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Seed Rate", f"{seed_rate}")
        with col2:
            st.metric("Total Seeds", f"{total_seeds:.1f} kg")
        with col3:
            yield_range = crop_info["expected_yield_tons"].split("-")
            avg_yield = float(yield_range[-1])
            st.metric("Expected Yield", f"{avg_yield * area:.1f} tons")
        
        if "Chemical" in fert_type or "रासायनिक" in fert_type or "Both" in fert_type or "दोन्ही" in fert_type:
            st.markdown("### 🧪 Chemical Fertilizers")
            st.markdown('<div class="fertilizer-card">', unsafe_allow_html=True)
            chem = crop_info["chemical_fertilizers"]
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                urea = float(chem["urea_kg"]) * area
                st.metric("Urea / युरिया", f"{urea:.1f} kg")
            with col2:
                dap = float(chem["dap_kg"]) * area
                st.metric("DAP / डीएपी", f"{dap:.1f} kg")
            with col3:
                mop = float(chem["mop_kg"]) * area
                st.metric("MOP / पोटॅश", f"{mop:.1f} kg")
            with col4:
                total = urea + dap + mop
                st.metric("Total / एकूण", f"{total:.1f} kg")
            st.write(f"**NPK Ratio:** {chem['total_npk']}")
            st.markdown("**Application Schedule:**")
            for schedule in chem['application_schedule']:
                st.write(f"• {schedule}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        if "Organic" in fert_type or "सेंद्रिय" in fert_type or "Both" in fert_type or "दोन्ही" in fert_type:
            st.markdown("### 🌱 Organic Fertilizers / सेंद्रिय खत")
            st.markdown('<div class="fertilizer-card">', unsafe_allow_html=True)
            org = crop_info["organic_fertilizers"]
            fym_range = org['fym_tons'].split('-')
            fym_total = float(fym_range[-1]) * area
            st.write(f"**FYM (शेणखत):** {org['fym_tons']} tons/acre × {area} acres = **{fym_total:.1f} tons**")
            if 'vermicompost_kg' in org:
                vermi_range = org['vermicompost_kg'].split('-')
                vermi_total = float(vermi_range[-1]) * area
                st.write(f"**Vermicompost:** {org['vermicompost_kg']} kg/acre = **{vermi_total:.0f} kg**")
            if 'neem_cake_kg' in org:
                neem = org['neem_cake_kg'].split('-') if '-' in str(org['neem_cake_kg']) else [org['neem_cake_kg']]
                neem_total = float(neem[0]) * area
                st.write(f"**Neem Cake:** {org['neem_cake_kg']} kg/acre = **{neem_total:.0f} kg**")
            if 'green_manure' in org:
                st.write(f"**Green Manure:** {org['green_manure']}")
            if 'biofertilizers' in org:
                st.write(f"**Biofertilizers:** {org['biofertilizers']}")
            st.markdown("**Application Schedule:**")
            for schedule in org['application_schedule']:
                st.write(f"• {schedule}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("### 🌾 Growing Information")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Spacing:** {crop_info['spacing']}")
            st.write(f"**Duration:** {crop_info['duration_days']} days")
            st.write(f"**Season:** {crop_info['best_season']}")
        with col2:
            st.write(f"**Soil:** {crop_info['soil_type']}")
            st.write(f"**Water:** {crop_info['water_requirement']}")
        with col3:
            st.write(f"**Market Price:** {crop_info['market_price_range']}")
            st.write(f"**Yield:** {crop_info['expected_yield_tons']} tons/acre")
        
        if st.session_state.notifications_enabled:
            msg = f"KrishiMitra: Seed calculation done for {crop} ({area} acres). Seeds needed: {total_seeds:.0f} kg."
            send_sms_notification(user['mobile'], msg)
            create_notification(user['id'], "calculation", msg)

def show_live_market_prices():
    """Market prices with CEDA, Manual, and API - ENHANCED WITH CEDA"""
    st.markdown("### 📊 Live Market Prices / थेट बाजारभाव")
    user = st.session_state.user_data
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 View Prices", "🎓 CEDA Data", "🌐 Government API", "✏️ Update Prices"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            commodity = st.selectbox("Commodity / वस्तू", list(CROP_DATABASE.keys()), key="market_price_commodity")
        with col2:
            st.info(f"📍 {user['district']} District")
        
        manual_data = get_manual_prices(commodity=commodity, district=user['district'], days=30)
        
        if manual_data is not None and len(manual_data) > 0:
            st.success("✅ Maharashtra Market Data (Manually Updated)")
            latest = manual_data.iloc[0]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Min Price", f"₹{latest['min_price']:,.0f}")
            with col2:
                st.metric("Max Price", f"₹{latest['max_price']:,.0f}")
            with col3:
                st.metric("Modal Price", f"₹{latest['modal_price']:,.0f}")
            st.info(f"**Market:** {latest['market']} | **District:** {latest['district']} | **Date:** {latest['price_date']}")
            st.markdown("### 📋 Recent Price Data")
            st.dataframe(manual_data, use_container_width=True)
            st.caption(f"Last updated: {latest['updated_at']}")
        else:
            st.info("📈 Multiple data sources available - check other tabs")
            crop_info = CROP_DATABASE[commodity]
            st.markdown(f"**Expected Market Price Range:** {crop_info['market_price_range']}")
            mandis = get_nearest_mandis(user['district'])
            st.markdown("### 🪙 Nearest Markets")
            for mandi in mandis[:3]:
                st.markdown(f"- 📍 {mandi}")
    
    with tab2:
        st.markdown("### 🎓 CEDA Ashoka University Agricultural Prices")
        st.markdown('<div class="ceda-attribution">', unsafe_allow_html=True)
        st.markdown(get_ceda_attribution())
        st.markdown('</div>', unsafe_allow_html=True)
        
        commodity_ceda = st.selectbox("Select Commodity", list(CROP_DATABASE.keys()), key="ceda_commodity")
        
        st.info("ℹ️ CEDA provides data through an interactive web portal. Click below for access instructions.")
        
        if st.button("📊 View CEDA Access Guide", type="primary", key="ceda_fetch"):
            data, instructions = fetch_ceda_prices(commodity_ceda, state="Maharashtra", district=user['district'])
            
            st.markdown(instructions)
            
            # Show direct link to CEDA portal
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.link_button("🌐 Open CEDA Portal", "https://ceda.ashoka.edu.in", use_container_width=True)
            with col2:
                st.link_button("📚 CEDA Documentation", "https://ceda.ashoka.edu.in/about", use_container_width=True)
            
            st.markdown("---")
            st.markdown('<div class="ceda-attribution">', unsafe_allow_html=True)
            st.markdown("""
            **📊 Data Attribution:**
            - Source: Centre for Economic Data and Analysis (CEDA), Ashoka University
            - License: Non-commercial educational and research use
            - Coverage: All India agricultural market data
            - Updates: Monthly/Weekly (check portal for latest)
            
            **💡 Why Manual Access?**
            CEDA uses a JavaScript-based interactive portal that requires manual interaction.
            Automated scraping would violate their terms of service and technical architecture.
            """)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Show example data structure
            st.markdown("### 📋 Example CEDA Data Format")
            st.info("""
            **Available Data Points:**
            - Modal Price (₹/quintal) - Most common trading price
            - Min Price (₹/quintal) - Lowest trading price
            - Max Price (₹/quintal) - Highest trading price
            - Arrival Quantity (quintals) - Market arrival volumes
            - Time Series: Monthly/Weekly trends
            - Geographic Coverage: District-level for all states
            """)
            
            # Sample data based on selected commodity
            crop_info = CROP_DATABASE[commodity_ceda]
            price_range = crop_info["market_price_range"].replace("₹", "").split("-")
            try:
                base_price = sum([float(p.split("/")[0]) for p in price_range]) / len(price_range)
            except:
                base_price = 2500
            
            # Generate sample data for selected crop
            import random
            random.seed(hash(commodity_ceda))  # Consistent random data for same crop
            
            sample_data = pd.DataFrame({
                'Month': ['09/2025', '08/2025', '07/2025', '06/2025'],
                'Modal Price (₹)': [
                    round(base_price + random.randint(-100, 100), 2),
                    round(base_price + random.randint(-100, 100), 2),
                    round(base_price + random.randint(-150, 50), 2),
                    round(base_price + random.randint(-150, 50), 2)
                ],
                'Min Price (₹)': [
                    round(base_price * 0.92 + random.randint(-50, 50), 2),
                    round(base_price * 0.93 + random.randint(-50, 50), 2),
                    round(base_price * 0.91 + random.randint(-50, 50), 2),
                    round(base_price * 0.90 + random.randint(-50, 50), 2)
                ],
                'Max Price (₹)': [
                    round(base_price * 1.08 + random.randint(-50, 50), 2),
                    round(base_price * 1.09 + random.randint(-50, 50), 2),
                    round(base_price * 1.07 + random.randint(-50, 50), 2),
                    round(base_price * 1.08 + random.randint(-50, 50), 2)
                ]
            })
            st.dataframe(sample_data, use_container_width=True)
            st.caption(f"Example: {commodity_ceda} prices (All India) - This is sample data format from CEDA Portal")
            st.warning("⚠️ Note: These are example prices to show the data format. Visit CEDA portal for actual current prices.")
    
    with tab3:
        st.markdown("### 🌐 Government API (Agmarknet)")
        commodity_api = st.selectbox("Commodity", list(CROP_DATABASE.keys()), key="api_commodity")
        only_maharashtra = st.checkbox("Show only Maharashtra data", value=True, key="maha_only_filter")
        
        if st.button("Fetch from API", type="primary", key="market_price_fetch"):
            with st.spinner("Fetching from Agmarknet..."):
                data, debug_msg = fetch_agmarknet_prices("Maharashtra", user['district'], commodity_api)
                
                if data is not None and only_maharashtra:
                    if 'state' in data.columns:
                        maha_data = data[data['state'].str.contains('Maharashtra', case=False, na=False)]
                        if len(maha_data) == 0:
                            st.warning(f"⚠️ No Maharashtra data available")
                            data = None
                        else:
                            data = maha_data
                
                if data is not None and len(data) > 0:
                    st.success("✅ Live Government Data")
                    latest = data.iloc[0]
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Min Price", f"₹{latest.get('min_price', 'N/A')}")
                    with col2:
                        st.metric("Max Price", f"₹{latest.get('max_price', 'N/A')}")
                    with col3:
                        st.metric("Modal Price", f"₹{latest.get('modal_price', 'N/A')}")
                    st.dataframe(data.head(20), use_container_width=True)
                else:
                    st.warning("⚠️ Try CEDA or manual prices.")
    
    with tab4:
        st.markdown("### ✏️ Update Market Prices Manually")
        with st.form("add_manual_price"):
            col1, col2 = st.columns(2)
            with col1:
                district = st.selectbox("District", list(MAHARASHTRA_LOCATIONS.keys()), key="manual_district")
                market_name = st.text_input("Market Name", key="manual_market")
                commodity_manual = st.selectbox("Commodity", list(CROP_DATABASE.keys()), key="manual_commodity")
                arrival_quantity = st.text_input("Arrival Quantity", key="manual_quantity")
            with col2:
                min_price = st.number_input("Min Price (₹/quintal)", min_value=0.0, step=10.0, key="manual_min")
                max_price = st.number_input("Max Price (₹/quintal)", min_value=0.0, step=10.0, key="manual_max")
                modal_price = st.number_input("Modal Price (₹/quintal)", min_value=0.0, step=10.0, key="manual_modal")
                price_date = st.date_input("Price Date", value=datetime.now().date(), key="manual_date")
            
            submitted = st.form_submit_button("💾 Save Price Data", use_container_width=True)
            if submitted:
                if market_name and min_price > 0 and max_price > 0 and modal_price > 0:
                    add_manual_price(district, market_name, commodity_manual, min_price, max_price, 
                                   modal_price, arrival_quantity, price_date, user['id'])
                    st.success(f"✅ Price data saved")
                    log_activity(user['id'], "Manual Price Update", commodity_manual, 0, {
                        "market": market_name, "modal_price": modal_price
                    })
                    st.rerun()

def show_best_practices():
    """Best practices - COMPLETE ORIGINAL"""
    st.markdown("### 🎯 Best Farming Practices")
    crop_name = st.selectbox("Select Crop", list(CROP_DATABASE.keys()))
    crop = CROP_DATABASE[crop_name]
    st.markdown(f"### 🌾 {crop_name} - Complete Guide")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.write(f"**Seed Rate:** {crop['seed_rate_kg_per_acre']}")
        st.write(f"**Spacing:** {crop['spacing']}")
        st.write(f"**Duration:** {crop['duration_days']} days")
        st.write(f"**Season:** {crop['best_season']}")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.write(f"**Soil:** {crop['soil_type']}")
        st.write(f"**Water:** {crop['water_requirement']}")
        st.write(f"**Yield:** {crop['expected_yield_tons']} tons/acre")
        st.write(f"**Price:** {crop['market_price_range']}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("### 🚜 High-Yield Methods")
    for idx, method in enumerate(crop['methods'], 1):
        with st.expander(f"Method {idx}: {method.split(':')[0]}"):
            st.write(method)
    
    st.markdown("### 💡 Expert Tips")
    for tip in crop['tips']:
        st.success(f"✓ {tip}")

def show_profit_calculator():
    """Profit calculator - COMPLETE ORIGINAL"""
    st.markdown("### 💰 Profit & ROI Calculator")
    user = st.session_state.user_data
    
    col1, col2 = st.columns(2)
    with col1:
        crop = st.selectbox("Crop", list(CROP_DATABASE.keys()))
        area = st.number_input("Area (Acres)", min_value=0.1, value=1.0, step=0.1)
        st.markdown("### Costs")
        seed_cost = st.number_input("Seed (₹)", value=5000)
        fert_cost = st.number_input("Fertilizer (₹)", value=8000)
        pest_cost = st.number_input("Pesticides (₹)", value=3000)
        labor = st.number_input("Labor (₹)", value=15000)
        irrig = st.number_input("Irrigation (₹)", value=5000)
        other = st.number_input("Other (₹)", value=2000)
    
    with col2:
        crop_info = CROP_DATABASE[crop]
        yield_range = crop_info["expected_yield_tons"].split("-")
        avg_yield = float(yield_range[-1])
        expected_yield = st.slider("Expected Yield (tons/acre)", 
                                   avg_yield * 0.5, avg_yield * 1.5, avg_yield, 0.1)
        price_str = crop_info["market_price_range"].replace("₹", "").split("-")
        try:
            avg_price = sum([float(p.split("/")[0]) for p in price_str]) / len(price_str)
        except:
            avg_price = 2000
        selling_price = st.number_input("Selling Price (₹/quintal)", value=int(avg_price))
        total_yield_tons = expected_yield * area
        total_quintals = total_yield_tons * 10
        gross_revenue = total_quintals * selling_price
        st.metric("Production", f"{total_quintals:.1f} quintals")
        st.metric("Revenue", f"₹{gross_revenue:,.0f}")
    
    if st.button("Calculate Profit", type="primary"):
        total_cost = seed_cost + fert_cost + pest_cost + labor + irrig + other
        net_profit = gross_revenue - total_cost
        roi = (net_profit / total_cost * 100) if total_cost > 0 else 0
        
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Cost", f"₹{total_cost:,.0f}")
        with col2:
            st.metric("Revenue", f"₹{gross_revenue:,.0f}")
        with col3:
            st.metric("Net Profit", f"₹{net_profit:,.0f}")
        with col4:
            st.metric("ROI", f"{roi:.1f}%")
        
        cost_data = pd.DataFrame({
            'Category': ['Seed', 'Fertilizer', 'Pesticides', 'Labor', 'Irrigation', 'Other'],
            'Amount': [seed_cost, fert_cost, pest_cost, labor, irrig, other]
        })
        fig = px.pie(cost_data, values='Amount', names='Category', title='Cost Distribution')
        st.plotly_chart(fig, use_container_width=True)
        
        if net_profit > 0:
            st.success(f"✅ Profitable! ROI: {roi:.1f}%")
        else:
            st.error("⚠️ Loss projected. Review costs or improve yield.")
        
        log_activity(user['id'], "Profit Calculation", crop, area, {
            "costs": total_cost, "revenue": gross_revenue, "profit": net_profit, "roi": roi
        })

def show_knowledge_base():
    """Knowledge base - COMPLETE ORIGINAL"""
    st.markdown("### 📚 Crop Knowledge Base")
    search = st.text_input("🔍 Search crops...")
    season_filter = st.selectbox("Filter by Season", ["All", "Kharif", "Rabi", "Zaid"])
    
    for crop_name, crop in CROP_DATABASE.items():
        if search and search.lower() not in crop_name.lower():
            continue
        if season_filter != "All" and season_filter not in crop["best_season"]:
            continue
        
        with st.expander(f"🌱 {crop_name}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Seed:** {crop['seed_rate_kg_per_acre']}")
                st.write(f"**Spacing:** {crop['spacing']}")
                st.write(f"**Duration:** {crop['duration_days']} days")
            with col2:
                st.write(f"**Soil:** {crop['soil_type']}")
                st.write(f"**Water:** {crop['water_requirement']}")
                st.write(f"**Season:** {crop['best_season']}")
            with col3:
                st.write(f"**Yield:** {crop['expected_yield_tons']} tons/acre")
                st.write(f"**Price:** {crop['market_price_range']}")

def show_seasonal_planner():
    """Seasonal planner - COMPLETE ORIGINAL"""
    st.markdown("### 📅 Seasonal Crop Planner")
    current_month = datetime.now().month
    if current_month in [6, 7, 8]:
        st.success("🌧️ **Kharif Season**")
    elif current_month in [10, 11, 12, 1, 2]:
        st.success("❄️ **Rabi Season**")
    else:
        st.info("☀️ **Zaid Season**")
    
    season_tab = st.radio("Select Season", ["Kharif", "Rabi", "Zaid"], horizontal=True)
    season = SEASONAL_CALENDAR[season_tab]
    
    st.markdown(f"## {season_tab} Season")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.write(f"**Description:** {season['description']}")
        st.write(f"**Sowing:** {season['sowing_period']}")
        st.write(f"**Harvesting:** {season['harvesting_period']}")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        for char in season['characteristics']:
            st.write(f"• {char}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("### Recommended Crops")
    for crop_name, crop_data in season['crops'].items():
        st.markdown('<div class="price-card">', unsafe_allow_html=True)
        st.markdown(f"#### {crop_name}")
        st.write(f"**Sowing:** {crop_data['sowing']}")
        st.write(f"**Harvesting:** {crop_data['harvesting']}")
        st.write(f"**Duration:** {crop_data['duration']}")
        st.markdown('</div>', unsafe_allow_html=True)

def show_weather_soil():
    """Weather & soil - COMPLETE ORIGINAL"""
    st.markdown("### 🌡️ Weather & Soil Information")
    user = st.session_state.user_data
    st.markdown(f"### 📍 {user['village']}, {user['tehsil']}, {user['district']}")
    
    if st.button("Check Weather"):
        weather = fetch_weather_data(user['district'], user['tehsil'])
        if weather:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Temperature", f"{weather['temperature']}°C")
            with col2:
                st.metric("Humidity", f"{weather['humidity']}%")
            with col3:
                st.metric("Wind", f"{weather['wind_speed']} m/s")
            st.info(f"**Conditions:** {weather['weather']}")
            st.metric("Pressure", f"{weather['pressure']} hPa")
        else:
            st.warning("Weather data unavailable")
    
    st.markdown("---")
    st.markdown("### 🧪 Soil Testing")
    st.info("""
    **Free Soil Health Card:**
    - Apply at: https://soilhealth.dac.gov.in/
    - Contact: District Agriculture Office
    """)

def show_marketplace():
    """Marketplace - COMPLETE ORIGINAL"""
    st.markdown("### 🛒 Marketplace - Buy & Sell Produce")
    user = st.session_state.user_data
    
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_crop = st.selectbox("Filter by Crop", ["All"] + list(CROP_DATABASE.keys()))
    with col2:
        filter_district = st.selectbox("Filter by District", ["All"] + list(MAHARASHTRA_LOCATIONS.keys()))
    with col3:
        sort_by = st.selectbox("Sort by", ["Latest", "Price: Low to High", "Price: High to Low"])
    
    conn = sqlite3.connect('krishimitra.db')
    c = conn.cursor()
    query = """SELECT ml.*, u.full_name, u.mobile, u.village, u.district 
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
    if sort_by == "Price: Low to High":
        query += " ORDER BY ml.price_per_unit ASC"
    elif sort_by == "Price: High to Low":
        query += " ORDER BY ml.price_per_unit DESC"
    else:
        query += " ORDER BY ml.created_at DESC"
    
    c.execute(query, params)
    listings = c.fetchall()
    conn.close()
    
    if listings:
        st.success(f"✅ Found {len(listings)} listings")
        for listing in listings:
            st.markdown(f"""
            <div class='marketplace-card'>
                <h4>🌾 {listing[2]} - {listing[3]} {listing[4]}</h4>
                <p><strong>Price:</strong> ₹{listing[5]:,.0f} per {listing[4]}</p>
                <p><strong>Quality:</strong> {listing[6]}</p>
                <p><strong>Location:</strong> {listing[13]}, {listing[14]}</p>
                <p><strong>Seller:</strong> {listing[11]} ({listing[12]})</p>
            </div>
            """, unsafe_allow_html=True)
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button(f"Place Bid 💼", key=f"bid_{listing[0]}"):
                    show_bid_form(listing)
            st.markdown("---")
    else:
        st.info("No listings found")
    
    if user.get('user_type') == 'Farmer':
        st.markdown("---")
        if st.button("➕ Create New Listing", type="primary", use_container_width=True):
            st.session_state.current_page = "🛍️ My Listings"
            st.rerun()

def show_bid_form(listing):
    """Bid form - COMPLETE ORIGINAL"""
    with st.form("place_bid_form"):
        st.subheader(f"Place Bid for {listing[2]}")
        user = st.session_state.user_data
        col1, col2 = st.columns(2)
        with col1:
            bid_amount = st.number_input("Your Bid (₹ per unit)", min_value=1.0, value=float(listing[5]))
        with col2:
            bid_quantity = st.number_input("Quantity", min_value=0.1, max_value=float(listing[3]), value=float(listing[3]))
        message = st.text_area("Message to Seller (Optional)")
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("Submit Bid 💰", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("Cancel", use_container_width=True)
        
        if submit:
            conn = sqlite3.connect('krishimitra.db')
            c = conn.cursor()
            c.execute("""INSERT INTO bids (listing_id, buyer_id, bid_amount, bid_quantity, 
                        buyer_name, buyer_phone, message)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (listing[0], user['id'], bid_amount, bid_quantity, 
                     user['full_name'], user['mobile'], message))
            conn.commit()
            conn.close()
            st.success("✅ Bid placed successfully!")
            log_activity(user['id'], "Bid Placed", listing[2], bid_quantity, {
                "listing_id": listing[0], "amount": bid_amount
            })
            create_notification(listing[1], "new_bid", 
                              f"New bid of ₹{bid_amount} for {listing[2]}")
            st.rerun()

def show_my_listings():
    """My listings - COMPLETE ORIGINAL"""
    st.markdown("### 🛍️ My Listings")
    user = st.session_state.user_data
    
    tab1, tab2 = st.tabs(["📦 Active Listings", "➕ Create New Listing"])
    
    with tab1:
        conn = sqlite3.connect('krishimitra.db')
        c = conn.cursor()
        c.execute("""SELECT * FROM marketplace_listings 
                     WHERE seller_id = ? ORDER BY created_at DESC""", (user['id'],))
        my_listings = c.fetchall()
        conn.close()
        
        if my_listings:
            for listing in my_listings:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{listing[2]}** - {listing[3]} {listing[4]}")
                    st.caption(f"Price: ₹{listing[5]:,.0f} | Status: {listing[9]}")
                with col2:
                    if st.button("View Bids", key=f"view_bids_{listing[0]}"):
                        show_listing_bids(listing)
                st.markdown("---")
        else:
            st.info("No listings yet")
    
    with tab2:
        with st.form("create_listing_form"):
            col1, col2 = st.columns(2)
            with col1:
                crop_name = st.selectbox("Crop", list(CROP_DATABASE.keys()))
                quantity = st.number_input("Quantity", min_value=0.1, step=0.1)
                unit = st.selectbox("Unit", ["Quintal", "Kg", "Tonnes"])
            with col2:
                price_per_unit = st.number_input("Price per Unit (₹)", min_value=1.0, step=10.0)
                quality_grade = st.selectbox("Quality Grade", ["A (Premium)", "B (Good)", "C (Standard)"])
                location = st.selectbox("Location", list(MAHARASHTRA_LOCATIONS.keys()))
            description = st.text_area("Description")
            submitted = st.form_submit_button("Create Listing", type="primary", use_container_width=True)
            
            if submitted and crop_name and quantity > 0 and price_per_unit > 0:
                conn = sqlite3.connect('krishimitra.db')
                c = conn.cursor()
                c.execute("""INSERT INTO marketplace_listings 
                            (seller_id, crop_name, quantity, unit, price_per_unit, 
                             quality_grade, location, description, status)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Active')""",
                        (user['id'], crop_name, quantity, unit, price_per_unit, 
                         quality_grade, location, description))
                conn.commit()
                conn.close()
                st.success("✅ Listing created!")
                log_activity(user['id'], "Listing Created", crop_name, quantity, {})
                st.rerun()

def show_listing_bids(listing):
    """Show bids for listing - COMPLETE ORIGINAL"""
    st.markdown(f"#### 📝 Bids for {listing[2]}")
    conn = sqlite3.connect('krishimitra.db')
    c = conn.cursor()
    c.execute("""SELECT * FROM bids WHERE listing_id = ? ORDER BY created_at DESC""", (listing[0],))
    bids = c.fetchall()
    conn.close()
    
    if bids:
        for bid in bids:
            st.markdown(f"""
            <div class='bid-card'>
                <p><strong>Buyer:</strong> {bid[5]} ({bid[6]})</p>
                <p><strong>Bid:</strong> ₹{bid[3]:,.0f} | Quantity: {bid[4]}</p>
                <p><strong>Status:</strong> {bid[8]}</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Accept ✅", key=f"accept_{bid[0]}"):
                    conn = sqlite3.connect('krishimitra.db')
                    c = conn.cursor()
                    c.execute("UPDATE bids SET status='Accepted' WHERE id=?", (bid[0],))
                    conn.commit()
                    conn.close()
                    st.success("Bid accepted!")
                    st.rerun()
            with col2:
                if st.button(f"Reject ❌", key=f"reject_{bid[0]}"):
                    conn = sqlite3.connect('krishimitra.db')
                    c = conn.cursor()
                    c.execute("UPDATE bids SET status='Rejected' WHERE id=?", (bid[0],))
                    conn.commit()
                    conn.close()
                    st.info("Bid rejected")
                    st.rerun()
    else:
        st.info("No bids yet")

def show_my_bids():
    """My bids - COMPLETE ORIGINAL"""
    st.markdown("### 💼 My Bids")
    user = st.session_state.user_data
    conn = sqlite3.connect('krishimitra.db')
    c = conn.cursor()
    c.execute("""SELECT b.*, ml.crop_name, u.full_name as seller_name, u.mobile as seller_phone
                 FROM bids b
                 JOIN marketplace_listings ml ON b.listing_id = ml.id
                 JOIN users u ON ml.seller_id = u.id
                 WHERE b.buyer_id = ? ORDER BY b.created_at DESC""", (user['id'],))
    my_bids = c.fetchall()
    conn.close()
    
    if my_bids:
        for bid in my_bids:
            st.markdown(f"""
            <div class='bid-card'>
                <h4>🌾 {bid[10]}</h4>
                <p><strong>Your Bid:</strong> ₹{bid[3]:,.0f}</p>
                <p><strong>Status:</strong> {bid[8]}</p>
                <p><strong>Seller:</strong> {bid[11]} ({bid[12]})</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("---")
    else:
        st.info("No bids yet")

def show_transportation():
    """Transportation - COMPLETE ORIGINAL"""
    st.markdown("### 🚚 Transportation Services")
    user = st.session_state.user_data
    tab1, tab2 = st.tabs(["📋 Available Services", "➕ Register Service"])
    
    with tab1:
        filter_district = st.selectbox("Filter by District", ["All"] + list(MAHARASHTRA_LOCATIONS.keys()))
        conn = sqlite3.connect('krishimitra.db')
        c = conn.cursor()
        if filter_district == "All":
            c.execute("SELECT * FROM transport_providers ORDER BY district")
        else:
            c.execute("SELECT * FROM transport_providers WHERE district=?", (filter_district,))
        providers = c.fetchall()
        conn.close()
        
        if providers:
            for provider in providers:
                st.markdown(f"""
                <div class='location-card'>
                    <h4>🚛 {provider[1]}</h4>
                    <p><strong>Type:</strong> {provider[2]}</p>
                    <p><strong>Rate:</strong> ₹{provider[4]}/km</p>
                    <p><strong>Contact:</strong> {provider[5]}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No providers registered")
    
    with tab2:
        if user.get('user_type') == 'Transport Provider':
            with st.form("register_transport"):
                col1, col2 = st.columns(2)
                with col1:
                    provider_name = st.text_input("Business Name")
                    vehicle_type = st.selectbox("Vehicle Type", 
                                               ["Mini Truck (1-2 tons)", "Medium Truck (3-5 tons)", 
                                                "Large Truck (6-10 tons)"])
                    capacity = st.text_input("Capacity")
                with col2:
                    rate_per_km = st.number_input("Rate per KM (₹)", min_value=1.0, value=15.0)
                    phone = st.text_input("Contact Number")
                    district = st.selectbox("District", list(MAHARASHTRA_LOCATIONS.keys()))
                
                if st.form_submit_button("Register Service", use_container_width=True):
                    if all([provider_name, capacity, phone, district]):
                        conn = sqlite3.connect('krishimitra.db')
                        c = conn.cursor()
                        c.execute("""INSERT INTO transport_providers 
                                    (provider_name, vehicle_type, capacity, rate_per_km, phone, district)
                                   VALUES (?, ?, ?, ?, ?, ?)""",
                                (provider_name, vehicle_type, capacity, rate_per_km, phone, district))
                        conn.commit()
                        conn.close()
                        st.success("✅ Service registered!")
                        st.rerun()
        else:
            st.info("Only Transport Providers can register services")

def show_storage_facilities():
    """Storage facilities - COMPLETE ORIGINAL"""
    st.markdown("### 🏪 Storage Facilities")
    user = st.session_state.user_data
    tab1, tab2 = st.tabs(["📋 Available Facilities", "➕ Register Facility"])
    
    with tab1:
        filter_location = st.selectbox("Filter by Location", ["All"] + list(MAHARASHTRA_LOCATIONS.keys()))
        conn = sqlite3.connect('krishimitra.db')
        c = conn.cursor()
        if filter_location == "All":
            c.execute("SELECT * FROM storage_facilities ORDER BY location")
        else:
            c.execute("SELECT * FROM storage_facilities WHERE location=?", (filter_location,))
        facilities = c.fetchall()
        conn.close()
        
        if facilities:
            for facility in facilities:
                st.markdown(f"""
                <div class='location-card'>
                    <h4>🏪 {facility[1]}</h4>
                    <p><strong>Type:</strong> {facility[2]}</p>
                    <p><strong>Rate:</strong> ₹{facility[4]}/quintal/month</p>
                    <p><strong>Contact:</strong> {facility[6]}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No facilities registered")
    
    with tab2:
        with st.form("register_storage"):
            col1, col2 = st.columns(2)
            with col1:
                facility_name = st.text_input("Facility Name")
                storage_type = st.selectbox("Storage Type", 
                                           ["Cold Storage", "Warehouse", "Godown"])
                capacity = st.text_input("Capacity")
            with col2:
                rate_per_quintal = st.number_input("Rate per Quintal/Month (₹)", min_value=1.0, value=10.0)
                phone = st.text_input("Contact Number")
                location = st.selectbox("Location", list(MAHARASHTRA_LOCATIONS.keys()))
            
            if st.form_submit_button("Register Facility", use_container_width=True):
                if all([facility_name, capacity, phone, location]):
                    conn = sqlite3.connect('krishimitra.db')
                    c = conn.cursor()
                    c.execute("""INSERT INTO storage_facilities 
                                (facility_name, storage_type, capacity, rate_per_quintal, location, phone)
                               VALUES (?, ?, ?, ?, ?, ?)""",
                            (facility_name, storage_type, capacity, rate_per_quintal, location, phone))
                    conn.commit()
                    conn.close()
                    st.success("✅ Facility registered!")
                    log_activity(user['id'], "Storage Registered", "", 0, {})
                    st.rerun()

def show_government_schemes_page():
    """Government schemes - COMPLETE ORIGINAL"""
    st.markdown("### 🏛️ Government Schemes for Farmers")
    for scheme_id, scheme in GOVERNMENT_SCHEMES.items():
        with st.expander(f"📋 {scheme['name']}"):
            st.write(f"**Benefit:** {scheme['benefit']}")
            st.write(f"**Eligibility:** {scheme['eligibility']}")
            st.write(f"**Website:** {scheme['website']}")
            st.write(f"**Helpline:** {scheme['helpline']}")
            st.write(f"**How to Apply:** {scheme['how_to_apply']}")

def show_nearest_mandis():
    """Nearest mandis - COMPLETE ORIGINAL"""
    st.markdown("### 🪙 Nearest Markets / जवळची मंडी")
    user = st.session_state.user_data
    mandis = get_nearest_mandis(user['district'])
    st.markdown(f"### {user['district']} District Markets")
    for mandi in mandis:
        st.markdown('<div class="price-card">', unsafe_allow_html=True)
        st.write(f"📍 **{mandi}**")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.info("""
    **Online Markets:**
    - eNAM: https://www.enam.gov.in/
    - Agmarknet: https://agmarknet.gov.in/
    """)

def show_disease_guide():
    """Disease guide - COMPLETE ORIGINAL"""
    st.markdown("### 🦠 Crop Disease Management")
    crop_selected = st.selectbox("Select Crop", list(CROP_DATABASE.keys()))
    st.markdown("### Common Diseases & Pests")
    
    if crop_selected in DISEASE_DATABASE:
        for disease in DISEASE_DATABASE[crop_selected]:
            st.markdown('<div class="fertilizer-card">', unsafe_allow_html=True)
            st.markdown(f"#### 🦠 {disease['name']}")
            st.write(f"**Symptoms:** {disease['symptoms']}")
            st.write(f"**Control:** {disease['control']}")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Disease information will be added soon")

def show_notifications():
    """Notifications - COMPLETE ORIGINAL"""
    st.markdown("### 📱 Your Notifications")
    user = st.session_state.user_data
    conn = sqlite3.connect('krishimitra.db')
    c = conn.cursor()
    c.execute('''SELECT notification_type, message, status, created_at
                 FROM notifications WHERE user_id=?
                 ORDER BY created_at DESC LIMIT 20''', (user['id'],))
    notifications = c.fetchall()
    conn.close()
    
    if notifications:
        for notif in notifications:
            status_icon = "✅" if notif[2] == "sent" else "⏳"
            st.markdown(f"{status_icon} **{notif[0]}**: {notif[1]}")
            st.caption(f"Date: {notif[3]}")
            st.markdown("---")
    else:
        st.info("No notifications yet")
    
    st.markdown("### 🧪 Test Notifications")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Send Test SMS", use_container_width=True):
            send_sms_notification(user['mobile'], "Test SMS from KrishiMitra!")
    with col2:
        if st.button("Send Test WhatsApp", use_container_width=True):
            send_whatsapp_notification(user['mobile'], "Test WhatsApp from KrishiMitra!")

def show_activity_history():
    """Activity history - COMPLETE ORIGINAL"""
    st.markdown("### 📊 Your Activity History")
    user = st.session_state.user_data
    activities = get_user_activities(user['id'], limit=50)
    
    if activities:
        df = pd.DataFrame(activities, columns=['Activity', 'Crop', 'Area (acres)', 'Data', 'Date'])
        st.dataframe(df, use_container_width=True)
        if len(df) > 0:
            fig = px.bar(df, x='Crop', y='Area (acres)', title='Crops Calculated')
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No activity history yet")

# Note: Add these functions to your main KrishiMitra file after show_dashboard()
# Due to response length limits, I'll create a second artifact with the remaining functions
# This artifact contains the first 70% of the complete code with CEDA integration

if __name__ == "__main__":
    main()