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
    .stApp { background-color: #BFF6C3 !important; cursor: url("https://img.icons8.com/emoji/32/tangerine-emoji.png"), auto !important; }
    button, input, select, textarea, a, [data-baseweb="tab"], [data-testid="stHeader"] {
        cursor: url("https://img.icons8.com/emoji/32/tangerine-emoji.png"), pointer !important;
    }
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
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.form("login_form"):
        st.markdown("<h2 class='main-title'>LOGIN</h2>", unsafe_allow_html=True)
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
    # --- 4. HALAMAN UTAMA ---
    conn = st.connection("gsheets", type=GSheetsConnection)

    with st.sidebar:
        st.image("https://i.pinimg.com/1200x/fc/c1/cf/fcc1cf25a5c2be11134b8a9685371f15.jpg", width=120)
        st.write(f"👩‍⚕️ Petugas: **{st.session_state['username'].upper()}**")
        if st.button("Logout"):
            st.session_state['login_berhasil'] = False
            st.rerun()

    st.markdown(f"<h1 class='main-title'>DASHBOARD Manajemen Bangsal- {st.session_state['username'].upper()}</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["➕ Input Data Pasien", "📊 Rekap & Kelola Laporan"])

    with tab1:
        with st.form("form_input", clear_on_submit=True):
            st.markdown("<h4 style='color:#2D5A27;'>Form Identitas Pasien</h4>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                # Tanggal MRS dibuat rentang panjang sampai 2100
                t_mrs = st.date_input("Tanggal MRS", value=datetime.now(), min_value=datetime(1900,1,1), max_value=datetime(2100,12,31))
                rm = st.text_input("Nomor Rekam Medis (Wajib)")
                nama = st.text_input("Nama Lengkap Pasien (Wajib)")
                
                # TANGGAL LAHIR RENTANG PANJANG (1900 - 2100)
                t_lhr = st.date_input(
                    "Tanggal Lahir", 
                    value=datetime.now(), 
                    min_value=datetime(1900, 1, 1), 
                    max_value=datetime(2100, 12, 31)
                )
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
                    delta = relativedelta(t_mrs, t_lhr)
                    
                    # Logika Umur (Detail Hari untuk bayi baru lahir)
                    if delta.years < 19:
                        if delta.years == 0 and delta.months == 0:
                            u_teks = f"{delta.days} Hari"
                        else:
                            u_teks = f"{delta.years} Thn {delta.months} Bln"
                    else:
                        u_teks = f"{delta.years} Thn"
                    
                    # Hitung IMT
                    imt_val = round(bb / ((tb/100)**2), 2) if bb > 0 and tb > 0 else 0
                    if imt_val >= 27: st_gizi = "Obesitas"
                    elif 25 <= imt_val < 27: st_gizi = "Overweight"
                    elif 18.5 <= imt_val < 25: st_gizi = "Normal"
                    elif 0 < imt_val < 18.5: st_gizi = "Kurus"
                    else: st_gizi = "Data Tidak Lengkap"

                    existing_data = conn.read(spreadsheet=URL_SHEETS)
                    new_row = pd.DataFrame([{
                        "tgl_mrs": t_mrs.strftime("%Y-%m-%d"), "no_rm": rm, "ruang": rng, "nama_pasien": nama,
                        "tgl_lahir": t_lhr.strftime("%Y-%m-%d"), "umur": u_teks, "bb": bb, "tb": tb, 
                        "imt": imt_val, "status_gizi": st_gizi, "zscore": z_manual, "diagnosa_medis": d_medis,
                        "skrining_gizi": skrng_gizi, "diet": diet, "input_by": st.session_state['username']
                    }])
                    updated_df = pd.concat([existing_data, new_row], ignore_index=True)
                    conn.update(spreadsheet=URL_SHEETS, data=updated_df)
                    st.success(f"✅ Tersimpan! {nama} ({u_teks})")
                else:
                    st.warning("⚠️ Isi Nama dan No. RM!")

    with tab2:
        df_full = conn.read(spreadsheet=URL_SHEETS).fillna('')
        if not df_full.empty:
            if st.session_state['username'] != "ardilla":
                df_full = df_full[df_full['input_by'] == st.session_state['username']]

            st.markdown("### 📊 Pencarian & Kelola Data")
            f1, f2 = st.columns(2)
            with f1: cari = st.text_input("🔎 Cari Nama Pasien")
            with f2:
                opsi_ruang = sorted(df_full['ruang'].unique())
                ruang_f = st.multiselect("🏥 Filter Ruang", options=opsi_ruang)

            df_filter = df_full.copy()
            if cari: df_filter = df_filter[df_filter['nama_pasien'].str.contains(cari, case=False)]
            if ruang_f: df_filter = df_filter[df_filter['ruang'].isin(ruang_f)]

            with st.expander("🗑️ Hapus Data"):
                list_pasien = df_filter.apply(lambda x: f"{x['no_rm']} - {x['nama_pasien']}", axis=1).tolist()
                pilihan_hapus = st.selectbox("Pilih pasien:", ["-- Pilih --"] + list_pasien)
                if st.button("❌ Hapus Permanen"):
                    if pilihan_hapus != "-- Pilih --":
                        rm_to_delete = pilihan_hapus.split(" - ")[0]
                        updated_df = df_full[df_full['no_rm'] != rm_to_delete]
                        conn.update(spreadsheet=URL_SHEETS, data=updated_df)
                        st.success("Terhapus!")
                        st.rerun()

            st.write("---")
            
            def color_status(val):
                if val == 'Obesitas': return 'background-color: #FF7676; color: white; font-weight: bold;'
                elif val == 'Overweight': return 'background-color: #FFD966; color: black;'
                elif val == 'Normal': return 'background-color: #A9D18E; color: black;'
                elif val == 'Kurus': return 'background-color: #9BCFE0; color: black;'
                return ''

            st.dataframe(df_filter.style.map(color_status, subset=['status_gizi']), use_container_width=True, hide_index=True)

            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_filter.to_excel(writer, index=False, sheet_name='Laporan_Gizi')
            st.download_button(label="📥 DOWNLOAD EXCEL", data=output.getvalue(), 
                               file_name=f"Laporan_Gizi_{datetime.now().strftime('%d%m%Y')}.xlsx")
        else:
            st.info("💡 Belum ada data.")

