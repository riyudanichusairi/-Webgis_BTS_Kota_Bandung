import streamlit as st
import folium
from streamlit_folium import st_folium
import json
from folium.plugins import Search
import pandas as pd
import branca.colormap as cm

# Konfigurasi halaman penuh (wide mode)
st.set_page_config(layout="wide", page_title="WebGIS Lamongan", page_icon="🌐")

# ==========================================
# 1. MEMBUAT PANEL SAMPING (SIDEBAR)
# ==========================================
with st.sidebar:
    col_left, col_center, col_right = st.columns([1.5, 7, 1.5])
    with col_center:
        st.write("") 
        try:
            st.image("logo_lamongan.png", use_container_width=True)
        except:
            st.warning("⚠️ Logo logo_lamongan.png tidak ditemukan.")
    
    st.title("WebGIS Penduduk Lamongan 2024")
    st.write(
        "Aplikasi Dashboard Geospasial Interaktif untuk visualisasi dan analisis data "
        "kependudukan tingkat Desa/Kelurahan di wilayah Kabupaten Lamongan, Provinsi Jawa Timur."
    )
    st.markdown("---")
    st.write("📌 **Panduan Penggunaan:**")
    st.caption("1. Gunakan panel filter di bawah untuk menyaring data berdasarkan 'Kecamatan' atau 'Desa'.")
    st.caption("2. Peta akan otomatis melakukan ZOOM ke area wilayah terfilter secara real-time.")
    st.caption("3. Peta, Metrik Utama, Tabel, dan Grafik akan berubah otomatis secara bersamaan.")
    st.caption("4. Arahkan kursor (*hover*) untuk melihat nama desa, dan **klik** wilayah desa untuk melihat tabel demografi lengkap.")
    
    st.markdown("---")
    st.write("📊 **Aksi Data:**")

# ==========================================
# 2. DATA MANAGEMENT (MEMBACA & EKSTRAK DATA BERDASARKAN ID)
# ==========================================
try:
    with open("kab_lamongan_popmap.geojson", "r") as f:
        geo_data = json.load(f)
except FileNotFoundError:
    st.error("❌ File 'kab_lamongan_popmap.geojson' tidak ditemukan. Harap pastikan file spasial berada di folder yang sama.")
    st.stop()

records = []
for fitur in geo_data['features']:
    props = fitur['properties']
    # PERBAIKAN: Membaca ID unik numerik (NO_KEC dan NO_KEL_DES) untuk menjamin akurasi join data
    records.append({
        'No_Kec': props.get('NO_KEC', '0'),
        'Kecamatan': props.get('KEC', 'Tidak Diketahui'),
        'No_Desa': props.get('NO_KEL_DES', '0'),
        'Desa': props.get('KEL_DES', 'Tidak Diketahui'),
        'Jumlah Penduduk': props.get('jumlah_penduduk', 0),
        'Laki-laki': props.get('laki_laki', 0),
        'Perempuan': props.get('perempuan', 0)
    })
df_raw = pd.DataFrame(records)

# Lakukan grouping agregasi berdasarkan ID Unik Desa (No_Desa) dan ID Kecamatan (No_Kec) 
# guna menyatukan poligon terpisah agar terhitung sebagai satu wilayah tunggal yang sinkron
df = df_raw.groupby(['No_Kec', 'Kecamatan', 'No_Desa', 'Desa'], as_index=False).agg({
    'Jumlah Penduduk': 'sum',
    'Laki-laki': 'sum',
    'Perempuan': 'sum'
})

# Title Aplikasi
st.title("Dashboard WebGIS Kepadatan Penduduk Kabupaten Lamongan 2024")

# ==========================================
# 3. WIDGET FILTER (DEKLARASI CONTAINER PLACEHOLDER)
# ==========================================
filter_container = st.container()

daftar_kecamatan = sorted(df['Kecamatan'].unique())

if 'kec_key' not in st.session_state:
    st.session_state.kec_key = "-- Semua Kecamatan --"

