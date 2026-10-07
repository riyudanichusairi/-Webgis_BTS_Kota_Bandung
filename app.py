import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import json
import pandas as pd
import plotly.express as px  # Ditambahkan untuk visualisasi grafik batang komparatif

# ==========================================
# 1. KONFIGURASI HALAMAN & STYLE CSS
# ==========================================
st.set_page_config(
    page_title="WebGIS Penduduk Lamongan 2024",
    layout="wide",
    initial_sidebar_state="expanded"  # Dibuat expanded agar sidebar panduan terlihat
)

# Custom CSS disesuaikan untuk nuansa bersih, modern, dan rapi sesuai gambar
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    .sidebar-logo-container {
        text-align: center;
        padding: 20px 10px;
    }
    .sidebar-title {
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 18px;
        font-weight: 700;
        color: #1e293b;
        margin-top: 10px;
        line-height: 1.3;
    }
    .sidebar-desc {
        font-size: 11px;
        color: #64748b;
        margin-top: 8px;
        text-align: justify;
    }
    
    /* Section & Card Styling */
    .section-title {
        font-family: Arial, sans-serif;
        font-size: 15px;
        font-weight: 700;
        color: #334155;
        margin-top: 25px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .filter-card {
        background-color: #ffffff;
        padding: 15px;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        margin-bottom: 15px;
    }
    
    /* Content Card */
    .bg-white-card {
        background-color: #ffffff;
        padding: 15px;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        height: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. KOMPONEN SIDEBAR (NAVIGASI & PANDUAN)
# ==========================================
with st.sidebar:
    st.markdown("""
        <div class="sidebar-logo-container">
            <!-- URL source gambar menggunakan logo Kabupaten Lamongan -->
            <img src="https://wikimedia.org" width="80">
            <div class="sidebar-title">WebGIS Penduduk<br>Lamongan 2024</div>
            <div class="sidebar-desc">
                Aplikasi Dashboard Geospatial Interaktif untuk visualisasi dan analisis data kependudukan tingkat Desa/Kelurahan di wilayah Kabupaten Lamongan, Provinsi Jawa Timur.
            </div>
        </div>
        <hr style="margin: 10px 0; border-color: #e2e8f0;">
        <div style="font-size: 12px; font-weight: bold; color: #dc2626; margin-bottom: 5px;">📍 Panduan Penggunaan:</div>
        <div style="font-size: 11px; color: #475569; line-height: 1.5;">
            1. Gunakan panel filter di bawah untuk menyaring data berdasarkan 'Kecamatan' atau 'Desa/Kelurahan'.<br><br>
            2. Peta akan otomatis melakukan ZOOM ke area wilayah terfilter secara real-time.<br><br>
            3. Ringkasan Kependudukan, Grafik, dan Tabel akan berubah secara otomatis.<br><br>
            4. Arahkan kursor (hover) pada peta untuk melihat detail demografi desa.
        </div>
        <hr style="margin: 20px 0; border-color: #e2e8f0;">
        <div style="font-size: 11px; font-weight: bold; color: #475569;">📊 Data Aktif:</div>
    """, unsafe_allow_html=True)
    
    # Tombol unduh diletakkan di bagian bawah sidebar
    st.download_button(
        label="💾 Unduh Data Terfilter (.CSV)",
        data="",
        file_name="data_penduduk_lamongan_filtered.csv",
        mime="text/csv",
        use_container_width=True
    )

# ==========================================
# 3. FUNGSI LOAD DATA & PRE-PROCESSING
# ==========================================
def load_geojson(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

# Silakan sesuaikan nama file GeoJSON kependudukan Kabupaten Lamongan Anda
batas_desa = load_geojson("batas_desa_lamongan.geojson") 

# PERBAIKAN: Mengisi data contoh yang utuh tanpa celah sintaks kosong maupun string kosong
raw_data = {
    "No":,
    "Kecamatan": ["Paciran", "Brondong", "Brondong", "Mantup", "Tikung", "Sukodadi", "Paciran", "Modo"],
    "Desa/Kelurahan": ["Sendangagung", "Brengkok", "Sendangharjo", "Mantup", "Tambakrigadung", "Sukodadi", "Kranji", "Mojorejo"],
    "Jumlah Penduduk":,
    "Laki-laki":,
    "Perempuan":,
    "lat": [-6.8837, -6.9012, -6.8950, -7.2415, -7.1622, -7.0985, -6.8722, -7.2110],
    "long": [112.3551, 112.2745, 112.3121, 112.4510, 112.4312, 112.3315, 112.3611, 112.1812]
}
df_all = pd.DataFrame(raw_data)

# ==========================================
# 4. DASBOR DATA PENYARINGAN (FILTER)
# ==========================================
st.markdown('<div class="section-title">🔍 Dasbor Data Penyaringan</div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    
    # Pilihan Langkah 1: Filter Kecamatan
    list_kec = ["--Semua Kecamatan--"] + sorted(list(df_all["Kecamatan"].unique()))
    selected_kec = st.selectbox("📍 Langkah 1: Filter Berdasarkan Kecamatan (Opsional)", list_kec)
    
    # Pilihan Langkah 2: Filter Desa/Kelurahan
    if selected_kec != "--Semua Kecamatan--":
        df_filtered_kec = df_all[df_all["Kecamatan"] == selected_kec]
        list_des = ["--Semua Desa/Kelurahan--"] + sorted(list(df_filtered_kec["Desa/Kelurahan"].unique()))
    else:
        list_des = ["--Semua Desa/Kelurahan--"] + sorted(list(df_all["Desa/Kelurahan"].unique()))
        
    selected_des = st.selectbox("📍 Langkah 2: Pilih Beberapa Desa/Kelurahan:", list_des)
    st.markdown('</div>', unsafe_allow_html=True)

# Eksekusi Filter
df_filtered = df_all.copy()
if selected_kec != "--Semua Kecamatan--":
    df_filtered = df_filtered[df_filtered["Kecamatan"] == selected_kec]
if selected_des != "--Semua Desa/Kelurahan--":
    df_filtered = df_filtered[df_filtered["Desa/Kelurahan"] == selected_des]

# ==========================================
# 5. RINGKASAN DATA KONTEN (METRIK)
# ==========================================
st.markdown('<div class="section-title">📊 Ringkasan Data Konten</div>', unsafe_allow_html=True)

total_penduduk = df_filtered["Jumlah Penduduk"].sum()
total_lk = df_filtered["Laki-laki"].sum()
total_pr = df_filtered["Perempuan"].sum()
total_wilayah = df_filtered["Desa/Kelurahan"].nunique() if not df_filtered.empty else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Jumlah Penduduk Total", value=f"{total_penduduk:,} Jiwa".replace(",", "."))
with col2:
    st.metric(label="Laki-laki", value=f"{total_lk:,} Jiwa".replace(",", "."))
with col3:
    st.metric(label="Perempuan", value=f"{total_pr:,} Jiwa".replace(",", "."))
with col4:
    st.metric(label="Jumlah Wilayah (Desa)", value=f"{total_wilayah} Wilayah")

# ==========================================
# 6. ANALISIS DAN DETAIL DATA TERFILTER (TABEL & GRAFIK)
# ==========================================
st.markdown('<div class="section-title">📉 Analisis dan Detail Data Terfilter</div>', unsafe_allow_html=True)

col_tabel, col_grafik = st.columns(2)

with col_tabel:
    st.markdown('<div class="bg-white-card"><b>📋 Tabel Detail Penduduk per Desa</b><br><br>', unsafe_allow_html=True)
    # Tampilan tabel dengan menyembunyikan kolom koordinat internal
    df_table_show = df_filtered[["No", "Kecamatan", "Desa/Kelurahan", "Jumlah Penduduk", "Laki-laki", "Perempuan"]]
    st.dataframe(df_table_show, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_grafik:
    st.markdown('<div class="bg-white-card"><b>📊 Grafik Perbandingan Populasi Desa</b><br><br>', unsafe_allow_html=True)
    if not df_filtered.empty:
        # Melakukan restrukturisasi data (melt) agar sesuai format grafik komparatif L/P
        df_melted = df_filtered.melt(
            id_vars=["Desa/Kelurahan"], 
            value_vars=["Laki-laki", "Perempuan"],
            var_name="Jenis Kelamin", 
            value_name="Populasi"
        )
        
        fig = px.bar(
            df_melted, 
            x="Desa/Kelurahan", 
            y="Populasi", 
            color="Jenis Kelamin",
            barmode="group",
            color_discrete_map={"Laki-laki": "#1e40af", "Perempuan": "#38bdf8"},
            height=300
        )
        fig.update_layout(
            margin=dict(l=20, r=20, t=10, b=20),
            xaxis_title=None,
            yaxis_title=None,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Tidak ada data untuk ditampilkan grafiknya.")
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 7. PANEL PETA INTERAKTIF KLOROPLET
# ==========================================
st.markdown('<div class="section-title">🗺️ Peta Interaktif Kloroplet Desa</div>', unsafe_allow_html=True)

# Titik tengah peta default disesuaikan ke area Kabupaten Lamongan
map_center = [-7.1283, 112.3148]
zoom_lv = 11

if selected_des != "--Semua Desa/Kelurahan--" and not df_filtered.empty:
    map_center = [df_filtered.iloc[0]['lat'], df_filtered.iloc[0]['long']]
    zoom_lv = 14
elif selected_kec != "--Semua Kecamatan--" and not df_filtered.empty:
    map_center = [df_filtered['lat'].mean(), df_filtered['long'].mean()]
    zoom_lv = 12

