# instal librari: pip install pandas streamlit openpyxl
# cara run: streamlit run scoring.py

import streamlit as st
import pandas as pd
import os
import json
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Audit Tool - Scoring Danagung", layout="wide")

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

    # --- INITIALIZE STATE DEFAULTS ---
if 'total_penghasilan' not in st.session_state:
    st.session_state['total_penghasilan'] = 48000000
    st.session_state['pengeluaran_usaha'] = 8000000
    st.session_state['p_sekolah'] = 2000000
    st.session_state['p_transport'] = 1500000
    st.session_state['p_listrik'] = 1000000
    st.session_state['p_telepon'] = 500000
    st.session_state['p_hutang'] = 2000000
    st.session_state['p_arisan'] = 0
    st.session_state['angs_diambil_val'] = 1184643

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
st.title("🔍 Scoring Verification Tool (Danagung Audit)")
selected_id_produk = st.sidebar.selectbox("Pilih ID Produk", df_hitung['id_produk'].unique())
params_max_angs_diambil = st.sidebar.slider("Batas Max Angsuran (%)", 10, 100, 70)


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
            st.session_state['p_sekolah'] = capa_main.get('pengeluaran_sekolah', 0)
            st.session_state['p_transport'] = capa_main.get('pengeluaran_transportasi', 0)
            st.session_state['p_listrik'] = capa_main.get('pengeluaran_listrik', 0)
            st.session_state['p_telepon'] = capa_main.get('pengeluaran_telepon', 0)
            st.session_state['p_hutang'] = capa_main.get('pengeluaran_hutang', 0)
            st.session_state['p_arisan'] = capa_main.get('pengeluaran_arisan', 0)
            st.session_state['angs_diambil_val'] = payload['pengajuan'].get('submission_loan', 0)
            
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

tab_cap, tab_char, tab_cond, tab_coll, tab_capi = st.tabs(["CAPACITY", "CHARACTER", "CONDITION", "COLLATERAL", "CAPITAL"])
user_inputs = {}

with tab_cap:
    st.subheader("CAPACITY")
    c1, c2 = st.columns(2)
    with c1:
        total_penghasilan = st.number_input("Total Penghasilan", value=st.session_state.get('total_penghasilan', 48000000))
        pengeluaran_usaha = st.number_input("Total Pengeluaran Usaha", value=st.session_state.get('pengeluaran_usaha', 8000000))
        
        st.markdown("---")
        st.write("### 🎓 Detail Biaya Pendidikan & Lainnya")
        
        p_sekolah = st.number_input("Pengeluaran Sekolah", value=st.session_state.get('p_sekolah', 2000000))
        p_transport = st.number_input("Pengeluaran Transportasi", value=st.session_state.get('p_transport', 1500000))
        p_listrik = st.number_input("Pengeluaran Listrik", value=st.session_state.get('p_listrik', 1000000))
        p_telepon = st.number_input("Pengeluaran Telepon", value=st.session_state.get('p_telepon', 500000))
        p_hutang = st.number_input("Pengeluaran Hutang", value=st.session_state.get('p_hutang', 2000000))
        p_arisan = st.number_input("Pengeluaran Arisan", value=st.session_state.get('p_arisan', 0))
        
        # Hitung totPengeluaran (Dasar perhitungan DSR & IDIR)
        totPengeluaran = pengeluaran_usaha + p_sekolah + p_transport + p_listrik + p_telepon + p_hutang + p_arisan
        
        # REVISI: Biaya Rumah Tangga = Total Pengeluaran (Disabled)
        p_rt = st.number_input("Biaya Rumah Tangga", value=totPengeluaran, disabled=True)
        
        st.error(f"Total Pengeluaran : Rp {totPengeluaran:,.0f}")
        angs_diambil = st.number_input("Angsuran yang Akan Diambil", value=st.session_state.get('angs_diambil_val', 1184643))

    with c2:
        # --- IMPLEMENTASI RUMUS JS PERSIS ---
        # 1. this.maksAngusuranDiambil = (total_penghasilan * params.max_angs_diambil / 100) - totPengeluaran
        maksAngsuran = (total_penghasilan * params_max_angs_diambil / 100) - totPengeluaran
        
        # 2. this.qq (DSR) = (totPengeluaran / total_penghasilan) * 100
        dsr_val = round((totPengeluaran / total_penghasilan * 100), 2) if total_penghasilan > 0 else 0
        
        # 3. this.ww (IDIR) = ((angs_diambil + totPengeluaran) / total_penghasilan) * 100
        idir_val = round(((angs_diambil + totPengeluaran) / total_penghasilan * 100), 2) if total_penghasilan > 0 else 0
        
        user_inputs.update({'dsr': dsr_val, 'idir': idir_val, 'jlh_penghasilan': total_penghasilan})
        
        st.metric("DSR (%)", f"{dsr_val}%")
        st.metric("IDIR (%)", f"{idir_val}%")
        st.warning(f"Sisa Kapasitas Angsuran (Maks): Rp {maksAngsuran:,.0f}")
        
        # Sisanya tetap membaca session state
        user_inputs['tenor'] = st.number_input("Tenor (Bulan/Minggu)", value=30)
        user_inputs['usia'] = st.number_input("Usia", value=41)
        user_inputs['lama_kerja'] = st.number_input("Lama Kerja (Tahun)", value=3.0)
        user_inputs['status_perkawinan'] = st.selectbox("Status Perkawinan", get_options_safe('status_perkawinan'))
        user_inputs['daya_listrik'] = st.selectbox("Daya Listrik", get_options_safe('daya_listrik'))
        user_inputs['periode_penghasilan'] = st.selectbox("Periode Penghasilan", get_options_safe('periode_penghasilan'))

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


