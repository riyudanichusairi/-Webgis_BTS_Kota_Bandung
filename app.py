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
    [data-testid="stSidebar"] { background-color: #0f172a; color: #f8fafc; }
    [data-testid="stSidebar"] .stSelectbox label { color: #cbd5e1 !important; font-weight: 500; }
    .main-title { font-family: 'Inter', sans-serif; color: #1e293b; font-size: 28px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 2px; }
    .sub-title { color: #64748b; font-size: 14px; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. CACHING DATA (MEMBUAT APLIKASI RINGAN)
# ==========================================
@st.cache_data(show_spinner="Memuat data spasial...")
def load_and_process_data():
    def read_json(path):
        try:
            with open(path, "r", encoding="utf-8") as f: return json.load(f)
        except Exception: return None

    # Integrasi berkas sesuai dengan repositori GitHub Anda
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
                                if val is None: return default
                                if isinstance(val, float) and val.is_integer(): return str(int(val))
                                return str(val).strip()
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
                    "tahun": get_prop(["tahun", "tahun_berdiri", "thn"]),
                    "status_izin": get_prop(["status_izin", "status", "izin", "legalitas"], "-"),
                    "no_izin": get_prop(["no_izin", "nomor_sk", "imb", "pbg"], "-")
                })
                
    df = pd.DataFrame(raw_rows) if raw_rows else pd.DataFrame(columns=[
        "id", "nama_provinsi", "nama_kabupaten_kota", "nama_kecamatan", "nama_desa_kelurahan",
        "pemilik_menara", "lokasi_menara", "long", "lat", "struktur_tower", "tinggi_tower", 
        "satuan", "tahun", "status_izin", "no_izin"
    ])
    return batas_kota, df

batas_kota, df_all = load_and_process_data()

# ==========================================
# 3. CONTROL PANEL (SIDEBAR FILTER)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color:#f8fafc; font-size:20px; font-weight:600; margin-bottom:20px;'>⚙️ Kontrol Spasial</h2>", unsafe_allow_html=True)
    
    # Filter 1: Kecamatan
    list_kec = ["Semua Kecamatan"] + sorted([x for x in df_all["nama_kecamatan"].unique() if x != "-"])
    selected_kec = st.selectbox("Wilayah Kecamatan:", list_kec)
    
    # Filter 2: Kelurahan (Hierarkis bersandar pada Kecamatan terpilih)
    if selected_kec != "Semua Kecamatan":
        df_kec_filtered = df_all[df_all["nama_kecamatan"] == selected_kec]
        list_kel = ["Semua Desa/Kelurahan"] + sorted([x for x in df_kec_filtered["nama_desa_kelurahan"].unique() if x != "-"])
    else:
        list_kel = ["Semua Desa/Kelurahan"] + sorted([x for x in df_all["nama_desa_kelurahan"].unique() if x != "-"])
    selected_kel = st.selectbox("Wilayah Kelurahan:", list_kel)
    
    # Filter 3: Pemilik Menara
    list_pemilik = ["Semua Pemilik Menara"] + sorted([x for x in df_all["pemilik_menara"].unique() if x != "-"])
    selected_pemilik = st.selectbox("Provider / Pemilik:", list_pemilik)
    
    # Filter 4: Jenis Struktur
    list_struktur = ["Semua Struktur Tower"] + sorted([x for x in df_all["struktur_tower"].unique() if x != "-"])
    selected_struktur = st.selectbox("Jenis Struktur:", list_struktur)
    
    st.markdown("---")
    st.markdown("<div style='font-size:11px; color:#94a3b8;'>Diskominfo Kota Bandung<br>v1.2.8 (Indentation Fixed)</div>", unsafe_allow_html=True)

# ==========================================
# PROSES PENJARINGAN DATA AKTIF
# ==========================================
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
# 4. KONTEN UTAMA & HEADER DASHBOARD
# ==========================================
st.markdown("<div class='main-title'>Geographic Information System Menara BTS</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Data Pemetaan Infrastruktur Telekomunikasi Digital Kota Bandung</div>", unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("Total Menara Terfilter", f"{len(df_filtered)} Unit")
with m2: st.metric("Cakupan Kecamatan", f"{df_filtered['nama_kecamatan'].nunique()}")
with m3: st.metric("Entitas Pemilik", f"{df_filtered['pemilik_menara'].nunique()}")
with m4: st.metric("Variasi Struktur", f"{df_filtered['struktur_tower'].nunique()}")

# ==========================================
# 5. PETA INTERAKTIF DIGITAL (Menggunakan Isolasi Kontainer)
# ==========================================
st.markdown("### 🗺️ Visualisasi Peta Spasial Terintegrasi")

# Wadah Peta terisolasi agar render Peta tidak mengganggu komponen di bawahnya
map_container = st.container()
with map_container:
    m = folium.Map(location=[-6.9175, 107.6191], zoom_start=12, tiles="openstreetmap")

    if batas_kota:
        folium.GeoJson(
            data=batas_kota, 
            name="Batas Administrasi", 
            style_function=lambda feature: {"fillColor": "#3b82f6", "color": "#2563eb", "weight": 1.5, "fillOpacity": 0.04}
        ).add_to(m)

    if not df_filtered.empty:
        marker_cluster = MarkerCluster(options={'maxClusterRadius': 35, 'disableClusteringAtZoom': 14}).add_to(m)
        for _, row in df_filtered.iterrows():
            popup_html = f"""
            <div style='font-family: "Segoe UI", Arial; font-size:12px; width:250px; color:#334155;'>
                <h4 style='margin:0 0 6px 0; color:#1e3a8a; font-size:13px;'>Detail Menara BTS</h4>
                <table style='width:100%; border-collapse: collapse; line-height: 1.5;'>
                    <tr><td style='vertical-align: top; width:90px;'><b>Pemilik</b></td><td>: {row['pemilik_menara']}</td></tr>
                    <tr><td style='vertical-align: top;'><b>Lokasi</b></td><td>: {row['lokasi_menara']}</td></tr>
                    <tr><td style='vertical-align: top;'><b>Kecamatan</b></td><td>: {row['nama_kecamatan']}</td></tr>
                    <tr><td style='vertical-align: top;'><b>Kelurahan</b></td><td>: {row['nama_desa_kelurahan']}</td></tr>
                    <tr><td style='vertical-align: top;'><b>Struktur</b></td><td>: {row['struktur_tower']}</td></tr>
                    <tr><td style='vertical-align: top;'><b>Dimensi</b></td><td>: {row['tinggi_tower']} {row['satuan']}</td></tr>
                    <tr><td style='vertical-align: top;'><b>Tahun</b></td><td>: {row['tahun']}</td></tr>
                    <tr><td style='vertical-align: top;'><b>Status Izin</b></td><td>: {row['status_izin']}</td></tr>
                    <tr><td style='vertical-align: top;'><b>No. Izin</b></td><td>: {row['no_izin']}</td></tr>
                </table>
            </div>
            """
            folium.Marker(
                location=[row['lat'], row['long']], 
                popup=folium.Popup(popup_html, max_width=280), 
                icon=folium.Icon(color="blue", icon="tower-broadcast", prefix="fa")
            ).add_to(marker_cluster)

    # Key dinamis pada st_folium untuk mencegah pembekuan render komponen lain
    st_folium(m, width="100%", height=520, key=f"webgis_map_len_{len(df_filtered)}", returned_objects=[])

# ==========================================
# 6. TABEL DATA TABULAR (Sinkron & Dijamin Muncul)
# ==========================================
st.markdown("### 📊 Detail Data Tabular Menara Terfilter")

if not df_filtered.empty:
    # Memilih dan mengurutkan kolom agar informasi utama lebih mudah dibaca pembaca
    df_display = df_filtered[[
        "id", "pemilik_menara", "struktur_tower", "tinggi_tower", "satuan",
        "nama_kecamatan", "nama_desa_kelurahan", "lokasi_menara", 
        "tahun", "status_izin", "no_izin", "long", "lat"
    ]].copy()
    
    # Mengubah nama kolom display menjadi representatif dan bersih
    df_display.columns = [
        "ID", "Pemilik / Provider", "Jenis Struktur", "Tinggi", "Satuan",
        "Kecamatan", "Kelurahan", "Alamat Lokasi", 
        "Tahun Berdiri"
    ]
    
    # Menampilkan tabel interaktif yang mendukung sorting, pencarian, dan resize kolom
    st.dataframe(
        df_display, 
        use_container_width=True, 
        hide_index=True
    )
else:
    st.warning("⚠️ Tidak ada data menara yang sesuai dengan kombinasi filter kontrol spasial saat ini.")
