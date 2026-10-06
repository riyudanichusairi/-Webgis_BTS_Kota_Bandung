import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import json
import pandas as pd
import os

# ==========================================
# 1. KONFIGURASI HALAMAN UTAMA (FULL SCREEN LAYOUT)
# ==========================================
st.set_page_config(
    page_title="Visualisasi Data Infrastruktur Menara Telekomunikasi",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Kustomisasi CSS Tingkat Lanjut - Diperbaiki agar fleksibel dan tidak pecah
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    
    div[data-testid="stSidebarUserContent"] {
        background-color: #ffffff !important;
        padding: 15px !important;
        border-right: 1px solid #cbd5e1;
    }
    
    .gov-header {
        background-color: #0b3c5d;
        padding: 12px 25px;
        color: #ffffff;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: -75px;
        margin-left: -4rem;
        margin-right: -4rem;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    .gov-header-title {
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 16px;
        font-weight: bold;
        letter-spacing: 0.5px;
    }
    .gov-header-subtitle {
        font-size: 11px;
        color: #93c5fd;
        font-family: Arial, sans-serif;
        margin-top: 2px;
    }
    .gov-header-right {
        font-size: 12px;
        font-family: Arial, sans-serif;
    }
    
    .panel-section-title {
        background-color: #f1f5f9;
        padding: 6px 10px;
        font-size: 12px;
        font-weight: bold;
        color: #1e293b;
        border-left: 4px solid #f59e0b;
        margin-top: 15px;
        margin-bottom: 10px;
        text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. KOMPONEN HEADER UTAMA ATAS (TOP BAR)
# ==========================================
st.markdown("""
    <div class="gov-header">
        <div>
            <div class="gov-header-title">🏛️ VISUALISASI DATA INFRASTRUKTUR TELEKOMUNIKASI</div>
            <div class="gov-header-subtitle">DIREKTORAT JENDERAL PENYELENGGARAAN POS DAN INFORMATIKA - KEMENTERIAN KOMUNIKASI DAN DIGITAL</div>
        </div>
        <div class="gov-header-right">
            <b>🏠 Home &nbsp;|&nbsp; 🌐 Diskominfo Kota Bandung</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 3. FUNGSI LOAD DATA DATASET SPASIAL
# ==========================================
def load_geojson(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

batas_kota = load_geojson("batas_kota_bandung.geojson")
data_bts = load_geojson("BTS_kota_bandung.geojson")

raw_rows = []
if data_bts:
    for idx, feature in enumerate(data_bts["features"], start=1):
        geom = feature["geometry"]
        props = feature["properties"]
        
        if geom["type"] == "Point":
            lon, lat = geom["coordinates"]
            
            def get_prop(keys_list, default="-"):
                for k in keys_list:
                    for actual_key in props.keys():
                        if actual_key.lower().strip() == k.lower().strip():
                            val = props[actual_key]
                            return str(val).strip() if val is not None else default
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

df_all = pd.DataFrame(raw_rows) if raw_rows else pd.DataFrame(columns=[
    "id", "nama_provinsi", "nama_kabupaten_kota", "nama_kecamatan", "nama_desa_kelurahan",
    "pemilik_menara", "lokasi_menara", "long", "lat", "struktur_tower", "tinggi_tower", "satuan", "tahun"
])

# ==========================================
# 4. PANEL PANEL KIRI (SIDEBAR CONTROL DAN DAFTAR LAYER)
# ==========================================
with st.sidebar:
    st.markdown('<div class="panel-section-title">🔍 Cari Data Berdasarkan Wilayah</div>', unsafe_allow_html=True)
    
    list_kec = ["-- Semua Kecamatan --"] + sorted([x for x in df_all["nama_kecamatan"].unique() if x != "-"])
    selected_kec = st.selectbox("Kecamatan", list_kec)
    
    if selected_kec != "-- Semua Kecamatan --":
        df_filtered_kec = df_all[df_all["nama_kecamatan"] == selected_kec]
        list_kel = ["-- Semua Desa/Kelurahan --"] + sorted([x for x in df_filtered_kec["nama_desa_kelurahan"].unique() if x != "-"])
    else:
        list_kel = ["-- Semua Desa/Kelurahan --"] + sorted([x for x in df_all["nama_desa_kelurahan"].unique() if x != "-"])
    selected_kel = st.selectbox("Kelurahan / Desa", list_kel)
    
    selected_pemilik = st.selectbox("Pemilik Menara", ["-- Semua Pemilik --"] + sorted([x for x in df_all["pemilik_menara"].unique() if x != "-"]))
    selected_struktur = st.selectbox("Struktur Tower", ["-- Semua Struktur --"] + sorted([x for x in df_all["struktur_tower"].unique() if x != "-"]))

    st.sidebar.markdown('<div class="panel-section-title">📂 Daftar Peta (Lapisan Layer)</div>', unsafe_allow_html=True)
    show_batas_prov = st.sidebar.checkbox("📁 Batas Provinsi", value=True)
    show_batas_kab = st.sidebar.checkbox("📁 Batas Kabupaten/Kota", value=True)
    show_batas_kec = st.sidebar.checkbox("📁 Batas Kecamatan", value=True)
    show_menara_layer = st.sidebar.checkbox("📍 Sebaran Titik Menara BTS", value=True)
    
    st.sidebar.markdown('<div class="panel-section-title">📊 Ringkasan Statistik</div>', unsafe_allow_html=True)
    st.sidebar.metric(label="Jumlah Menara Terfilter", value=f"{len(df_all)} Unit")

# --- MENJALANKAN STRATEGI FILTER DATA PANDAS ---
df_filtered = df_all.copy()
if selected_kec != "-- Semua Kecamatan --":
    df_filtered = df_filtered[df_filtered["nama_kecamatan"] == selected_kec]
if selected_kel != "-- Semua Desa/Kelurahan --":
    df_filtered = df_filtered[df_filtered["nama_desa_kelurahan"] == selected_kel]
if selected_pemilik != "-- Semua Pemilik --":
    df_filtered = df_filtered[df_filtered["pemilik_menara"] == selected_pemilik]
if selected_struktur != "-- Semua Struktur --":
    df_filtered = df_filtered[df_filtered["struktur_tower"] == selected_struktur]


# ==========================================
# 5. AREA UTAMA KANAN (MAP DAN DATA SPASIAL TABULAR)
# ==========================================

# Membuat peta dasar Citra Satelit Esri agar kontras wilayah terlihat jelas
m = folium.Map(
    location=[-6.9175, 107.6191], 
    zoom_start=12, 
    tiles="https://arcgisonline.com{z}/{y}/{x}",
    attr="Esri World Imagery"
)

if (show_batas_prov or show_batas_kab or show_batas_kec) and batas_kota:
    folium.GeoJson(
        data=batas_kota,
        style_function=lambda feature: {
            "fillColor": "#eab308",
            "color": "#eab308",
            "weight": 1.5,
            "fillOpacity": 0.05,
        }
    ).add_to(m)

custom_icon_path = "tower_icon.png"
has_custom_icon = os.path.exists(custom_icon_path)

if show_menara_layer and not df_filtered.empty:
    marker_cluster = MarkerCluster(
        options={'maxClusterRadius': 40, 'disableClusteringAtZoom': 14}
    ).add_to(m)
    
    for _, row in df_filtered.iterrows():
        p_html = "<div style='font-family:Arial; font-size:12px; width:220px; color:#1e293b;'>" + \
                 "<b style='color:#0b3c5d;'>Detail Menara Telekomunikasi</b><hr style='margin:4px 0;'>" + \
                 "<b>Pemilik:</b> " + str(row['pemilik_menara']) + "<br>" + \
                 "<b>Kecamatan:</b> " + str(row['nama_kecamatan']) + "<br>" + \
                 "<b>Kelurahan:</b> " + str(row['nama_desa_kelurahan']) + "<br>" + \
                 "<b>Struktur:</b> " + str(row['struktur_tower']) + "<br>" + \
                 "<b>Tinggi:</b> " + str(row['tinggi_tower']) + " " + str(row['satuan']) + "<br>" + \
                 "<b>Tahun:</b> " + str(row['tahun']) + "<br><hr style='margin:4px 0;'>" + \
                 "<b>Lat:</b> " + str(row['lat']) + "<br><b>Long:</b> " + str(row['long']) + "</div>"
        
        if has_custom_icon:
            icon_obj = folium.CustomIcon(custom_icon_path, icon_size=(35, 35), icon_anchor=(17.5, 35))
        else:
            icon_obj = folium.Icon(color="red", icon="signal", prefix="fa")
            
        folium.Marker(
            location=[row['lat'], row['long']],
            popup=folium.Popup(p_html, max_width=250),
            icon=icon_obj
        ).add_to(marker_cluster)

# Merender peta tanpa pembungkus div kaku agar langsung mengunci posisi di layar utama kanan
st_folium(m, width="100%", height=450, key="webgis_map", returned_objects=[])

# Merender tabel tabular tepat di bawah peta secara fleksibel
