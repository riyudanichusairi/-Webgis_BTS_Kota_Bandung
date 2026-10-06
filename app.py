import streamlit as st
import folium
from streamlit_folium import st_folium
import json

# 1. Pengaturan Konfigurasi Tampilan Halaman Streamlit
st.set_page_config(
    page_title="WebGIS Menara BTS Kota Bandung",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Judul Utama Aplikasi
st.title("🗺️ WebGIS Menara BTS Kota Bandung")
st.markdown("Aplikasi Geo-Informasi interaktif untuk memetakan sebaran menara BTS di wilayah administrasi Kota Bandung.")

# 3. Fungsi untuk Membaca File GeoJSON dengan Aman
def load_geojson(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"⚠️ File tidak ditemukan: `{file_path}`. Pastikan nama file di GitHub sudah benar.")
        return None
    except Exception as e:
        st.error(f"Error saat membaca file {file_path}: {e}")
        return None

# Memuat data spasial dari repositori
batas_kota = load_geojson("batas_kota_bandung.geojson")
data_bts = load_geojson("BTS_kota_bandung.geojson")

# 4. Membuat Menu Kontrol di Sidebar (Panel Samping)
st.sidebar.header("⚙️ Kontrol Lapisan Peta")
st.sidebar.markdown("Pilih lapisan data yang ingin ditampilkan pada peta:")

# Checkbox kontrol layer
show_batas = st.sidebar.checkbox("Tampilkan Batas Kota Bandung", value=True)
show_bts = st.sidebar.checkbox("Tampilkan Titik Menara BTS", value=True)

# Informasi Tambahan di Sidebar
st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Tips:** Klik pada titik ikon menara BTS untuk melihat detail properti/informasi spesifik menara tersebut."
)

# 5. Inisialisasi Peta Folium (Pusat Koordinat di Kota Bandung)
# Koordinat tengah Kota Bandung berkisar di lintang -6.9175 dan bujur 107.6191
m = folium.Map(location=[-6.9175, 107.6191], zoom_start=12, tiles="OpenStreetMap")

# --- LAYER 1: Batas Kota Bandung (Poligon) ---
if show_batas and batas_kota:
    folium.GeoJson(
        data=batas_kota,
        name="Batas Kota Bandung",
        style_function=lambda feature: {
            "fillColor": "#3186cc",  # Warna isian poligon
            "color": "#000000",      # Warna garis tepi poligon (Hitam)
            "weight": 2,             # Ketebalan garis tepi
            "fillOpacity": 0.2,      # Transparansi isian
        },
        tooltip=folium.GeoJsonTooltip(
            fields=list(batas_kota['features'][0]['properties'].keys())[:2], # Mengambil properti nama wilayah otomatis
            aliases=["Properti 1:", "Properti 2:"],
            localize=True
        )
    ).add_to(m)

# --- LAYER 2: Titik Menara BTS (Point) ---
if show_bts and data_bts:
    # Menggunakan metode perulangan (looping) agar penanda (marker) bisa disesuaikan ikon dan popup-nya
    for feature in data_bts["features"]:
        geom = feature["geometry"]
        props = feature["properties"]
        
        # Validasi tipe geometri titik
        if geom["type"] == "Point":
            lon, lat = geom["coordinates"]
            
            # Menyusun teks informasi Popup dari seluruh properti yang ada di data atribut GeoJSON Anda
            popup_html = "<h4>Informasi Menara BTS</h4><table border='1' style='border-collapse: collapse; width:100%;'>"
            for key, val in props.items():
                popup_html += f"<tr><td style='padding:5px; font-weight:bold;'>{key}</td><td style='padding:5px;'>{val}</td></tr>"
            popup_html += "</table>"
            
            # Membuat komponen popup berbasis HTML kustom
            popup_obj = folium.Popup(popup_html, max_width=300)
            
            # Menambahkan penanda titik ke peta dasar
            folium.Marker(
                location=[lat, lon], # Aturan urutan koordinat Folium: [Latitude, Longitude]
                popup=popup_obj,
                icon=folium.Icon(color="red", icon="signal", prefix="fa") # Menggunakan ikon sinyal menara merah
            ).add_to(m)

# 6. Menampilkan Peta Interaktif di Area Utama Streamlit
st_folium(m, width="100%", height=600, returned_objects=[])
