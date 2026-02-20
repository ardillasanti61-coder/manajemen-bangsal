import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- 1. PENGATURAN HALAMAN ---
st.set_page_config(page_title="Sistem Gizi Pasien", layout="wide")

# CSS untuk tampilan yang lebih segar dan modern
st.markdown("""
    <style>
    /* Background Gradasi Segar */
    .stApp { 
        background: linear-gradient(135deg, #f1f8e9 0%, #dcedc8 100%); 
    }
    
    /* Desain Kotak Form */
    [data-testid="stForm"] {
        max-width: 500px;
        margin: auto;
        background-color: white !important;
        padding: 30px !important;
        border-radius: 25px !important;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.1);
        border: 1px solid #a5d6a7;
    }
    
    /* Judul Utama */
    .main-title { 
        color: #2e7d32; 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 800; 
        text-align: center;
        margin-top: -20px;
    }
    
    /* Sub Judul */
    .sub-title {
        text-align: center;
        color: #558b2f;
        font-style: italic;
        margin-bottom: 25px;
    }

    /* Gaya Tombol */
    div.stButton > button {
        background: linear-gradient(to right, #2e7d32, #66bb6a) !important;
        color: white !important;
        border-radius: 15px !important;
        border: none !important;
        font-weight: bold;
        transition: 0.3s;
        width: 100%;
    }
    
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0px 5px 15px rgba(46, 125, 50, 0.3);
    }

    /* Styling Tabel */
    .stDataFrame {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIKA LOGIN ---
if 'login_berhasil' not in st.session_state:
    st.session_state['login_berhasil'] = False
    st.session_state['username'] = ""

if not st.session_state['login_berhasil']:
    # Gambar Banner di Halaman Login
    st.image("https://images.unsplash.com/photo-1490818387583-1baba5e638af?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80", use_container_width=True)
    st.markdown("<h1 class='main-title'>🥗 SISTEM GIZI PASIEN</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Manajemen Nutrisi Terpadu & Profesional</p>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        st.markdown("<h3 style='text-align:center; color:#2e7d32;'>Silakan Masuk</h3>", unsafe_allow_html=True)
        user_input = st.text_input("Username")
        pw_input = st.text_input("Password", type="password")
        if st.form_submit_button("MASUK KE SISTEM"):
            users = {"ardilla": "dilla123", "ahligizi1": "gizi123", "ahligizi2": "gizi456"}
            if user_input in users and pw_input == users[user_input]:
                st.session_state['login_berhasil'] = True
                st.session_state['username'] = user_input
                st.rerun()
            else:
                st.error("Username atau Password Salah!")
else:
    # --- 3. DATABASE ---
    DB_NAME = 'gizi_rs_v3.db'

    def init_db():
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS pasien (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            tgl_mrs TEXT, no_rm TEXT, ruang TEXT, nama_pasien TEXT, 
            tgl_lahir TEXT, umur TEXT, bb REAL, tb REAL, imt REAL, 
            status_gizi TEXT, zscore TEXT, diagnosa_medis TEXT, skrining_gizi TEXT, diet TEXT, input_by TEXT)''')
        conn.commit()
        conn.close()

    def ambil_data_db():
        conn = sqlite3.connect(DB_NAME)
        query = "SELECT * FROM pasien ORDER BY tgl_mrs DESC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def hapus_data(id_pasien):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM pasien WHERE id = ?", (id_pasien,))
        conn.commit()
        conn.close()

    init_db()

    # Sidebar
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3448/3448621.png", width=80)
        st.write(f"👤 Petugas: **{st.session_state['username'].upper()}**")
        if st.button("🚪 Keluar Aplikasi"):
            st.session_state['login_berhasil'] = False
            st.rerun()

    # Header Dashboard
    st.image("https://images.unsplash.com/photo-1512621776951-a57141f2eefd?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80", use_container_width=True)
    st.markdown(f"<h1 class='main-title'>DASHBOARD GIZI - {st.session_state['username'].upper()}</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["➕ Input Data Pasien", "📊 Rekap & Ekspor Laporan"])

    with tab1:
        with st.form("form_input", clear_on_submit=True):
            st.markdown("<h4 style='color:#2e7d32;'>Identitas Pasien</h4>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                t_mrs = st.date_input("Tanggal MRS", value=datetime.now())
                rm = st.text_input("Nomor Rekam Medis")
                nama = st.text_input("Nama Lengkap Pasien")
                t_lhr = st.date_input("Tanggal Lahir", value=datetime(2000, 1, 1))
                rng = st.selectbox("Ruang Perawatan", ["Anna", "Maria", "Fransiskus", "Teresa", "Monika", "Clement", "ICU/ICCU"])
            with c2:
                d_medis = st.text_input("Diagnosa Medis")
                skrng_gizi = st.selectbox("Skrining Gizi (MST)", ["Tidak Berisiko", "Berisiko"])
                bb = st.number_input("Berat Badan (kg)", min_value=0.0)
                tb = st.number_input("Tinggi Badan (cm)", min_value=0.0)
                z_manual = st.text_input("Z-Score", placeholder="Contoh: -1.5 SD")
                diet = st.text_input("Jenis Diet Gizi")
            
            if st.form_submit_button("SIMPAN DATA KE DATABASE"):
                if rm and nama:
                    u_teks = f"{relativedelta(t_mrs, t_lhr).years} Thn"
                    imt_val = round(bb / ((tb/100)**2), 2) if bb > 0 and tb > 0 else 0
                    if imt_val >= 27: st_gizi = "Obesitas"
                    elif imt_val >= 25: st_gizi = "Overweight"
                    elif imt_val >= 18.5: st_gizi = "Normal"
                    else: st_gizi = "Kurus"

                    conn = sqlite3.connect(DB_NAME)
                    c = conn.cursor()
                    c.execute('''INSERT INTO pasien 
                        (tgl_mrs, no_rm, ruang, nama_pasien, tgl_lahir, umur, bb, tb, imt, status_gizi, zscore, diagnosa_medis, skrining_gizi, diet, input_by) 
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                        (t_mrs.strftime("%Y-%m-%d"), rm, rng, nama, t_lhr.strftime("%Y-%m-%d"), 
                         u_teks, bb, tb, imt_val, st_gizi, z_manual, d_medis, skrng_gizi, diet, st.session_state['username']))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Data {nama} berhasil diamankan!")
                    st.rerun()
                else:
                    st.warning("⚠️ Nama dan No. RM wajib diisi!")

    with tab2:
        df_full = ambil_data_db()
        if st.session_state['username'] != "ardilla":
            df_full = df_full[df_full['input_by'] == st.session_state['username']]

        if not df_full.empty:
            st.markdown("<h4 style='color:#2e7d32;'>Saring & Cari Data</h4>", unsafe_allow_html=True)
            f1, f2, f3 = st.columns(3)
            with f1:
                cari_nama = st.text_input("🔎 Cari Nama Pasien")
            with f2:
                filter_ruang = st.multiselect("🏥 Filter Ruangan", options=sorted(df_full['ruang'].unique()))
            with f3:
                df_full['bulan_mrs'] = pd.to_datetime(df_full['tgl_mrs']).dt.strftime('%B %Y')
                filter_bulan = st.multiselect("📅 Filter Bulan MRS", options=sorted(df_full['bulan_mrs'].unique()))

            # Proses Filter
            df_filter = df_full.copy()
            if cari_nama:
                df_filter = df_filter[df_filter['nama_pasien'].str.contains(cari_nama, case=False)]
            if filter_ruang:
                df_filter = df_filter[df_filter['ruang'].isin(filter_ruang)]
            if filter_bulan:
                df_filter = df_filter[df_filter['bulan_mrs'].isin(filter_bulan)]

            st.write(f"Menampilkan **{len(df_filter)}** catatan medis")
            kolom_tampil = ['tgl_mrs', 'no_rm', 'nama_pasien', 'ruang', 'status_gizi', 'zscore', 'skrining_gizi', 'input_by']
            st.dataframe(df_filter, use_container_width=True, hide_index=True, column_order=kolom_tampil)
            
            # --- EKSPOR KE EXCEL ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_export = df_filter.drop(columns=['bulan_mrs'])
                df_export.to_excel(writer, index=False, sheet_name='Laporan Gizi')
                
                worksheet = writer.sheets['Laporan Gizi']
                worksheet.page_setup.paperSize = '13' # F4
                worksheet.page_setup.orientation = worksheet.ORIENTATION_LANDSCAPE
                
                # Tambah baris tanda tangan
                last_row = len(df_export) + 3
                worksheet.cell(row=last_row, column=2, value="Kepala Instalasi Gizi")
                worksheet.cell(row=last_row, column=6, value="Kepala Ruangan")
                nama_row = last_row + 4
                worksheet.cell(row=nama_row, column=2, value="( ____________________ )")
                worksheet.cell(row=nama_row, column=6, value="( ____________________ )")

            st.download_button(
                label=f"📤 EKSPOR {len(df_filter)} DATA KE EXCEL (F4)",
                data=output.getvalue(),
                file_name=f"Laporan_Gizi_{datetime.now().strftime('%d%m%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

            # --- HAPUS DATA ---
            st.markdown("---")
            with st.expander("🗑️ Hapus Data Salah Input"):
                opsi_hapus = {f"{row['nama_pasien']} ({row['no_rm']}) - ID:{row['id']}": row['id'] for _, row in df_filter.iterrows()}
                pilihan = st.selectbox("Pilih data yang akan dibuang:", ["-- Pilih --"] + list(opsi_hapus.keys()))
                if pilihan != "-- Pilih --":
                    konfirmasi = st.checkbox("Saya yakin ingin menghapus data ini secara permanen")
                    if st.button("HAPUS SEKARANG"):
                        if konfirmasi:
                            hapus_data(opsi_hapus[pilihan])
                            st.success("Data berhasil dihapus!")
                            st.rerun()
                        else:
                            st.error("Centang konfirmasi dulu!")
        else:
            st.info("Belum ada data yang tersimpan.")
