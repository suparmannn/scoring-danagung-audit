# instal librari: pip install pandas streamlit openpyxl
# cara run: streamlit run scoring.py
# import json
# import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
import os
import json
import numpy as np
from datetime import datetime
from automation import apply_automation, get_scenario_presets
from streamlit_lottie import st_lottie
from fpdf import FPDF
# import requests

st.set_page_config(page_title="Audit Tool - Scoring Danagung", layout="wide")

# --- CUSTOM CSS UNTUK STYLING INPUT ---
# --- REVISI CSS (Ganti Poin 3 & 5) ---
st.markdown("""
    <style>
            
    @keyframes pulse {
        0% { opacity: 0.5; transform: scale(1); }
        50% { opacity: 0.8; transform: scale(1.05); text-shadow: 0 0 10px #eab308; }
        100% { opacity: 0.5; transform: scale(1); }
    }
    .watermark {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 9999;
        color: #eab308; /* Warna Gold Danagung */
        font-family: 'Courier New', monospace;
        font-weight: bold;
        animation: pulse 3s infinite ease-in-out;
        background: rgba(30, 41, 59, 0.7);
        padding: 5px 15px;
        border-radius: 20px;
        border: 1px solid #eab308;
    }     
            .footer-watermark {
        position: fixed;
        bottom: 10px;
        right: 20px;
        color: #eab308; /* Warna Gold */
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 0.85rem;
        font-weight: bold;
        opacity: 0.6;
        z-index: 100;
        letter-spacing: 1px;
    }
    /* 1. & 2. (Tetap seperti kode Anda) */
    .main { background-color: #0f172a; }
    .report-card { 
        background-color: #1e293b; 
        padding: 25px; 
        border-radius: 15px; 
        border-left: 8px solid #eab308; 
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); 
        margin-bottom: 20px; 
    }

    /* 3. REVISI: Styling untuk box DISPLAY ONLY (Warna Slate Grey) */
    div[data-testid="stTextInput"] input:disabled {
        background-color: #334155 !important; /* Warna Slate (Bukan Biru) */
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: bold;
        font-size: 1.1rem;
        opacity: 1;
        border: none !important;
        border-radius: 10px !important;
        height: 45px;
    }
    
    /* Hilangkan border container agar lebih rapi */
    div[data-testid="stTextInput"] div[data-baseweb="input"] {
        background-color: transparent !important;
        border: none !important;
    }

    /* 4. (Tetap seperti kode Anda) */
    .stTable { border-radius: 10px; overflow: hidden; border: 1px solid #334155; }
    .stTable th { background-color: #334155 !important; color: #e2e8f0 !important; text-transform: uppercase; }

    /* 5. REVISI: Tooltip agar selalu di atas dan berwarna Gold OJK */
    .stTooltipIcon {
        color: #eab308 !important;
        margin-bottom: 5px;
    }
            
            /* Efek kartu melayang saat di-hover */
.report-card:hover {
    transform: translateY(-5px);
    transition: all 0.3s ease;
    box-shadow: 0 10px 20px rgba(234, 179, 8, 0.2);
    border-left: 12px solid #eab308 !important;
}

# /* --- STYLING TABS DANAGUNG --- */
#     /* Container utama Tab */
#     div[data-testid="stTabs"] {
#         background-color: #e2e8f0; /* Menyesuaikan background dark slate Bapak */
#         padding: 10px 20px 0px 20px;
#         border-radius: 15px 15px 0 0;
#     }

    /* Style untuk setiap tombol Tab */
    button[data-baseweb="tab"] {
        color: #1e293b !important; /* Warna teks saat tidak aktif (Abu-abu) */
        font-weight: bold;
        font-size: 1rem;
        transition: all 0.3s ease;
    }

    /* Efek saat kursor di atas Tab (Hover) */
    button[data-baseweb="tab"]:hover {
        color: #c21b1b !important; /* Berubah jadi Merah Danagung */
        background-color: rgba(194, 27, 27, 0.1);
    }

    /* Style untuk Tab yang sedang AKTIF (Emas) */
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #eab308 !important; /* Teks jadi Emas */
        border-bottom: 3px solid #eab308 !important; /* Garis bawah Emas */
        background-color: rgba(234, 179, 8, 0.05); /* Tanda tipis emas di background */
    }

    /* Menghilangkan garis bawah default Streamlit yang tipis */
    div[data-testid="stTabs"] [data-baseweb="tab-list"] {
        border-bottom: 1px solid #334155;
    }
            
            /* --- STYLE LIST ALA SLIDE PPT --- */
    .ppt-container {
        margin: 20px 0;
    }

    .ppt-card {
        background: #1e293b; /* Warna gelap slate */
        border-left: 10px solid #c21b1b; /* Aksen Merah Danagung */
        padding: 20px;
        margin-bottom: 15px;
        border-radius: 0 15px 15px 0;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.3);
        transition: transform 0.3s ease;
    }

    .ppt-card:hover {
        transform: scale(1.02);
        border-left: 10px solid #eab308; /* Berubah jadi Emas saat di-hover */
    }

    .ppt-title {
        color: #eab308; /* Warna Emas untuk Judul */
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
    }

    .ppt-content {
        color: #e2e8f0;
        font-size: 1rem;
        line-height: 1.5;
    }

    .ppt-icon {
        margin-right: 10px;
        font-size: 1.4rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. LOAD DATA ---
# --- INITIALIZE COLLATERAL STATE ---
@st.cache_data
def load_excel():
    file_path = 'Simulasi Skoring Danagung.xlsx'
    if not os.path.exists(file_path):
        st.error(f"File '{file_path}' tidak ditemukan!")
        st.stop()
    df_data = pd.read_excel(file_path, sheet_name='DATA SCORE')
    df_hitung = pd.read_excel(file_path, sheet_name='HITUNG SCORE')
    
    df_data.columns = df_data.columns.str.strip()
    df_hitung.columns = df_hitung.columns.str.strip()
    
    # --- PERBAIKAN: Isi sel kosong dengan 0 agar tidak jadi NaN ---
    df_hitung['bobot'] = pd.to_numeric(df_hitung['bobot'], errors='coerce').fillna(0)
    df_hitung['bobot.1'] = pd.to_numeric(df_hitung['bobot.1'], errors='coerce').fillna(0)
    
    return df_data, df_hitung


df_data, df_hitung = load_excel()
if 'collaterals' not in st.session_state:
    st.session_state.collaterals = [] # List untuk menampung banyak agunan

# --- INITIALIZE DSR/IDIR SETTINGS ---
param_fields = {
    'p_rt_murni': 'Biaya RT Pokok',
    'p_sekolah': 'Biaya Sekolah',
    'p_transport': 'Transportasi',
    'p_listrik': 'Listrik',
    'p_telepon': 'Telepon',
    'p_hutang': 'Hutang Lain (SLIK)',
    'p_arisan': 'Arisan'
}

if 'dsr_active_params' not in st.session_state:
    st.session_state.dsr_active_params = ['p_hutang'] # Default DSR hanya hutang
if 'idir_active_params' not in st.session_state:
    st.session_state.idir_active_params = list(param_fields.keys()) # Default IDIR semua masuk

  # --- INITIALIZE STATE DEFAULTS ---
# Kita cek satu per satu agar variabel baru tetap terbuat meskipun aplikasi sedang running
if 'total_penghasilan' not in st.session_state: st.session_state['total_penghasilan'] = 29212124
if 'pengeluaran_usaha' not in st.session_state: st.session_state['pengeluaran_usaha'] = 9220230
if 'p_rt_murni' not in st.session_state: st.session_state['p_rt_murni'] = 293234 
if 'p_sekolah' not in st.session_state: st.session_state['p_sekolah'] = 23032
if 'p_transport' not in st.session_state: st.session_state['p_transport'] = 200000
if 'p_listrik' not in st.session_state: st.session_state['p_listrik'] = 1000000
if 'p_telepon' not in st.session_state: st.session_state['p_telepon'] = 2000
if 'p_hutang' not in st.session_state: st.session_state['p_hutang'] = 450000
if 'p_arisan' not in st.session_state: st.session_state['p_arisan'] = 239000
if 'angs_diambil_val' not in st.session_state: st.session_state['angs_diambil_val'] = 306638
if 'cap_tenor' not in st.session_state: st.session_state['cap_tenor'] = 30 # Pastikan ini ada agar LTV tidak 0%

# --- 2. ENCODER & HELPERS ---
class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        return super(NpEncoder, self).default(obj)
    
    # --- HELPER FUNCTIONS ---
def format_rp(val):
    """Mengubah angka (int/float) jadi teks format Rp 1.000.000"""
    return f"Rp {val:,.0f}".replace(",", ".")

def parse_rp(text):
    """Membersihkan teks format Rp agar jadi angka murni (int)"""
    clean = "".join(filter(str.isdigit, str(text)))
    return int(clean) if clean else 0

def get_idx(options, state_key, default_idx=0):
    """Mencari posisi index kata berdasarkan session state secara aman"""
    val = st.session_state.get(state_key)
    if val in options:
        return options.index(val)
    return default_idx

    

class CreditReport(FPDF):
    def header(self):
        # Logo Danagung (Jika file ada)
        if os.path.exists('logo_danagung.png'):
            self.image('logo_danagung.png', 10, 8, 33)
        
        self.set_font('helvetica', 'B', 15)
        self.set_text_color(194, 27, 27) # Merah Danagung
        self.cell(80)
        self.cell(30, 10, 'LAPORAN AUDIT SCORING KREDIT', 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Halaman {self.page_no()} | © 2026 BPR Danagung - Audit Tool v1.0', 0, 0, 'C')

# TAMBAHKAN 'risk_description' di dalam kurung (parameter ke-4)
def generate_pdf_report(data_json, risk_status, risk_color_hex, risk_description):
    # Fungsi bantu untuk membersihkan teks agar tidak error encoding
    def clean_text(text):
        if text is None: return ""
        # Ganti simbol Rp yang aneh dengan Rp standar
        text = str(text).replace('Rp', 'Rp.').replace('–', '-').replace('—', '-')
        # Encode ke latin-1 dan abaikan karakter yang tidak dikenal agar tidak crash
        return text.encode('latin-1', 'replace').decode('latin-1')

    pdf = CreditReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # --- 1. INFORMASI PEMOHON ---
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, clean_text(' I. PROFIL PEMOHON'), 0, 1, 'L', fill=True)
    pdf.set_font('helvetica', '', 10)
    
    pdf.cell(50, 8, clean_text('Nama Nasabah:'), 0, 0)
    pdf.cell(0, 8, f": {clean_text(data_json['data']['pemohon']['name'])}", 0, 1)
    
    pdf.cell(50, 8, clean_text('Estimasi Plafon:'), 0, 0)
    # Gunakan format_rp tapi bersihkan hasilnya
    plafon_str = format_rp(data_json["data"]["pengajuan"]["submission_loan"])
    pdf.cell(0, 8, f": {clean_text(plafon_str)}", 0, 1)
    pdf.ln(5)

    # --- 2. HASIL SCORING (TABEL) ---
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, clean_text(' II. RINCIAN POIN SCORING'), 0, 1, 'L', fill=True)
    
    # Header Tabel
    pdf.set_fill_color(234, 179, 8) 
    pdf.set_text_color(255)
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(50, 10, ' Kategori', 1, 0, 'C', fill=True)
    pdf.cell(70, 10, ' Total Poin', 1, 0, 'C', fill=True)
    pdf.cell(70, 10, ' Skor Akhir Pilar', 1, 1, 'C', fill=True)
    
    # Isi Tabel
    pdf.set_text_color(0)
    pdf.set_font('helvetica', '', 10)
    for pilar, point in data_json["data"]["scoring_point"].items():
        pdf.cell(50, 8, f" {pilar.upper()}", 1, 0)
        pdf.cell(70, 8, f" {point}", 1, 0, 'C')
        pdf.cell(70, 8, f" {point}", 1, 1, 'C')
    
    pdf.ln(10)

    # --- 3. KESIMPULAN RISIKO ---
    h = risk_color_hex.lstrip('#')
    rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    
    pdf.set_font('helvetica', 'B', 14)
    pdf.set_text_color(*rgb)
    pdf.cell(0, 15, clean_text(f'STATUS ANALISA: {risk_status.upper()}'), 1, 1, 'C')
    
    pdf.ln(5)
    pdf.set_text_color(0)
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(0, 8, clean_text('Analisa Auditor Kredit:'), 0, 1)
    pdf.set_font('helvetica', 'I', 10)
    
    # Gunakan clean_text untuk deskripsi yang panjang dari Excel
    pdf.multi_cell(0, 6, clean_text(risk_description))

    # --- FINAL: OUTPUT HANDLING ---
    # Logika agar aman di versi library fpdf lama maupun baru
   # --- FINAL: OUTPUT HANDLING (PASTI JADI BINARY) ---
    pdf_output = pdf.output()
    
    # Jika output masih berupa string, kita paksa jadi binary dengan encoding latin-1
    if isinstance(pdf_output, str):
        return pdf_output.encode('latin-1')
    
    # Jika sudah berupa bytearray (versi fpdf2), tinggal diconvert ke bytes
    return bytes(pdf_output)

KOLEKTIBILITAS_DATA = {
    "tanpa_agunan": {
        "KOL 1 Tanpa Agunan": 5, "KOL 2 Tanpa Agunan": 4, "KOL 3 Tanpa Agunan": 3, 
        "KOL 4 Tanpa Agunan": 2, "KOL 5 Tanpa Agunan": 1
    },
    "dengan_agunan": {
        "KOL 1 Agunan": 5, "KOL 2 Agunan": 3, "KOL 3 Agunan": 2, 
        "KOL 4 Agunan": 1, "KOL 5 Agunan": 0
    },
    "debitur_baru": { "NO DIN": 2 }
}

CONFIG_FILE = 'config_perhitungan.json'

def save_config(dsr_list, idir_list):
    config_data = {
        "dsr_params": dsr_list,
        "idir_params": idir_list,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f, indent=4)
    st.sidebar.success("✅ Konfigurasi Berhasil Disimpan!")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return None

# --- MASTER DATA RISIKO (BE REFERENCE) ---
@st.cache_data
def load_master_risiko():
    file_path = 'master_risiko.json'
    if not os.path.exists(file_path):
        st.error(f"File '{file_path}' tidak ditemukan! Pastikan master data risiko sudah ada.")
        return []
    with open(file_path, 'r') as f:
        return json.load(f)
MASTER_RISIKO_SCORE = load_master_risiko()

def get_options_safe(group_name):
    if group_name in KOLEKTIBILITAS_DATA:
        return list(KOLEKTIBILITAS_DATA[group_name].keys())
    opts = df_data[df_data['group'] == group_name]['description'].dropna().unique().tolist()
    return opts if opts else ["⚠️ Need JSON / Master Not Found"]

def find_point(group_name, value):
    if group_name in KOLEKTIBILITAS_DATA:
        return KOLEKTIBILITAS_DATA[group_name].get(value, 0)
    subset = df_data[df_data['group'] == group_name]
    if subset.empty: return 0
    if isinstance(value, (int, float)):
        for _, row in subset.iterrows():
            if row['range_min'] <= value <= row['range_max']: return row['point']
    else:
        match = subset[subset['description'].astype(str).str.strip() == str(value).strip()]
        if not match.empty: return match['point'].iloc[0]
    return 0

def find_rule_id(group_name, value):
    subset = df_data[df_data['group'] == group_name]
    if subset.empty: return None
    if isinstance(value, (int, float)):
        for _, row in subset.iterrows():
            if row['range_min'] <= value <= row['range_max']: return row['_id']
    else:
        match = subset[subset['description'].astype(str).str.strip() == str(value).strip()]
        if not match.empty: return match['_id'].iloc[0]
    return None

def show_point(group_name, value):
    p = find_point(group_name, value)
    st.markdown(f"<small style='color: #007bff;'>Poin: <b>{p}</b></small>", unsafe_allow_html=True)

# --- 3. UI INPUTS ---
st.title("")
selected_id_produk = st.sidebar.selectbox("Pilih ID Produk", df_hitung['id_produk'].unique())
params_max_angs_diambil = st.sidebar.slider("Batas Max DSR (%)", 10, 70, 40, help="Standar perbankan aman di 30-40%")
user_inputs = {}
# # --- UPDATE TAB LIST ---
# tab_cap, tab_char, tab_cond, tab_coll, tab_capi, tab_risk = st.tabs([
#     "CAPACITY", "CHARACTER", "CONDITION", "COLLATERAL", "CAPITAL", "🛡️ RISK MASTER"
# ])
# --- 3. UI HEADER (GANTI st.title LAMA DENGAN INI) ---
header_col1, header_col2 = st.columns([1, 4])

with header_col1:
    # 1. Coba load animasi Lottie untuk logo
    # Asumsi nama filenya adalah 'logo_animasi.json'
    path_lottie_logo = "logo_animasi.json" 
    
    if os.path.exists(path_lottie_logo):
        lottie_logo_data = load_lottie_local(path_lottie_logo)
        st_lottie(
            lottie_logo_data,
            speed=1,
            reverse=False,
            loop=True,
            quality="high", # Biar animasinya tajam
            height=100,     # Sesuaikan tingginya agar pas dengan teks BPR DANAGUNG
            key="logo_header"
        )
    # 2. Jika file Lottie tidak ada, pakai gambar PNG lama
    elif os.path.exists('logo_danagung.png'):
        st.image('logo_danagung.png', width=200)
    # 3. Jika dua-duanya tidak ada, baru pakai placeholder Merah
    else:
        st.markdown("""
            <div style='width:120px; height:70px; background:#c21b1b; border-radius:8px; 
            display:flex; align-items:center; justify-content:center; color:white; font-weight:bold; font-size:12px;'>
            LOGO DANAGUNG
            </div>
        """, unsafe_allow_html=True)

with header_col2:
    st.markdown("""
        <div style='margin-left: 10px;'>
            <h1 style='margin-top: 0; margin-bottom: 5px; color: #c21b1b !important; font-size: 2rem;'>BPR DANAGUNG</h1>
            <p style='color: #64748b !important; font-size: 1.1rem; margin: 0;'>Sistem Verifikasi Scoring & Audit Risiko Kredit</p>
            <hr style='margin: 10px 0; border: none; height: 2px; background: linear-gradient(to right, #c21b1b, #f4f7f9);'>
        </div>
    """, unsafe_allow_html=True)

# Setelah Header baru panggil Tab
tab_cap, tab_char, tab_cond, tab_coll, tab_capi, tab_risk = st.tabs([
    "CAPACITY", "CHARACTER", "CONDITION", "COLLATERAL", "CAPITAL", "🛡️ RISK MASTER"
])


        # --- MODUL AUTOMATION DI SIDEBAR ---
# 1. Fungsi load yang lebih aman
def load_lottie_local(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)

# Load animasi dari file yang Bapak upload ke GitHub tadi
lottie_robot = load_lottie_local("Ai_Robot.json")

with st.sidebar:
    st.markdown("---")
    st.header("🤖 Robot Automation")
    
    # Sekarang pasti muncul karena filenya ada di dalam server Bapak sendiri
    if lottie_robot:
        st_lottie(lottie_robot, height=150, key="robot_hosting")
    
    st.caption("Pilih skenario untuk pengujian cepat")
    
    # Ambil list nama skenario dari file automation.py
    scenarios = ["Manual Input"] + list(get_scenario_presets().keys())
    selected_mode = st.selectbox("Pilih Skenario Audit", scenarios)
    
    if selected_mode != "Manual Input":
        if st.button("🚀 Jalankan Auto-Fill"):
            if apply_automation(selected_mode):
                st.success(f"Berhasil memuat profil: {selected_mode}")
                # Paksa rerun agar input di Tab Capacity berubah otomatis
                st.rerun()



# --- JSON IMPORTER (AUTO-FILL FEATURE) ---
# with st.sidebar.expander("📥 Import Data dari JSON"):
#     json_input_raw = st.text_area("Paste JSON Payload di sini:")
#     if st.button("Load Data JSON"):
#         try:
#             input_data = json.loads(json_input_raw)
#             payload = input_data.get('payload', input_data) # Support format wrap atau direct
            
#             # 1. Simpan ke Session State untuk Kapasitas
         
#             capa_main = payload['scoring']['capa'][0]
#             st.session_state['total_penghasilan'] = capa_main.get('total_penghasilan', 0)
#             st.session_state['pengeluaran_usaha'] = capa_main.get('total_pengeluaran_usaha', 0)
#             st.session_state['p_rt_murni'] = capa_main.get('pengeluaran_rumah_tangga', 0) # <--- MAPPING BARU
#             st.session_state['p_sekolah'] = capa_main.get('pengeluaran_sekolah', 0)
#             st.session_state['p_transport'] = capa_main.get('pengeluaran_transportasi', 0)
#             st.session_state['p_listrik'] = capa_main.get('pengeluaran_listrik', 0)
#             st.session_state['p_telepon'] = capa_main.get('pengeluaran_telepon', 0)
#             st.session_state['p_hutang'] = capa_main.get('pengeluaran_hutang', 0)
#             st.session_state['p_arisan'] = capa_main.get('pengeluaran_arisan', 0)
#             st.session_state['angs_diambil_val'] = capa_main.get('angs_diambil', 0)
            
#             # 2. Simpan Data Agunan (CRUD)
#             st.session_state.collaterals = []
#             for item in payload['scoring'].get('coll_agunan', []):
#                 new_asset = {
#                     "unit_name": item.get('unit_name'),
#                     "address": item.get('address', item.get('desc')),
#                     "lt": item.get('luas_tanah', 0),
#                     "lb": item.get('luas_bangunan', 0),
#                     "merk": item.get('merk', ""),
#                     "thn": item.get('tahun', 2020),
#                     "hrg": item.get('harga', 0),
#                 }
#                 # Mapping scores agunan
#                 for s in item.get('scores', []):
#                     if s['group'] == 'proses_aset': new_asset['proses_aset'] = s['value']
#                     if s['group'] == 'akses_jalan_roda_4': new_asset['akses_jalan'] = s['value']
#                     if s['group'] == 'domisili': new_asset['domisili'] = s['value']
#                     if s['group'] == 'kepemilikan_aset': new_asset['kepemilikan'] = s['value']
                
#                 st.session_state.collaterals.append(new_asset)
            
#             st.success("Data berhasil di-load! Silakan cek setiap Tab.")
#             st.rerun()
#         except Exception as e:
#             st.error(f"Format JSON salah: {e}")

# --- UPDATE SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.subheader("🛡️ External Checking")
val_credit_check = st.sidebar.number_input("Skor Credit Checking (SLIK/OJK)", value=550)

# --- MASTER PARAMETER LIST ---
PARAM_FIELDS = {
    # 'total_penghasilan': 'Total Penghasilan',
    'pengeluaran_usaha': 'Total Pengeluaran Usaha (Non-Beban)',
    'p_rt_murni': 'Total Biaya Rumah Tangga',
    'p_sekolah': 'Biaya Sekolah',
    'p_transport': 'Transportasi',
    'p_listrik': 'Listrik',
    'p_telepon': 'Telepon',
    'p_hutang': 'Hutang Lain (SLIK)',
    'p_arisan': 'Arisan'
}



# --- LOAD SAVED SETTINGS ---
saved_data = load_config()
default_dsr = saved_data['dsr_params'] if saved_data else ['p_hutang']
default_idir = saved_data['idir_params'] if saved_data else list(PARAM_FIELDS.keys())

# Ambil list semua field scoring dari Excel
all_scoring_groups = df_hitung['group'].unique().tolist()
default_scoring = saved_data.get('active_scoring', all_scoring_groups) if saved_data else all_scoring_groups

with st.sidebar:
    st.markdown("### ⚙️ Konfigurasi Kebijakan")
    
    with st.expander("📊 Rumus DSR & IDIR"):
        selected_dsr = st.multiselect("Beban masuk DSR:", list(PARAM_FIELDS.keys()), 
                                     default=default_dsr, format_func=lambda x: PARAM_FIELDS[x])
        selected_idir = st.multiselect("Beban masuk IDIR:", list(PARAM_FIELDS.keys()), 
                                      default=default_idir, format_func=lambda x: PARAM_FIELDS[x])

    with st.expander("🎯 Filter Poin Scoring"):
        st.write("Pilih field yang akan berkontribusi pada total poin:")
        active_scoring_fields = st.multiselect("Field Aktif:", all_scoring_groups, default=default_scoring)

    if st.button("💾 Simpan Permanen Setting", use_container_width=True):
        config_to_save = {
            "dsr_params": selected_dsr,
            "idir_params": selected_idir,
            "active_scoring": active_scoring_fields,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_to_save, f, indent=4)
        st.success("Konfigurasi Berhasil Disimpan!")

with st.sidebar:
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #64748b; font-size: 0.8rem;'>
            Audit Tool v1.0<br>
            <b>© 2026 M. Suparman</b>
        </div>
        """, 
        unsafe_allow_html=True
    )

