import streamlit as st
import folium
from folium.plugins import MarkerCluster, MeasureControl
from branca.element import MacroElement
from jinja2 import Template
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
    [data-testid="stSidebar"] .stTextInput label { color: #cbd5e1 !important; font-weight: 500; }
    .main-title { font-family: 'Inter', sans-serif; color: #1e293b; font-size: 28px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 2px; }
    .sub-title { color: #64748b; font-size: 14px; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# CUSTOM CLASS UNTUK SEARCH BAR ALAMAT
# ==========================================
class LeafletGeosearch(MacroElement):
    """Menambahkan Search Bar alamat di pojok kanan atas peta menggunakan Leaflet Geosearch"""
    def __init__(self):
        super(LeafletGeosearch, self).__init__()
        self._template = Template("""
            {% macro header(this, kwargs) %}
            <link rel="stylesheet" href="https://unpkg.com" />
            <script src="https://unpkg.com"></script>
            <style>
                .leaflet-top.leaflet-right .leaflet-geosearch-button {
                    margin-top: 10px !important;
                    margin-right: 10px !important;
                }
            </style>
            {% endmacro %}

            {% macro script(this, kwargs) %}
            const provider = new window.GeoSearch.OpenStreetMapProvider();
            const searchControl = new window.GeoSearch.GeoSearchControl({
                provider: provider,
                style: 'bar',
                position: 'topright',
                showMarker: true,
                showPopup: false,
                marker: {
                    icon: new L.Icon.Default(),
                    draggable: false,
                },
                maxMarkers: 1,
                retainZoomLevel: false,
                animateZoom: true,
                autoClose: true,
                searchLabel: 'Cari lokasi/alamat...',
                keepResult: true
            });
            {{this._parent.get_name()}}.addControl(searchControl);
            {% endmacro %}
        """)

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
    
    # Pencarian Berdasarkan ID Menara
    search_id = st.text_input("Cari ID Menara:", placeholder="Contoh: 1, 2, atau 15...")
    
    st.markdown("<hr style='margin:10px 0; border-color:#334155;'>", unsafe_allow_html=True)
    
    # Filter 1: Kecamatan
    list_kec = ["Semua Kecamatan"] + sorted([x for x in df_all["nama_kecamatan"].unique() if x != "-"])
    selected_kec = st.selectbox("Wilayah Kecamatan:", list_kec)
    
    # Filter 2: Kelurahan
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
    st.markdown("<div style='font-size:11px; color:#94a3b8;'>Diskominfo Kota Bandung<br>v1.7.0 (Fixed Iloc Correctly)</div>", unsafe_allow_html=True)

# ==========================================
# PROSES PENJARINGAN DATA AKTIF (LOGIKA FILTER)
# ==========================================
df_filtered = df_all.copy()
is_single_id_found = False
map_center = [-6.9175, 107.6191]
map_zoom = 12

# Jika pengguna memasukkan ID Pencarian
if search_id.strip():
    df_id_match = df_all[df_all["id"].str.strip() == search_id.strip()]
    if not df_id_match.empty:
        df_filtered = df_id_match
        # PERBAIKAN TOTAL DI SINI: Ditambahkan indeks numerik [0] agar membaca baris awal dengan benar
        map_center = [float(df_filtered.iloc[0]["lat"]), float(df_filtered.iloc[0]["long"])]
        map_zoom = 17  
        is_single_id_found = True
    else:
        df_filtered = pd.DataFrame(columns=df_all.columns)
else:
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
with m2: st.metric("Cakupan Kecamatan", f"{df_filtered['nama_kecamatan'].nunique() if not df_filtered.empty else 0}")
with m3: st.metric("Entitas Pemilik", f"{df_filtered['pemilik_menara'].nunique() if not df_filtered.empty else 0}")
