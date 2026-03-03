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

tab_cap, tab_char, tab_cond, tab_coll, tab_capi = st.tabs(["CAPACITY", "CHARACTER", "CONDITION", "COLLATERAL", "CAPITAL"])
user_inputs = {}

with tab_cap:
    st.subheader("CAPACITY")
    c1, c2 = st.columns(2)
    with c1:
        total_penghasilan = st.number_input("Total Penghasilan", value=48000000)
        pengeluaran_usaha = st.number_input("Total Pengeluaran Usaha", value=8000000)
        
        # Hitung dulu total pengeluaran detail (tanpa RT dulu)
        detail_pengeluaran = 0 # Inisialisasi
        
        st.markdown("---")
        st.write("### 🎓 Detail Biaya Pendidikan & Lainnya")
        
        p_sekolah = st.number_input("Pengeluaran Sekolah", value=2000000)
        p_transport = st.number_input("Pengeluaran Transportasi", value=1500000)
        p_listrik = st.number_input("Pengeluaran Listrik", value=1000000)
        p_telepon = st.number_input("Pengeluaran Telepon", value=500000)
        p_hutang = st.number_input("Pengeluaran Hutang", value=2000000)
        p_arisan = st.number_input("Pengeluaran Arisan", value=0)
        
        # Total Pengeluaran adalah jumlah dari usaha + semua detail di atas
        totPengeluaran = pengeluaran_usaha + p_sekolah + p_transport + p_listrik + p_telepon + p_hutang + p_arisan
        
        # Pengeluaran Rumah Tangga otomatis mengikuti total dan di-disable
        p_rt = st.number_input("Biaya Rumah Tangga", value=totPengeluaran, disabled=True)
        
        st.error(f"Total Pengeluaran : Rp {totPengeluaran:,.0f}")
        angs_diambil = st.number_input("Angsuran yang Akan Diambil", value=1184643)

    with c2:
        # Rumus tetap sama menggunakan totPengeluaran
        dsr_val = round((totPengeluaran / total_penghasilan * 100), 2) if total_penghasilan > 0 else 0
        idir_val = round(((angs_diambil + totPengeluaran) / total_penghasilan * 100), 2) if total_penghasilan > 0 else 0
        maksAngsuran = (total_penghasilan * params_max_angs_diambil / 100) - totPengeluaran
        
        user_inputs.update({'dsr': dsr_val, 'idir': idir_val, 'jlh_penghasilan': total_penghasilan})
        st.metric("DSR (%)", f"{dsr_val}%")
        st.metric("IDIR (%)", f"{idir_val}%")
        st.warning(f"Max Rekomendasi Angsuran: Rp {maksAngsuran:,.0f}")
    
        
        
        user_inputs['tenor'] = st.number_input("Tenor (Bulan/Minggu)", value=30)
        show_point('tenor', user_inputs['tenor'])
        user_inputs['usia'] = st.number_input("Usia", value=41)
        show_point('usia', user_inputs['usia'])
        user_inputs['lama_kerja'] = st.number_input("Lama Kerja (Tahun)", value=3.0)
        show_point('lama_kerja', user_inputs['lama_kerja'])
        user_inputs['status_perkawinan'] = st.selectbox("Status Perkawinan", get_options_safe('status_perkawinan'))
        show_point('status_perkawinan', user_inputs['status_perkawinan'])
        user_inputs['daya_listrik'] = st.selectbox("Daya Listrik", get_options_safe('daya_listrik'))
        show_point('daya_listrik', user_inputs['daya_listrik'])
        user_inputs['periode_penghasilan'] = st.selectbox("Periode Penghasilan", get_options_safe('periode_penghasilan'))
        show_point('periode_penghasilan', user_inputs['periode_penghasilan'])

