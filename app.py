import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import json
import pandas as pd

# ==========================================
# 1. KONFIGURASI HALAMAN & THEME GLOBAL
# ==========================================
st.set_page_config(
    page_title="Dashboard WebGIS Menara Kota Bandung",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Modern Minimalis
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #0f172a;
        color: #f8fafc;
    }
    [data-testid="stSidebar"] .stSelectbox label {
        color: #cbd5e1 !important;
        font-weight: 500;
    }
    .main-title {
        font-family: 'Inter', sans-serif;
        color: #1e293b;
        font-size: 28px;
        font-weight: 700;
        letter-spacing: -0.5px;
        margin-bottom: 2px;
    }
    .sub-title {
        color: #64748b;
        font-size: 14px;
        margin-bottom: 25px;
    }
    .card-container {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. CACHING DATA (MEMBUAT APLIKASI RINGAN)
# ==========================================
@st.cache_data(show_spinner="Memuat data spasial...")
def load_and_process_data():
    # Fungsi pembacaan GeoJSON aman
    def read_json(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    batas_kota = read_json("batas_kota_bandung.geojson")
    data_bts = read_json("BTS_kota_bandung.geojson")
    
    raw_rows = []
    if data_bts and "features" in data_bts:
        for idx, feature in enumerate(data_bts["features"], start=1):
            geom = feature.get("geometry", {})
            props = feature.get("properties", {})
            
            if geom and geom.get("type") == "Point":
                lon, lat = geom["coordinates"]
                
                def get_prop(keys_list, default="-"):
                    for k in keys_list:
                        for actual_key in props.keys():
                            if actual_key.lower().strip() == k.lower().strip():
                                val = props[actual_key]
                                if val is not None:
                                    # HILANGKAN .0 JIKA ADA: Mengubah float/int ke string bersih tanpa desimal
                                    val_str = str(val).strip()
                                    if val_str.endswith('.0'):
                                        val_str = val_str[:-2]
                                    return val_str
                                return default
                    return default

                raw_rows.append({
                    "id": get_prop(["id", "objectid", "no"], str(idx)),
                    "nama_provinsi": get_prop(["nama_provinsi", "provinsi", "prov"], "JAWA BARAT"),
                    "nama_kabupaten_kota": get_prop(["nama_kabupaten_kota", "kabupaten", "kota"], "KOTA BANDUNG"),
                    "nama_kecamatan": get_prop(["nama_kecamatan", "kecamatan", "kec"]),
                    "nama_desa_kelurahan": get_prop(["nama_desa_kelurahan", "kelurahan", "desa", "kel"]),
                    "pemilik_menara": get_prop(["pemilik_menara", "pemilik", "provider", "operator", "site_name", "nama"]),
                    "lokasi_menara": get_prop(["lokasi_menara", "lokasi", "alamat"]),
                    "long": lon,
                    "lat": lat,
                    "struktur_tower": get_prop(["struktur_tower", "struktur", "tipe", "type"]),
                    "tinggi_tower": get_prop(["tinggi_tower", "tinggi", "height"]),
                    "satuan": get_prop(["satuan", "unit"], "Meter"),
                    "tahun": get_prop(["tahun", "tahun_berdiri", "thn"])
                })
                
    if raw_rows:
        df = pd.DataFrame(raw_rows)
        # PAKSA KOLOM MENJADI TEKS/STRING AGAR PANDAS TIDAK MENGUBAHNYA KE FLOAT
        df["id"] = df["id"].astype(str)
        df["struktur_tower"] = df["struktur_tower"].astype(str)
        df["tinggi_tower"] = df["tinggi_tower"].astype(str)
        df["tahun"] = df["tahun"].astype(str)
    else:
        df = pd.DataFrame(columns=[
            "id", "nama_provinsi", "nama_kabupaten_kota", "nama_kecamatan", "nama_desa_kelurahan",
            "pemilik_menara", "lokasi_menara", "long", "lat", "struktur_tower", "tinggi_tower", "satuan", "tahun"
        ])
        
    return batas_kota, df

# Eksekusi fungsi load data terpangkas cache
batas_kota, df_all = load_and_process_data()
