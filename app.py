import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import json
import pandas as pd

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="Dashboard WebGIS Menara Kota Bandung",
    page_icon="🗺️",
    layout="wide"
)

# Style UI Minimalis Modern
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #0f172a; color: #f8fafc; }
    [data-testid="stSidebar"] .stSelectbox label { color: #cbd5e1 !important; }
    .main-title { font-family: 'Inter', sans-serif; color: #1e293b; font-size: 26px; font-weight: 700; }
    .sub-title { color: #64748b; font-size: 14px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. MEMUAT DATA DENGAN CACHE AMAN
# ==========================================
@st.cache_data(show_spinner="Memuat data spasial...")
def load_data():
    def read_geojson(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return None

    batas_kota = read_geojson("batas_kota_bandung.geojson")
    data_bts = read_geojson("BTS_kota_bandung.geojson")
    
    rows = []
    if data_bts and "features" in data_bts:
        for idx, feat in enumerate(data_bts["features"], start=1):
            geom = feat.get("geometry", {})
            props = feat.get("properties", {})
            
            if geom and geom.get("type") == "Point":
                coords = geom.get("coordinates", [0, 0])
                
                # Normalisasi pembacaan properti (Case-Insensitive)
                p = {k.lower().strip(): v for k, v in props.items() if v is not None}
                
                rows.append({
                    "id": p.get("id", p.get("objectid", str(idx))),
                    "nama_provinsi": p.get("nama_provinsi", p.get("provinsi", "JAWA BARAT")),
                    "nama_kabupaten_kota": p.get("nama_kabupaten_kota", p.get("kabupaten", "KOTA BANDUNG")),
                    "nama_kecamatan": p.get("nama_kecamatan", p.get("kecamatan", "-")),
                    "nama_desa_kelurahan": p.get("nama_desa_kelurahan", p.get("kelurahan", "-")),
                    "pemilik_menara": p.get("pemilik_menara", p.get("pemilik", p.get("provider", "-"))),
                    "lokasi_menara": p.get("lokasi_menara", p.get("lokasi", p.get("alamat", "-"))),
                    "long": coords[0],
                    "lat": coords[1],
                    "struktur_tower": p.get("struktur_tower", p.get("struktur", p.get("tipe", "-"))),
                    "tinggi_tower": p.get("tinggi_tower", p.get("tinggi", "-")),
                    "satuan": p.get("satuan", "Meter"),
                    "tahun": p.get("tahun", "-")
                })
                
    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["id", "nama_provinsi", "nama_kabupaten_kota", "nama_kecamatan", "nama_desa_kelurahan", "pemilik_menara", "lokasi_menara", "long", "lat", "struktur_tower", "tinggi_tower", "satuan", "tahun"])
    return batas_kota, df

batas_kota, df_all = load_data()

# ==========================================
# 3. PANEL KONTROL (SIDEBAR)
# ==========================================
with st.sidebar:
    st.markdown("<h3 style='color:#f8fafc;'>⚙️ Kontrol Spasial</h3>", unsafe_allow_html=True)
    
    tipe_peta = st.selectbox(
        "Tampilan Peta (Basemap):",
        ["Google Maps Standar", "Google Satellite", "Google Hybrid"]
    )
    
    st.markdown("---")
    
    list_kec = ["Semua Kecamatan"] + sorted([x for x in df_all["nama_kecamatan"].unique() if x != "-"])
    selected_kec = st.selectbox("Kecamatan:", list_kec)
    
    df_filtered = df_all.copy()
    if selected_kec != "Semua Kecamatan":
        df_filtered = df_filtered[df_filtered["nama_kecamatan"] == selected_kec]
        
    list_kel = ["Semua Desa/Kelurahan"] + sorted([x for x in df_filtered["nama_desa_kelurahan"].unique() if x != "-"])
    selected_kel = st.selectbox("Kelurahan:", list_kel)
    if selected_kel != "Semua Desa/Kelurahan":
        df_filtered = df_filtered[df_filtered["nama_desa_kelurahan"] == selected_kel]
        
    list_pemilik = ["Semua Pemilik Menara"] + sorted([x for x in df_filtered["pemilik_menara"].unique() if x != "-"])
    selected_pemilik = st.selectbox("Pemilik:", list_pemilik)
    if selected_pemilik != "Semua Pemilik Menara":
        df_filtered = df_filtered[df_filtered["pemilik_menara"] == selected_pemilik]

# ==========================================
# 4. TAMPILAN DASHBOARD UTAMA
# ==========================================
st.markdown("<div class='main-title'>Geographic Information System Menara BTS</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Data Infrastruktur Telekomunikasi Digital Kota Bandung</div>", unsafe_allow_html=True)

# Indikator Ringkas Statistik
col1, col2, col3 = st.columns(3)
col1.metric("Total Menara Terfilter", f"{len(df_filtered)} Unit")
col2.metric("Jumlah Kecamatan", f"{df_filtered['nama_kecamatan'].nunique()}")
col3.metric("Entitas Provider/Pemilik", f"{df_filtered['pemilik_menara'].nunique()}")

# ==========================================
# 5. PETA GOOGLE MAPS
# ==========================================
st.markdown("### 🗺️ Visualisasi Peta Spasial Terintegrasi")

map_dict = {
    "Google Maps Standar": "http://google.com{x}&y={y}&z={z}",
    "Google Satellite": "http://google.com{x}&y={y}&z={z}",
    "Google Hybrid": "http://google.com{x}&y={y}&z={z}"
}

m = folium.Map(
    location=[-6.9175, 107.6191], 
    zoom_start=12, 
    tiles=map_dict.get(tipe_peta), 
    attr="© Google Maps"
)

if batas_kota:
    folium.GeoJson(
        data=batas_kota,
        style_function=lambda x: {"fillColor": "#3b82f6", "color": "#2563eb", "weight": 2, "fillOpacity": 0.05}
    ).add_to(m)

if not df_filtered.empty:
    cluster = MarkerCluster(options={'maxClusterRadius': 35, 'disableClusteringAtZoom': 14}).add_to(m)
    for _, row in df_filtered.iterrows():
        html = f"""
        <div style='font-family:Arial; font-size:12px; width:220px;'>
            <b>Pemilik:</b> {row['pemilik_menara']}<br>
            <b>Kecamatan:</b> {row['nama_kecamatan']}<br>
            <b>Kelurahan:</b> {row['nama_desa_kelurahan']}<br>
            <b>Struktur:</b> {row['struktur_tower']}<br>
            <b>Tinggi:</b> {row['tinggi_tower']} {row['satuan']}
        </div>
        """
        folium.Marker(
            location=[row['lat'], row['long']],
            popup=folium.Popup(html, max_width=250),
            icon=folium.Icon(color="red", icon="signal", prefix="fa")
        ).add_to(cluster)

st_folium(m, width="100%", height=500, key="map_bts", returned_objects=[])

# ==========================================
# 6. TABEL ATRIBUT DATA TABULAR
# ==========================================
st.markdown("### 📊 Dataset Atribut Menara")
st.dataframe(df_filtered, use_container_width=True, hide_index=True)