with st.expander("🛠️ Technical Specifications (Built by M. Suparman)"):
    st.markdown("""
    <div style="background: #1e293b; padding: 15px; border-radius: 10px;">
        <ul style="list-style-type: none; color: #e2e8f0; padding-left: 0;">
            <li style="margin-bottom: 10px;">✅ <b>Engine:</b> Danagung Scoring v1.0</li>
            <li style="margin-bottom: 10px;">✅ <b>Method:</b> Weighted Multi-Criteria Analysis</li>
            <li style="margin-bottom: 10px;">✅ <b>Automation:</b> Scenario-Based Robot Logic</li>
            <li style="margin-bottom: 10px;">✅ <b>Security:</b> Audit-Ready Integrity Check</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    

with tab_risk:
    st.subheader("📋 Master Matrix Risiko")
    
    # Konversi JSON ke DataFrame agar rapi
    df_risk_ui = pd.json_normalize(MASTER_RISIKO_SCORE)
    
    # Gabung kolom range agar enak dibaca
    df_risk_ui['Score_Range'] = df_risk_ui['range_score.min'].astype(str) + " - " + df_risk_ui['range_score.max'].astype(str)
    df_risk_ui['Credit_Check_Range'] = df_risk_ui['range_score_credit_checking.min'].astype(str) + " - " + df_risk_ui['range_score_credit_checking.max'].astype(str)
    
    # Seleksi kolom yang relevan
    cols_to_show = ['_id', 'nama_risiko', 'Score_Range', 'Credit_Check_Range', 'level', 'deskripsi']
    
    # Tampilkan tabel dengan desain interaktif
    st.dataframe(df_risk_ui[cols_to_show].rename(columns={
        'nama_risiko': 'Status Risiko',
        'level': 'Level',
        'deskripsi': 'Analisa'
    }), use_container_width=True, hide_index=True)

total_coll_fe_points = 0
coll_agunan_json = []

for asset in st.session_state.collaterals:
    p_unit = find_point('agunan', asset['unit_name'])
    p_kep = find_point('kepemilikan_aset', asset['kepemilikan'])
    # Estimasi poin detail lingkungan & akses (default 5 jika ya/tidak)
    p_det = 30 # (Proses + Domisili + Akses + 3 Lingkungan = 6 field * 5)
    total_coll_fe_points += (p_unit + p_kep + p_det)
    
    # Build list agunan untuk JSON
    coll_agunan_json.append({
        "unit_name": asset['unit_name'],
        "scores": [{"group": "agunan", "point": p_unit}, {"group": "kepemilikan_aset", "point": p_kep}]
    })

with tab_cap:
    st.subheader("CAPACITY")
    c1, c2 = st.columns(2)
    with c1:
        total_penghasilan = st.number_input("Total Penghasilan", value=st.session_state.get('total_penghasilan', 0))
        pengeluaran_usaha = st.number_input("Total Pengeluaran Usaha (Non-Beban)", value=st.session_state.get('pengeluaran_usaha', 0))
        
        st.markdown("---")
        st.write("### 🏠 Rincian Biaya Rumah Tangga")
        
        # Input rincian terlebih dahulu
        p_sekolah = st.number_input("Pengeluaran Sekolah", value=st.session_state.get('p_sekolah', 0))
        p_transport = st.number_input("Pengeluaran Transportasi", value=st.session_state.get('p_transport', 0))
        p_listrik = st.number_input("Pengeluaran Listrik", value=st.session_state.get('p_listrik', 0))
        p_telepon = st.number_input("Pengeluaran Telepon", value=st.session_state.get('p_telepon', 0))
        p_hutang = st.number_input("Pengeluaran Hutang Lain", value=st.session_state.get('p_hutang', 0))
        p_arisan = st.number_input("Pengeluaran Arisan", value=st.session_state.get('p_arisan', 0))
        
        # FIX: Biaya Pokok otomatis menjumlahkan semua rincian di atas
        p_rt_murni_calc = p_sekolah + p_transport + p_listrik + p_telepon + p_hutang + p_arisan

        # Definisikan rincian buat muncul di tooltip
        tooltip_detail = f"""
        Rincian Perhitungan:
        - Sekolah: Rp {p_sekolah:,.0f}
        - Transport: Rp {p_transport:,.0f}
        - Listrik: Rp {p_listrik:,.0f}
        - Telepon: Rp {p_telepon:,.0f}
        - Hutang: Rp {p_hutang:,.0f}
        - Arisan: Rp {p_arisan:,.0f}
        
        Total Otomatis = Rp {p_rt_murni_calc:,.0f}
        """

        # Ini hanya untuk TAMPILAN (berisi String)
        p_rt_murni = st.text_input(
            "Biaya Rumah Tangga (Total Pengeluaran) - Auto Calculated", 
            value=f"Rp {p_rt_murni_calc:,.0f}", # Format ribuan agar rapi
            disabled=True,
            help=tooltip_detail
        )


        # --- INPUT UTAMA UNTUK LTV ---
        # Simpan di memori agar bisa dibaca di Tab Collateral
        angs_diambil = st.number_input("Angsuran yang Akan Diambil", 
                                        value=st.session_state.get('angs_diambil_val', 306638), 
                                        key='angs_diambil_val')
        tenor_val = st.number_input("Tenor (Bulan)", 
                                    value=int(st.session_state.get('cap_tenor', 30)), 
                                    key="cap_tenor")

      
        # st.error(f"Beban Terpilih: DSR (Rp {beban_dsr:,.0f}) | IDIR (Rp {beban_idir:,.0f})")
   
    with c2:
        # --- 1. RUMUS STANDAR PERBANKAN ---

        current_vals = {
            # 'total_penghasilan': total_penghasilan, 
            'pengeluaran_usaha': pengeluaran_usaha,
            'p_rt_murni': p_rt_murni_calc, 
            'p_sekolah': p_sekolah,
            'p_transport': p_transport,
            'p_listrik': p_listrik,
            'p_telepon': p_telepon,
            'p_hutang': p_hutang,
            'p_arisan': p_arisan
        }

        # Sekarang sum() tidak akan error karena isinya angka semua
        # Pakai .get(p, 0) supaya kalau key tidak ketemu, aplikasi tidak crash
        beban_dsr = sum(current_vals.get(p, 0) for p in selected_dsr)
        beban_idir = sum(current_vals.get(p, 0) for p in selected_idir)
        
        
        # IDIR: Angsuran Baru / Pendapatan
        idir_val = round((angs_diambil / total_penghasilan * 100), 2) if total_penghasilan > 0 else 0
        
        # DSR: (Beban Hutang Lama + Angsuran Baru) / Pendapatan
        total_cicilan_dsr = beban_dsr + angs_diambil
        dsr_val = round((total_cicilan_dsr / total_penghasilan * 100), 2) if total_penghasilan > 0 else 0
        
        # --- 2. TAMPILAN METRIC UTAMA ---
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("DSR (%)", f"{dsr_val}%", help="Rumus: (Beban Lama Terpilih + Angsuran Baru) / Pendapatan")
        with col_m2:
            st.metric("IDIR (%)", f"{idir_val}%", help="Rumus: Angsuran Baru / Pendapatan")
        
        st.markdown("---")

      # --- 3. PROGRESS BAR & STATUS ---
        st.write(f"**Pemanfaatan Kuota DSR ({params_max_angs_diambil}%)**")
        plafon_maks_kebijakan = (total_penghasilan * params_max_angs_diambil / 100)
        
        rasio_pemanfaatan = total_cicilan_dsr / plafon_maks_kebijakan if plafon_maks_kebijakan > 0 else 0
        
        # Logika Warna Aman/Warning/Reject
        if rasio_pemanfaatan <= 0.8:
            bar_color = "#22c55e" # Hijau
            status_text = "AMAN"
        elif rasio_pemanfaatan <= 1.0:
            bar_color = "#eab308" # Kuning
            status_text = "WARNING"
        else:
            bar_color = "#ef4444" # Merah
            status_text = "OVERLIMIT / REJECT"
        
        st.progress(min(max(rasio_pemanfaatan, 0.0), 1.0))

        # --- 4. CATATAN VERIFIKASI ---
        st.markdown(f"""
            <div style="background-color: #f1f5f9; padding: 15px; border-radius: 10px; border-left: 8px solid {bar_color};">
                <p style="color: #475569; margin: 0; font-size: 0.8rem; font-weight: bold;">ANALISA KAPASITAS:</p>
                <p style="color: #1e293b; margin: 5px 0; font-size: 0.9rem;">
                    • <b>Batas Maksimal DSR:</b> {params_max_angs_diambil}%<br>
                    • <b>DSR Aktual:</b> {dsr_val}%<br>
                    • <b>Status:</b> <span style="color:{bar_color}; font-weight:bold;">{status_text}</span>
                </p>
            </div>
        """, unsafe_allow_html=True)

        # Disposable Income (Sisa uang setelah SEMUA pengeluaran)
        sisa_uang_rill = total_penghasilan - (angs_diambil + beban_idir)
        if sisa_uang_rill >= 0:
            st.success(f"Sisa Disposable Income: **{format_rp(sisa_uang_rill)}**")
        else:
            st.error(f"Defisit Kemampuan Bayar: **{format_rp(abs(sisa_uang_rill))}**")

        st.markdown("---")

        # 4. INPUT WIDGETS (Agar sinkron dengan Robot Automation)
        # Gunakan session_state.get agar input berubah otomatis saat robot jalan
       
        usia_val = st.number_input("Usia", value=int(st.session_state.get('cap_usia', 41)), key="cap_usia")
        kerja_val = st.number_input("Lama Kerja (Tahun)", value=float(st.session_state.get('cap_work', 3.0)), key="cap_work")

        opts_merit = get_options_safe('status_perkawinan')
        merit_val = st.selectbox("Status Perkawinan", opts_merit, index=get_idx(opts_merit, 'cap_merit'), key="cap_merit_ui")

        opts_power = get_options_safe('daya_listrik')
        power_val = st.selectbox("Daya Listrik", opts_power, index=get_idx(opts_power, 'cap_power'), key="cap_power_ui")

        opts_period = get_options_safe('periode_penghasilan')
        period_val = st.selectbox("Periode Penghasilan", opts_period, index=get_idx(opts_period, 'cap_period'), key="cap_period_ui")

        # 5. UPDATE DATA UNTUK PROSES AUDIT
        user_inputs.update({
            'dsr': dsr_val, 
            'idir': idir_val, 
            'jlh_penghasilan': total_penghasilan,
            'tenor': tenor_val,
            'usia': usia_val,
            'lama_kerja': kerja_val,
            'status_perkawinan': merit_val,
            'daya_listrik': power_val,
            'periode_penghasilan': period_val
        })



        with st.expander("💡 Info Logika Slider"):
            st.caption(f"""
                Slider 'Batas Max' di sidebar adalah plafon kebijakan bank ({params_max_angs_diambil}%). 
                Angka ini tidak merubah pengeluaran rill nasabah, melainkan merubah 'Batas Plafon' 
                untuk melihat apakah pengeluaran aktual nasabah masih masuk dalam kuota atau tidak.
            """)

with tab_char:
    st.subheader("CHARACTER")
    c1, c2 = st.columns(2)
    with c1:
        # Tujuan Pinjaman
        opts_tujuan = get_options_safe('tujuan_pinjaman')
        user_inputs['tujuan_pinjaman'] = st.selectbox("Tujuan Pinjaman", opts_tujuan, 
                                                     index=get_idx(opts_tujuan, 'char_tujuan'), 
                                                     key="char_tujuan_ui")
        show_point('tujuan_pinjaman', user_inputs['tujuan_pinjaman'])
        
      # --- 1. GABUNG OPSI DARI DICTIONARY (Bukan Excel) ---
        list_status = (
            list(KOLEKTIBILITAS_DATA['tanpa_agunan'].keys()) + 
            list(KOLEKTIBILITAS_DATA['dengan_agunan'].keys()) + 
            list(KOLEKTIBILITAS_DATA['debitur_baru'].keys())
        )
        
        selected_status = st.selectbox(
            "Status Kolektibilitas", 
            list_status, 
            index=get_idx(list_status, 'char_kolektibilitas'), 
            key="char_kol_ui"
        )

        # --- 2. LOGIKA PENENTUAN POIN & GROUP ---
        inherited_point = 0
        current_group = ""

        if selected_status in KOLEKTIBILITAS_DATA['tanpa_agunan']:
            inherited_point = KOLEKTIBILITAS_DATA['tanpa_agunan'][selected_status]
            current_group = 'tanpa_agunan'
        elif selected_status in KOLEKTIBILITAS_DATA['dengan_agunan']:
            inherited_point = KOLEKTIBILITAS_DATA['dengan_agunan'][selected_status]
            current_group = 'dengan_agunan'
        else:
            inherited_point = KOLEKTIBILITAS_DATA['debitur_baru'][selected_status]
            current_group = 'debitur_baru'

        # Simpan ke user_inputs agar terbaca di tabel hasil audit
        user_inputs[current_group] = selected_status
        st.markdown(f"<small style='color: #007bff;'>Poin Status: <b>{inherited_point}</b></small>", unsafe_allow_html=True)
        
        # --- 3. LOGIKA INSTITUSI KEUANGAN ---
        inst_val = st.text_input("Institusi Keuangan", value="Modal Usaha", key="inst_val_ui")
        user_inputs['intitusi_name'] = inst_val # Simpan namanya
        
        # Simpan poin kolektibilitas ke session state untuk ditarik JSON Constructor
        st.session_state['point_institusi'] = inherited_point 
        st.markdown(f"<small style='color: green;'>Poin Institusi (Auto Match Status): <b>{inherited_point}</b></small>", unsafe_allow_html=True)
        
    with c2:
        # List field dan label
        fields = ['lama_tinggal', 'kepemilikan_no_hp', 'asuransi_kesehatan', 'hubungan_bank', 'kartu_kredit', 'bayar_telepon', 'bayar_listrik', 'sisa_hutang']
        labels = ["Lama Tinggal", "Lama No HP", "Asuransi Kesehatan", "Hubungan Bank", "Kartu Kredit", "Telepon", "Listrik", "Sisa Hutang"]
        
        # Mapping key dari automation.py
        auto_keys = ['char_lama_tinggal', 'char_hp', 'char_asuransi', 'char_hubungan', 'char_kartu', 'char_telp_bayar', 'char_listrik_bayar', 'char_sisa_hutang']

        for f, l, ak in zip(fields, labels, auto_keys):
            opts = get_options_safe(f)
            user_inputs[f] = st.selectbox(l, opts, index=get_idx(opts, ak), key=f"char_{f}_ui")
            show_point(f, user_inputs[f])
            

with tab_cond:
    st.subheader("CONDITION")
    # Mapping field dan key automation
    cond_mapping = {
        'pekerjaan': ('Pekerjaan', 'cond_job'),
        'jenis_aset': ('Jenis Aset', 'cond_asset'),
        'kepemilikan_aset': ('Kepemilikan Aset', 'cond_own')
    }
    
    for f, (label, ak) in cond_mapping.items():
        opts = get_options_safe(f)
        user_inputs[f] = st.selectbox(label, opts, index=get_idx(opts, ak), key=f"cond_{f}_ui")
        show_point(f, user_inputs[f])

with tab_coll:
    st.subheader("COLLATERAL (Dynamic Assets)")
    
    if st.button("➕ Tambah Data Agunan"):
        st.session_state.collaterals.append({
            "unit_name": "Rumah", "address": "", "lt": 0, "lb": 0, "merk": "", "thn": 2020, "hrg": 0,
            "total_taksasi": 0, "ltv": 0,
            "proses_aset": "On Hand", "akses_jalan": "YA", "domisili": "Alamat Agunan sesuai KTP", 
            "kepemilikan": "Milik Sendiri", "kuburan": "TIDAK", "sutet": "TIDAK", "sungai": "TIDAK"
        })

    for i, col_item in enumerate(st.session_state.collaterals):
        with st.expander(f"📌 Agunan Ke-{i+1}: {col_item['unit_name']}", expanded=True):
            c1, c2 = st.columns(2)
            
            # --- JENIS AGUNAN ---
            unit_opts = ["Rumah", "Tanah", "Ruko", "Mobil", "Motor"]
            idx_unit = unit_opts.index(col_item['unit_name']) if col_item['unit_name'] in unit_opts else 0
            
            col_item['unit_name'] = c1.selectbox(f"Jenis Agunan #{i}", unit_opts, index=idx_unit, key=f"unit_{i}")
            
            # TAMPILKAN POIN UNIT
            p_unit = find_point('agunan', col_item['unit_name'])
            c1.markdown(f"<small style='color: #eab308;'>Poin Jenis Agunan: <b>{p_unit}</b></small>", unsafe_allow_html=True)
            
            col_item['address'] = c2.text_input(f"Alamat/Lokasi #{i}", value=col_item.get('address') or "", key=f"addr_{i}")
            
            # --- LOGIKA FIELD TEKNIS ---
            if col_item['unit_name'] in ["Rumah", "Ruko"]:
                col_item['lt'] = c1.number_input(f"Luas Tanah #{i}", value=int(col_item.get('lt') or 0), key=f"lt_{i}")
                col_item['lb'] = c2.number_input(f"Luas Bangunan #{i}", value=int(col_item.get('lb') or 0), key=f"lb_{i}")
            elif col_item['unit_name'] == "Tanah":
                col_item['lt'] = c1.number_input(f"Luas Tanah #{i}", value=int(col_item.get('lt') or 0), key=f"lt_{i}")
                col_item['lb'] = 0
            else: # Kendaraan
                col_item['merk'] = c1.text_input(f"Merk/Tipe #{i}", value=col_item.get('merk') or "", key=f"merk_{i}")
                col_item['thn'] = c2.number_input(f"Tahun #{i}", value=int(col_item.get('thn') or 2020), key=f"thn_{i}")
                col_item['hrg'] = c2.number_input(f"Estimasi Harga #{i}", value=int(col_item.get('hrg') or 0), key=f"hrg_{i}")

        # --- TAMBAHAN BARU: PENILAIAN TAKSASI & LTV ---
         
                # --- DI DALAM LOOP TAB COLLATERAL ---
         
            st.write("**💰 Penilaian Taksasi & LTV**")
            v1, v2, v3 = st.columns(3)
            
            # 1. Input Nilai Taksasi
            col_item['total_taksasi'] = v1.number_input(f"Total Nilai Taksasi #{i}", 
                                                        value=int(col_item.get('total_taksasi', 0)), 
                                                        step=1000000, key=f"taks_{i}")
            
            # 2. Ambil data dari memori (Session State)
         
            v_angs = st.session_state.get('angs_diambil_val', 0)
            v_tenor = st.session_state.get('cap_tenor', 0)
            plafon_kredit = v_angs * v_tenor 
            
            if col_item['total_taksasi'] > 0:
                # Hitung dan bulatkan 2 angka di belakang koma
                raw_ltv = (plafon_kredit / col_item['total_taksasi'] * 100)
                ltv_calc = round(raw_ltv, 2) 
            else:
                ltv_calc = 0
            
            col_item['ltv'] = ltv_calc
            
            # Tampilkan dengan format 2 desimal (Contoh: 45.99%)
            v2.text_input(
                f"LTV (%) Auto Calculated#{i}", 
                value=f"{ltv_calc:,.2f}%", # Format string agar selalu 2 desimal
                disabled=True
            )

            # 3. Poin LTV (Bakal otomatis narik ke Excel)
            p_ltv = find_point('comperation_agunan', ltv_calc)
            v3.markdown(f"<br><small style='color: #eab308;'>Poin LTV: <b>{p_ltv}</b></small>", unsafe_allow_html=True)

            


            st.markdown("---")
            st.write("**📝 Scoring Detail**")
            s1, s2, s3 = st.columns(3)

            # Helper internal untuk index
            def get_col_idx(opts, current_val):
                return opts.index(current_val) if current_val in opts else 0

            # 1. PROSES ASET
            opt_proses = get_options_safe('proses_aset')
            col_item['proses_aset'] = s1.selectbox(f"Proses Aset #{i}", opt_proses, 
                                                  index=get_col_idx(opt_proses, col_item.get('proses_aset')), 
                                                  key=f"pr_{i}")
            p_proses = find_point('proses_aset', col_item['proses_aset'])
            s1.markdown(f"<small style='color: #3b82f6;'>Poin: <b>{p_proses}</b></small>", unsafe_allow_html=True)
            
            # 2. DOMISILI (SESUAI KTP)
            opt_dom = get_options_safe('domisili')
            col_item['domisili'] = s2.selectbox(f"Sesuai KTP #{i}", opt_dom, 
                                               index=get_col_idx(opt_dom, col_item.get('domisili')), 
                                               key=f"dm_{i}")
            p_dom = find_point('domisili', col_item['domisili'])
            s2.markdown(f"<small style='color: #3b82f6;'>Poin: <b>{p_dom}</b></small>", unsafe_allow_html=True)
            
            # 3. KEPEMILIKAN
            opt_own = get_options_safe('kepemilikan_aset')
            col_item['kepemilikan'] = s3.selectbox(f"Kepemilikan #{i}", opt_own, 
                                                  index=get_col_idx(opt_own, col_item.get('kepemilikan')), 
                                                  key=f"kp_{i}")
            p_own = find_point('kepemilikan_aset', col_item['kepemilikan'])
            s3.markdown(f"<small style='color: #3b82f6;'>Poin: <b>{p_own}</b></small>", unsafe_allow_html=True)

            # --- LOGIKA LINGKUNGAN (KHUSUS PROPERTI) ---
            p_env_total = 0
            if col_item['unit_name'] in ["Rumah", "Tanah", "Ruko"]:
                st.write("**🏘️ Kondisi Lingkungan**")
                env1, env2, env3 = st.columns(3)
                env4, _, _ = st.columns(3)

                # Akses Jalan
                opt_jln = get_options_safe('akses_jalan_roda_4')
                col_item['akses_jalan'] = env1.selectbox(f"Akses Roda 4 #{i}", opt_jln, index=get_col_idx(opt_jln, col_item.get('akses_jalan')), key=f"ak_{i}")
                p_jln = find_point('akses_jalan_roda_4', col_item['akses_jalan'])
                env1.markdown(f"<small style='color: #64748b;'>Poin: {p_jln}</small>", unsafe_allow_html=True)
                
                # Kuburan
                opt_kbr = get_options_safe('dalam_200m_terdapat_kuburan')
                col_item['kuburan'] = env2.selectbox(f"Ada Kuburan? #{i}", opt_kbr, index=get_col_idx(opt_kbr, col_item.get('kuburan')), key=f"kb_{i}")
                p_kbr = find_point('dalam_200m_terdapat_kuburan', col_item['kuburan'])
                env2.markdown(f"<small style='color: #64748b;'>Poin: {p_kbr}</small>", unsafe_allow_html=True)

                # Sutet
                opt_stt = get_options_safe('dalam_200m_terdapat_sutet')
                col_item['sutet'] = env3.selectbox(f"Ada Sutet? #{i}", opt_stt, index=get_col_idx(opt_stt, col_item.get('sutet')), key=f"st_{i}")
                p_stt = find_point('dalam_200m_terdapat_sutet', col_item['sutet'])
                env3.markdown(f"<small style='color: #64748b;'>Poin: {p_stt}</small>", unsafe_allow_html=True)

                # Sungai
                opt_sng = get_options_safe('dalam_200m_terdapat_sungai')
                col_item['sungai'] = env4.selectbox(f"Ada Sungai? #{i}", opt_sng, index=get_col_idx(opt_sng, col_item.get('sungai')), key=f"sg_{i}")
                p_sng = find_point('dalam_200m_terdapat_sungai', col_item['sungai'])
                env4.markdown(f"<small style='color: #64748b;'>Poin: {p_sng}</small>", unsafe_allow_html=True)
                
                p_env_total = p_jln + p_kbr + p_stt + p_sng
            else:
                # Kendaraan tidak dapet poin lingkungan
                col_item['akses_jalan'] = "YA"; col_item['kuburan'] = "TIDAK"
                col_item['sutet'] = "TIDAK"; col_item['sungai'] = "TIDAK"
                p_env_total = 0

            # RINGKASAN POIN AGUNAN INI
            total_agunan_i = p_unit + p_proses + p_dom + p_own + p_env_total
            st.info(f"Sub-Total Poin Agunan #{i+1}: **{total_agunan_i}**")

            if st.button(f"🗑️ Hapus Agunan #{i+1}", key=f"del_{i}"):
                st.session_state.collaterals.pop(i)
                st.rerun()

with tab_capi:
    st.subheader("CAPITAL")
    capi_mapping = {
        'kepemilikan_rumah': ('Kepemilikan Rumah', 'capi_rumah'),
        'perumahan': ('Perumahan', 'capi_perumahan'),
        'tipe_rumah': ('Tipe Rumah', 'capi_tipe')
    }
    
    for f, (label, ak) in capi_mapping.items():
        opts = get_options_safe(f)
        user_inputs[f] = st.selectbox(label, opts, index=get_idx(opts, ak), key=f"capi_{f}_ui")
        show_point(f, user_inputs[f])

  # --- MASTER BOBOT HARDCODE ---
WEIGHT_CONFIG = {
    "001": {"capacity": 0.25, "character": 0.20, "condition": 0.30, "capital": 0.25, "collateral": 0.0},
    "002": {"capacity": 0.15, "character": 0.20, "condition": 0.30, "capital": 0.15, "collateral": 0.20},
    "003": {"capacity": 0.15, "character": 0.20, "condition": 0.30, "capital": 0.15, "collateral": 0.20},
}




# --- 5. LOGIKA TOMBOL & HASIL (DENGAN SESSION STATE AGAR TIDAK RESET) ---

# Inisialisasi state agar hasil audit tidak hilang saat slider digeser
if 'audit_run' not in st.session_state:
    st.session_state.audit_run = False

if st.button("RUN AUDIT CALCULATION", type="primary", use_container_width=True):
    st.session_state.audit_run = True

# Hanya jalan jika tombol pernah diklik
if st.session_state.audit_run:
    prod_id = str(selected_id_produk).strip()
    cat_weight_map = WEIGHT_CONFIG.get(prod_id, WEIGHT_CONFIG["002"])

    # 1. RE-CALCULATE VARIABLES
    current_vals_murni = {
        'p_rt_murni': p_rt_murni_calc, 'p_sekolah': p_sekolah,
        'p_transport': p_transport, 'p_listrik': p_listrik,
        'p_telepon': p_telepon, 'p_hutang': p_hutang, 'p_arisan': p_arisan
    }
    
    beban_idir_audit = sum(current_vals_murni.get(p, 0) for p in selected_idir)
    total_beban_aktual_audit = angs_diambil + beban_idir_audit
    maksAngsuran_audit = (total_penghasilan * params_max_angs_diambil / 100) - beban_idir_audit

    details = []
    rules_table = df_hitung[df_hitung['id_produk'] == selected_id_produk]


    
    
    # 2. LOOP PILAR (Capacity, Character, Condition, Capital)
    for _, row in rules_table.iterrows():
        f_name = row['group']
        if f_name in active_scoring_fields:
            # Gunakan .strip() agar spasi gaib tidak bikin skor 0
            val_input = str(user_inputs.get(f_name, "")).strip()
            p = find_point(f_name, val_input)
            w = row['bobot']
        else:
            p, w = 0, 0
        details.append({'Category': str(row['score_type']).lower().strip(), 'Field': f_name, 'Point': p, 'Weight': w, 'Weighted': p * w})

    # 3. MASUKKAN POIN COLLATERAL (YANG TADI HILANG)
   # 3. MASUKKAN POIN COLLATERAL (LOGIKA BARU - TANPA ANGKA GAIB)
    total_p_coll = 0
    for asset in st.session_state.collaterals:
        p_u = find_point('agunan', asset.get('unit_name'))
        p_p = find_point('proses_aset', asset.get('proses_aset'))
        p_d = find_point('domisili', asset.get('domisili'))
        p_k = find_point('kepemilikan_aset', asset.get('kepemilikan'))
        
        # Tambahkan Poin LTV (comperation_agunan)
        p_ltv_val = find_point('comperation_agunan', asset.get('ltv', 0))
        
        p_env = 0
        if asset.get('unit_name') in ["Rumah", "Tanah", "Ruko"]:
            p_env += find_point('akses_jalan_roda_4', asset.get('akses_jalan'))
            p_env += find_point('dalam_200m_terdapat_kuburan', asset.get('kuburan'))
            p_env += find_point('dalam_200m_terdapat_sutet', asset.get('sutet'))
            p_env += find_point('dalam_200m_terdapat_sungai', asset.get('sungai'))
        
        # Sertakan p_ltv_val ke dalam total
        total_p_coll += (p_u + p_p + p_d + p_k + p_ltv_val + p_env)

    # Update detail untuk summary tabel
    details.append({
        'Category': 'collateral', 
        'Field': 'dynamic_collateral', 
        'Point': total_p_coll, 
        'Weight': 1.0, 
        'Weighted': total_p_coll
    })

    # 4. PROSES SUMMARY & SKOR FINAL
    df_res = pd.DataFrame(details)
    summary = df_res.groupby('Category').agg({'Point': 'sum', 'Weighted': 'sum'}).reset_index()
    summary['Cat_Weight'] = summary['Category'].map(cat_weight_map).fillna(0)
    
    # RUMUS BE: (Total Poin Kategori * Bobot Produk) * 100
    summary['Skor_BE'] = summary['Weighted'] * summary['Cat_Weight'] * 100
    total_be_score = round(summary['Skor_BE'].sum(), 0)

    # LOOKUP RISIKO
    final_risk_data = next((risk for risk in MASTER_RISIKO_SCORE if risk['range_score']['min'] <= total_be_score <= risk['range_score']['max'] and risk['range_score_credit_checking']['min'] <= val_credit_check <= risk['range_score_credit_checking']['max']), {"nama_risiko": "Manual Review", "level": "N/A", "deskripsi": "Skor diluar jangkauan."})
    color_map = {"Risiko Rendah": "#22c55e", "Risiko Sedang": "#eab308", "Risiko Tinggi": "#ef4444", "Reject": "#ef4444"}
    risk_color = color_map.get(final_risk_data['nama_risiko'], "#3b82f6")
    

    # --- FITUR BARU: SCORING SENSITIVITY (STRESS TEST) ---
    st.markdown("---")
    st.subheader("🔍 Sensitivity Analysis")
    st.write("Simulasi jika terjadi penurunan kondisi finansial nasabah (Worst Case Scenario). Example : kalau nasabah tiba-tiba penghasilannya turun 20% karena krisis ekonomi? Apakah kodenya tetap 'Aman' atau langsung 'Reject'?")

    # 1. Slider untuk Simulasi Penurunan Penghasilan
    stress_factor = st.slider("Simulasi Penurunan Penghasilan (%)", 0, 50, 20, help="Geser untuk simulasi penurunan penghasilan (Misal: 20%)")
    
    # 2. Kalkulasi Ulang (Kondisi Stress)
    income_stressed = total_penghasilan * (1 - (stress_factor / 100))
    
    # Hitung ulang DSR/IDIR di kondisi stress
    # Gunakan total_cicilan_dsr (karena ini total beban hutang yang valid)
    idir_stressed = round((total_cicilan_dsr / income_stressed * 100), 2) if income_stressed > 0 else 0
    
    # Hitung ulang Skor BE (Asumsi poin Kapasitas turun jika penghasilan turun)
    # Kita buat simulasi skor BE turun proporsional dengan faktor stress pada pilar Capacity
    reduction_impact = (total_be_score * (stress_factor/100) * 0.4) # Asumsi bobot kapasitas 40%
    score_stressed = round(total_be_score - reduction_impact, 0)

    # 3. Lookup Risiko Baru (Kondisi Stress)
    stressed_risk_data = next((
        risk for risk in MASTER_RISIKO_SCORE 
        if risk['range_score']['min'] <= score_stressed <= risk['range_score']['max']
        and risk['range_score_credit_checking']['min'] <= val_credit_check <= risk['range_score_credit_checking']['max']
    ), {"nama_risiko": "High Risk", "deskripsi": "Skor anjlok drastis."})

    # Tentukan Warna Status Stress
    stress_color = "#22c55e" if "Rendah" in stressed_risk_data['nama_risiko'] else ("#eab308" if "Sedang" in stressed_risk_data['nama_risiko'] else "#ef4444")

    # 4. Tampilan Visual Perbandingan
    col_sim1, col_sim2 = st.columns(2)
    
    with col_sim1:
        st.info(f"**Kondisi Saat Ini**")
        st.write(f"Penghasilan: {format_rp(total_penghasilan)}")
        st.write(f"IDIR: {idir_val}%")
        st.write(f"Status: **{final_risk_data['nama_risiko']}**")

    with col_sim2:
        st.warning(f"**Kondisi Stress (-{stress_factor}%)**")
        st.write(f"Penghasilan: {format_rp(income_stressed)}")
        st.write(f"IDIR: {idir_stressed}%")
        st.markdown(f"Status: <span style='color:{stress_color}; font-weight:bold;'>{stressed_risk_data['nama_risiko']}</span>", unsafe_allow_html=True)

    # Pesan Kesimpulan Stress Test
    if stressed_risk_data['nama_risiko'] != final_risk_data['nama_risiko']:
        st.error(f"⚠️ **Peringatan Auditor:** Kredit ini SENSITIF terhadap penurunan penghasilan. Penurunan {stress_factor}% merubah status menjadi {stressed_risk_data['nama_risiko']}.")
    else:
        st.success(f"✅ **Kesimpulan:** Kredit ini RESILIEN (Kuat). Penurunan {stress_factor}% tidak merubah status risiko.")

    # --- UI OUTPUT (REPORT CARD) ---
    st.divider()
    st.markdown(f"""
        <div class="report-card" style="border-left: 8px solid {risk_color};">
            <h3 style='margin:0; color:#e2e8f0;'>HASIL ANALISA RISIKO</h3>
            <h1 style='color:{risk_color}; margin:10px 0;'>{final_risk_data['nama_risiko']}</h1>
            <p style='color:#94a3b8;'>Skor Akhir: <b style='color:white; font-size:24px;'>{total_be_score}</b></p>
            <hr style='border: 0.5px solid #334155;'>
            <p style='color:#e2e8f0;'><b>Analisa Auditor:</b> {final_risk_data['deskripsi']}</p>
        </div>
    """, unsafe_allow_html=True)

    summary_display = summary.copy()
    summary_display['Total Poin'] = summary_display['Point'].astype(int)
    summary_display['Weighted Subtotal'] = summary_display['Weighted'].map("{:,.2f}".format)
    summary_display['Bobot Produk'] = (summary_display['Cat_Weight']).map("{:,.2f}".format)
    summary_display['Skor Final'] = summary_display['Skor_BE'].map("{:,.2f}".format)
    st.table(summary_display[['Category', 'Total Poin', 'Weighted Subtotal', 'Bobot Produk', 'Skor Final']])

    # --- JSON CONSTRUCTOR (FIX NAMEERROR) ---

    # --- PROSES PEMBENTUKAN JSON SUPER DETAILED ---
    # --- HELPER: Logic Null untuk Capa ---
    def get_val_or_null(param_key, actual_value):
        if param_key in selected_dsr or param_key in selected_idir:
            return actual_value
        return None

    def to_bool(val):
        if val == "YA": return True
        if val == "TIDAK": return False
        return None
    

    # --- PROSES PEMBENTUKAN JSON SUPER DETAILED ---
    # 1. Bangun List Character secara Manual agar Presisi
    char_list_json = []
    

    # Lewati group kolektibilitas agar tidak double mapping
    for _, row in df_res[df_res['Category'] == 'character'].iterrows():
        f_name = row['Field']
        if f_name in ['tanpa_agunan', 'dengan_agunan', 'debitur_baru']:
            continue
            
        char_list_json.append({
            "id": find_rule_id(f_name, user_inputs.get(f_name)),
            "group": f_name,
            "text": str(user_inputs.get(f_name)),
            "value": str(user_inputs.get(f_name)),
            "point": int(row['Point'])
        })

    # Tambahkan Kolektibilitas (Data Poin dari Dictionary KOLEKTIBILITAS_DATA)
    current_kol_status = user_inputs.get('tanpa_agunan') or user_inputs.get('dengan_agunan') or user_inputs.get('debitur_baru')
    kol_group = "tanpa_agunan" if user_inputs.get('tanpa_agunan') else ("dengan_agunan" if user_inputs.get('dengan_agunan') else "debitur_baru")
    
    if current_kol_status:
        char_list_json.append({
            "id": find_rule_id(kol_group, current_kol_status),
            "group": kol_group,
            "text": str(current_kol_status),
            "value": str(current_kol_status),
            "point": int(st.session_state.get('point_institusi', 0))
        })

    # Tambahkan Manual Group "intitusi" (Sesuai Ekspektasi Bapak)
    char_list_json.append({
        "id": None,
        "group": "intitusi",
        "text": None,
        "value": None,
        "point": int(st.session_state.get('point_institusi', 0))
    })

    json_output = {
        "error": 0,
        "error_code": 0,
        "message": "OK",
        "response_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": {
            "pemohon": {
                "name": "NASABAH DANAGUNG",
                "domisili_address": "Alamat sesuai KTP"
            },
            "pengajuan": {
                "product_id": prod_id,
                "submission_loan": angs_diambil * tenor_val,
                "tenor": tenor_val,
                "tenor_id": f"{tenor_val}M",
                "tenor_type": "BULAN",
                "interest_rate": 0, 
                "use_ltv": True if st.session_state.collaterals else False,
                "ltv_value": st.session_state.collaterals[0].get('ltv', 0) if st.session_state.collaterals else 0,
                "range_interest_rate": "0%"
            },
            "scoring": {
                "char": char_list_json,
                
                "capa": [
                    {
                        "total_penghasilan": total_penghasilan,
                        "total_pengeluaran_usaha": pengeluaran_usaha,
                        "pengeluaran_rumah_tangga": get_val_or_null('p_rt_murni', p_rt_murni_calc),
                        "pengeluaran_transportasi": get_val_or_null('p_transport', p_transport),
                        "pengeluaran_listrik": get_val_or_null('p_listrik', p_listrik),
                        "pengeluaran_telepon": get_val_or_null('p_telepon', p_telepon),
                        "pengeluaran_hutang": get_val_or_null('p_hutang', p_hutang),
                        "pengeluaran_arisan": get_val_or_null('p_arisan', p_arisan),
                        "max_angs": plafon_maks_kebijakan,
                        "angs_diambil": angs_diambil,
                        "idir": idir_val,
                        "dsr": dsr_val
                    }
                ],

                "cond": [
                    {
                        "id": find_rule_id(row['Field'], user_inputs.get(row['Field'])),
                        "group": row['Field'],
                        "text": str(user_inputs.get(row['Field'])),
                        "value": str(user_inputs.get(row['Field'])),
                        "point": int(row['Point'])
                    } for _, row in df_res[df_res['Category'] == 'condition'].iterrows()
                ],

                "capi": [
                    {
                        "id": find_rule_id(row['Field'], user_inputs.get(row['Field'])),
                        "group": row['Field'],
                        "text": str(user_inputs.get(row['Field'])),
                        "value": str(user_inputs.get(row['Field'])),
                        "point": int(row['Point'])
                    } for _, row in df_res[df_res['Category'] == 'capital'].iterrows()
                ],

                "coll": [
                    {
                        "group": "comperation_agunan",
                        "point": find_point('comperation_agunan', asset.get('ltv', 0)),
                        "total_taksasi": asset.get('total_taksasi', 0),
                        "ltv": asset.get('ltv', 0)
                    } for asset in st.session_state.collaterals
                ],

                "coll_agunan": [
                    {
                        "agunan_id": f"AGN-{i}",
                        "unit_name": asset['unit_name'],
                        "unit_id": "RMH" if asset['unit_name'] == "Rumah" else ("TNH" if asset['unit_name'] == "Tanah" else ("RKO" if asset['unit_name'] == "Ruko" else "MBL")),
                        "type_id": "AT" if asset['unit_name'] in ["Rumah", "Tanah", "Ruko"] else "AB",
                        "type_name": "Aset Tetap" if asset['unit_name'] in ["Rumah", "Tanah", "Ruko"] else "Aset Bergerak",
                        "desc": asset.get('address', ""),
                        "luas_tanah": str(asset.get('lt', 0)),
                        "luas_bangunan": str(asset.get('lb', 0)),
                        "harga": asset.get('hrg', 0),
                        "taksasi": asset.get('total_taksasi', 0),
                        "is_akses_roda_empat": to_bool(asset.get('akses_jalan')),
                        "is_terdapat_kuburan": to_bool(asset.get('kuburan')),
                        "is_terdapat_sutet": to_bool(asset.get('sutet')),
                        "is_terdapat_sungai": to_bool(asset.get('sungai')),
                        "is_sesuai_domisili": True if asset.get('domisili') == "Alamat Agunan sesuai KTP" else False,
                        "address": asset['address'],
                        "scores": [
                            {"group": "agunan", "point": find_point('agunan', asset['unit_name'])},
                            {"group": "proses_aset", "point": find_point('proses_aset', asset.get('proses_aset'))},
                            {"group": "kepemilikan_aset", "point": find_point('kepemilikan_aset', asset.get('kepemilikan'))}
                        ]
                    } for i, asset in enumerate(st.session_state.collaterals)
                ]
            },
            "scoring_point": {
                "char": float(summary[summary['Category'] == 'character']['Skor_BE'].sum()),
                "capa": float(summary[summary['Category'] == 'capacity']['Skor_BE'].sum()),
                "cond": float(summary[summary['Category'] == 'condition']['Skor_BE'].sum()),
                "capi": float(summary[summary['Category'] == 'capital']['Skor_BE'].sum())
            }
        }
    }
    # st.download_button("💾 Download Result JSON", json.dumps(json_output, indent=4, cls=NpEncoder), "audit_result.json")
    with st.expander("🔍 Lihat Preview JSON"):
        st.json(json_output)

        # --- BAGIAN DOWNLOAD REPORT (TARUH DI SINI) ---
    st.markdown("---")
    st.subheader("📥 Download Official Report")
    
    try:
        # Panggil fungsi yang sudah kita perbaiki di atas
        final_pdf_bin = generate_pdf_report(
            json_output, 
            final_risk_data['nama_risiko'], 
            risk_color, 
            final_risk_data['deskripsi']
        )
        
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                label="📄 Download Report PDF (Audit)",
                data=final_pdf_bin,
                file_name=f"Audit_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
        with col_dl2:
            st.download_button(
                label="💾 Download Result JSON (System)", 
                data=json.dumps(json_output, indent=4, cls=NpEncoder), 
                file_name=f"audit_result_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )
            
        st.success("✅ Laporan siap diunduh. Silakan pilih format yang diinginkan.")
        
    except Exception as e:
        st.error(f"Sistem gagal membuat PDF: {e}")
