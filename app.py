import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import json

# 1. Pengaturan Konfigurasi Tampilan Halaman Streamlit (Tema Modern)
st.set_page_config(
    page_title="WebGIS Infrastruktur BTS Kota Bandung",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Kustomisasi CSS untuk mempercantik UI Streamlit agar terlihat seperti Dasbor Profesional
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stSidebarUserContent"] { background-color: #ffffff; padding: 20px; }
    h1 { color: #1e293b; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 700; }
    .stCheckbox { font-size: 16px !important; font-weight: 500; color: #475569; }
    </style>
    """, unsafe_allow_html=True)

# 2. Judul Utama Aplikasi & Deskrpsi Dashbor
st.title("📊 Dasbor Spasial Menara BTS Kota Bandung")
st.markdown("Analisis sebaran infrastruktur telekomunikasi dan batas wilayah administrasi Kota Bandung secara *real-time*.")
st.markdown("---")

# 3. Fungsi Membaca File GeoJSON dengan Pembersihan String Aman
def load_geojson(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Gagal memuat file {file_path}: {e}")
        return None

# Memuat data
batas_kota = load_geojson("batas_kota_bandung.geojson")
data_bts = load_geojson("BTS_kota_bandung.geojson")

# 4. Panel Samping (Sidebar Layout Modern)
st.sidebar.markdown("### 🛠️ KONTROL PETA")
st.sidebar.markdown("Sesuaikan lapisan data dan tema peta di bawah ini:")

# Pilihan Basemap Modern
basemap_style = st.sidebar.selectbox(
    "Pilih Gaya Peta (Basemap):",
    ["CartoDB Positron (Terang Minimalis)", "CartoDB Dark Matter (Tema Gelap)", "OpenStreetMap Standard"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📂 LAPISAN DATA")
show_batas = st.sidebar.checkbox("Tampilkan Batas Wilayah Kota", value=True)
show_bts = st.sidebar.checkbox("Aktifkan Klaster Menara BTS", value=True)

# Menghitung statistik cepat jika data tersedia
st.sidebar.markdown("---")
st.sidebar.markdown("### 📈 STATISTIK SINGKAT")
if data_bts and "features" in data_bts:
    total_bts = len(data_bts["features"])
    st.sidebar.metric(label="Total Menara Terdata", value=f"{total_bts} Unit")

# 5. Penentuan Peta Dasar (Basemap Mapping)
tiles_map = {
    "CartoDB Positron (Terang Minimalis)": "CartoDB Positron",
    "CartoDB Dark Matter (Tema Gelap)": "CartoDB Dark Matter",
    "OpenStreetMap Standard": "OpenStreetMap"
}
selected_tiles = tiles_map[basemap_style]

# Inisialisasi Peta Dasar Folium
m = folium.Map(location=[-6.9175, 107.6191], zoom_start=12, tiles=selected_tiles)

# --- LAPISAN 1: Batas Wilayah Poligon (Moderenisasi Gaya) ---
if show_batas and batas_kota:
    # Memilih warna garis batas luar agar kontras dengan tipe peta dasar yang dipilih
    line_color = "#1e293b" if "Dark" not in selected_tiles else "#38bdf8"
    
    folium.GeoJson(
        data=batas_kota,
        name="Batas Kota Bandung",
        style_function=lambda feature: {
            "fillColor": "#3b82f6",  # Warna biru modern
            "color": line_color,     # Kontras dinamis
            "weight": 2.5,           # Garis batas lebih tajam
            "fillOpacity": 0.1,      # Transparansi tipis agar peta dasar tetap terlihat jernih
        },
        tooltip=folium.GeoJsonTooltip(
            fields=list(batas_kota['features'][0]['properties'].keys())[:2] if 'features' in batas_kota and len(batas_kota['features']) > 0 else [],
            aliases=["Wilayah:", "Kode:"],
            localize=True,
            sticky=True
        )
    ).add_to(m)

# --- LAPISAN 2: Titik Menara BTS menggunakan Fitur Klasterisasi ---
if show_bts and data_bts:
    # Menginisialisasi plugin cluster agar ribuan ikon merah menyatu saat peta di-zoom out
    marker_cluster = MarkerCluster(
        name="Klaster Menara BTS",
        options={
            'maxClusterRadius': 50,  # Jarak piksel pengelompokan ikon
            'disableClusteringAtZoom': 15  # Di tingkat zoom ini, klaster akan otomatis pecah menjadi titik asli
        }
    ).add_to(m)

    for feature in data_bts["features"]:
        geom = feature["geometry"]
        props = feature["properties"]
        
        if geom["type"] == "Point":
            lon, lat = geom["coordinates"]
            
            # Membuat desain tabel Popup informasi yang rapi, bersih, dan estetik
            popup_html = """
            <div style='font-family: Arial, sans-serif; width: 220px; font-size: 12px; color: #334155;'>
                <h5 style='margin: 0 0 8px 0; color: #0f172a; border-bottom: 2px solid #3b82f6; padding-bottom: 4px;'>📍 Detail Menara</h5>
                <table style='width: 100%; border-collapse: collapse;'>
            """
            for key, val in props.items():
                # Membatasi penampilan data agar isi popup tidak terlalu panjang kebawah
                if val and str(val).strip():
                    popup_html += f"<tr style='border-bottom: 1px solid #f1f5f9;'><td style='padding: 4px 0; font-weight: bold; width: 40%;'>{key}</td><td style='padding: 4px 0;'>{val}</td></tr>"
            popup_html += "</table></div>"
            
            # Menempelkan titik penanda ke dalam objek klaster (buku langsung ke peta m)
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=250),
                icon=folium.Icon(color="blue", icon="broadcast-tower", prefix="fa") # Ikon tipe tower modern
            ).add_to(marker_cluster)

# 6. Tampilkan ke Layar Dasbor Utama dengan Ukuran Proporsional
st_folium(m, width="100%", height=650, returned_objects=[])
