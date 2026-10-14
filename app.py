import streamlit as st
import folium
from folium.plugins import MarkerCluster, MeasureControl
import json
import pandas as pd
import streamlit.components.v1 as components

# ==========================================
# 1. KONFIGURASI HALAMAN & THEME GLOBAL
# ==========================================
st.set_page_config(
    page_title="PORTAL GIS MENARA BANDUNG",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Modern Minimalis - MENYESUAIKAN PERSIS SEPERTI GAMBAR
st.markdown("""
    <style>
    /* Mengubah warna latar belakang seluruh aplikasi dan sidebar */
    .stApp {
        background-color: #ffffff;
    }
    
    [data-testid="stSidebar"] { 
        background-color: #112244 !important; 
        color: #ffffff !important; 
    }
    
    /* Menyesuaikan warna komponen teks inside sidebar */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #ffffff !important;
    }

    /* Styling Banner Header Atas Konten Utama */
    .header-banner {
        background-color: #1a4a9f;
        padding: 15px 30px;
        border-radius: 4px;
        margin-bottom: 25px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .header-title {
        color: white;
        font-family: 'Arial', sans-serif;
        font-size: 26px;
        font-weight: bold;
        letter-spacing: 1px;
    }
    
    /* Metrik Ringkas Khusus di Sidebar */
    .sidebar-metric-container {
        display: flex;
        justify-content: space-between;
        margin-bottom: 20px;
        background-color: rgba(255, 255, 255, 0.05);
        padding: 10px;
        border-radius: 6px;
    }
    .sidebar-metric-box {
        text-align: center;
        flex: 1;
    }
    .sidebar-metric-val {
        font-size: 20px;
        font-weight: 700;
        color: #ffffff;
    }
    .sidebar-metric-lbl {
        font-size: 11px;
        color: #cbd5e1;
    }

    iframe { border: 1px solid #e2e8f0; border-radius: 8px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05); }
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

    batas_kota = read_json("batas_kota_bandung.geojson")
    data_bts = read_json("BTS_kota_bandung.geojson")
    
    raw_rows = []
    if data_bts and "features" in data_bts:
        for idx, feature in enumerate(data_bts["features"], start=1):
            geom = feature.get("geometry", {})
            props = feature.get("properties", {})
            
            if geom and geom.get("type") == "Point":
                lon, lat = geom["coordinates"]
                
                try:
                    lat_val = float(lat)
                    lon_val = float(lon)
                except ValueError:
                    continue

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
                    "id": get_prop(["id", "objectid", "no"], f"TWR-BDG-{idx:03d}"),
                    "nama_provinsi": get_prop(["nama_provinsi", "provinsi", "prov"], "Jawa Barat"),
                    "nama_kabupaten_kota": get_prop(["nama_kabupaten_kota", "kabupaten", "kota"], "Kota Bandung"),
                    "nama_kecamatan": get_prop(["nama_kecamatan", "kecamatan", "kec"], "Gedebage"),
                    "nama_desa_kelurahan": get_prop(["nama_desa_kelurahan", "kelurahan", "desa", "kel"], "Rancabolang"),
                    "pemilik_menara": get_prop(["pemilik_menara", "pemilik", "provider", "operator"], "TOWER BERSAMA GROUP"),
                    "lokasi_menara": get_prop(["lokasi_menara", "lokasi", "alamat"], "JL. GEDEBAGE SELATAN"),
                    "long": lon_val,
                    "lat": lat_val,
                    "struktur_tower": get_prop(["struktur_tower", "struktur", "tipe"], "4 KAKI"),
                    "tinggi_tower": get_prop(["tinggi_tower", "tinggi", "height"], "42"),
                    "satuan": get_prop(["satuan", "unit"], "Meter")  # Perbaikan: Kolom satuan ditambahkan di sini
                })
                
    df = pd.DataFrame(raw_rows) if raw_rows else pd.DataFrame(columns=[
        "id", "nama_provinsi", "nama_kabupaten_kota", "nama_kecamatan", "nama_desa_kelurahan",
        "pemilik_menara", "lokasi_menara", "long", "lat", "struktur_tower", "tinggi_tower", "satuan"
    ])
    return batas_kota, df

batas_kota, df_all = load_and_process_data()

# ==========================================
# 3. CONTROL PANEL (SIDEBAR KIRI)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='font-size:22px; font-weight:700; margin-bottom:2px;'>GIS Menara BTS</h2>", unsafe_allow_html=True)
    st.markdown("<h3 style='font-size:18px; font-weight:500; margin-bottom:20px; color:#cbd5e1 !important;'>Kota Bandung</h3>", unsafe_allow_html=True)
    
    # Grid Informasi Ringkasan Metrik di Sidebar sesuai gambar
    st.markdown(f"""
    <div class='sidebar-metric-container'>
        <div class='sidebar-metric-box'>
            <div class='sidebar-metric-val'>{len(df_all)}</div>
            <div class='sidebar-metric-lbl'>Unit</div>
        </div>
        <div class='sidebar-metric-box'>
            <div class='sidebar-metric-val'>{df_all['nama_kecamatan'].nunique()}</div>
            <div class='sidebar-metric-lbl'>Kec</div>
        </div>
        <div class='sidebar-metric-box'>
            <div class='sidebar-metric-val'>{df_all['pemilik_menara'].nunique()}</div>
            <div class='sidebar-metric-lbl'>Pemilik</div>
        </div>
        <div class='sidebar-metric-box'>
            <div class='sidebar-metric-val'>{df_all['struktur_tower'].nunique()}</div>
            <div class='sidebar-metric-lbl'>Struktur</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<h3 style='font-size:14px; font-weight:600; margin-bottom:10px;'>⚙️ Kontrol Spasial</h3>", unsafe_allow_html=True)
    
    df_filtered = df_all.copy()

    # Filter Wilayah Kecamatan
    list_kec = sorted([x for x in df_filtered["nama_kecamatan"].unique() if x != "-"])
    selected_kec = st.multiselect("Wilayah Kecamatan:", list_kec, placeholder="Pilih atau ketik Kecamatan...")
    if selected_kec:
        df_filtered = df_filtered[df_filtered["nama_kecamatan"].isin(selected_kec)]

    # Filter Wilayah Kelurahan
    list_kel = sorted([x for x in df_filtered["nama_desa_kelurahan"].unique() if x != "-"])
    selected_kel = st.multiselect("Wilayah Kelurahan:", list_kel, placeholder="Pilih atau ketik Kelurahan...")
    if selected_kel:
        df_filtered = df_filtered[df_filtered["nama_desa_kelurahan"].isin(selected_kel)]

    # Filter Penyedia / Pemilik
    list_pemilik = sorted([x for x in df_filtered["pemilik_menara"].unique() if x != "-"])
    selected_pemilik = st.multiselect("Penyedia / Pemilik:", list_pemilik, placeholder="Pilih atau ketik Penyedia...")
    if selected_pemilik:
        df_filtered = df_filtered[df_filtered["pemilik_menara"].isin(selected_pemilik)]

    # Filter Jenis Struktur
    list_struktur = sorted([x for x in df_filtered["struktur_tower"].unique() if x != "-"])
    selected_struktur = st.multiselect("Jenis Struktur:", list_struktur, placeholder="Pilih atau ketik Jenis Struktur...")
    if selected_struktur:
        df_filtered = df_filtered[df_filtered["struktur_tower"].isin(selected_struktur)]

    # Filter ID Menara
    list_id = sorted([x for x in df_filtered["id"].unique() if x != "-"])
    selected_id = st.multiselect("ID Menara:", list_id, placeholder="Pilih atau ketik ID...")
    if selected_id:
        df_filtered = df_filtered[df_filtered["id"].isin(selected_id)]

# Terapkan hasil akhir penyaringan data aktif (.isin)
df_filtered = df_all.copy()
if selected_id: df_filtered = df_filtered[df_filtered["id"].isin(selected_id)]
if selected_kec: df_filtered = df_filtered[df_filtered["nama_kecamatan"].isin(selected_kec)]
if selected_kel: df_filtered = df_filtered[df_filtered["nama_desa_kelurahan"].isin(selected_kel)]
if selected_pemilik: df_filtered = df_filtered[df_filtered["pemilik_menara"].isin(selected_pemilik)]
if selected_struktur: df_filtered = df_filtered[df_filtered["struktur_tower"].isin(selected_struktur)]

# ==========================================
# 4. HEADER BANNER UTAMA (TOP NAV BANNER)
# ==========================================
st.markdown("""
<div class='header-banner'>
    <div class='header-title'>PORTAL GIS MENARA BANDUNG</div>
    <div>
        <img src='https://wikimedia.org' width='45' alt='Logo Bandung'>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 5. PETA INTERAKTIF DIGITAL
# ==========================================
st.markdown("### 🗺️ Visualisasi Peta Persebaran Menara")

LAT_AWAL = -6.9175
LONG_AWAL = 107.6191
ZOOM_AWAL = 12

m = folium.Map(
    location=[LAT_AWAL, LONG_AWAL], 
    zoom_start=ZOOM_AWAL, 
    tiles="openstreetmap",
    control_scale=True
)

# Menambahkan Measure Control ke pojok kanan atas
measure_control = MeasureControl(
    position='topright',
    primary_length_unit='meters',
    secondary_length_unit='kilometers',
    primary_area_unit='sqmeters',
    secondary_area_unit='hectares',
    line_options={'color': '#1d4ed8', 'weight': 5, 'opacity': 0.8}
)
m.add_child(measure_control)

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
        <div style="font-family: Arial, sans-serif; font-size:12px; width:220px;">
            <b>ID:</b> {row['id']}<br>
            <b>Pemilik:</b> {row['pemilik_menara']}<br>
            <b>Lokasi:</b> {row['lokasi_menara']}<br>
            <b>Kecamatan:</b> {row['nama_kecamatan']}<br>
            <b>Struktur:</b> {row['struktur_tower']}<br>
            <b>Tinggi:</b> {row['tinggi_tower']} {row['satuan']}<br>
            <b>Koordinat:</b> ({row['lat']}, {row['long']})
        </div>
        """
        folium.Marker(
            location=[row['lat'], row['long']],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color="blue", icon="tower-broadcast", prefix="fa")
        ).add_to(marker_cluster)

# --- TOMBOL KOTAK RESET TETAP DI TOPLEFT (DI BAWAH TOMBOL ZOOM) ---
id_peta = m.get_name()

custom_button_js = f"""
<script>
document.addEventListener("DOMContentLoaded", function() {{
    var mapObj = window["{id_peta}"] || {id_peta};
    if (mapObj) {{
        var customControl = L.control({{ position: 'topleft' }});
        
        customControl.onAdd = function(map) {{
            var div = L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-custom');
            
            div.innerHTML = '<i class="fa-regular fa-square" style="color: #333333;"></i>';
            
            div.style.backgroundColor = 'white';
            div.style.width = '34px';
            div.style.height = '34px';
            div.style.lineHeight = '34px';
            div.style.textAlign = 'center';
            div.style.cursor = 'pointer';
            div.style.fontSize = '15px';
            div.title = 'Kembali ke Posisi Awal';
            
            div.onclick = function() {{
                mapObj.setView([{LAT_AWAL}, {LONG_AWAL}], {ZOOM_AWAL});
            }};
            return div;
        }};
        
        customControl.addTo(mapObj);
    }}
}});
</script>
"""

# Menyuntikkan skrip JS langsung ke root objek HTML Folium
m.get_root().html.add_child(folium.Element(custom_button_js))

# --- PERBAIKAN UKURAN KONTANER IFRAME (MENGATASI POTONGAN BAWAH) ---
# 1. Menambahkan margin bawah otomatis di dalam dokumen HTML peta agar Leaflet tidak mepet ke bawah
m.get_root().html.add_child(folium.Element("<style>.folium-map { bottom: 20px !important; }</style>"))

html_map = m._repr_html_()

# 2. Meningkatkan tinggi render kontainer komponen menjadi 600 (sebelumnya 550) 
# dan mengizinkan scrolling otomatis jika resolusi layar pengguna menyusut
components.html(html_map, height=600, scrolling=True)

# ==========================================
# 6. TABEL DATA TABULAR
# ==========================================
st.markdown("### 📊 Detail Data Tabular Menara")

if df_filtered.empty:
    st.warning("⚠️ Tidak ada data menara yang sesuai dengan kombinasi filter kontrol spasial saat ini.")
else:
    # 1. Buat duplikat data khusus untuk tabel dan hapus kolom 'long' & 'lat'
    df_tabel = df_filtered.drop(columns=["long", "lat"])
    
    # 2. Tampilkan DataFrame yang sudah bersih dari kolom koordinat
    st.dataframe(df_tabel, use_container_width=True, hide_index=True)
