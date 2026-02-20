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
    .stForm, .stTabs { 
        background-color: #F9FBF9 !important; 
        padding: 20px !important; 
        border-radius: 15px !important;
    }
    .main-title { color: #2D5A27; font-weight: 700; text-align: center; }
    div.stButton > button {
        background-color: #2D5A27 !important;
        color: white !important;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIKA LOGIN & USER ---
if 'login_berhasil' not in st.session_state:
    st.session_state['login_berhasil'] = False
    st.session_state['username'] = ""

if not st.session_state['login_berhasil']:
    st.markdown("<h2 class='main-title'>🌿 Login Sistem Gizi</h2>", unsafe_allow_html=True)
    with st.form("login_form"):
        user_input = st.text_input("Username")
        pw_input = st.text_input("Password", type="password")
        if st.form_submit_button("Masuk"):
            users = {
                "ardilla": "dilla123",
                "ahligizi1": "gizi123",
                "ahligizi2": "gizi456"
            }
            if user_input in users and pw_input == users[user_input]:
                st.session_state['login_berhasil'] = True
                st.session_state['username'] = user_input
                st.rerun()
            else:
                st.error("Username atau Password Salah!")
else:
    # --- 3. DATABASE ---
    def init_db():
        conn = sqlite3.connect('gizi_rs_v2.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS pasien (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            tgl_mrs TEXT, no_rm TEXT, ruang TEXT, nama_pasien TEXT, 
            tgl_lahir TEXT, umur TEXT, bb REAL, tb REAL, imt REAL, 
            status_gizi TEXT, diagnosa_medis TEXT, skrining_gizi TEXT, diet TEXT, input_by TEXT)''')
        conn.commit()
        conn.close()

    def ambil_data_db(user):
        conn = sqlite3.connect('gizi_rs_v2.db')
        if user == "ardilla":
            query = "SELECT * FROM pasien ORDER BY tgl_mrs DESC"
        else:
            query = f"SELECT * FROM pasien WHERE input_by = '{user}' ORDER BY tgl_mrs DESC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    init_db()

    with st.sidebar:
        st.write(f"👤 Login sebagai: **{st.session_state['username']}**")
        if st.button("🚪 Logout"):
            st.session_state['login_berhasil'] = False
            st.rerun()

    st.markdown(f"<h1 class='main-title'>Dashboard Manajemen Bangsal - {st.session_state['username'].upper()}</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🍏 Input Data", "📋 Rekap Data"])

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
                skrng_gizi = st.selectbox("Risiko", ["Berisiko", "Tidak Berisiko"])
                bb = st.number_input("Berat Badan (kg)", min_value=0.0)
                tb = st.number_input("Tinggi Badan (cm)", min_value=0.0)
                diet = st.text_input("Jenis Diet")
            
            if st.form_submit_button("Simpan Data"):
                if rm and nama:
                    u_teks = f"{relativedelta(t_mrs, t_lhr).years} Thn"
                    imt_val = round(bb / ((tb/100)**2), 2) if bb > 0 and tb > 0 else 0
                    
                    # LOGIKA STATUS GIZI (SUDAH DIRAPIKAN)
                    if imt_val == 0:
                        st_gizi = "Belum Dihitung"
                    elif imt_val > 27: 
                        st_gizi = "Obesitas"
                    elif imt_val >= 25: 
                        st_gizi = "Overweight"
                    elif imt_val < 18.5: 
                        st_gizi = "Kurus"
                    else:
                        st_gizi = "Normal"

                    conn = sqlite3.connect('gizi_rs_v2.db')
                    c = conn.cursor()
                    c.execute('''INSERT INTO pasien 
                        (tgl_mrs, no_rm, ruang, nama_pasien, tgl_lahir, umur, bb, tb, imt, status_gizi, diagnosa_medis, skrining_gizi, diet, input_by) 
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                        (t_mrs.strftime("%Y-%m-%d"), rm, rng, nama, t_lhr.strftime("%Y-%m-%d"), 
                         u_teks, bb, tb, imt_val, st_gizi, d_medis, skrng_gizi, diet, st.session_state['username']))
                    conn.commit()
                    conn.close()
                    st.success(f"Data {nama} Berhasil Disimpan!")
                    st.rerun()
                else:
                    st.warning("Mohon isi Nama dan No. RM!")

    with tab2:
        df = ambil_data_db(st.session_state['username'])
        if not df.empty:
            st.subheader("📋 Rekapitulasi Data Pasien")
            kolom_ringkas = ['tgl_mrs', 'no_rm', 'nama_pasien', 'status_gizi', 'skrining_gizi', 'input_by']
            st.dataframe(df, use_container_width=True, hide_index=True, column_order=kolom_ringkas)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            
            st.markdown("---")
            st.download_button(
                label="📊 Download Laporan Lengkap (Excel)",
                data=output.getvalue(),
                file_name=f"rekap_gizi_{st.session_state['username']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.info("Belum ada data pasien.")
