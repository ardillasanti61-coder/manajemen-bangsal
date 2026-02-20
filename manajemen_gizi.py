import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from io import BytesIO
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- 1. PENGATURAN HALAMAN ---
st.set_page_config(page_title="Sistem Gizi Pasien", layout="wide")

# GANTI INI dengan link Google Sheets kamu!
URL_SHEETS = "https://docs.google.com/spreadsheets/d/1oPJUfBl5Ht74IUbt_Qv8XzG51bUmpCwJ_FL7iBO6UR0/edit?gid=0#gid=0"

# CSS untuk tampilan
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f1f8e9 0%, #dcedc8 100%); }
    [data-testid="stForm"] {
        background-color: white !important;
        padding: 40px !important;
        border-radius: 25px !important;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.1);
        border: 1px solid #a5d6a7;
    }
    .main-title { color: #2e7d32; font-family: 'Segoe UI'; font-weight: 800; }
    div.stButton > button {
        background: linear-gradient(to right, #2e7d32, #66bb6a) !important;
        color: white !important;
        border-radius: 15px !important;
        font-weight: bold; width: 100%; height: 3em;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIKA LOGIN ---
if 'login_berhasil' not in st.session_state:
    st.session_state['login_berhasil'] = False
    st.session_state['username'] = ""

if not st.session_state['login_berhasil']:
    st.write("##")
    col_img, col_space, col_login = st.columns([1.5, 0.2, 1])
    with col_img:
        st.image("https://images.unsplash.com/photo-1490818387583-1baba5e638af?w=800", use_container_width=True)
        st.markdown("<h1 class='main-title'>🥗 SISTEM GIZI PASIEN</h1>", unsafe_allow_html=True)
    with col_login:
        with st.form("login_form"):
            st.markdown("<h2 style='text-align:center; color:#2e7d32;'>Silakan Login</h2>", unsafe_allow_html=True)
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
    # --- 3. KONEKSI GOOGLE SHEETS ---
    conn = st.connection("gsheets", type=GSheetsConnection)

    # Sidebar
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3448/3448621.png", width=80)
        st.write(f"👤 Petugas: **{st.session_state['username'].upper()}**")
        if st.button("🚪 Keluar Aplikasi"):
            st.session_state['login_berhasil'] = False
            st.rerun()

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
            
            if st.form_submit_button("SIMPAN DATA KE CLOUD"):
                if rm and nama:
                    # Logika perhitungan
                    u_teks = f"{relativedelta(t_mrs, t_lhr).years} Thn"
                    imt_val = round(bb / ((tb/100)**2), 2) if bb > 0 and tb > 0 else 0
                    if imt_val >= 27: st_gizi = "Obesitas"
                    elif imt_val >= 25: st_gizi = "Overweight"
                    elif imt_val >= 18.5: st_gizi = "Normal"
                    else: st_gizi = "Kurus"

                    # Ambil data lama dari Sheets
                    existing_data = conn.read(spreadsheet=URL_SHEETS)
                    
                    # Buat baris baru
                    new_row = pd.DataFrame([{
                        "tgl_mrs": t_mrs.strftime("%Y-%m-%d"),
                        "no_rm": rm, "ruang": rng, "nama_pasien": nama,
                        "tgl_lahir": t_lhr.strftime("%Y-%m-%d"), "umur": u_teks,
                        "bb": bb, "tb": tb, "imt": imt_val, "status_gizi": st_gizi,
                        "zscore": z_manual, "diagnosa_medis": d_medis,
                        "skrining_gizi": skrng_gizi, "diet": diet,
                        "input_by": st.session_state['username']
                    }])

                    # Update ke Sheets
                    updated_df = pd.concat([existing_data, new_row], ignore_index=True)
                    conn.update(spreadsheet=URL_SHEETS, data=updated_df)
                    
                    st.success(f"✅ Data {nama} berhasil diamankan di Google Sheets!")
                else:
                    st.warning("⚠️ Nama dan No. RM wajib diisi!")

    with tab2:
        df_full = conn.read(spreadsheet=URL_SHEETS)
        if not df_full.empty:
            if st.session_state['username'] != "ardilla":
                df_full = df_full[df_full['input_by'] == st.session_state['username']]

            # Filter
            f1, f2 = st.columns(2)
            with f1:
                cari = st.text_input("🔎 Cari Nama")
            with f2:
                ruang_f = st.multiselect("🏥 Filter Ruang", options=sorted(df_full['ruang'].unique()))

            df_filter = df_full.copy()
            if cari: df_filter = df_filter[df_filter['nama_pasien'].str.contains(cari, case=False)]
            if ruang_f: df_filter = df_filter[df_filter['ruang'].isin(ruang_f)]

            st.dataframe(df_filter, use_container_width=True, hide_index=True)

            # Ekspor Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_filter.to_excel(writer, index=False, sheet_name='Laporan')
            
            st.download_button(
                label="📤 EKSPOR KE EXCEL",
                data=output.getvalue(),
                file_name="Laporan_Gizi.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("Belum ada data di Google Sheets.")
