import urllib.parse
import streamlit as st
from jobspy.model import Country

PERMANENT_BLOCK_MARKERS = ("403", "cf-waf", "forbidden", "cloudflare", "just a moment")

def inject_custom_css():
    """Inject CSS agar antarmuka nyaman digunakan di layar HP (Mobile-friendly)."""
    st.markdown("""
    <style>
        @media (max-width: 768px) {
            .stButton button {
                font-size: 18px !important;
                padding: 0.75rem 1.5rem !important;
                min-height: 50px !important;
            }
            .stCheckbox label {
                font-size: 16px !important;
            }
            .stTextInput input, .stSelectbox select, .stNumberInput input {
                font-size: 16px !important;
                min-height: 44px !important;
            }
            .stExpander {
                margin-bottom: 8px !important;
            }
        }
        .dua-card {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            margin: 16px 0;
            border-right: 4px solid #2e7d32;
        }
        .dua-card p {
            font-size: 18px;
            line-height: 1.8;
            color: #1a1a1a;
        }
        .dua-card .attribution {
            font-size: 14px;
            color: #555;
            font-style: italic;
            margin-top: 8px;
        }
    </style>
    """, unsafe_allow_html=True)

def render_dua_cards():
    """Menampilkan pesan penguat dan doa saat pencarian berlangsung."""
    st.markdown("""
    <div class="dua-card">
        <p>"Barang siapa memperbanyak istighfar; niscaya Allah memberikan jalan keluar bagi setiap kesedihannya, kelapangan untuk setiap kesempitannya dan rizki dari arah yang tidak disangka-sangka."</p>
        <div class="attribution">— HR. Ahmad dari Ibnu Abbas</div>
    </div>
    <div class="dua-card">
        <p>"Aku (Nabi Nuh) berkata (pada mereka), 'Beristighfarlah kepada Rabb kalian, sungguh Dia Maha Pengampun. Niscaya Dia akan menurunkan kepada kalian hujan yang lebat dari langit. Dan Dia akan memperbanyak harta serta anak-anakmu, juga mengadakan kebun-kebun dan sungai-sungai untukmu.'"</p>
        <div class="attribution">— QS. Nuh: 10-12</div>
    </div>
    """, unsafe_allow_html=True)

def is_permanent_block(error_msg: str) -> bool:
    """Mendeteksi blokir permanen dari Cloudflare / WAF."""
    if not error_msg:
        return False
    lowered = error_msg.lower()
    return any(marker in lowered for marker in PERMANENT_BLOCK_MARKERS)

def glassdoor_supports_country(country_str: str) -> bool:
    """Validasi apakah Glassdoor mendukung negara yang dipilih."""
    try:
        country = Country.from_string(country_str)
    except ValueError:
        return False
    return len(country.value) == 3

def build_google_search_term(search_term: str, location: str, hours_old: int, exclude_age: bool = False, custom_exclude: str = "") -> str:
    """Membuat sintaks pencarian otomatis untuk Google Jobs."""
    term = search_term.strip() if search_term and search_term.strip() else "jobs"
    if not term.lower().endswith("jobs"):
        term += " jobs"

    if location and location.strip():
        term += f" near {location.strip()}"

    if hours_old and hours_old > 0:
        if hours_old <= 24:
            term += " since yesterday"
        elif hours_old <= 24 * 7:
            term += " this week"
        elif hours_old <= 24 * 30:
            term += " this month"

    if exclude_age:
        term += " -usia -age -umur"

    if custom_exclude and custom_exclude.strip():
        for word in custom_exclude.strip().split():
            if word.strip():
                term += f" -{word.strip()}"

    return term