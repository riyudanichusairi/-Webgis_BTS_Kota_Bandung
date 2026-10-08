import streamlit as st
import folium
from folium.plugins import MarkerCluster, MeasureControl
import json
import pandas as pd
# Menggunakan st_folium atau komponen html yang dibungkus dengan benar
import streamlit.components.v1 as components

# ==========================================
# 1. KONFIGURASI HALAMAN & THEME GLOBAL
# ==========================================
st.set_page_config(
    page_title="Dashboard WebGIS Menara Kota Bandung",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 1. KONFIGURASI HALAMAN & THEME GLOBAL
# ==========================================
st.set_page_config(
    page_title="Dashboard WebGIS Menara Kota Bandung",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Modern Minimalis - WARNA LATAR SIDEBAR DIUBAH MENJADI BIRU MUDA
st.markdown("""
    <style>
    /* Mengubah latar belakang sidebar menjadi biru muda cerah (#a0c4ff) */
    /* Serta mengubah warna tulisan utama menjadi abu gelap/hitam (#1e293b) agar terbaca */
    [data-testid="stSidebar"] { 
        background-color: #a0c4ff; 
        color: #1e293b; 
    }
    
    /* Menyesuaikan warna judul header cth: Kontrol Spasial */
    [data-testid="stSidebar"] h2 {
        color: #1e293b !important;
    }
    
    /* Menyesuaikan warna label teks multiselect/selectbox di atas kolom input */
    [data-testid="stSidebar"] .stSelectbox label, 
    [data-testid="stSidebar"] .stMultiSelect label { 
        color: #0f172a !important; 
        font-weight: 600; 
    }
    
    /* Menyesuaikan teks info/footer di bagian paling bawah sidebar agar tidak samar */
    [data-testid="stSidebar"] div[style*="font-size:11px"] {
        color: #334155 !important;
        font-weight: 500;
    }
    
    .main-title { font-family: 'Inter', sans-serif; color: #1e293b; font-size: 28px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 2px; }
    .sub-title { color: #64748b; font-size: 14px; margin-bottom: 25px; }
    iframe { border: none; border-radius: 8px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
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
                    "id": get_prop(["id", "objectid", "no"], str(idx)),
                    "nama_provinsi": get_prop(["nama_provinsi", "provinsi", "prov"], "JAWA BARAT"),
                    "nama_kabupaten_kota": get_prop(["nama_kabupaten_kota", "kabupaten", "kota"], "KOTA BANDUNG"),
                    "nama_kecamatan": get_prop(["nama_kecamatan", "kecamatan", "kec"]),
                    "nama_desa_kelurahan": get_prop(["nama_desa_kelurahan", "kelurahan", "desa", "kel"]),
                    "pemilik_menara": get_prop(["pemilik_menara", "pemilik", "provider", "operator", "site_name", "nama"]),
                    "lokasi_menara": get_prop(["lokasi_menara", "lokasi", "alamat"]),
                    "long": lon_val,
                    "lat": lat_val,
                    "struktur_tower": get_prop(["struktur_tower", "struktur", "tipe", "type"]),
                    "tinggi_tower": get_prop(["tinggi_tower", "tinggi", "height"]),
                    "satuan": get_prop(["satuan", "unit"], "Meter"),
                    "tahun": get_prop(["tahun", "tahun_berdiri", "thn"])
                })
                
    df = pd.DataFrame(raw_rows) if raw_rows else pd.DataFrame(columns=[
        "id", "nama_provinsi", "nama_kabupaten_kota", "nama_kecamatan", "nama_desa_kelurahan",
        "pemilik_menara", "lokasi_menara", "long", "lat", "struktur_tower", "tinggi_tower", 
        "satuan", "tahun", "status_izin", "no_izin"
    ])
    return batas_kota, df

batas_kota, df_all = load_and_process_data()

# ==========================================
# 3. CONTROL PANEL (SIDEBAR FILTER MULTISELECT)
# ==========================================
with st.sidebar:
    # 📌 LOGO BARU (Besar & Rapi menyesuaikan lebar sidebar)
    # Catatan: Ganti "logo_diskominfo.png" dengan file gambar lokal atau link URL gambar online Anda
    st.image("logo_diskominfo.png", use_container_width=True)
    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True) # Spacer pemisah rapi
    
    st.markdown("<h2 style='color:#f8fafc; font-size:15px; font-weight:450; margin-bottom:15px;'>⚙️ Kontrol Spasial</h2>", unsafe_allow_html=True)
    
    list_id = sorted([x for x in df_all["id"].unique() if x != "-"], key=lambda x: int(x) if x.isdigit() else x)
    selected_id = st.multiselect("ID Menara:", list_id, placeholder="Pilih atau ketik ID...")
    
    list_kec = sorted([x for x in df_all["nama_kecamatan"].unique() if x != "-"])
    selected_kec = st.multiselect("Wilayah Kecamatan:", list_kec, placeholder="Pilih atau ketik Kecamatan...")
    
    if selected_kec:
        df_kec_filtered = df_all[df_all["nama_kecamatan"].isin(selected_kec)]
        list_kel = sorted([x for x in df_kec_filtered["nama_desa_kelurahan"].unique() if x != "-"])
    else:
        list_kel = sorted([x for x in df_all["nama_desa_kelurahan"].unique() if x != "-"])
    selected_kel = st.multiselect("Wilayah Kelurahan:", list_kel, placeholder="Pilih atau ketik Kelurahan...")
    
    list_pemilik = sorted([x for x in df_all["pemilik_menara"].unique() if x != "-"])
    selected_pemilik = st.multiselect("Provider / Pemilik:", list_pemilik, placeholder="Pilih atau ketik Provider...")
    
    list_struktur = sorted([x for x in df_all["struktur_tower"].unique() if x != "-"])
    selected_struktur = st.multiselect("Jenis Struktur:", list_struktur, placeholder="Pilih atau ketik Jenis Struktur...")
    
    st.markdown("---")
    st.markdown("<div style='font-size:11px; color:#94a3b8;'>Diskominfo Kota Bandung<br>v1.5.1 (Map Render Fixed)</div>", unsafe_allow_html=True)

# ==========================================
# PROSES PENJARINGAN DATA AKTIF (.isin)
# ==========================================
df_filtered = df_all.copy()

if selected_id:
    df_filtered = df_filtered[df_filtered["id"].isin(selected_id)]

if selected_kec: 
    df_filtered = df_filtered[df_filtered["nama_kecamatan"].isin(selected_kec)]

if selected_kel: 
    df_filtered = df_filtered[df_filtered["nama_desa_kelurahan"].isin(selected_kel)]

if selected_pemilik: 
    df_filtered = df_filtered[df_filtered["pemilik_menara"].isin(selected_pemilik)]

if selected_struktur: 
    df_filtered = df_filtered[df_filtered["struktur_tower"].isin(selected_struktur)]

# ==========================================
# 4. KONTEN UTAMA & HEADER DASHBOARD
# ==========================================
st.markdown("<div class='main-title'>Geographic Information System Menara BTS</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Data Pemetaan Infrastruktur Telekomunikasi Digital Kota Bandung</div>", unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("Total Menara Terfilter", f"{len(df_filtered)} Unit")
with m2: st.metric("Total Kecamatan Terfilter", f"{df_filtered['nama_kecamatan'].nunique()}")
with m3: st.metric("Total Pemilik Menara Terfilter", f"{df_filtered['pemilik_menara'].nunique()}")
with m4: st.metric("Total Struktur Menara Terfilter", f"{df_filtered['struktur_tower'].nunique()}")

# ==========================================
# 5. PETA INTERAKTIF DIGITAL
# ==========================================
st.markdown("### 🗺️ Visualisasi Peta Persebaran Menara")

# Inisialisasi Peta dasar dengan koordinat Kota Bandung
m = folium.Map(location=[-6.9175, 107.6191], zoom_start=12, tiles="openstreetmap", control_scale=True)

measure_control = MeasureControl(
    position='topleft',
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
            <b>Tinggi:</b> {row['tinggi_tower']} {row['satuan']}
        </div>
        """
        folium.Marker(
            location=[row['lat'], row['long']],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color="blue", icon="tower-broadcast", prefix="fa")
        ).add_to(marker_cluster)

# --- PERBAIKAN UTAMA RENDER PETA ---
# Menggunakan penanganan kompilasi objek HTML m HTML bawaan yang eksplisit dan bersih
html_map = m._repr_html_()
components.html(html_map, height=550, scrolling=False)

# ==========================================
# 6. TABEL DATA TABULAR
# ==========================================
st.markdown("### 📊 Detail Data Tabular Menara")

if df_filtered.empty:
    st.warning("⚠️ Tidak ada data menara yang sesuai dengan kombinasi filter kontrol spasial saat ini.")
else:
    # Menambahkan hide_index=True untuk menyembunyikan kolom indeks paling kiri
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

