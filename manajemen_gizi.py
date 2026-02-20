import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- 1. PENGATURAN HALAMAN ---
st.set_page_config(page_title="Sistem Gizi Pasien", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #B2D3C2; }
    [data-testid="stForm"] {
        max-width: 450px;
        margin: auto;
        background-color: white !important;
        padding: 30px !important;
        border-radius: 20px !important;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
    }
    .main-title { color: #2D5A27; font-weight: 700; text-align: center; }
    div.stButton > button {
        background-color: #2D5A27 !important;
        color: white !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIKA LOGIN ---
if 'login_berhasil' not in st.session_state:
    st.session_state['login_berhasil'] = False
    st.session_state['username'] = ""

if not st.session_state['login_berhasil']:
    st.write("<br><br>", unsafe_allow_html=True)
    st.image("https://cdn-icons-png.flaticon.com/512/3448/3448621.png", width=100)
    st.markdown("<h2 class='main-title'>SISTEM GIZI PASIEN</h2>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        st.markdown("<p style='text-align:center;'>Silakan Login</p>", unsafe_allow_html=True)
        user_input = st.text_input("Username")
        pw_input = st.text_input("Password", type="password")
        if st.form_submit_button("MASUK"):
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

    with st.sidebar:
        st.write(f"👤 Login: **{st.session_state['username']}**")
        if st.button("🚪 Logout"):
            st.session_state['login_berhasil'] = False
            st.rerun()

    st.markdown(f"<h1 class='main-title'>Dashboard Gizi - {st.session_state['username'].upper()}</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🍏 Input Data", "📋 Rekap & Ekspor"])

    with tab1:
        with st.form("form_input", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                t_mrs = st.date_input("Tanggal MRS", value=datetime.now())
                rm = st.text_input("Rekam Medis")
                nama = st.text_input("Nama Pasien")
                t_lhr = st.date_input("Tanggal Lahir", value=datetime(2000, 1, 1))
                rng = st.selectbox("Ruang", ["Anna", "Maria", "Fransiskus", "Teresa", "Monika", "Clement", "ICU/ICCU"])
            with c2:
                d_medis = st.text_input("Diagnosa Medis")
                skrng_gizi = st.selectbox("Risiko Malnutrisi", ["Tidak Berisiko", "Berisiko"])
                bb = st.number_input("Berat Badan (kg)", min_value=0.0)
                tb = st.number_input("Tinggi Badan (cm)", min_value=0.0)
                z_manual = st.text_input("Z-Score (Manual)", placeholder="Misal: -2 SD")
                diet = st.text_input("Jenis Diet")
            
            if st.form_submit_button("Simpan Data"):
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
                    st.success(f"Data {nama} Berhasil Disimpan!")
                    st.rerun()
                else:
                    st.warning("Mohon isi Nama dan No. RM!")

    with tab2:
        df_full = ambil_data_db()
        
        if st.session_state['username'] != "ardilla":
            df_full = df_full[df_full['input_by'] == st.session_state['username']]

        if not df_full.empty:
            st.subheader("🔍 Filter & Pencarian")
            f1, f2, f3 = st.columns(3)
            with f1:
                cari_nama = st.text_input("Cari Nama Pasien")
            with f2:
                filter_ruang = st.multiselect("Pilih Ruangan", options=sorted(df_full['ruang'].unique()))
            with f3:
                df_full['bulan_mrs'] = pd.to_datetime(df_full['tgl_mrs']).dt.strftime('%B %Y')
                filter_bulan = st.multiselect("Pilih Bulan MRS", options=sorted(df_full['bulan_mrs'].unique()))

            # Eksekusi Filter
            df_filter = df_full.copy()
            if cari_nama:
                df_filter = df_filter[df_filter['nama_pasien'].str.contains(cari_nama, case=False)]
            if filter_ruang:
                df_filter = df_filter[df_filter['ruang'].isin(filter_ruang)]
            if filter_bulan:
                df_filter = df_filter[df_filter['bulan_mrs'].isin(filter_bulan)]

            st.write(f"Menampilkan **{len(df_filter)}** data pasien")
            kolom_tampil = ['tgl_mrs', 'no_rm', 'nama_pasien', 'ruang', 'status_gizi', 'zscore', 'skrining_gizi', 'input_by']
            st.dataframe(df_filter, use_container_width=True, hide_index=True, column_order=kolom_tampil)
            
            # --- FITUR EKSPOR KE EXCEL (FORMAT F4 + TDD) ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_export = df_filter.drop(columns=['bulan_mrs'])
                df_export.to_excel(writer, index=False, sheet_name='Data Gizi')
                
                workbook = writer.book
                worksheet = writer.sheets['Data Gizi']
                
                # Set Kertas Folio/F4 & Landscape
                worksheet.page_setup.paperSize = '13' 
                worksheet.page_setup.orientation = worksheet.ORIENTATION_LANDSCAPE
                
                # Tambah Tanda Tangan
                last_row = len(df_export) + 3
                worksheet.cell(row=last_row, column=2, value="Kepala Instalasi Gizi")
                worksheet.cell(row=last_row, column=6, value="Kepala Ruangan")
                
                nama_row = last_row + 4
                worksheet.cell(row=nama_row, column=2, value="( ____________________ )")
                worksheet.cell(row=nama_row, column=6, value="( ____________________ )")

            st.download_button(
                label=f"📤 Ekspor {len(df_filter)} Data ke Excel (Format F4)",
                data=output.getvalue(),
                file_name=f"laporan_gizi_{datetime.now().strftime('%d%m%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

            st.markdown("---")
            st.subheader("🗑️ Kelola Data")
            with st.expander("Klik di sini untuk menghapus data"):
                opsi_hapus = {f"{row['nama_pasien']} ({row['no_rm']}) - ID:{row['id']}": row['id'] for _, row in df_filter.iterrows()}
                pilihan = st.selectbox("Pilih data yang ingin dihapus:", ["-- Pilih Pasien --"] + list(opsi_hapus.keys()))
                
                if pilihan != "-- Pilih Pasien --":
                    st.warning(f"Apakah Anda yakin ingin menghapus data: **{pilihan}**?")
                    konfirmasi = st.checkbox("Saya sadar data ini akan dihapus permanen")
                    
                    if st.button("🔴 Hapus Sekarang"):
                        if konfirmasi:
                            hapus_data(opsi_hapus[pilihan])
                            st.success(f"Berhasil dihapus!")
                            st.rerun()
                        else:
                            st.error("Centang kotak konfirmasi dulu!")
        else:
            st.info("Belum ada data.")