# ==========================================
# 4. LOGIKA FILTERING DATA UNTUK SEMUA ELEMEN
# ==========================================
with filter_container:
    st.markdown("---")
    st.markdown("### 🔍 Penyaringan Data Dashboard")
    
    kecamatan_terpilih = st.selectbox(
        "📍 **Langkah 1: Filter Berdasarkan Kecamatan (Opsional):**",
        options=["-- Semua Kecamatan --"] + daftar_kecamatan,
        key="kecamatan_box"
    )

if kecamatan_terpilih != "-- Semua Kecamatan --":
    df_kec = df[df['Kecamatan'] == kecamatan_terpilih]
    daftar_desa = sorted(df_kec['Desa'].unique())
else:
    df_kec = df
    daftar_desa = sorted(df['Desa'].unique())

with filter_container:
    desa_terpilih = st.multiselect(
        "🔍 **Langkah 2: Pilih Beberapa Desa/Kelurahan:**",
        options=daftar_desa,
        placeholder="Ketik atau pilih nama beberapa desa...",
        key="desa_box"
    )

# Sinkronisasi data spasial geojson menggunakan No_KEL_DES & NO_KEC
if desa_terpilih:
    df_filter = df[df['Desa'].isin(desa_terpilih)]
    geo_data_filter = geo_data.copy()
    geo_data_filter['features'] = [
        f for f in geo_data['features'] 
        if f['properties'].get('KEL_DES') in desa_terpilih
    ]
    label_status = "Hasil Seleksi Desa"

elif kecamatan_terpilih != "-- Semua Kecamatan --":
    df_filter = df_kec
    list_desa_kec = df_kec['Desa'].tolist()
    geo_data_filter = geo_data.copy()
    geo_data_filter['features'] = [
        f for f in geo_data['features'] 
        if f['properties'].get('KEC') == kecamatan_terpilih
    ]
    label_status = f"Kec. {kecamatan_terpilih}"

else:
    df_filter = df
    geo_data_filter = geo_data
    label_status = "Total Lamongan"

# Penghitungan metrik utama secara dinamis (Dijamin 100% sama dengan baris tabel riil)
total_penduduk = int(df_filter['Jumlah Penduduk'].sum())
total_laki = int(df_filter['Laki-laki'].sum())
total_perempuan = int(df_filter['Perempuan'].sum())
total_desa = int(len(df_filter)) # Menghitung jumlah entitas desa terfilter unik

# Pembuatan tombol download data di sidebar
# Menghapus kolom kode ID internal sebelum diunduh agar pengguna awam tidak bingung
df_download = df_filter.drop(columns=['No_Kec', 'No_Desa'])
csv_data = df_download.to_csv(index=False).encode('utf-8')
with st.sidebar:
    st.download_button(
        label="📥 Unduh Data Terfilter (CSV)",
        data=csv_data,
        file_name=f"data_penduduk_lamongan_{label_status.replace(' ', '_')}.csv",
        mime="text/csv"
    )

# ==========================================
# 5. MENAMPILKAN ELEMEN VISUAL 
# ==========================================

# --- POSISI 1: KARTU METRIK DI ATAS ---
st.markdown("### 📊 Ringkasan Data Konten")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Penduduk", f"{total_penduduk:,} Jiwa")
m2.metric("Laki-laki", f"{total_laki:,} Jiwa")
m3.metric("Perempuan", f"{total_perempuan:,} Jiwa")
m4.metric("Jumlah Wilayah (Desa)", f"{total_desa} Wilayah")

st.markdown("---")

# --- POSISI 2: TABEL & GRAFIK (DI TENGAH) ---
st.markdown("### 📈 Analisis dan Detail Data Terfilter")
col_tabel, col_grafik = st.columns(2)

