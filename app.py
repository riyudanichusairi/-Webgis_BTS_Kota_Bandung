import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import json
import pandas as pd

# 1. Konfigurasi Tampilan Halaman Streamlit (Mode Penuh / Tanpa Sidebar untuk layout ini)
st.set_page_config(
    page_title="Aplikasi GIS Menara Telekomunikasi",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Kustomisasi Gaya CSS agar Persis seperti Aplikasi Pemerintah pada Gambar
st.markdown("""
    <style>
    /* Mengatur latar belakang aplikasi abu-abu terang */
    .main { background-color: #f4f6f9; }
    
    /* Header Utama */
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
    .header-left span {
        font-size: 14px;
        color: #94a3b8;
    }
    .header-right {
        font-family: Arial, sans-serif;
        font-size: 11px;
        color: #64748b;
        text-align: right;
        line-height: 1.4;
    }
    
    /* Panel Kotak Peta (Biru) */
    .map-card {
        background-color: #ffffff;
        border-radius: 4px;
        border: 1px solid #cbd5e1;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }
    .map-card-header {
        background-color: #1e3a8a; /* Biru Donker khas Instansi */
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
    
    /* Panel Judul Tabel */
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
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Struktur Komponen Top Header (Instansi)
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

# 4. Membaca Data GeoJSON
def load_geojson(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

batas_kota = load_geojson("batas_kota_bandung.geojson")
data_bts = load_geojson("BTS_kota_bandung.geojson")

# 5. PEMBUATAN PANEL PETA KOTAK BIRU
st.markdown('<div class="map-card"><div class="map-card-header">🌐 PETA MENARA TELEKOMUNIKASI</div><div class="map-card-body">', unsafe_allow_html=True)

# Inisialisasi Peta Folium standar Google Maps (OpenStreetMap)
m = folium.Map(location=[-6.9175, 107.6191], zoom_start=12, tiles="OpenStreetMap")

# Plot Batas Wilayah Poligon
if batas_kota:
    folium.GeoJson(
        data=batas_kota,
        style_function=lambda feature: {
            "fillColor": "#22c55e",  # Hijau transparan lembut
            "color": "#16a34a",      # Garis tepi hijau
            "weight": 2,
            "fillOpacity": 0.08,
        }
    ).add_to(m)

# Plot Titik Menara dengan Fitur Klaster (Mengikuti permintaan modernisasi sebelumnya agar tetap rapi)
if data_bts:
    marker_cluster = MarkerCluster(
        options={'maxClusterRadius': 40, 'disableClusteringAtZoom': 14}
    ).add_to(m)

    # List wadah menampung data tabular untuk tabel di bawah
    rows_list = []
    
    for idx, feature in enumerate(data_bts["features"], start=1):
        geom = feature["geometry"]
        props = feature["properties"]
        
        if geom["type"] == "Point":
            lon, lat = geom["coordinates"]
            
            # Pengkondisian agar popup rapi saat diklik
            popup_html = "<div style='font-family:Arial; font-size:12px; width:200px;'>"
            popup_html += "<b>Detail Menara BTS</b><hr style='margin:4px 0;'>"
            for k, v in props.items():
                if v: popup_html += f"<b>{k}:</b> {v}<br>"
            popup_html += f"<b>Latitude:</b> {lat}<br><b>Longitude:</b> {lon}</div>"
            
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=250),
                icon=folium.Icon(color="red", icon="signal", prefix="fa")
            ).add_to(marker_cluster)
            
            # Masukkan data ke array tabel (Disesuaikan struktur kolom seperti gambar user)
            rows_list.append({
                "NO": idx,
                "SITE NAME": props.get("SITE_NAME", props.get("Nama", props.get("name", "Menara BTS"))),
                "ALAMAT": props.get("ALAMAT", props.get("Alamat", "-")),
                "DESA/KELURAHAN/KECAMATAN": props.get("KECAMATAN", props.get("Kecamatan", "-")),
                "TAHUN BERDIRI": props.get("TAHUN", props.get("Tahun", "-")),
                "TINGGI": props.get("TINGGI", props.get("Tinggi", "-")),
                "LATITUDE": lat,
                "LONGITUDE": lon,
                "STATUS": props.get("STATUS", props.get("Status", "Existing"))
            })

# Merender Peta di dalam bingkai Card HTML
st_folium(m, width="100%", height=500, returned_objects=[])
st.markdown('</div></div>', unsafe_allow_html=True)


# 6. PEMBUATAN PANEL TABEL DATA (DATA MENARA TELEKOMUNIKASI)
st.markdown('<div class="table-section-title">📊 DATA MENARA TELEKOMUNIKASI</div>', unsafe_allow_html=True)

if data_bts and len(rows_list) > 0:
    # Mengubah array data menjadi Dataframe Pandas
    df = pd.DataFrame(rows_list)
    
    # Menampilkan tabel interaktif bawaan Streamlit yang sudah mendukung fungsi Cari (Search) dan Sorting kolom
    st.dataframe(
        df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "NO": st.column_config.NumberColumn(width="small"),
            "LATITUDE": st.column_config.NumberColumn(format="%.6f"),
            "LONGITUDE": st.column_config.NumberColumn(format="%.6f"),
        }
    )
else:
    st.info("Belum ada data menara yang dapat dimuat ke dalam tabel.")