with tab_char:
    st.subheader("CHARACTER")
    c1, c2 = st.columns(2)
    with c1:
        user_inputs['tujuan_pinjaman'] = st.selectbox("Tujuan Pinjaman", get_options_safe('tujuan_pinjaman'))
        show_point('tujuan_pinjaman', user_inputs['tujuan_pinjaman'])
        
        # --- UPDATE: Gabung Status Dropdown ---
        list_status = get_options_safe('tanpa_agunan') + get_options_safe('dengan_agunan')
        selected_status = st.selectbox("Status Kolektibilitas", list_status)
        
        # Cari poin status untuk di-inherit ke Institusi
        # Cek apakah status yang dipilih masuk group tanpa atau dengan agunan
        if selected_status in get_options_safe('tanpa_agunan'):
            inherited_point = find_point('tanpa_agunan', selected_status)
        else:
            inherited_point = find_point('dengan_agunan', selected_status)
            
        user_inputs['status'] = selected_status
        st.markdown(f"<small style='color: #007bff;'>Poin Status: <b>{inherited_point}</b></small>", unsafe_allow_html=True)
        
        # --- UPDATE: Institusi inherit poin dari Status ---
        user_inputs['intitusi'] = st.text_input("Institusi Keuangan", value="Modal Usaha")
        st.session_state['point_institusi'] = inherited_point # Simpan ke session untuk dihitung nanti
        st.markdown(f"<small style='color: green;'>Poin Institusi (Auto Match Status): <b>{inherited_point}</b></small>", unsafe_allow_html=True)

        
    with c2:
        fields = ['lama_tinggal', 'kepemilikan_no_hp', 'asuransi_kesehatan', 'hubungan_bank', 'kartu_kredit', 'bayar_telepon', 'bayar_listrik', 'sisa_hutang']
        labels = ["Lama Tinggal", "Lama No HP", "Asuransi Kesehatan", "Hubungan Bank", "Kartu Kredit", "Telepon", "Listrik", "Sisa Hutang"]
        for f, l in zip(fields, labels):
            user_inputs[f] = st.selectbox(l, get_options_safe(f))
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
            col_item['unit_name'] = c1.selectbox(f"Jenis Agunan #{i}", ["Rumah", "Tanah", "Ruko", "Mobil", "Motor"], key=f"unit_{i}")
            col_item['address'] = c2.text_input(f"Alamat/Lokasi #{i}", key=f"addr_{i}")
            
            # LOGIKA FIELD TEKNIS
            if col_item['unit_name'] in ["Rumah", "Ruko"]:
                col_item['lt'] = c1.number_input(f"Luas Tanah #{i}", value=col_item.get('lt', 0), key=f"lt_{i}")
                col_item['lb'] = c2.number_input(f"Luas Bangunan #{i}", value=col_item.get('lb', 0), key=f"lb_{i}")
            elif col_item['unit_name'] == "Tanah":
                col_item['lt'] = c1.number_input(f"Luas Tanah #{i}", value=col_item.get('lt', 0), key=f"lt_{i}")
                # Tanah tidak ada luas bangunan
            else: # Mobil / Motor
                col_item['merk'] = c1.text_input(f"Merk/Tipe #{i}", key=f"merk_{i}")
                col_item['thn'] = c2.number_input(f"Tahun #{i}", value=2020, key=f"thn_{i}")
                col_item['hrg'] = c2.number_input(f"Estimasi Harga #{i}", value=0, key=f"hrg_{i}")

            st.write("**--- Scoring Detail ---**")
            s1, s2, s3 = st.columns(3)
            col_item['proses_aset'] = s1.selectbox(f"Proses Aset #{i}", get_options_safe('proses_aset'), key=f"pr_{i}")
            col_item['domisili'] = s2.selectbox(f"Sesuai KTP #{i}", get_options_safe('domisili'), key=f"dm_{i}")
            col_item['kepemilikan'] = s3.selectbox(f"Kepemilikan #{i}", get_options_safe('kepemilikan_aset'), key=f"kp_{i}")
            
            # LOGIKA LINGKUNGAN (Hanya untuk Aset Tetap)
            if col_item['unit_name'] in ["Rumah", "Tanah", "Ruko"]:
                col_item['akses_jalan'] = s1.selectbox(f"Akses Jalan Roda 4 #{i}", get_options_safe('akses_jalan_roda_4'), key=f"ak_{i}")
                col_item['kuburan'] = s2.selectbox(f"Dalam 200m terdapat kuburan? #{i}", get_options_safe('dalam_200m_terdapat_kuburan'), key=f"kb_{i}")
                col_item['sutet'] = s3.selectbox(f"Dalam 200m terdapat Sutet? #{i}", get_options_safe('dalam_200m_terdapat_sutet'), key=f"st_{i}")
                col_item['sungai'] = s1.selectbox(f"Dalam 200m terdapat Sungai? #{i}", get_options_safe('dalam_200m_terdapat_sungai'), key=f"sg_{i}")
            else:
                # Default untuk aset bergerak agar JSON tidak error
                col_item['akses_jalan'] = "YA"
                col_item['kuburan'] = "TIDAK"; col_item['sutet'] = "TIDAK"; col_item['sungai'] = "TIDAK"

            if st.button(f"🗑️ Hapus Agunan #{i+1}", key=f"del_{i}"):
                st.session_state.collaterals.pop(i)
                st.rerun()

with tab_capi:
    st.subheader("CAPITAL")
    for f in ['kepemilikan_rumah', 'perumahan', 'tipe_rumah']:
        user_inputs[f] = st.selectbox(f.replace('_', ' ').title(), get_options_safe(f))
        show_point(f, user_inputs[f])


