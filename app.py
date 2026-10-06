import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import json
import pandas as pd

# ==========================================
# 1. KONFIGURASI HALAMAN & STYLE CSS
# ==========================================
st.set_page_config(
    page_title="Aplikasi GIS Menara Telekomunikasi",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #ffffff;
        padding: 15px 30px;
        border-bottom: 2px solid #e5e7eb;
        margin-bottom: 20px;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .header-left h1 {
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 24px;
        font-weight: 700;
        color: #334155;
        margin: 0;
    }
    .header-right {
        font-family: Arial, sans-serif;
        font-size: 11px;
        color: #64748b;
        text-align: right;
        line-height: 1.4;
    }
    
    .map-card {
        background-color: #ffffff;
        border-radius: 4px;
        border: 1px solid #cbd5e1;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }
    .map-card-header {
        background-color: #1e3a8a;
        color: #ffffff;
        padding: 10px 15px;
        font-weight: bold;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-top-left-radius: 3px;
        border-top-right-radius: 3px;
    }
    .map-card-body {
        padding: 0px;
    }
    
    .filter-card {
        background-color: #ffffff;
        padding: 15px;
        border: 1px solid #cbd5e1;
        border-radius: 4px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .table-section-title {
        background-color: #ffffff;
        padding: 12px 15px;
        font-weight: bold;
        font-size: 14px;
        color: #1e293b;
        border: 1px solid #cbd5e1;
        border-bottom: none;
        text-transform: uppercase;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        margin-top: 25px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. KOMPONEN HEADER ATAS
# ==========================================
st.markdown("""
    <div class="header-container">
        <div class="header-left">
            <h1>Aplikasi GIS <span style="font-size:14px; font-weight:normal; color:#64748b;">(Geographic Information System)</span></h1>
            <div style="font-size: 18px; font-weight: 600; color: #1e3a8a; margin-top:2px;">Menara Telekomunikasi Kota Bandung <span style="font-size:12px; font-weight:normal; color:#64748b;">(Ver. 1.0)</span></div>
        </div>
        <div class="header-right">
            🏛️ Dinas Komunikasi dan Informatika Kota Bandung<br>
            🏢 Balai Kota, Jl. Wastukencana No. 2, Telp./Fax. (022) 4232338
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 3. FUNGSI LOAD DATA & PRE-PROCESSING
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
# 4. PANEL FILTER DATA
# ==========================================
st.markdown('<div class="table-section-title">🔍 FILTER DATA MENARA</div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        list_kec = ["Semua Kecamatan"] + sorted([x for x in df_all["nama_kecamatan"].unique() if x != "-"])
        selected_kec = st.selectbox("Nama Kecamatan:", list_kec)
        
    with col2:
        if selected_kec != "Semua Kecamatan":
            df_filtered_kec = df_all[df_all["nama_kecamatan"] == selected_kec]
            list_kel = ["Semua Desa/Kelurahan"] + sorted([x for x in df_filtered_kec["nama_desa_kelurahan"].unique() if x != "-"])
        else:
            list_kel = ["Semua Desa/Kelurahan"] + sorted([x for x in df_all["nama_desa_kelurahan"].unique() if x != "-"])
        selected_kel = st.selectbox("Nama Desa/Kelurahan:", list_kel)
        
    with col3:
        list_pemilik = ["Semua Pemilik Menara"] + sorted([x for x in df_all["pemilik_menara"].unique() if x != "-"])
        selected_pemilik = st.selectbox("Pemilik Menara:", list_pemilik)
        
    with col4:
        list_struktur = ["Semua Struktur Tower"] + sorted([x for x in df_all["struktur_tower"].unique() if x != "-"])
        selected_struktur = st.selectbox("Struktur Tower:", list_struktur)
        
    st.markdown('</div>', unsafe_allow_html=True)

# Eksekusi Operasi Penjaringan Data
df_filtered = df_all.copy()
if selected_kec != "Semua Kecamatan":
    df_filtered = df_filtered[df_filtered["nama_kecamatan"] == selected_kec]
if selected_kel != "Semua Desa/Kelurahan":
    df_filtered = df_filtered[df_filtered["nama_desa_kelurahan"] == selected_kel]
if selected_pemilik != "Semua Pemilik Menara":
    df_filtered = df_filtered[df_filtered["pemilik_menara"] == selected_pemilik]
if selected_struktur != "Semua Struktur Tower":
    df_filtered = df_filtered[df_filtered["struktur_tower"] == selected_struktur]


# ==========================================
# 5. PANEL PETA INTERAKTIF 
# ==========================================
st.markdown('<div class="map-card"><div class="map-card-header">🌐 PETA MENARA TELEKOMUNIKASI</div><div class="map-card-body">', unsafe_allow_html=True)

m = folium.Map(location=[-6.9175, 107.6191], zoom_start=12, tiles="OpenStreetMap")

if batas_kota:
    folium.GeoJson(
        data=batas_kota,
        style_function=lambda feature: {
            "fillColor": "#22c55e",
            "color": "#16a34a",
            "weight": 2,
            "fillOpacity": 0.08,
        }
    ).add_to(m)

if not df_filtered.empty:
    marker_cluster = MarkerCluster(
        options={'maxClusterRadius': 40, 'disableClusteringAtZoom': 14}
    ).add_to(m)
    
    for _, row in df_filtered.iterrows():
        popup_html = f"""
        <div style='font-family:Arial; font-size:12px; width:220px;'>
            <b>Detail Menara BTS</b><hr style='margin:4px 0;'>
            <b>Pemilik:</b> {row['pemilik_menara']}<br>
            <b>Kecamatan:</b> {row['nama_kecamatan']}<br>
            <b>Kelurahan:</b> {row['nama_desa_kelurahan']}<br>
            <b>Struktur:</b> {row['struktur_tower']}<br>
            <b>Tinggi:</b> {row['tinggi_tower']} {row['satuan']}<br>
            <b>Tahun:</b> {row['tahun']}<br>
            <hr style='margin:4px 0;'>
            <b>Lat:</b> {row['lat']}<br><b>Long:</b> {row['long']}
        </div>
        """
        folium.Marker(
            location=[row['lat'], row['long']],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color="red", icon="signal", prefix="fa")
        ).add_to(marker_cluster)

st_folium(m, width="100%", height=480, key="webgis_map", returned_objects=[])
st.markdown('</div></div>', unsafe_allow_html=True)


# ==========================================
# 6. PANEL TABEL DATA TABULAR 
# ==========================================
st.markdown('<div class="table-section-title">📊 DATA MENARA TELEKOMUNIKASI</div>', unsafe_allow_html=True)

with st.container():
    if not df_filtered.empty:
        # Merender tabel secara langsung dan bersih untuk menghindari potensi syntax error pada format angka koordinat
        st.dataframe(df_filtered, use_container_width=True, hide_index=True)
    else:
