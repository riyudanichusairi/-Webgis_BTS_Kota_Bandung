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
    .header-left style-span {
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
# 3. FUNGSI LOAD DATA
# ==========================================
def load_geojson(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

batas_kota = load_geojson("batas_kota_bandung.geojson")
data_bts = load_geojson("BTS_kota_bandung.geojson")

# ==========================================
# 4. BINGKAI PETA INTERAKTIF
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

rows_list = []

if data_bts:
    marker_cluster = MarkerCluster(
        options={'maxClusterRadius': 40, 'disableClusteringAtZoom': 14}
    ).add_to(m)
    
    for idx, feature in enumerate(data_bts["features"], start=1):
        geom = feature["geometry"]
        props = feature["properties"]
        
        if geom["type"] == "Point":
            lon, lat = geom["coordinates"]
            
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
            
            def get_prop(keys_list, default="-"):
                for k in keys_list:
                    for actual_key in props.keys():
                        if actual_key.lower().strip() == k.lower().strip():
                            return props[actual_key]
                return default

            rows_list.append({
                "id": get_prop(["id", "objectid", "no"], idx),
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

st_folium(m, width="100%", height=500, returned_objects=[])
st.markdown('</div></div>', unsafe_allow_html=True)

# ==========================================
# 5. TABEL DATA TABULAR (JUDUL SESUAI KEBUTUHAN)
# ==========================================
st.markdown('<div class="table-section-title">📊 DATA MENARA TELEKOMUNIKASI</div>', unsafe_allow_html=True)

if len(rows_list) > 0:
    df = pd.DataFrame(rows_list)
    st.dataframe(
        df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "long": st.column_config.NumberColumn(format="%.6f"),
            "lat": st.column_config.NumberColumn(format="%.6f"),
        }
    )
else:
    st.info("Belum ada data menara yang dapat dimuat ke dalam tabel.")
