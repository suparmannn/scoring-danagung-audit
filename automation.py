import streamlit as st

def get_scenario_presets():
    """Data profil nasabah berdasarkan Master Excel DATA SCORE"""
    return {
        "Risiko Rendah (Lolos)KDA Produk 2": {
            # --- CAPACITY ---
            "total_penghasilan": 50000000,
            "pengeluaran_usaha": 5000000,
            "p_sekolah": 1000000,
            "p_transport": 500000,
            "p_listrik": 1000000,
            "p_telepon": 100000,
            "p_hutang": 0,
            "p_arisan": 200000,
            "angs_diambil_val": 2000000,
            "val_credit_check": 850,
            "cap_tenor": 36,
            "cap_usia": 35,
            "cap_work": 10.0,
            "cap_merit": "Kawin",
            "cap_power": "2200",
            "cap_period": "Bulanan",
            
            # --- CHARACTER ---
            "char_tujuan": "Modal Kerja",
            "char_kolektibilitas": "KOL 1 Agunan",
            "char_lama_tinggal": "> 10 Tahun",
            "char_hp": "> 2 Tahun",
            "char_asuransi": "ADA",
            "char_hubungan": "> 2 Tahun",
            "char_kartu": "Ada",
            "char_telp_bayar": "Lancar",
            "char_listrik_bayar": "Lancar",
            "char_sisa_hutang": "Tidak Ada",
            
            # --- CONDITION ---
            "cond_job": "TNI/POLRI",
            "cond_asset": "Kendaraan Roda 4 dan 2",
            "cond_own": "Milik Sendiri",
            
            # --- CAPITAL ---
            "capi_rumah": "Milik Sendiri/Pasangan",
            "capi_perumahan": "Perumahan",
            "capi_tipe": "< 36 m2",

            # --- COLLATERAL ---
            "collaterals": [
                {"unit_name": "Rumah", "address": "Jl. Danagung No. 1", "lt": 150, "lb": 120, "proses_aset": "On Hand", "domisili": "Alamat Agunan sesuai KTP", "kepemilikan": "Milik Sendiri", "akses_jalan": "YA", "kuburan": "TIDAK", "sutet": "TIDAK", "sungai": "TIDAK"}
            ]
        },
        "Reject (Risiko Tinggi)KTA Produk 1": {
            # --- CAPACITY ---
            "total_penghasilan": 5000000,
            "pengeluaran_usaha": 2000000,
            "p_sekolah": 500000,
            "p_transport": 1000000,
            "p_listrik": 500000,
            "p_telepon": 100000,
            "p_hutang": 3000000, # Hutang Besar
            "p_arisan": 0,
            "angs_diambil_val": 1500000,
            "val_credit_check": 100,
            "cap_tenor": 12,
            "cap_usia": 21,
            "cap_work": 0.5,
            "cap_merit": "Belum Kawin",
            "cap_power": "450",
            "cap_period": "Mingguan",
            
            # --- CHARACTER ---
            "char_tujuan": "Konsumtif",
            "char_kolektibilitas": "KOL 5 Agunan",
            "char_lama_tinggal": "< 1 Tahun",
            "char_hp": "< 1 Tahun",
            "char_asuransi": "TIDAK ADA",
            "char_hubungan": "Tidak Ada",
            "char_kartu": "Tidak Ada",
            "char_telp_bayar": "Tidak Lancar",
            "char_listrik_bayar": "Tidak Lancar",
            "char_sisa_hutang": "> 100 Juta",
            
            # --- CONDITION ---
            "cond_job": "Lain-lain",
            "cond_asset": "Tidak Punya",
            "cond_own": "Milik Keluarga",
            
            # --- CAPITAL ---
            "capi_rumah": "Sewa / Kontrak",
            "capi_perumahan": "Non Perumahan",
            "capi_tipe": "Semi Permanen",
            "collaterals": []
        }
    }

def apply_automation(scenario_name):
    presets = get_scenario_presets()
    if scenario_name in presets:
        data = presets[scenario_name]
        for key, value in data.items():
            st.session_state[key] = value
        # Tandai bahwa audit perlu di-run ulang
        st.session_state.audit_run = False 
        return True
    return False