# --- 4. CALCULATION & JSON GENERATION (FE POINTS vs BE WEIGHTED) ---
if st.button("RUN AUDIT CALCULATION", type="primary", use_container_width=True):
    # 1. Filter rules untuk produk
    rules_table = df_hitung[df_hitung['id_produk'] == selected_id_produk]
    
    # Ambil bobot kategori unik untuk perhitungan BE
    cat_weights_df = rules_table[['score_type.1', 'bobot.1']].dropna()
    cat_weights_df['score_type.1'] = cat_weights_df['score_type.1'].str.lower()
    cat_weight_map = cat_weights_df.drop_duplicates('score_type.1').set_index('score_type.1')['bobot.1'].to_dict()

    details = []
    for _, row in rules_table.iterrows():
        excel_f = row['group']
        ui_f = "tujuan_pinjaman" if excel_f == "purpose" else excel_f
        
        if pd.notna(excel_f) and ui_f in user_inputs:
            # Ambil poin murni dari master
            p = find_point(ui_f, user_inputs[ui_f])
            if ui_f == 'intitusi': p = st.session_state.get('point_institusi', 0)
            
            details.append({
                'Category': str(row['score_type']).lower(), 
                'Field': ui_f, 
                'Value': user_inputs[ui_f], 
                'Point': p,             # Poin FE
                'Field_Weight': row['bobot'], 
                'Weighted_Score': p * row['bobot'] # Poin x Bobot Field
            })

    # Manual injection Institusi
    if 'intitusi' in user_inputs and not any(d['Field'] == 'intitusi' for d in details):
        details.append({
            'Category': 'character', 'Field': 'intitusi', 'Value': user_inputs['intitusi'], 
            'Point': st.session_state.get('point_institusi', 0), 'Field_Weight': 0, 'Weighted_Score': 0
        })
    
    df_res = pd.DataFrame(details)
    
    # --- 2. PERHITUNGAN DUA VERSI (FE & BE) ---
    summary = df_res.groupby('Category').agg({
        'Point': 'sum',           # TOTAL POIN MURNI (Untuk dikirim ke BE)
        'Weighted_Score': 'sum'   # TOTAL POIN x BOBOT FIELD
    }).reset_index()

    # Hitung Skor Akhir BE (Bobot Field x Bobot Kategori)
    summary['Cat_Weight'] = summary['Category'].map(cat_weight_map).fillna(0)
    summary['Final_BE_Score'] = summary['Weighted_Score'] * summary['Cat_Weight'] * 100
    
    # Skor Akhir Keseluruhan (Penentu Risiko)
    total_final_score = round(summary['Final_BE_Score'].sum(), 0)
    
    # --- 3. TAMPILAN PANEL HASIL ---
    st.divider()
    st.subheader("🏁 Ringkasan Skor Audit")
    
    # Penentuan Resiko berdasarkan Skor Akhir BE
    if total_final_score < 400:
        risk_status, risk_color = "Risiko Tinggi", "red"
        risk_desc = "Berdasarkan hasil scoring, Anda tidak memenuhi persyaratan yang ditetapkan."
    elif total_final_score < 600:
        risk_status, risk_color = "Risiko Sedang", "orange"
        risk_desc = "Memerlukan tinjauan manual (Kapasitas pas-pasan)."
    else:
        risk_status, risk_color = "Risiko Rendah", "green"
        risk_desc = "Selamat! Memenuhi kriteria sistem."

    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Skor Akhir (BE)", f"{total_final_score}")
    with c2:
        st.markdown(f"Hasil : **<span style='color:{risk_color}'>{risk_status}</span>**", unsafe_allow_html=True)
        st.write(f"_{risk_desc}_")

    # Tampilkan Tabel Perbandingan agar Anda tidak bingung
    st.write("### 📊 Perbandingan Poin vs Skor Berbobot")
    display_summary = summary.rename(columns={
        'Point': 'Total Poin (FE)', 
        'Final_BE_Score': 'Skor Akhir (BE)',
        'Cat_Weight': 'Bobot 5C'
    })
    st.table(display_summary[['Category', 'Total Poin (FE)', 'Bobot 5C', 'Skor Akhir (BE)']])

    # --- 4. KONSTRUKSI JSON (Scoring Point = Total Poin FE) ---
    def get_scoring_list(category_key):
        filtered = df_res[df_res['Category'] == category_key.lower()]
        return [{"id": find_rule_id(r['Field'], r['Value']), "group": r['Field'], "text": str(r['Value']), "value": r['Value'], "point": int(r['Point'])} for _, r in filtered.iterrows()]

    # AGUNAN JSON
    coll_agunan_json = []
    for asset in st.session_state.collaterals:
        is_at = asset['unit_name'] in ["Rumah", "Tanah", "Ruko"]
        item = {
            "agunan_id": str(np.random.randint(100000, 999999)),
            "unit_name": asset['unit_name'], "type_id": "AT" if is_at else "AB", "desc": asset['address'],
            "scores": [{"group": "agunan", "value": asset['unit_name'], "point": 5}, {"group": "kepemilikan_aset", "value": asset['kepemilikan'], "point": find_point('kepemilikan_aset', asset['kepemilikan'])}]
        }
        if is_at:
            item.update({"luas_tanah": str(asset.get('lt', 0)), "luas_bangunan": str(asset.get('lb', 0))})
        else:
            item.update({"merk": asset.get('merk', ""), "tahun": int(asset.get('thn', 2020)), "harga": int(asset.get('hrg', 0))})
        coll_agunan_json.append(item)

    # --- FINAL JSON ---
    json_output = {
        "error": 0, "message": "OK",
        "data": {
            "pengajuan": {"product_id": str(selected_id_produk), "total_score": total_final_score, "risk_status": risk_status},
            "scoring": {
                "char": get_scoring_list('character'),
                "capa": [{
                    "total_penghasilan": total_penghasilan, "total_pengeluaran": totPengeluaran,
                    "max_angs": maksAngsuran, "angs_diambil": angs_diambil, "idir": idir_val, "dsr": dsr_val
                }] + get_scoring_list('capacity'),
                "cond": get_scoring_list('condition'),
                "capi": get_scoring_list('capital'),
                "coll": [{"group": "comperation_agunan", "point": 5, "total_taksasi": 0, "ltv": 0}],
                "coll_agunan": coll_agunan_json
            },
            # DI SINI KITA KIRIM POIN MURNI (FE) SESUAI REQUEST
            "scoring_point": summary.set_index('Category')['Point'].to_dict()
        }
    }
    

    # DOWNLOAD & PREVIEW
    json_string = json.dumps(json_output, indent=4, cls=NpEncoder)
    st.divider()
    st.download_button("💾 Download Result JSON", json_string, "scoring_audit_result.json", "application/json")
    with st.expander("🔍 Lihat Preview JSON"):
        st.json(json_output)
