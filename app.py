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

# Plot Titik Menara dengan Fitur Klaster
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
            
            # Pengkondisian agar popup rapi saat diklik di peta
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
            
            # --- PEMETAAN ATRIBUT GEOJSON KE KOLOM BARU ANDA ---
            # Kode di bawah otomatis mencari nama properti di GeoJSON Anda (tidak sensitif huruf besar/kecil)
            def get_prop(keys_list, default="-"):
                for k in keys_list:
                    # Cari kunci yang mirip di data properti GeoJSON Anda
                    for actual_key in props.keys():
                        if actual_key.lower().strip() == k.lower().strip():
                            return props[actual_key]
                return default

            rows_list.append({
                "id": get_prop(["id", "objectid", "no"]),
                "nama_provinsi": get_prop(["nama_provinsi", "provinsi", "prov"], "JAWA BARAT"),
                "nama_kabupaten_kota": get_prop(["nama_kabupaten_kota", "kabupaten", "kota"], "KOTA BANDUNG"),
                "nama_kecamatan": get_prop(["nama_kecamatan", "kecamatan", "kec"]),
                "nama_desa_kelurahan": get_prop(["nama_desa_kelurahan", "kelurahan", "desa", "kel"]),
                "pemilik_menara": get_prop(["pemilik_menara", "pemilik", "provider", "operator", "site_name"]),
                "lokasi_menara": get_prop(["lokasi_menara", "lokasi", "alamat"]),
                "long": lon,
                "lat": lat,
                "struktur_tower": get_prop(["struktur_tower", "struktur", "tipe", "type"]),
                "tinggi_tower": get_prop(["tinggi_tower", "tinggi", "height"]),
                "satuan": get_prop(["satuan", "unit"], "Meter"),
                "tahun": get_prop(["tahun", "tahun_berdiri", "thn"])
            })

# Merender Peta di dalam bingkai Card HTML
st_folium(m, width="100%", height=500, returned_objects=[])
st.markdown('</div></div>', unsafe_allow_html=True)


# 6. PEMBUATAN PANEL TABEL DATA (DATA MENARA TELEKOMUNIKASI)
st.markdown('<div class="table-section-title">📊 DATA MENARA TELEKOMUNIKASI</div>', unsafe_allow_html=True)

if data_bts and len(rows_list) > 0:
    # Mengubah array data menjadi Dataframe Pandas
    df = pd.DataFrame(rows_list)
    
    # Menampilkan tabel interaktif bawaan Streamlit sesuai urutan kolom yang Anda minta
    st.dataframe(
        df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "id": st.column_config.Column(width="small"),
            "long": st.column_config.NumberColumn(format="%.6f"),
            "lat": st.column_config.NumberColumn(format="%.6f"),
        }
    )
else:
    st.info("Belum ada data menara yang dapat dimuat ke dalam tabel.")
