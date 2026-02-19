import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO
from datetime import datetime
from dateutil.relativedelta import relativedelta
from fpdf import FPDF

# --- 1. PENGATURAN HALAMAN & TEMA SAGE GREEN ---
st.set_page_config(page_title="Sistem Gizi Pasien", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    /* Warna Background Utama Sage Green */
    .stApp {
        background-color: #B2D3C2; 
    }
    /* Container Putih Bersih */
    .stForm, .login-box, .stTabs {
        background-color: #F9FBF9 !important;
        padding: 30px !important;
        border-radius: 20px !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08) !important;
    }
    .main-title {
        color: #2D5A27;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 20px;
    }
    /* Tombol Hijau Tua Solid */
    div.stButton > button:first-child {
        background-color: #2D5A27 !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIKA LOGIN ---
if 'login_berhasil' not in st.session_state:
    st.session_state['login_berhasil'] = False

if not st.session_state['login_berhasil']:
    col_img, col_form = st.columns([1.3, 1], gap="large")
    with col_img:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Gambar Buah/Sayur Segar di Login
        st.image("https://images.unsplash.com/photo-1490818387583-1baba5e638af?q=80&w=1000&auto=format&fit=crop", use_container_width=True)
        
    with col_form:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<h2 style='color: #2D5A27;'>🌿 Login Sistem Gizi</h2>", unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            if st.button("Masuk Sekarang", use_container_width=True):
                if user == "ahligizi" and pw == "admin123":
                    st.session_state['login_berhasil'] = True
                    st.rerun()
                else:
                    st.error("Akses Ditolak!")
            st.markdown('</div>', unsafe_allow_html=True)
else:
    # --- 3. DATABASE ---
    def init_db():
        conn = sqlite3.connect('gizi_rs.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS pasien (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            tgl_mrs TEXT, no_rm TEXT, ruang TEXT, no_kamar TEXT, 
            nama_pasien TEXT, tgl_lahir TEXT, umur TEXT, 
            diagnosis_medis TEXT, skrining_gizi TEXT, diet TEXT)''')
        conn.commit()
        conn.close()

    def ambil_data_db():
        conn = sqlite3.connect('gizi_rs.db')
        df = pd.read_sql_query("SELECT * FROM pasien ORDER BY tgl_mrs DESC", conn)
        conn.close()
        return df

    init_db()

    # --- 4. TAMPILAN UTAMA ---
    st.markdown("<h1 class='main-title'>🥗 Dashboard Manajemen Gizi</h1>", unsafe_allow_html=True)
    
    with st.sidebar:
        st.image("https://images.unsplash.com/photo-1610832958506-aa56368176cf?q=80&w=1000&auto=format&fit=crop", use_container_width=True)
        st.markdown("---")
        ka_gizi = st.text_input("Kepala Instalasi Gizi", "Nama, S.Gz")
        ka_ruang = st.text_input("Kepala Ruangan", "Nama, S.Kep")
        if st.button("🚪 Logout"):
            st.session_state['login_berhasil'] = False
            st.rerun()

    tab1, tab2 = st.tabs(["🍏 Pendaftaran Pasien", "📋 Rekapitulasi Data"])

    with tab1:
        with st.form("form_input", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                # Tanggal MRS juga dibuka sampai tahun 2100
                t_mrs = st.date_input("Tanggal MRS", 
                                      value=datetime.now(),
                                      min_value=datetime(1900, 1, 1),
                                      max_value=datetime(2100, 12, 31))
                rm = st.text_input("Nomor Rekam Medis (RM)")
                rng = st.selectbox("Ruangan", ["Anna", "Maria", "Fransiskus", "Teresa", "Monika", "Clement", "ICU/ICCU"])
                kmr = st.text_input("Nomor Kamar")
            with c2:
                nama = st.text_input("Nama Lengkap Pasien")
                
                # --- PERBAIKAN TAHUN DISINI ---
                # Sekarang bisa pilih tahun dari 1900 sampai 2100
                t_lhr = st.date_input(
                    "Tanggal Lahir", 
                    value=datetime(2000, 1, 1),
                    min_value=datetime(1900, 1, 1),
                    max_value=datetime(2100, 12, 31)
                )
                
                skrining = st.selectbox("Skrining Gizi", ["Risiko Rendah", "Risiko Sedang", "Risiko Tinggi"])
                diet_p = st.text_input("Jenis Diet Pasien")
            
            diag = st.text_area("Diagnosis Medis")
            
            if st.form_submit_button("✅ Simpan ke Database"):
                if rm and nama:
                    # Hitung Umur Otomatis
                    diff = relativedelta(t_mrs, t_lhr)
                    u_teks = f"{diff.years} Thn {diff.months} Bln"
                    
                    conn = sqlite3.connect('gizi_rs.db')
                    c = conn.cursor()
                    c.execute('''INSERT INTO pasien 
                        (tgl_mrs, no_rm, ruang, no_kamar, nama_pasien, tgl_lahir, umur, diagnosis_medis, skrining_gizi, diet) 
                        VALUES (?,?,?,?,?,?,?,?,?,?)''', 
                        (t_mrs.strftime("%Y-%m-%d"), rm, rng, kmr, nama, t_lhr.strftime("%Y-%m-%d"), u_teks, diag, skrining, diet_p))
                    conn.commit()
                    conn.close()
                    st.success(f"Data {nama} Berhasil Disimpan!")
                    st.rerun()

    with tab2:
        df = ambil_data_db()
        if not df.empty:
            kolom = ['tgl_mrs', 'no_rm', 'ruang', 'no_kamar', 'nama_pasien', 'tgl_lahir', 'umur', 'diagnosis_medis', 'skrining_gizi', 'diet']
            st.dataframe(df[kolom], use_container_width=True, hide_index=True)
            
            # Ekspor Ke Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df[kolom].to_excel(writer, index=False)
            st.download_button("📊 Download Rekap (Excel)", output.getvalue(), "rekap_gizi_lengkap.xlsx")
        else:
            st.info("Belum ada data pasien yang terdaftar.")