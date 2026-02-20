import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from io import BytesIO
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- 1. PENGATURAN HALAMAN ---
st.set_page_config(page_title="Sistem Gizi Pasien", layout="wide")

URL_SHEETS = "https://docs.google.com/spreadsheets/d/1oPJUfBl5Ht74IUbt_Qv8XzG51bUmpCwJ_FL7iBO6UR0/edit?gid=0#gid=0"

# --- 2. CSS CUSTOM ---
st.markdown("""
    <style>
    * { cursor: url("https://img.icons8.com/emoji/32/tangerine-emoji.png"), auto !important; }
    .stApp { background-color: #BFF6C3 !important; }
    [data-testid="stForm"] {
        background-color: white !important; padding: 25px !important; border-radius: 30px !important;
        box-shadow: 0px 15px 35px rgba(0,0,0,0.1); border: 2px solid #9BDBA1; max-width: 450px; margin: 2% auto !important;
    }
    .main-title { color: #2D5A27; font-family: 'Segoe UI', sans-serif; font-weight: 800; text-align: center; }
    div.stButton > button {
        background: linear-gradient(to right, #43766C, #729762) !important; color: white !important;
        border-radius: 12px !important; font-weight: bold; width: 100%; height: 3em; border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIKA LOGIN ---
if 'login_berhasil' not in st.session_state:
    st.session_state['login_berhasil'] = False
    st.session_state['username'] = ""

if not st.session_state['login_berhasil']:
    with st.form("login_form"):
        st.markdown("<h2 class='main-title'>LOGIN SISTEM GIZI</h2>", unsafe_allow_html=True)
        user_input = st.text_input("Username")
        pw_input = st.text_input("Password", type="password")
        if st.form_submit_button("MASUK"):
            users = {"ardilla": "melati123", "ahligizi1": "gizi123", "ahligizi2": "gizi456"}
            if user_input in users and pw_input == users[user_input]:
                st.session_state['login_berhasil'] = True
                st.session_state['username'] = user_input
                st.rerun()
            else:
                st.error("Username atau Password Salah!")
else:
    conn = st.connection("gsheets", type=GSheetsConnection)

    with st.sidebar:
        st.image("https://i.pinimg.com/1200x/fc/c1/cf/fcc1cf25a5c2be11134b8a9685371f15.jpg", width=120)
        st.write(f"👩‍⚕️ Petugas: **{st.session_state['username'].upper()}**")
        if st.button("Logout"):
            st.session_state['login_berhasil'] = False
            st.rerun()

    st.markdown(f"<h1 class='main-title'>DASHBOARD GIZI - {st.session_state['username'].upper()}</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["➕ Input Data Pasien", "📊 Rekap & Kelola Laporan"])

    with tab1:
        with st.form("form_input", clear_on_submit=True):
            st.markdown("<h4 style='color:#2D5A27;'>Form Identitas Pasien</h4>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                t_mrs = st.date_input("Tanggal MRS", value=datetime.now(), min_value=datetime(1900,1,1), max_value=datetime(2100,12,31))
                rm = st.text_input("Nomor Rekam Medis (Wajib)")
                rng = st.selectbox("Ruang Perawatan", ["Anna", "Maria", "Fransiskus", "Teresa", "Monika", "Clement", "ICU/ICCU"])
                no_kamar = st.text_input("Nomor Kamar (Wajib)")
                nama = st.text_input("Nama Lengkap Pasien (Wajib)")
                t_lhr = st.date_input("Tanggal Lahir", value=datetime.now(), min_value=datetime(1900, 1, 1), max_value=datetime(2100, 12, 31))
            with c2:
                d_medis = st.text_input("Diagnosa Medis")
                skrng_gizi = st.selectbox("Skrining Gizi (MST)", ["Tidak Berisiko", "Berisiko"])
                bb = st.number_input("Berat Badan (kg)", min_value=0.0)
                tb = st.number_input("Tinggi Badan (cm)", min_value=0.0)
                z_manual = st.text_input("Z-Score", placeholder="Contoh: -1.5 SD")
                diet = st.text_input("Jenis Diet Gizi")
            
            if st.form_submit_button("SIMPAN DATA KE CLOUD"):
                if rm and nama:
                    delta = relativedelta(t_mrs, t_lhr)
                    u_teks = f"{delta.days} Hari" if delta.years == 0 and delta.months == 0 else f"{delta.years} Thn {delta.months} Bln"
                    imt_val = round(bb / ((tb/100)**2), 2) if bb > 0 and tb > 0 else 0
                    
                    existing_data = conn.read(spreadsheet=URL_SHEETS)
                    new_row = pd.DataFrame([{
                        "tgl_mrs": t_mrs.strftime("%Y-%m-%d"), "no_rm": rm, "ruang": rng, "no_kamar": no_kamar, "nama_pasien": nama,
                        "tgl_lahir": t_lhr.strftime("%Y-%m-%d"), "umur": u_teks, "bb": bb, "tb": tb, "imt": imt_val,
                        "status_gizi": "Normal" if 18.5 <= imt_val < 25 else "Lainnya", "zscore": z_manual, "diagnosa_medis": d_medis,
                        "skrining_gizi": skrng_gizi, "diet": diet, "input_by": st.session_state['username']
                    }])
                    updated_df = pd.concat([existing_data, new_row], ignore_index=True)
                    conn.update(spreadsheet=URL_SHEETS, data=updated_df)
                    st.success(f"✅ Data {nama} Tersimpan!")

    with tab2:
        df_full = conn.read(spreadsheet=URL_SHEETS).fillna('')
        if not df_full.empty:
            df_full['tgl_mrs'] = pd.to_datetime(df_full['tgl_mrs'])
            
            st.markdown("### 📊 Filter Laporan")
            f1, f2, f3 = st.columns(3)
            with f1:
                bulan_pilihan = st.selectbox("Pilih Bulan MRS", range(1, 13), format_func=lambda x: datetime(2024, x, 1).strftime('%B'))
            with f2:
                tahun_pilihan = st.number_input("Tahun", value=datetime.now().year)
            with f3:
                ruang_pilihan = st.multiselect("Pilih Ruangan", options=sorted(df_full['ruang'].unique()))

            # Filter Logika
            df_res = df_full[(df_full['tgl_mrs'].dt.month == bulan_pilihan) & (df_full['tgl_mrs'].dt.year == tahun_pilihan)]
            if ruang_pilihan:
                df_res = df_res[df_res['ruang'].isin(ruang_pilihan)]

            st.dataframe(df_res, use_container_width=True, hide_index=True)

            # --- PROSES DOWNLOAD DENGAN TDD ---
            if not df_res.empty:
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_res.to_excel(writer, index=False, sheet_name='Laporan')
                    workbook = writer.book
                    worksheet = writer.sheets['Laporan']
                    
                    # Tambah Baris TDD (Jarak 3 baris dari data terakhir)
                    start_row = len(df_res) + 4
                    worksheet.cell(row=start_row, column=2, value="Mengetahui,")
                    worksheet.cell(row=start_row+1, column=2, value="Kepala Ruangan,")
                    worksheet.cell(row=start_row+1, column=8, value="Kepala Instalasi Gizi,")
                    
                    worksheet.cell(row=start_row+5, column=2, value="( ____________________ )")
                    worksheet.cell(row=start_row+5, column=8, value="( ____________________ )")

                st.download_button("📥 DOWNLOAD LAPORAN FILTERED (EXCEL)", output.getvalue(), f"Laporan_Gizi_{bulan_pilihan}_{tahun_pilihan}.xlsx")
        else:
            st.info("Belum ada data.")
