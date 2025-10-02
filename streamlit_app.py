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

# Page configuration
st.set_page_config(
    page_title="KrishiMitra Maharashtra - Complete System",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
    </style>
    """, unsafe_allow_html=True)

# ====================
# ALL 36 MAHARASHTRA DISTRICTS - COMPLETE DATA
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
    }
}

# Initialize session state
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'location_data' not in st.session_state:
    st.session_state.location_data = {'district': None, 'tehsil': None, 'village': None}
if 'notifications_enabled' not in st.session_state:
    st.session_state.notifications_enabled = False

# ====================
# COMPLETE CROP DATABASE (ALL 12 CROPS)
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
            "Direct Seeded Rice (DSR): Drill seeds at 8-10 kg/acre, reduces water usage by 30%, labor saving method",
            "Drip irrigation in aerobic rice cultivation reduces water use by 40-50% while maintaining yields",
            "Use of drum seeder for uniform spacing and optimal plant population"
        ],
        "tips": [
            "Maintain 2-5 cm water level during vegetative stage",
            "Apply zinc sulfate at 10 kg/acre to prevent zinc deficiency",
            "Use pheromone traps for stem borer management",
            "Implement alternate wetting and drying (AWD) to save water"
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
                "Neem cake: Apply as basal at sowing",
                "Biofertilizers: Seed treatment before sowing"
            ]
        },
        "methods": [
            "Zero tillage: Direct seeding with specialized drill, saves fuel and time",
            "Raised bed planting: 20-30% water savings, better drainage, 10-15% yield increase",
            "Happy Seeder: Direct drill wheat after rice without burning stubble",
            "Precision land leveling improves water efficiency by 25%"
        ],
        "tips": [
            "Sow within first fortnight of November for optimal yields",
            "Apply first irrigation at Crown Root Initiation (21 days)",
            "Use certified seed for 15-20% higher yields",
            "Foliar spray of 2% urea at flowering boosts grain protein"
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
                "First: 25% N + 50% K at square formation (30-35 days)",
                "Second: 25% N at flowering (60 days)",
                "Third: 25% N at boll development (90 days)"
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
                "Vermicompost: Apply at sowing in furrows",
                "Neem cake: Apply at sowing and 45 days after",
                "Biofertilizers: Seed treatment and soil application"
            ]
        },
        "methods": [
            "High Density Planting: 90cm x 30cm spacing, 15-25% yield increase",
            "Bt cotton hybrids reduce insecticide use by 50%",
            "Drip irrigation saves 40-50% water",
            "Growth regulators prevent excessive vegetative growth"
        ],
        "tips": [
            "Deep plowing to 25-30cm improves root development",
            "Install pheromone traps @ 5 traps/acre for monitoring",
            "Pick cotton at 80% boll opening for best quality",
            "Practice crop rotation to break pest cycle"
        ]
    },
    "Sugarcane": {
        "seed_rate_kg_per_acre": "12000-14000 (3-bud setts)",
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
                "30 days: 25% N + 50% K",
                "60 days: 25% N",
                "90 days: 25% N"
            ]
        },
        "organic_fertilizers": {
            "fym_tons": "8-10",
            "pressmud_tons": "3-4",
            "vermicompost_kg": "1000-1200",
            "biofertilizers": "Azospirillum + PSB + Trichoderma @ 2 kg each",
            "green_manure": "Sunhemp 10-12 kg/acre",
            "application_schedule": [
                "FYM + Pressmud: Apply in trenches before planting",
                "Vermicompost: Mix in trenches",
                "Biofertilizers: Treat setts before planting",
                "Green manure: Grow and incorporate before main crop"
            ]
        },
        "methods": [
            "Trench planting: 30cm deep trenches, 20-25% higher yield",
            "Ring pit method: 75% less seed material, 40% water saving",
            "Sub-surface drip: 30-40% water saving, 15-20% yield increase",
            "Tissue culture plants ensure disease-free crop"
        ],
        "tips": [
            "Use healthy setts from 6-8 month old crop",
            "Treat setts with fungicide and insecticide",
            "Apply trash mulching for moisture conservation",
            "Harvest at 10-12 months for optimal sucrose (min 10%)"
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
                "First: 50% N at knee-high (25-30 days)",
                "Second: 25% N at tasseling (45-50 days)"
            ]
        },
        "organic_fertilizers": {
            "fym_tons": "5-6",
            "vermicompost_kg": "600-800",
            "poultry_manure_kg": "400-500",
            "neem_cake_kg": "100",
            "biofertilizers": "Azospirillum + PSB @ 2 kg each",
            "application_schedule": [
                "FYM/Poultry: Apply 2-3 weeks before sowing",
                "Vermicompost: Mix at final land preparation",
                "Neem cake: Apply at sowing",
                "Biofertilizers: Seed treatment"
            ]
        },
        "methods": [
            "Hybrid seeds yield 30-40% more than composites",
            "Drip irrigation with fertigation increases efficiency by 40-60%",
            "Intercropping with legumes improves soil health",
            "Mechanized planting ensures uniform spacing"
        ],
        "tips": [
            "Apply 4-5 irrigations at critical stages",
            "Earthing up at 30-35 days prevents lodging",
            "Control fall armyworm using IPM",
            "Harvest when grain moisture is 20-22%"
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
                "30 days: 25% N + 25% K",
                "50 days: 25% N + 25% K"
            ]
        },
        "organic_fertilizers": {
            "fym_tons": "6-8",
            "vermicompost_kg": "800-1000",
            "neem_cake_kg": "100-120",
            "bone_meal_kg": "50",
            "biofertilizers": "Azotobacter + PSB @ 2 kg each",
            "application_schedule": [
                "FYM: Mix 2-3 weeks before transplanting",
                "Vermicompost: Apply in pits at transplanting",
                "Neem cake: Mix at transplanting",
                "Biofertilizers: Root dipping before transplanting"
            ]
        },
        "methods": [
            "Polyhouse: Year-round production, 121-162 tons/acre yield",
            "Drip + mulch: 50% water saving, better quality",
            "Staking and pruning: 15-20% more yield",
            "Hybrid F1 varieties with disease resistance"
        ],
        "tips": [
            "Transplant 30-35 day old seedlings in evening",
            "Apply calcium and boron sprays to prevent cracking",
            "Monitor whitefly using yellow sticky traps",
            "Harvest at breaker to light red stage"
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
                "30 days: 25% N + 25% K at first earthing",
                "45 days: 25% N + 25% K at second earthing"
            ]
        },
        "organic_fertilizers": {
            "fym_tons": "6-8",
            "vermicompost_kg": "1000-1200",
            "neem_cake_kg": "100",
            "bone_meal_kg": "60-80",
            "biofertilizers": "Azotobacter + PSB @ 2 kg each",
            "application_schedule": [
                "FYM: Apply 3-4 weeks before planting",
                "Vermicompost: Mix in furrows at planting",
                "Neem cake: Apply at planting",
                "Biofertilizers: Tuber treatment"
            ]
        },
        "methods": [
            "Micro-tuber technology: 20-30% yield increase",
            "Ridge and furrow: Better drainage, easier harvest",
            "Drip irrigation: 30-40% water saving",
            "Potato planter for uniform depth"
        ],
        "tips": [
            "Cut tubers with 2-3 eyes, cure 24-48 hours",
            "Earthing up 2-3 times prevents greening",
            "De-haulm 10-15 days before harvest",
            "Store at 2-4°C with 90-95% humidity"
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
                "50 days: 25% N + 25% K"
            ]
        },
        "organic_fertilizers": {
            "fym_tons": "4-5",
            "vermicompost_kg": "600-800",
            "neem_cake_kg": "80-100",
            "sulphur_kg": "20-25",
            "biofertilizers": "Azospirillum + PSB @ 2 kg each",
            "application_schedule": [
                "FYM: Apply 3 weeks before transplanting",
                "Vermicompost: Mix in beds",
                "Neem cake: Apply at transplanting",
                "Biofertilizers: Root dipping"
            ]
        },
        "methods": [
            "Raised bed: 15-20% yield increase",
            "Drip irrigation: 40% water saving",
            "Hybrid varieties: 30-40% more yield",
            "Precision transplanter"
        ],
        "tips": [
            "Transplant 45-50 day seedlings, 6-7mm thickness",
            "Apply sulfur for better pungency",
            "Stop irrigation 10-15 days before harvest",
            "Cure bulbs in shade 7-10 days"
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
                "Rhizobium: Seed treatment mandatory",
                "PSB: Seed treatment or soil application"
            ]
        },
        "methods": [
            "Ridge and furrow for better drainage",
            "Seed inoculation with Rhizobium mandatory",
            "Broad bed in high rainfall areas",
            "Weed management critical in first 45 days"
        ],
        "tips": [
            "Sow within first fortnight of June",
            "Rhizobium + fungicide seed treatment",
            "Critical irrigation at flowering and pod filling",
            "Harvest when 95% pods turn brown"
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
                "Gypsum: Apply at flowering (35-40 days)",
                "Rhizobium: Seed treatment mandatory"
            ]
        },
        "methods": [
            "Ridge and furrow improves pod filling",
            "Gypsum at flowering increases yield by 20%",
            "Drip irrigation increases efficiency",
            "Mulching conserves moisture"
        ],
        "tips": [
            "Rhizobium + fungicide seed treatment",
            "Apply gypsum @ 200 kg/acre at flowering",
            "Avoid waterlogging during pod development",
            "Harvest when leaves turn yellow"
        ]
    },
    "Pomegranate": {
        "seed_rate_kg_per_acre": "445 plants (12ft x 9ft)",
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
            "fym_tons": "10-12 per year",
            "vermicompost_kg": "1000-1200",
            "neem_cake_kg": "200",
            "biofertilizers": "Azotobacter + PSB @ 3 kg each",
            "application_schedule": [
                "FYM: Apply annually in two splits",
                "Vermicompost: Apply during flowering",
                "Neem cake: Apply every 3 months"
            ]
        },
        "methods": [
            "Drip irrigation with fertigation is standard",
            "Training and pruning for shape and yield",
            "Bahar treatment for controlling flowering time",
            "High density planting possible"
        ],
        "tips": [
            "Maintain soil pH 6.5-7.5",
            "Regular pruning to maintain vigor",
            "Protect from fruit cracking",
            "Harvest when fruit develops color"
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
                "Vermicompost: Apply in pits",
                "Neem cake: Mix at transplanting",
                "Biofertilizers: Root dipping"
            ]
        },
        "methods": [
            "Raised bed planting for better drainage",
            "Drip irrigation + mulch: Water saving",
            "Hybrid varieties with disease resistance",
            "Protective cultivation in polyhouse"
        ],
        "tips": [
            "Transplant 40-45 day old seedlings",
            "Provide stakes for support",
            "Monitor for thrips and mites",
            "Multiple pickings increase yield"
        ]
    }
}

# ====================
# SEASONAL CALENDAR - COMPLETE
# ====================
SEASONAL_CALENDAR = {
    "Kharif": {
        "description": "Monsoon crops sown with monsoon, harvested at end",
        "sowing_period": "June - August",
        "harvesting_period": "September - November",
        "characteristics": [
            "Warm weather and significant rainfall required",
            "Depends on monsoon rains",
            "Temperature: 25-35°C",
            "Rainfall: 50-100 cm"
        ],
        "crops": {
            "Rice": {"sowing": "June-July", "harvesting": "Oct-Nov", "duration": "120-150 days", "key_states": "Maharashtra, Punjab, Haryana"},
            "Cotton": {"sowing": "May-June", "harvesting": "Oct-Jan", "duration": "150-180 days", "key_states": "Maharashtra, Gujarat, Telangana"},
            "Soybean": {"sowing": "June-July", "harvesting": "Sep-Oct", "duration": "90-120 days", "key_states": "Maharashtra, MP, Rajasthan"},
            "Maize": {"sowing": "June-July", "harvesting": "Sep-Oct", "duration": "80-110 days", "key_states": "Maharashtra, Karnataka, Rajasthan"},
            "Groundnut": {"sowing": "June-July", "harvesting": "Oct-Nov", "duration": "120-140 days", "key_states": "Gujarat, Andhra Pradesh, Tamil Nadu"}
        }
    },
    "Rabi": {
        "description": "Winter crops sown in winter, harvested in spring",
        "sowing_period": "October - December",
        "harvesting_period": "March - May",
        "characteristics": [
            "Cool weather for growth, warm for ripening",
            "Needs irrigation",
            "Temperature: 10-25°C",
            "Rainfall: 25-65 cm"
        ],
        "crops": {
            "Wheat": {"sowing": "Oct-Nov", "harvesting": "Mar-Apr", "duration": "110-130 days", "key_states": "Punjab, Haryana, UP"},
            "Potato": {"sowing": "Oct-Nov", "harvesting": "Jan-Mar", "duration": "90-120 days", "key_states": "UP, West Bengal, Bihar"},
            "Onion": {"sowing": "Oct-Dec", "harvesting": "Mar-May", "duration": "120-150 days", "key_states": "Maharashtra, Karnataka, Gujarat"},
            "Tomato": {"sowing": "Oct-Nov", "harvesting": "Jan-Mar", "duration": "65-90 days", "key_states": "Maharashtra, Karnataka, AP"},
            "Chilli": {"sowing": "Oct-Nov", "harvesting": "Feb-Apr", "duration": "120-150 days", "key_states": "Andhra Pradesh, Karnataka, Maharashtra"}
        }
    },
    "Zaid": {
        "description": "Summer crops between Rabi and Kharif",
        "sowing_period": "March - May",
        "harvesting_period": "June - August",
        "characteristics": [
            "Short duration summer crops",
            "Irrigation throughout required",
            "Temperature: 25-40°C",
            "Primarily vegetables"
        ],
        "crops": {
            "Watermelon": {"sowing": "Feb-Mar", "harvesting": "May-Jun", "duration": "90-100 days", "key_states": "Karnataka, UP, Rajasthan"},
            "Cucumber": {"sowing": "Mar-Apr", "harvesting": "Jun-Jul", "duration": "60-70 days", "key_states": "Punjab, Haryana, UP"},
            "Muskmelon": {"sowing": "Feb-Mar", "harvesting": "May-Jun", "duration": "85-100 days", "key_states": "UP, Punjab, Rajasthan"}
        }
    }
}

# ====================
# DISEASE DATABASE - COMPLETE
# ====================
DISEASE_DATABASE = {
    "Rice": [
        {"name": "Blast Disease", "symptoms": "Leaf spots, neck blast, diamond-shaped lesions", "control": "Spray Tricyclazole 75% WP @ 60g/acre or Carbendazim @ 100g/acre"},
        {"name": "Brown Plant Hopper", "symptoms": "Yellowing, hopper burn, drying", "control": "Use Imidacloprid @ 20ml/acre or plant resistant varieties like Swarna Sub1"},
        {"name": "Bacterial Leaf Blight", "symptoms": "Water-soaked lesions, yellowing", "control": "Use resistant varieties, spray Streptocycline @ 15g + Copper oxychloride @ 200g/acre"},
        {"name": "Sheath Blight", "symptoms": "Oval lesions on leaf sheath", "control": "Validamycin @ 200ml/acre or Hexaconazole @ 80ml/acre"}
    ],
    "Wheat": [
        {"name": "Yellow Rust", "symptoms": "Yellow pustules in rows", "control": "Spray Propiconazole @ 100ml/acre or Mancozeb @ 200g/acre"},
        {"name": "Brown Rust", "symptoms": "Brown pustules scattered", "control": "Spray Tebuconazole @ 100ml/acre"},
        {"name": "Aphids", "symptoms": "Sticky leaves, stunted growth", "control": "Use Dimethoate @ 200ml/acre or neem oil @ 1L/acre"},
        {"name": "Loose Smut", "symptoms": "Black spore masses replacing grains", "control": "Use certified disease-free seeds, Vitavax @ 2.5g/kg seed treatment"}
    ],
    "Cotton": [
        {"name": "Pink Bollworm", "symptoms": "Bored bolls, rosette flowers", "control": "Pheromone traps @ 5/acre, spray Emamectin benzoate @ 80g/acre"},
        {"name": "Whitefly", "symptoms": "Leaf yellowing, honeydew, sooty mold", "control": "Yellow sticky traps, Imidacloprid @ 40ml/acre or Thiamethoxam @ 20g/acre"},
        {"name": "Wilt", "symptoms": "Wilting, yellowing, plant death", "control": "Crop rotation, Carbendazim soil drench @ 200g/acre"},
        {"name": "American Bollworm", "symptoms": "Damaged bolls and squares", "control": "NPV @ 250 LE/acre or Chlorantraniliprole @ 60ml/acre"}
    ],
    "Tomato": [
        {"name": "Late Blight", "symptoms": "Brown water-soaked lesions", "control": "Mancozeb @ 400g/acre or Copper oxychloride @ 400g/acre"},
        {"name": "Early Blight", "symptoms": "Target spot lesions", "control": "Mancozeb @ 400g/acre, remove infected leaves"},
        {"name": "Whitefly", "symptoms": "Yellowing, virus transmission", "control": "Yellow sticky traps @ 10/acre, Imidacloprid @ 40ml/acre"},
        {"name": "Fruit Borer", "symptoms": "Holes in fruits", "control": "Bt spray @ 200g/acre or Spinosad @ 100ml/acre"}
    ],
    "Onion": [
        {"name": "Purple Blotch", "symptoms": "Purple spots on leaves", "control": "Mancozeb @ 400g/acre spray, crop rotation"},
        {"name": "Thrips", "symptoms": "Silver streaks on leaves", "control": "Fipronil @ 80ml/acre or Imidacloprid @ 40ml/acre"},
        {"name": "Basal Rot", "symptoms": "Rotting at base", "control": "Improve drainage, Carbendazim soil drench @ 200g/acre"},
        {"name": "Stemphylium Blight", "symptoms": "Purple colored spots", "control": "Mancozeb @ 400g/acre or Azoxystrobin @ 80g/acre"}
    ],
    "Potato": [
        {"name": "Late Blight", "symptoms": "Water-soaked lesions turning brown", "control": "Mancozeb @ 400g/acre or Metalaxyl @ 200g/acre"},
        {"name": "Early Blight", "symptoms": "Concentric ring spots", "control": "Chlorothalonil @ 200g/acre"},
        {"name": "Aphids", "symptoms": "Curling leaves, virus transmission", "control": "Imidacloprid @ 40ml/acre or Thiamethoxam @ 20g/acre"}
    ],
    "Sugarcane": [
        {"name": "Red Rot", "symptoms": "Reddening of internal tissues", "control": "Use resistant varieties, remove infected canes"},
        {"name": "Smut", "symptoms": "Whip-like structures", "control": "Hot water treatment of setts @ 52°C for 30 min"},
        {"name": "Top Borer", "symptoms": "Dead hearts, bunchy tops", "control": "Chlorantraniliprole @ 60ml/acre"}
    ],
    "Chilli": [
        {"name": "Anthracnose", "symptoms": "Circular lesions on fruits", "control": "Mancozeb @ 400g/acre or Azoxystrobin @ 80g/acre"},
        {"name": "Thrips", "symptoms": "Silvering of leaves", "control": "Fipronil @ 80ml/acre or sticky traps"},
        {"name": "Powdery Mildew", "symptoms": "White powdery growth", "control": "Sulfur @ 400g/acre or Carbendazim @ 100g/acre"}
    ]
}

# ====================
# GOVERNMENT SCHEMES - COMPLETE
# ====================
GOVERNMENT_SCHEMES = {
    "PM-KISAN": {
        "name": "PM Kisan Samman Nidhi",
        "name_marathi": "पीएम किसान सम्मान निधी",
        "benefit": "₹6000/year in 3 installments of ₹2000 each",
        "eligibility": "All landholding farmers (small & marginal)",
        "website": "https://pmkisan.gov.in/",
        "helpline": "011-24300606, 155261",
        "how_to_apply": "Visit pmkisan.gov.in, register with Aadhaar, land details. Or visit nearest CSC"
    },
    "PMFBY": {
        "name": "Pradhan Mantri Fasal Bima Yojana",
        "name_marathi": "पीएम फसल बीमा योजना",
        "benefit": "Crop insurance at 2% (Kharif), 1.5% (Rabi), 5% (Horticulture)",
        "eligibility": "All farmers - landowners and tenants",
        "website": "https://pmfby.gov.in/",
        "helpline": "1800-180-1551",
        "how_to_apply": "Apply through banks, insurance companies, or CSC within sowing cutoff dates"
    },
    "Soil Health Card": {
        "name": "Soil Health Card Scheme",
        "name_marathi": "मृदा आरोग्य कार्ड योजना",
        "benefit": "Free soil testing every 2 years with fertilizer recommendations",
        "eligibility": "All farmers",
        "website": "https://soilhealth.dac.gov.in/",
        "helpline": "1800-180-1551",
        "how_to_apply": "Contact nearest Soil Testing Laboratory or District Agriculture Office"
    },
    "KCC": {
        "name": "Kisan Credit Card",
        "name_marathi": "किसान क्रेडिट कार्ड",
        "benefit": "Easy credit at 4% interest (with 3% subvention + 3% prompt repayment incentive = effective 1% interest)",
        "eligibility": "Farmers with land records",
        "website": "Contact nearest bank",
        "helpline": "1800-180-1111",
        "how_to_apply": "Visit any nationalized bank with land documents, Aadhaar, PAN"
    },
    "Maharashtra Jalyukt Shivar": {
        "name": "Jalyukt Shivar Abhiyan",
        "name_marathi": "जलयुक्त शिवार अभियान",
        "benefit": "Water conservation - Well deepening, farm ponds, watershed development",
        "eligibility": "Maharashtra farmers",
        "website": "https://jalyuktshivar.maharashtra.gov.in/",
        "helpline": "Collector Office - District level",
        "how_to_apply": "Contact District Collector Office or Gram Panchayat"
    },
    "Maharashtra CM Solar Pump": {
        "name": "Mukhyamantri Saur Krishi Vahini Yojana",
        "name_marathi": "मुख्यमंत्री सौर कृषी पंप योजना",
        "benefit": "90% subsidy on solar pump (up to 5 HP)",
        "eligibility": "Maharashtra farmers without electricity connection",
        "website": "https://www.mahadiscom.in/solar/",
        "helpline": "1800-102-3435",
        "how_to_apply": "Apply online at MSEDCL website with land documents"
    },
    "National Beekeeping & Honey Mission": {
        "name": "NBHM - Honey Mission",
        "name_marathi": "राष्ट्रीय मधमाशी पालन मोहीम",
        "benefit": "Subsidy on beekeeping equipment, training",
        "eligibility": "All farmers, especially SC/ST/Women (higher subsidy)",
        "website": "https://nbhm.nhmprojects.com/",
        "helpline": "Contact Khadi and Village Industries Commission (KVIC)",
        "how_to_apply": "Apply through District Industries Centre or online"
    },
    "PMKSY - Micro Irrigation": {
        "name": "PM Krishi Sinchayee Yojana - Drip/Sprinkler",
        "name_marathi": "पीएम कृषी सिंचन योजना",
        "benefit": "Subsidy on drip/sprinkler irrigation systems (40-55%)",
        "eligibility": "All farmers",
        "website": "https://pmksy.gov.in/",
        "helpline": "District Horticulture/Agriculture Office",
        "how_to_apply": "Contact District Agriculture Office with land details"
    }
}

# ====================
# DATABASE FUNCTIONS
# ====================

def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect('krishimitra.db')
    c = conn.cursor()
    
    # Users table
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
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Activities table
    c.execute('''CREATE TABLE IF NOT EXISTS activities
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  activity_type TEXT,
                  crop_name TEXT,
                  area_acres REAL,
                  activity_data TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    # Notifications table
    c.execute('''CREATE TABLE IF NOT EXISTS notifications
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  notification_type TEXT,
                  message TEXT,
                  status TEXT DEFAULT 'pending',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  sent_at TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash password"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password, full_name, mobile, email, district, tehsil, village, farm_size):
    """Create user account"""
    try:
        conn = sqlite3.connect('krishimitra.db')
        c = conn.cursor()
        
        password_hash = hash_password(password)
        
        c.execute('''INSERT INTO users (username, password_hash, full_name, mobile, email, 
                     district, tehsil, village, farm_size_acres)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (username, password_hash, full_name, mobile, email, district, tehsil, village, farm_size))
        
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        return True, user_id
    except sqlite3.IntegrityError:
        return False, "Username already exists"
    except Exception as e:
        return False, str(e)

def authenticate_user(username, password):
    """Authenticate user"""
    conn = sqlite3.connect('krishimitra.db')
    c = conn.cursor()
    
    password_hash = hash_password(password)
    
    c.execute('''SELECT id, username, full_name, mobile, email, district, tehsil, village, farm_size_acres
                 FROM users WHERE username=? AND password_hash=?''',
              (username, password_hash))
    
    user = c.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'full_name': user[2],
            'mobile': user[3],
            'email': user[4],
            'district': user[5],
            'tehsil': user[6],
            'village': user[7],
            'farm_size': user[8]
        }
    return None

def log_activity(user_id, activity_type, crop_name, area_acres, activity_data):
    """Log user activity"""
    conn = sqlite3.connect('krishimitra.db')
    c = conn.cursor()
    
    c.execute('''INSERT INTO activities (user_id, activity_type, crop_name, area_acres, activity_data)
                 VALUES (?, ?, ?, ?, ?)''',
              (user_id, activity_type, crop_name, area_acres, json.dumps(activity_data)))
    
    conn.commit()
    conn.close()

def get_user_activities(user_id, limit=10):
    """Get user activities"""
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
    """Create notification"""
    conn = sqlite3.connect('krishimitra.db')
    c = conn.cursor()
    
    c.execute('''INSERT INTO notifications (user_id, notification_type, message)
                 VALUES (?, ?, ?)''',
              (user_id, notification_type, message))
    
    conn.commit()
    conn.close()

# ====================
# NOTIFICATION FUNCTIONS
# ====================

def send_sms_notification(mobile, message):
    """Send SMS using Twilio"""
    try:
        # For demo
        st.info(f"📱 SMS: {message[:50]}... to {mobile}")
        
        # Actual Twilio code:
        """
        from twilio.rest import Client
        account_sid = st.secrets["twilio"]["account_sid"]
        auth_token = st.secrets["twilio"]["auth_token"]
        phone_number = st.secrets["twilio"]["phone_number"]
        
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=message,
            from_=phone_number,
            to=f"+91{mobile}"
        )
        return True, message.sid
        """
        
        return True, "demo_message_id"
        
    except Exception as e:
        return False, str(e)

def send_whatsapp_notification(mobile, message):
    """Send WhatsApp using Twilio"""
    try:
        # For demo
        st.success(f"💬 WhatsApp: {message[:50]}... to {mobile}")
        
        # Actual Twilio code:
        """
        from twilio.rest import Client
        account_sid = st.secrets["twilio"]["account_sid"]
        auth_token = st.secrets["twilio"]["auth_token"]
        whatsapp_number = st.secrets["twilio"]["whatsapp_number"]
        
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=message,
            from_=whatsapp_number,
            to=f'whatsapp:+91{mobile}'
        )
        return True, message.sid
        """
        
        return True, "demo_whatsapp_id"
        
    except Exception as e:
        return False, str(e)

# ====================
# API FUNCTIONS
# ====================

def fetch_agmarknet_prices(state, district, commodity):
    """Fetch from Agmarknet"""
    try:
        try:
            api_key = st.secrets["api_keys"]["data_gov_in"]
        except:
            api_key = "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b"
            
        url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
        
        params = {
            "api-key": api_key,
            "format": "json",
            "filters[state]": state,
            "filters[district]": district,
            "filters[commodity]": commodity,
            "limit": 30
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'records' in data and len(data['records']) > 0:
                return pd.DataFrame(data['records'])
        return None
    except:
        return None

def fetch_weather_data(district, tehsil):
    """Fetch weather"""
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
    """Get nearest mandis"""
    mandis = {
        "Pune": ["Pune Market Yard", "Baramati APMC", "Daund APMC", "Junnar APMC"],
        "Nashik": ["Nashik APMC", "Malegaon Market", "Sinnar APMC", "Lasalgaon APMC"],
        "Nagpur": ["Nagpur Cotton Market", "Kamptee APMC", "Katol Market"],
        "Aurangabad": ["Aurangabad APMC", "Paithan Market", "Gangapur APMC"],
        "Solapur": ["Solapur APMC", "Pandharpur Market", "Barshi APMC"],
        "Kolhapur": ["Kolhapur APMC", "Kagal Market", "Ichalkaranji Market"],
        "Ahmednagar": ["Ahmednagar APMC", "Sangamner Market", "Kopargaon APMC"],
        "Thane": ["Kalyan Market", "Bhiwandi APMC", "Palghar Market"],
        "Mumbai Suburban": ["Vashi APMC", "Turbhe Market"],
        "Satara": ["Satara APMC", "Karad Market", "Wai APMC"],
        "Sangli": ["Sangli APMC", "Miraj Market", "Islampur Market"]
    }
    return mandis.get(district, ["Contact District Agriculture Office for APMC info"])

def generate_sample_prices(crop_name):
    """Generate sample prices"""
    import random
    dates = [datetime.now() - timedelta(days=x) for x in range(30, 0, -1)]
    base_price = random.randint(1500, 3500)
    prices = [base_price + random.randint(-300, 400) for _ in dates]
    return pd.DataFrame({'Date': dates, 'Price (₹/quintal)': prices})

# ====================
# MAIN APPLICATION
# ====================

def main():
    init_database()
    
    st.markdown('<div class="main-header">🌾 KrishiMitra Maharashtra</div>', unsafe_allow_html=True)
    st.markdown("### संपूर्ण कृषी व्यवस्थापन प्रणाली | Complete Agriculture Management System")
    
    if st.session_state.user_data is None:
        show_auth_page()
    else:
        show_main_app()

def show_auth_page():
    """Authentication page"""
    tab1, tab2 = st.tabs(["🔐 Login / प्रवेश", "📝 Register / नोंदणी"])
    
    with tab1:
        st.markdown("### Login / प्रवेश करा")
        
        username = st.text_input("Username / वापरकर्ता नाव", key="login_user")
        password = st.text_input("Password / पासवर्ड", type="password", key="login_pass")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Login / प्रवेश", type="primary", use_container_width=True):
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
                    st.error("Invalid username or password / चुकीचे तपशील")
    
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
            district = st.selectbox("District / जिल्हा", list(MAHARASHTRA_LOCATIONS.keys()), key="reg_dist")
            
            tehsil = None
            village = None
            
            if district:
                tehsils = list(MAHARASHTRA_LOCATIONS[district]["tehsils"].keys())
                tehsil = st.selectbox("Tehsil / तालुका", tehsils, key="reg_teh")
                
                if tehsil:
                    villages = MAHARASHTRA_LOCATIONS[district]["tehsils"][tehsil]
                    village = st.selectbox("Village / गाव", villages, key="reg_vil")
            
            farm_size = st.number_input("Farm Size (Acres)", min_value=0.1, value=1.0, step=0.5, key="reg_size")
        
        if st.button("Register / नोंदणी करा", type="primary"):
            # Validation
            if not all([new_username, new_password, full_name, mobile, district, tehsil, village]):
                st.error("Please fill all required fields / सर्व माहिती भरा")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters")
            elif not mobile.isdigit() or len(mobile) != 10:
                st.error("Please enter valid 10-digit mobile number")
            else:
                success, result = create_user(new_username, new_password, full_name, mobile, 
                                             email, district, tehsil, village, farm_size)
                if success:
                    st.success("✅ Account created successfully! Please login")
                else:
                    st.error(f"Error: {result}")

def show_main_app():
    """Main application after login"""
    user = st.session_state.user_data
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {user['full_name']}")
        st.markdown(f"**📍 {user['village']}, {user['tehsil']}**")
        st.markdown(f"**🌾 Farm: {user['farm_size']} acres**")
        
        st.markdown("---")
        
        # Notification toggle
        st.markdown("### 🔔 Notifications")
        enable_sms = st.checkbox("SMS Alerts", value=st.session_state.notifications_enabled)
        enable_whatsapp = st.checkbox("WhatsApp Alerts")
        
        if enable_sms or enable_whatsapp:
            st.session_state.notifications_enabled = True
            st.success("✅ Enabled")
        
        st.markdown("---")
        
        # Navigation
        page = st.radio("Navigation", [
            "🏠 Dashboard",
            "🌱 Seed & Fertilizer",
            "📊 Market Prices",
            "🎯 Best Practices",
            "💰 Profit Calculator",
            "📚 Crop Knowledge",
            "📅 Seasonal Planner",
            "🌡️ Weather & Soil",
            "🏛️ Govt Schemes",
            "🏪 Nearest Mandis",
            "🐛 Disease Guide",
            "📱 Notifications",
            "📊 My Activity"
        ])
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user_data = None
            st.rerun()
    
    # Route to pages
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
    elif page == "🏛️ Govt Schemes":
        show_government_schemes_page()
    elif page == "🏪 Nearest Mandis":
        show_nearest_mandis()
    elif page == "🐛 Disease Guide":
        show_disease_guide()
    elif page == "📱 Notifications":
        show_notifications()
    elif page == "📊 My Activity":
        show_activity_history()

def show_dashboard():
    """Dashboard"""
    user = st.session_state.user_data
    
    st.markdown(f"### 🏠 Dashboard - Welcome {user['full_name']}!")
    
    # Season info
    current_month = datetime.now().month
    if current_month in [6, 7, 8]:
        st.success("🌧️ **Kharif Season Active** - Time for Rice, Cotton, Soybean!")
    elif current_month in [10, 11, 12, 1, 2]:
        st.success("❄️ **Rabi Season Active** - Time for Wheat, Onion, Potato!")
    else:
        st.info("☀️ **Zaid Season** - Summer vegetables with irrigation")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Your Farm", f"{user['farm_size']} acres")
    with col2:
        activities = get_user_activities(user['id'], limit=1000)
        st.metric("Activities", len(activities))
    with col3:
        st.metric("District", user['district'])
    with col4:
        st.metric("Notifications", "ON" if st.session_state.notifications_enabled else "OFF")
    
    # Recent activities
    st.markdown("### 📊 Recent Activities")
    recent = get_user_activities(user['id'], limit=5)
    
    if recent:
        for act in recent:
            st.markdown(f"- **{act[0]}**: {act[1]} ({act[2]} acres) - {act[4]}")
    else:
        st.info("No activities yet. Start using calculators!")
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.button("🌱 Calculate Seeds", use_container_width=True)
    with col2:
        st.button("📊 Check Prices", use_container_width=True)
    with col3:
        st.button("🌡️ Weather", use_container_width=True)

def show_seed_fertilizer_calculator():
    """Seed & fertilizer calculator - COMPLETE"""
    st.markdown("### 🌱 Seed & Fertilizer Calculator")
    st.markdown("### बी आणि खत मोजणी")
    
    col1, col2 = st.columns(2)
    
    with col1:
        crop = st.selectbox("Select Crop / पीक निवडा", list(CROP_DATABASE.keys()))
        area = st.number_input("Area (Acres) / क्षेत्र (एकर)", min_value=0.1, value=1.0, step=0.1)
    
    with col2:
        planting_method = st.selectbox("Method / पद्धत", ["Standard", "High Density", "SRI/SCI"])
        fert_type = st.radio("Fertilizer / खत", ["Chemical / रासायनिक", "Organic / सेंद्रिय", "Both / दोन्ही"])
    
    if st.button("Calculate / मोजणी करा", type="primary"):
        crop_info = CROP_DATABASE[crop]
        
        # Log activity
        log_activity(user['id'], "Seed Calculation", crop, area, {"method": planting_method, "fert": fert_type})
        
        # Seed calculation
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
        
        # Display
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
        
        # Chemical fertilizers
        if "Chemical" in fert_type or "Both" in fert_type:
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
            
            st.markdown("**Application Schedule / वापर वेळापत्रक:**")
            for schedule in chem['application_schedule']:
                st.write(f"• {schedule}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Organic fertilizers
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
                st.write(f"**Vermicompost (गांडुळखत):** {org['vermicompost_kg']} kg/acre × {area} acres = **{vermi_total:.0f} kg**")
            
            if 'neem_cake_kg' in org:
                neem = org['neem_cake_kg'].split('-') if '-' in str(org['neem_cake_kg']) else [org['neem_cake_kg']]
                neem_total = float(neem[0]) * area
                st.write(f"**Neem Cake:** {org['neem_cake_kg']} kg/acre = **{neem_total:.0f} kg**")
            
            if 'green_manure' in org:
                st.write(f"**Green Manure:** {org['green_manure']}")
            
            if 'biofertilizers' in org:
                st.write(f"**Biofertilizers:** {org['biofertilizers']}")
            
            if 'gypsum_kg' in org:
                st.write(f"**Gypsum:** {org['gypsum_kg']} kg/acre")
            
            if 'pressmud_tons' in org:
                st.write(f"**Pressmud:** {org['pressmud_tons']} tons/acre")
            
            st.markdown("**Application Schedule:**")
            for schedule in org['application_schedule']:
                st.write(f"• {schedule}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Growing info
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
        
        # Send notification if enabled
        if st.session_state.notifications_enabled:
            user = st.session_state.user_data
            msg = f"KrishiMitra: Seed calculation done for {crop} ({area} acres). Seeds needed: {total_seeds:.0f} kg. Check app for fertilizer details."
            send_sms_notification(user['mobile'], msg)
            create_notification(user['id'], "calculation", msg)

# Continuing with remaining functions...

def show_live_market_prices():
    """Market prices"""
    st.markdown("### 📊 Live Market Prices / थेट बाजारभाव")
    
    user = st.session_state.user_data
    
    col1, col2 = st.columns(2)
    
    with col1:
        commodity = st.selectbox("Commodity / वस्तू", list(CROP_DATABASE.keys()))
    
    with col2:
        st.info(f"📍 {user['district']} District")
    
    if st.button("Fetch Prices / भाव आणा", type="primary"):
        with st.spinner("Fetching from Agmarknet..."):
            data = fetch_agmarknet_prices("Maharashtra", user['district'], commodity)
            
            if data is not None and len(data) > 0:
                st.success("✅ Live Government Data")
                
                try:
                    latest = data.iloc[0]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Min Price", f"₹{latest.get('min_price', 'N/A')}")
                    with col2:
                        st.metric("Max Price", f"₹{latest.get('max_price', 'N/A')}")
                    with col3:
                        st.metric("Modal Price", f"₹{latest.get('modal_price', 'N/A')}")
                    
                    st.dataframe(data.head(10), use_container_width=True)
                    
                except:
                    st.dataframe(data.head(10))
            else:
                st.warning("Live data unavailable. Showing sample trend:")
                sample_data = generate_sample_prices(commodity)
                
                fig = px.line(sample_data, x='Date', y='Price (₹/quintal)',
                             title=f'{commodity} Price Trend')
                st.plotly_chart(fig, use_container_width=True)
                
                st.info("""
                **Get Live Data:**
                - Agmarknet: https://agmarknet.gov.in/
                - eNAM: https://www.enam.gov.in/
                - Helpline: 1800-270-0224
                """)

def show_best_practices():
    """Best practices"""
    st.markdown("### 🎯 Best Farming Practices")
    
    crop_name = st.selectbox("Select Crop", list(CROP_DATABASE.keys()))
    crop = CROP_DATABASE[crop_name]
    
    st.markdown(f"### 🌾 {crop_name} - Complete Guide")
    
    # Basic info
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
    
    # Methods
    st.markdown("### 🚜 High-Yield Methods")
    for idx, method in enumerate(crop['methods'], 1):
        with st.expander(f"Method {idx}: {method.split(':')[0]}"):
            st.write(method)
    
    # Tips
    st.markdown("### 💡 Expert Tips")
    for tip in crop['tips']:
        st.success(f"✓ {tip}")

def show_profit_calculator():
    """Profit calculator - COMPLETE"""
    st.markdown("### 💰 Profit & ROI Calculator")
    
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
        
        # Cost breakdown chart
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
        
        # Log activity
        user = st.session_state.user_data
        log_activity(user['id'], "Profit Calculation", crop, area, {
            "costs": total_cost, "revenue": gross_revenue, "profit": net_profit, "roi": roi
        })

def show_knowledge_base():
    """Knowledge base"""
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
    """Seasonal planner - COMPLETE"""
    st.markdown("### 📅 Seasonal Crop Planner")
    
    current_month = datetime.now().month
    current_month_name = datetime.now().strftime("%B")
    
    if current_month in [6, 7, 8]:
        st.success("🌧️ **Kharif Season** - Time for monsoon crops!")
    elif current_month in [10, 11, 12, 1, 2]:
        st.success("❄️ **Rabi Season** - Time for winter crops!")
    else:
        st.info("☀️ **Zaid Season** - Summer vegetables!")
    
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
        st.write(f"**States:** {crop_data['key_states']}")
        st.markdown('</div>', unsafe_allow_html=True)

def show_weather_soil():
    """Weather & soil"""
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
            st.info("Visit IMD: https://mausam.imd.gov.in/")
    
    st.markdown("---")
    st.markdown("### 🧪 Soil Testing")
    
    st.info("""
    **Free Soil Health Card:**
    - Apply at: https://soilhealth.dac.gov.in/
    - Contact: District Agriculture Office
    - Get tested every 2 years
    - Receive customized fertilizer recommendations
    - Improve soil health and save costs
    """)
    
    st.markdown(f"**Contact:** District Agriculture Office, {user['district']}")

def show_government_schemes_page():
    """Government schemes - COMPLETE"""
    st.markdown("### 🏛️ Government Schemes for Farmers")
    st.markdown("### शेतकऱ्यांसाठी सरकारी योजना")
    
    for scheme_id, scheme in GOVERNMENT_SCHEMES.items():
        with st.expander(f"📋 {scheme['name']} / {scheme.get('name_marathi', '')}"):
            st.write(f"**Benefit:** {scheme['benefit']}")
            st.write(f"**Eligibility:** {scheme['eligibility']}")
            st.write(f"**Website:** {scheme['website']}")
            st.write(f"**Helpline:** {scheme['helpline']}")
            st.write(f"**How to Apply:** {scheme['how_to_apply']}")
            
            if scheme_id == "PM-KISAN":
                st.success("✅ Most farmers eligible! Check pmkisan.gov.in")
            elif scheme_id == "PMFBY":
                st.warning("⏰ Apply before sowing deadline")

def show_nearest_mandis():
    """Nearest mandis"""
    st.markdown("### 🏪 Nearest Markets / जवळची मंडी")
    
    user = st.session_state.user_data
    mandis = get_nearest_mandis(user['district'])
    
    st.markdown(f"### {user['district']} District Markets")
    
    for mandi in mandis:
        st.markdown('<div class="price-card">', unsafe_allow_html=True)
        st.write(f"📍 **{mandi}**")
        st.write("Contact: District APMC Office")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.info("""
    **Online Markets:**
    - eNAM: https://www.enam.gov.in/
    - Agmarknet: https://agmarknet.gov.in/
    - Helpline: 1800-270-0224
    """)

def show_disease_guide():
    """Disease guide - COMPLETE"""
    st.markdown("### 🐛 Crop Disease Management")
    
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
    
    st.markdown("### 💡 General IPM Practices")
    st.success("✓ Use pheromone traps and light traps regularly")
    st.success("✓ Maintain field hygiene - remove infected plants")
    st.success("✓ Use disease-resistant varieties")
    st.success("✓ Apply neem-based organic pesticides")
    st.success("✓ Encourage natural predators (ladybirds, spiders)")
    st.success("✓ Practice crop rotation")
    st.success("✓ Monitor fields regularly for early detection")

def show_notifications():
    """Notifications page"""
    st.markdown("### 📱 Your Notifications")
    
    user = st.session_state.user_data
    
    conn = sqlite3.connect('krishimitra.db')
    c = conn.cursor()
    
    c.execute('''SELECT notification_type, message, status, created_at
                 FROM notifications WHERE user_id=?
                 ORDER BY created_at DESC LIMIT 20''',
              (user['id'],))
    
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
    """Activity history"""
    st.markdown("### 📊 Your Activity History")
    
    user = st.session_state.user_data
    activities = get_user_activities(user['id'], limit=50)
    
    if activities:
        df = pd.DataFrame(activities, columns=['Activity', 'Crop', 'Area (acres)', 'Data', 'Date'])
        st.dataframe(df, use_container_width=True)
        
        # Activity chart
        fig = px.bar(df, x='Crop', y='Area (acres)', title='Crops Calculated')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No activity history yet. Start using the app!")

if __name__ == "__main__":
    main()