with col_tabel:
    st.markdown("#### 📋 Tabel Detail Penduduk per Desa")
    # Mengurutkan tabel berdasarkan populasi tertinggi
    df_tabel_tampil = df_filter.sort_values(by="Jumlah Penduduk", ascending=False).reset_index(drop=True)
    
    # Hanya menampilkan kolom informasi publik ke user (Menyembunyikan No_Kec dan No_Desa dari tabel UI)
    df_tabel_tampil = df_tabel_tampil[['Kecamatan', 'Desa', 'Jumlah Penduduk', 'Laki-laki', 'Perempuan']]
    
    # KODE ALL JOIN: Menyisipkan kolom nomor urut "No." dimulai dari angka 1 di kolom pertama
    df_tabel_tampil.insert(0, 'No.', df_tabel_tampil.index + 1)
    
    # Menampilkan tabel bersih tanpa kolom indeks 0 abu-abu bawaan Pandas
    st.dataframe(df_tabel_tampil, use_container_width=True, height=350, hide_index=True)

with col_grafik:
    st.markdown("#### 📊 Grafik Perbandingan Populasi Desa")
    if not df_filter.empty:
        df_chart = df_filter.set_index("Desa")[["Laki-laki", "Perempuan"]]
        st.bar_chart(df_chart, use_container_width=True, height=350)
    else:
        st.info("💡 Tidak ada data yang tersedia untuk dibuatkan grafik berdasarkan filter saat ini.")

st.markdown("---")

# --- POSISI 3: PETA INTERAKTIF KLOROPLET (DI PALING BAWAH) ---
st.markdown("### 🗺️ Peta Interaktif Kloroplet Desa")

map_center = [-7.14, 112.33]
map_zoom = 10

m = folium.Map(
    location=map_center, 
    zoom_start=map_zoom, 
    tiles=None,
    control_scale=True
)

folium.TileLayer(
    tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attr='&copy; OpenStreetMap contributors',
    name='Peta Jalan (OpenStreetMap)'
).add_to(m)

colormap_peta = cm.StepColormap(
    colors=['#ffffcc', '#7fcdbb', '#41b6c4', '#1d91c0', '#253494', '#081d58'],
    index=[0, 1000, 2000, 3000, 4500, 6000, 10000],
    vmin=0,
    vmax=10000,
    caption="Jumlah Penduduk Kabupaten Lamongan per Desa (Jiwa)"
)

def ganti_warna(fitur):
    jumlah_pop = fitur['properties'].get('jumlah_penduduk', 0)
    return {
        'fillColor': colormap_peta(jumlah_pop), 
        'color': '#666666',      
        'weight': 0.5,           
        'fillOpacity': 0.75       
    }

choro_layer = folium.GeoJson(
    geo_data_filter,
    name="Kloroplet Penduduk Lamongan",
    style_function=ganti_warna,
    control=True,
    highlight_function=lambda x: {'weight': 2.5, 'color': '#ff7800', 'fillOpacity': 0.9}
).add_to(m)

if kecamatan_terpilih != "-- Semua Kecamatan --" or desa_terpilih:
    if geo_data_filter['features']: 
        bounds = choro_layer.get_bounds()
        m.fit_bounds(bounds) 

peta_search = Search(
    layer=choro_layer,
    geom_type="Polygon",
    placeholder="Cari nama desa/kelurahan...",
    collapsed=False,
    position="topright",
    search_label="KEL_DES",
    search_zoom=14,
    weight=3,
    fill_color="#ff7800",
    fill_opacity=0.4
).add_to(m)

folium.features.GeoJsonPopup(
    fields=["KEC", "KEL_DES", "jumlah_penduduk", "laki_laki", "perempuan"],
    aliases=["Kecamatan:", "Desa/Kelurahan:", "Jumlah Penduduk (Jiwa):", "Jumlah Laki-laki:", "Jumlah Perempuan:"],
    labels=True,
    style="font-family: sans-serif; font-size: 13px; font-weight: bold; padding: 10px; border: 1px solid #ccc; min-width: 240px;"
).add_to(choro_layer)

folium.features.GeoJsonTooltip(
    fields=["KEL_DES"],
    aliases=["Desa: "],
    labels=False,
    sticky=True
).add_to(choro_layer)

colormap_peta.add_to(m)

st_folium(m, width='100%', height=550, returned_objects=[])
