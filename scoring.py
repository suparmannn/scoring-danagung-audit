# instal librari: pip install pandas streamlit openpyxl
# cara run: streamlit run scoring.py

import streamlit as st
import pandas as pd
import os
import json
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Audit Tool - Scoring Danagung", layout="wide")

# --- CUSTOM CSS UNTUK STYLING INPUT ---
# --- REVISI CSS (Ganti Poin 3 & 5) ---
st.markdown("""
    <style>
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
if 'total_penghasilan' not in st.session_state:
    st.session_state['total_penghasilan'] = 29212124
    st.session_state['pengeluaran_usaha'] = 9220230
    st.session_state['p_rt_murni'] = 293234 
    st.session_state['p_sekolah'] = 23032
    st.session_state['p_transport'] = 200000
    st.session_state['p_listrik'] = 1000000
    st.session_state['p_telepon'] = 2000
    st.session_state['p_hutang'] = 450000
    st.session_state['p_arisan'] = 239000
    st.session_state['angs_diambil_val'] = 306638

# --- 2. ENCODER & HELPERS ---
class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        return super(NpEncoder, self).default(obj)

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
params_max_angs_diambil = st.sidebar.slider("Batas Max Angsuran (%)", 10, 100, 70)
user_inputs = {}
# # --- UPDATE TAB LIST ---
# tab_cap, tab_char, tab_cond, tab_coll, tab_capi, tab_risk = st.tabs([
#     "CAPACITY", "CHARACTER", "CONDITION", "COLLATERAL", "CAPITAL", "🛡️ RISK MASTER"
# ])
# --- 3. UI HEADER (GANTI st.title LAMA DENGAN INI) ---
header_col1, header_col2 = st.columns([1, 4])

with header_col1:
    # Cek apakah file logo ada, jika tidak pakai placeholder
    if os.path.exists('logo_danagung.png'):
        st.image('logo_danagung.png', width=200)
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


# --- JSON IMPORTER (AUTO-FILL FEATURE) ---
with st.sidebar.expander("📥 Import Data dari JSON"):
    json_input_raw = st.text_area("Paste JSON Payload di sini:")
    if st.button("Load Data JSON"):
        try:
            input_data = json.loads(json_input_raw)
            payload = input_data.get('payload', input_data) # Support format wrap atau direct
            
            # 1. Simpan ke Session State untuk Kapasitas
         
            capa_main = payload['scoring']['capa'][0]
            st.session_state['total_penghasilan'] = capa_main.get('total_penghasilan', 0)
            st.session_state['pengeluaran_usaha'] = capa_main.get('total_pengeluaran_usaha', 0)
            st.session_state['p_rt_murni'] = capa_main.get('pengeluaran_rumah_tangga', 0) # <--- MAPPING BARU
            st.session_state['p_sekolah'] = capa_main.get('pengeluaran_sekolah', 0)
            st.session_state['p_transport'] = capa_main.get('pengeluaran_transportasi', 0)
            st.session_state['p_listrik'] = capa_main.get('pengeluaran_listrik', 0)
            st.session_state['p_telepon'] = capa_main.get('pengeluaran_telepon', 0)
            st.session_state['p_hutang'] = capa_main.get('pengeluaran_hutang', 0)
            st.session_state['p_arisan'] = capa_main.get('pengeluaran_arisan', 0)
            st.session_state['angs_diambil_val'] = capa_main.get('angs_diambil', 0)
            
            # 2. Simpan Data Agunan (CRUD)
            st.session_state.collaterals = []
            for item in payload['scoring'].get('coll_agunan', []):
                new_asset = {
                    "unit_name": item.get('unit_name'),
                    "address": item.get('address', item.get('desc')),
                    "lt": item.get('luas_tanah', 0),
                    "lb": item.get('luas_bangunan', 0),
                    "merk": item.get('merk', ""),
                    "thn": item.get('tahun', 2020),
                    "hrg": item.get('harga', 0),
                }
                # Mapping scores agunan
                for s in item.get('scores', []):
                    if s['group'] == 'proses_aset': new_asset['proses_aset'] = s['value']
                    if s['group'] == 'akses_jalan_roda_4': new_asset['akses_jalan'] = s['value']
                    if s['group'] == 'domisili': new_asset['domisili'] = s['value']
                    if s['group'] == 'kepemilikan_aset': new_asset['kepemilikan'] = s['value']
                
                st.session_state.collaterals.append(new_asset)
            
            st.success("Data berhasil di-load! Silakan cek setiap Tab.")
            st.rerun()
        except Exception as e:
            st.error(f"Format JSON salah: {e}")

# --- UPDATE SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.subheader("🛡️ External Checking")
val_credit_check = st.sidebar.number_input("Skor Credit Checking (SLIK/OJK)", value=550)

# --- MASTER PARAMETER LIST ---
PARAM_FIELDS = {
    'total_penghasilan': 'Total Penghasilan',
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

with tab_risk:
    st.subheader("📋 Master Matrix Risiko (BE Logic Reference)")
    
    # Konversi JSON ke DataFrame agar rapi
    df_risk_ui = pd.json_normalize(MASTER_RISIKO_SCORE)
    
    # Gabung kolom range agar enak dibaca
    df_risk_ui['BE_Score_Range'] = df_risk_ui['range_score.min'].astype(str) + " - " + df_risk_ui['range_score.max'].astype(str)
    df_risk_ui['Credit_Check_Range'] = df_risk_ui['range_score_credit_checking.min'].astype(str) + " - " + df_risk_ui['range_score_credit_checking.max'].astype(str)
    
    # Seleksi kolom yang relevan
    cols_to_show = ['_id', 'nama_risiko', 'BE_Score_Range', 'Credit_Check_Range', 'level', 'deskripsi']
    
    # Tampilkan tabel dengan desain interaktif
    st.dataframe(df_risk_ui[cols_to_show].rename(columns={
        'nama_risiko': 'Status Risiko',
        'level': 'Level',
        'deskripsi': 'Analisa BE'
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

        # --- PERBAIKAN DI SINI ---
        # Gunakan p_rt_murni_calc (angka), JANGAN p_rt_murni (teks)
        current_vals = {
            'p_rt_murni': p_rt_murni_calc, # <--- Ganti bagian ini
            'p_sekolah': p_sekolah,
            'p_transport': p_transport,
            'p_listrik': p_listrik,
            'p_telepon': p_telepon,
            'p_hutang': p_hutang,
            'p_arisan': p_arisan
        }

        # Sekarang sum() tidak akan error karena isinya angka semua
        beban_dsr = sum(current_vals[p] for p in selected_dsr)
        beban_idir = sum(current_vals[p] for p in selected_idir)
        
        st.error(f"Beban Terpilih: DSR (Rp {beban_dsr:,.0f}) | IDIR (Rp {beban_idir:,.0f})")
        angs_diambil = st.number_input("Angsuran yang Akan Diambil", value=st.session_state.get('angs_diambil_val', 0))

    with c2:
        # FIX: Definisi Rumus & Maks Angsuran agar tidak NameError
        dsr_val = round((beban_dsr / total_penghasilan * 100), 2) if total_penghasilan > 0 else 0
        idir_val = round(((angs_diambil + beban_idir) / total_penghasilan * 100), 2) if total_penghasilan > 0 else 0
        
        # Rumus Maks Angsuran berdasarkan batas % yang dipilih di sidebar
        maksAngsuran = (total_penghasilan * params_max_angs_diambil / 100) - beban_idir
        
        st.metric("DSR (%)", f"{dsr_val}%", help="Hanya menghitung parameter yang dipilih di Settings")
        st.metric("IDIR (%)", f"{idir_val}%", help="Menghitung angsuran baru + parameter pilihan di Settings")
        st.warning(f"Sisa Kapasitas Angsuran (Maks): Rp {maksAngsuran:,.0f}")
        
        # Simpan ke user_inputs untuk proses audit
        user_inputs.update({
            'dsr': dsr_val, 'idir': idir_val, 'jlh_penghasilan': total_penghasilan,
            'tenor': st.number_input("Tenor", value=30),
            'usia': st.number_input("Usia", value=41),
            'lama_kerja': st.number_input("Lama Kerja", value=3.0),
            'status_perkawinan': st.selectbox("Status Perkawinan", get_options_safe('status_perkawinan')),
            'daya_listrik': st.selectbox("Daya Listrik", get_options_safe('daya_listrik')),
            'periode_penghasilan': st.selectbox("Periode Penghasilan", get_options_safe('periode_penghasilan'))
        })

with tab_char:
    st.subheader("CHARACTER")
    c1, c2 = st.columns(2)
    with c1:
        user_inputs['tujuan_pinjaman'] = st.selectbox("Tujuan Pinjaman", get_options_safe('tujuan_pinjaman'))
        show_point('tujuan_pinjaman', user_inputs['tujuan_pinjaman'])
        
        # --- MERGED STATUS DROPDOWN ---
        list_status = get_options_safe('tanpa_agunan') + get_options_safe('dengan_agunan')
        selected_status = st.selectbox("Status Kolektibilitas", list_status)
        
        # Logic Point Inheritance
        if selected_status in get_options_safe('tanpa_agunan'):
            inherited_point = find_point('tanpa_agunan', selected_status)
        else:
            inherited_point = find_point('dengan_agunan', selected_status)
            
        user_inputs['status'] = selected_status
        st.markdown(f"<small style='color: #007bff;'>Poin Status: <b>{inherited_point}</b></small>", unsafe_allow_html=True)
        
        # --- INSTITUSI (Inherit Point) ---
        user_inputs['intitusi'] = st.text_input("Institusi Keuangan", value="Modal Usaha")
        st.session_state['point_institusi'] = inherited_point 
        st.markdown(f"<small style='color: green;'>Poin Institusi (Auto Match Status): <b>{inherited_point}</b></small>", unsafe_allow_html=True)
        
    with c2:
        for f, l in zip(['lama_tinggal', 'kepemilikan_no_hp', 'asuransi_kesehatan', 'hubungan_bank', 'kartu_kredit', 'bayar_telepon', 'bayar_listrik', 'sisa_hutang'], 
                        ["Lama Tinggal", "Lama No HP", "Asuransi Kesehatan", "Hubungan Bank", "Kartu Kredit", "Telepon", "Listrik", "Sisa Hutang"]):
            user_inputs[f] = st.selectbox(l, get_options_safe(f), key=f"char_{f}")
            show_point(f, user_inputs[f])

with tab_cond:
    st.subheader("CONDITION")
    for f in ['pekerjaan', 'jenis_aset', 'kepemilikan_aset']:
        user_inputs[f] = st.selectbox(f.replace('_', ' ').title(), get_options_safe(f))
        show_point(f, user_inputs[f])

with tab_coll:
    st.subheader("COLLATERAL (Dynamic Assets)")
    
    if st.button("➕ Tambah Data Agunan"):
        st.session_state.collaterals.append({
            "unit_name": "Rumah", "address": "", "lt": 0, "lb": 0, "merk": "", "thn": 2020, "hrg": 0,
            "proses_aset": "On Hand", "akses_jalan": "YA", "domisili": "Alamat Agunan sesuai KTP", 
            "kepemilikan": "Milik Sendiri", "kuburan": "TIDAK", "sutet": "TIDAK", "sungai": "TIDAK"
        })

    for i, col_item in enumerate(st.session_state.collaterals):
        with st.expander(f"📌 Agunan Ke-{i+1}: {col_item['unit_name']}", expanded=True):
            c1, c2 = st.columns(2)
            unit_opts = ["Rumah", "Tanah", "Ruko", "Mobil", "Motor"]
            col_item['unit_name'] = c1.selectbox(f"Jenis Agunan #{i}", unit_opts, 
                                                index=unit_opts.index(col_item['unit_name']) if col_item['unit_name'] in unit_opts else 0,
                                                key=f"unit_{i}")
            col_item['address'] = c2.text_input(f"Alamat/Lokasi #{i}", value=col_item.get('address') or "", key=f"addr_{i}")
            
            # --- LOGIKA FIELD TEKNIS ---
            if col_item['unit_name'] in ["Rumah", "Ruko"]:
                col_item['lt'] = c1.number_input(f"Luas Tanah #{i}", value=int(col_item.get('lt') or 0), key=f"lt_{i}")
                col_item['lb'] = c2.number_input(f"Luas Bangunan #{i}", value=int(col_item.get('lb') or 0), key=f"lb_{i}")
            elif col_item['unit_name'] == "Tanah":
                col_item['lt'] = c1.number_input(f"Luas Tanah #{i}", value=int(col_item.get('lt') or 0), key=f"lt_{i}")
                col_item['lb'] = 0 # Tanah tidak punya bangunan
            else: # Kendaraan
                col_item['merk'] = c1.text_input(f"Merk/Tipe #{i}", value=col_item.get('merk') or "", key=f"merk_{i}")
                col_item['thn'] = c2.number_input(f"Tahun #{i}", value=int(col_item.get('thn') or 2020), key=f"thn_{i}")
                col_item['hrg'] = c2.number_input(f"Estimasi Harga #{i}", value=int(col_item.get('hrg') or 0), key=f"hrg_{i}")

            st.write("**--- Scoring Detail ---**")
            s1, s2, s3 = st.columns(3)
            def get_choice_idx(opts, val): return opts.index(val) if val in opts else 0

            col_item['proses_aset'] = s1.selectbox(f"Proses Aset #{i}", get_options_safe('proses_aset'), index=get_choice_idx(get_options_safe('proses_aset'), col_item.get('proses_aset')), key=f"pr_{i}")
            col_item['domisili'] = s2.selectbox(f"Sesuai KTP #{i}", get_options_safe('domisili'), index=get_choice_idx(get_options_safe('domisili'), col_item.get('domisili')), key=f"dm_{i}")
            col_item['kepemilikan'] = s3.selectbox(f"Kepemilikan #{i}", get_options_safe('kepemilikan_aset'), index=get_choice_idx(get_options_safe('kepemilikan_aset'), col_item.get('kepemilikan')), key=f"kp_{i}")
            
            # --- LOGIKA LINGKUNGAN: Hanya untuk Aset Tetap ---
            if col_item['unit_name'] in ["Rumah", "Tanah", "Ruko"]:
                col_item['akses_jalan'] = s1.selectbox(f"Akses Roda 4 #{i}", get_options_safe('akses_jalan_roda_4'), index=get_choice_idx(get_options_safe('akses_jalan_roda_4'), col_item.get('akses_jalan')), key=f"ak_{i}")
                col_item['kuburan'] = s2.selectbox(f"Ada Kuburan? #{i}", get_options_safe('dalam_200m_terdapat_kuburan'), index=get_choice_idx(get_options_safe('dalam_200m_terdapat_kuburan'), col_item.get('kuburan')), key=f"kb_{i}")
                col_item['sutet'] = s3.selectbox(f"Ada Sutet? #{i}", get_options_safe('dalam_200m_terdapat_sutet'), index=get_choice_idx(get_options_safe('dalam_200m_terdapat_sutet'), col_item.get('sutet')), key=f"st_{i}")
                col_item['sungai'] = s1.selectbox(f"Ada Sungai? #{i}", get_options_safe('dalam_200m_terdapat_sungai'), index=get_choice_idx(get_options_safe('dalam_200m_terdapat_sungai'), col_item.get('sungai')), key=f"sg_{i}")
            else:
                # Default untuk kendaraan (Hapus data lingkungan agar JSON bersih)
                col_item['akses_jalan'] = "YA"; col_item['kuburan'] = "TIDAK"
                col_item['sutet'] = "TIDAK"; col_item['sungai'] = "TIDAK"

            if st.button(f"🗑️ Hapus Agunan #{i+1}", key=f"del_{i}"):
                st.session_state.collaterals.pop(i)
                st.rerun()

with tab_capi:
    st.subheader("CAPITAL")
    for f in ['kepemilikan_rumah', 'perumahan', 'tipe_rumah']:
        user_inputs[f] = st.selectbox(f.replace('_', ' ').title(), get_options_safe(f))
        show_point(f, user_inputs[f])

  # --- MASTER BOBOT HARDCODE ---
WEIGHT_CONFIG = {
    "001": {"capacity": 0.25, "character": 0.20, "condition": 0.30, "capital": 0.25, "collateral": 0.0},
    "002": {"capacity": 0.15, "character": 0.20, "condition": 0.30, "capital": 0.15, "collateral": 0.20},
    "003": {"capacity": 0.15, "character": 0.20, "condition": 0.30, "capital": 0.15, "collateral": 0.20},
}


# --- 5. Button PERHITUNGAN & OUTPUT ---

if st.button("RUN AUDIT CALCULATION", type="primary", use_container_width=True):
    prod_id = str(selected_id_produk).strip()
    cat_weight_map = WEIGHT_CONFIG.get(prod_id, WEIGHT_CONFIG["002"])

    details = []
    rules_table = df_hitung[df_hitung['id_produk'] == selected_id_produk]
    
    # 1. LOOP KALKULASI DATA
    for _, row in rules_table.iterrows():
        f_name = row['group']
        # --- FITUR BARU: Filter Poin Scoring ---
        if f_name in active_scoring_fields:
            p = find_point(f_name, user_inputs.get(f_name, 0))
            w = row['bobot']
        else:
            # Jika tidak dicentang di sidebar, poin otomatis 0
            p = 0
            w = 0
            
        details.append({
            'Category': str(row['score_type']).lower().strip(),
            'Field': f_name, 
            'Point': p, 'Weight': w, 'Weighted': p * w
        })

    # 2. INPUT AGUNAN DINAMIS
    total_coll_points_raw = 0
    for asset in st.session_state.collaterals:
        p_a = find_point('agunan', asset['unit_name']) or 5
        p_k = find_point('kepemilikan_aset', asset['kepemilikan']) or 5
        total_coll_points_raw += (p_a + p_k + 30)

    details.append({
        'Category': 'collateral', 'Field': 'dynamic_collateral', 'Value': f"{len(st.session_state.collaterals)} Assets",
        'Point': total_coll_points_raw, 'Weight': 1.0, 'Weighted': total_coll_points_raw
    })

    # 3. PROSES SUMMARY & SKOR BE
    df_res = pd.DataFrame(details)
    summary = df_res.groupby('Category').agg({'Point': 'sum', 'Weighted': 'sum'}).reset_index()
    summary['Cat_Weight'] = summary['Category'].map(cat_weight_map).fillna(0)
    summary['Skor_BE'] = summary['Weighted'] * summary['Cat_Weight'] * 100
    total_be_score = round(summary['Skor_BE'].sum(), 0)

    # 4. LOOKUP RISIKO & DEFINISI WARNA (WAJIB DI SINI AGAR TIDAK ERROR)
    final_risk_data = next((
        risk for risk in MASTER_RISIKO_SCORE 
        if risk['range_score']['min'] <= total_be_score <= risk['range_score']['max']
        and risk['range_score_credit_checking']['min'] <= val_credit_check <= risk['range_score_credit_checking']['max']
    ), {"_id": 0, "nama_risiko": "Manual Review", "level": "N/A", "deskripsi": "Skor diluar jangkauan."})

    # Tentukan Warna Berdasarkan Status
    color_map = {"Risiko Rendah": "#22c55e", "Risiko Sedang": "#eab308", "Risiko Tinggi": "#ef4444", "Reject": "#ef4444"}
    risk_color = color_map.get(final_risk_data['nama_risiko'], "#3b82f6")

    # 5. PROSES DISPLAY TABLE (CLEAN FORMAT)
    summary_display = summary.copy()
    summary_display['Total Poin'] = summary_display['Point'].astype(int)
    summary_display['Weighted Subtotal'] = summary_display['Weighted'].map("{:,.2f}".format)
    summary_display['Bobot Produk'] = (summary_display['Cat_Weight']).map("{:,.2f}".format)
    summary_display['Skor Final'] = summary_display['Skor_BE'].map("{:,.2f}".format)
    summary_display = summary_display[['Category', 'Total Poin', 'Weighted Subtotal', 'Bobot Produk', 'Skor Final']]

    # 6. UI OUTPUT (PREMIUM OJK STYLE)
    st.divider()
    st.markdown(f"""
        <div class="report-card">
            <h3 style='margin:0; color:#e2e8f0;'>HASIL ANALISA RISIKO</h3>
            <h1 style='color:{risk_color}; margin:10px 0;'>{final_risk_data['nama_risiko']}</h1>
            <p style='color:#94a3b8;'>Skor Akhir: <b style='color:white; font-size:24px;'>{total_be_score}</b></p>
            <hr style='border: 0.5px solid #334155;'>
            <p style='color:#e2e8f0;'><b>Analisa Auditor:</b> {final_risk_data['deskripsi']}</p>
        </div>
    """, unsafe_allow_html=True)

    st.table(summary_display)

    # 7. JSON CONSTRUCTOR
    def get_scoring_list_internal(category_key):
        if df_res.empty: return []
        filtered = df_res[df_res['Category'] == category_key.lower()]
        return [{"id": find_rule_id(r['Field'], r.get('Value', '')), "group": r['Field'], 
                 "text": str(r.get('Value', '')), "value": r.get('Value', ''), "point": int(r['Point'])} 
                for _, r in filtered.iterrows()]

    json_output = {
        "error": 0, "message": "OK", "response_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": {
            "pengajuan": {"product_id": prod_id, "total_be_score": total_be_score, "risk_status": final_risk_data['nama_risiko']},
            "risk_analysis": final_risk_data,
            "scoring": {
                "char": get_scoring_list_internal('character'),
                "capa": [{
                        "total_penghasilan": total_penghasilan, "total_pengeluaran": p_rt_murni,
                        "max_angs": maksAngsuran, "angs_diambil": angs_diambil,
                        "idir": idir_val, "dsr": dsr_val
                }] + get_scoring_list_internal('capacity'),
                "cond": get_scoring_list_internal('condition'),
                "capi": get_scoring_list_internal('capital'),
                "coll_agunan": coll_agunan_json
            }
        }
    }

    # DOWNLOAD & PREVIEW
    st.download_button("💾 Download Result JSON", json.dumps(json_output, indent=4, cls=NpEncoder), "scoring_audit_result.json", "application/json")
    with st.expander("🔍 Lihat Preview JSON"):
        st.json(json_output)