# --- 4. CALCULATION & JSON GENERATION (FIX ERROR & ADD RISK STATUS) ---
if st.button("RUN AUDIT CALCULATION", type="primary", use_container_width=True):
    # 1. Filter rules untuk produk
    rules_table = df_hitung[df_hitung['id_produk'] == selected_id_produk]
    
    # FIX: Ambil bobot kategori unik (menghindari InvalidIndexError)
    # Kita ambil kolom score_type.1 dan bobot.1, buang yang kosong, lalu ambil baris unik pertama
    cat_weights_df = rules_table[['score_type.1', 'bobot.1']].dropna()
    cat_weights_df['score_type.1'] = cat_weights_df['score_type.1'].str.lower()
    cat_weight_map = cat_weights_df.drop_duplicates('score_type.1').set_index('score_type.1')['bobot.1'].to_dict()

    details = []
    for _, row in rules_table.iterrows():
        excel_f = row['group']
        ui_f = "tujuan_pinjaman" if excel_f == "purpose" else excel_f
        
        if pd.notna(excel_f) and ui_f in user_inputs:
            p = find_point(ui_f, user_inputs[ui_f])
            if ui_f == 'intitusi': p = st.session_state.get('point_institusi', 0)
            
            details.append({
                'Category': str(row['score_type']).lower(), 
                'Field': ui_f, 'Value': user_inputs[ui_f], 
                'Point': p, 'Weight': row['bobot'], 
                'Weighted': p * row['bobot'] * 100
            })

    # Manual injection Institusi jika belum masuk
    if 'intitusi' in user_inputs and not any(d['Field'] == 'intitusi' for d in details):
        details.append({'Category': 'character', 'Field': 'intitusi', 'Value': user_inputs['intitusi'], 'Point': st.session_state.get('point_institusi', 0), 'Weight': 0, 'Weighted': 0})
    
    df_res = pd.DataFrame(details)
    summary = df_res.groupby('Category')['Weighted'].sum().reset_index()
    summary['Cat_Weight'] = summary['Category'].map(cat_weight_map).fillna(0)
    summary['Final_Score'] = summary['Weighted'] * summary['Cat_Weight']
    
    # --- HITUNG TOTAL SKOR AKHIR ---
    total_score = round(summary['Final_Score'].sum(), 0)
    
    # Penentuan Resiko (Threshold bisa disesuaikan)
    if total_score < 400:
        risk_status = "Risiko Tinggi"
        risk_desc = "Anda tidak memenuhi persyaratan yang ditetapkan."
        risk_color = "red"
    elif total_score < 550:
        risk_status = "Risiko Sedang"
        risk_desc = "Memerlukan tinjauan manual lebih lanjut."
        risk_color = "orange"
    else:
        risk_status = "Risiko Rendah"
        risk_desc = "Memenuhi persyaratan yang ditetapkan."
        risk_color = "green"

    st.divider()
    
    # --- TAMPILAN HASIL SCORING (UI REVISI) ---
    st.write("### 📊 Hasil Scoring")
    res_c1, res_c2 = st.columns([1, 2])
    with res_c1:
        st.metric("Total Skor", f"{total_score}")
    with res_c2:
        st.markdown(f"Hasil : **<span style='color:{risk_color}'>{risk_status}</span>**", unsafe_allow_html=True)
        st.write(f"_{risk_desc}_")

    st.table(summary)

    # --- AGUNAN JSON ---
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
            item['scores'].extend([{"group": "akses_jalan_roda_4", "value": asset['akses_jalan'], "point": find_point('akses_jalan_roda_4', asset['akses_jalan'])}])
        else:
            item.update({"merk": asset.get('merk', ""), "tahun": int(asset.get('thn', 2020)), "harga": int(asset.get('hrg', 0))})
        coll_agunan_json.append(item)

    # Helper function scoring list
    def get_scoring_list(category_key):
        filtered = df_res[df_res['Category'] == category_key.lower()]
        return [{"id": find_rule_id(r['Field'], r['Value']), "group": r['Field'], "text": str(r['Value']), "value": r['Value'], "point": int(r['Point'])} for _, r in filtered.iterrows()]

    # --- KONSTRUKSI JSON ---
    json_output = {
        "error": 0, "message": "OK", "response_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": {
            "pengajuan": {"product_id": str(selected_id_produk), "tenor": user_inputs.get('tenor'), "total_score": total_score, "risk_status": risk_status},
            "scoring": {
                "char": get_scoring_list('character'),
                "capa": [{
                    "total_penghasilan": total_penghasilan, "total_pengeluaran": totPengeluaran,
                    "total_pengeluaran_usaha": pengeluaran_usaha, "pengeluaran_sekolah": p_sekolah,
                    "pengeluaran_transportasi": p_transport, "pengeluaran_listrik": p_listrik,
                    "pengeluaran_telepon": p_telepon, "pengeluaran_hutang": p_hutang,
                    "pengeluaran_arisan": p_arisan, "max_angs": maksAngsuran,
                    "angs_diambil": angs_diambil, "idir": user_inputs['idir'], "dsr": user_inputs['dsr']
                }] + get_scoring_list('capacity'),
                "cond": get_scoring_list('condition'),
                "capi": get_scoring_list('capital'),
                "coll": [{"group": "comperation_agunan", "point": 5, "total_taksasi": 0, "ltv": 0}],
                "coll_agunan": coll_agunan_json
            },
            "scoring_point": {k: (0 if pd.isna(v) else v) for k, v in summary.set_index('Category')['Final_Score'].to_dict().items()}
        }
    }

    # DOWNLOAD & PREVIEW
    json_string = json.dumps(json_output, indent=4, cls=NpEncoder)
    st.divider()
    st.download_button("💾 Download Result JSON", json_string, "scoring_audit_result.json", "application/json")
    with st.expander("🔍 Lihat Preview JSON"):
        st.json(json_output)