import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from io import BytesIO
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- 1. PENGATURAN HALAMAN ---
st.set_page_config(page_title="Sistem Gizi Pasien - Ardilla", layout="wide")

# URL Google Sheet kamu
URL_SHEETS = "https://docs.google.com/spreadsheets/d/1oPJUfBl5Ht74IUbt_Qv8XzG51bUmpCwJ_FL7iBO6UR0/edit"

# --- 2. CSS CUSTOM (Tema Hijau Oranye) ---
st.markdown("""
    <style>
    * { cursor: url("https://img.icons8.com/emoji/32/tangerine-emoji.png"), auto !important; }
    .stApp { background-color: #BFF6C3 !important; }
    [data-testid="stForm"] {
        background-color: white !important; padding: 25px !important; border-radius: 30px !important;
        box-shadow: 0px 15px 35px rgba(0,0,0,0.1); border: 2px solid #9BDBA1; max-width: 550px; margin: 2% auto !important;
    }
    .main-title { color: #2D5A27; font-family: 'Segoe UI', sans-serif; font-weight: 800; text-align: center; }
    div.stButton > button {
        background: linear-gradient(to right, #43766C, #729762) !important; color: white !important;
        border-radius: 12px !important; font-weight: bold; width: 100%; height: 3em; border: none !important;
    }
    .metric-box {
        background-color: white; padding: 15px; border-radius: 15px; text-align: center;
        border: 2px solid #9BDBA1; margin-bottom: 20px; color: #2D5A27;
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
        st.markdown("<h2 class='main-title'>LOGIN SISTEM GIZI</h2>", unsafe_allow_html=True)
        user_input = st.text_input("Username")
        pw_input = st.text_input("Password", type="password")
        if st.form_submit_button("MASUK"):
            users = {"ardilla": "melati123", "ahligizi1": "gizi123"}
            if user_input in users and pw_input == users[user_input]:
                st.session_state['login_berhasil'] = True
                st.session_state['username'] = user_input
                st.rerun()
            else:
                st.error("Username atau Password Salah!")
else:
    # --- 4. KONEKSI DATA ---
    conn = st.connection("gsheets", type=GSheetsConnection)
    list_ruang = ["Anna", "Maria", "Fransiskus", "Teresa", "Monika", "Clement", "ICU/ICCU"]

    with st.sidebar:
        st.image("https://i.pinimg.com/1200x/fc/c1/cf/fcc1cf25a5c2be11134b8a9685371f15.jpg", width=120)
        st.write(f"👩‍⚕️ Petugas: **{st.session_state['username'].upper()}**")
        if st.button("Logout"):
            st.session_state['login_berhasil'] = False
            st.rerun()

    st.markdown(f"<h1 class='main-title'>Manajemen Bangsal - {st.session_state['username'].upper()}</h1>", unsafe_allow_html=True)
    
    tab1, tab_ncp, tab2, tab_rekap_ncp = st.tabs(["➕ Identitas", "📝 Data Klinis", "📊 Rekap Identitas", "📜 Rekap Klinis"])

    # Load Database
    df_identitas = conn.read(spreadsheet=URL_SHEETS, worksheet="Sheet1", ttl=0).fillna('')
    df_ncp = conn.read(spreadsheet=URL_SHEETS, worksheet="NCP", ttl=0).fillna('')

    # --- TAB 1: INPUT IDENTITAS & ANTROPOMETRI ---
    with tab1:
        with st.form("form_identitas", clear_on_submit=True):
            st.markdown("<h4 style='color:#2D5A27;'>Form Identitas & Skrining</h4>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                t_mrs = st.date_input("Tanggal MRS", value=datetime.now())
                rm = st.text_input("Nomor Rekam Medis (Wajib)")
                nama = st.text_input("Nama Lengkap Pasien (Wajib)")
                t_lhr = st.date_input("Tanggal Lahir", value=datetime.now())
            with c2:
                rng = st.selectbox("Ruang Perawatan", list_ruang)
                no_kamar = st.text_input("Nomor Kamar (Wajib)")
                d_medis = st.text_input("Diagnosa Medis")
                skrining_gizi = st.selectbox("Hasil Skrining Gizi", ["Berisiko", "Tidak Berisiko"])
                diet = st.text_input("Jenis Diet Gizi")

            st.markdown("---")
            st.markdown("<h5 style='color:#2D5A27;'>Antropometri</h5>", unsafe_allow_html=True)
            ca1, ca2, ca3, ca4 = st.columns(4)
            with ca1: bb = st.number_input("BB (kg)", min_value=0.0, step=0.1)
            with ca2: tb = st.number_input("TB (cm)", min_value=0.0, step=0.1)
            with ca3: lila = st.number_input("LILA (cm)", min_value=0.0, step=0.1)
            with ca4: ulna = st.number_input("ULNA (cm)", min_value=0.0, step=0.1)
            
            z_score = st.text_input("Z-Score (Khusus Anak)")
            
            if st.form_submit_button("SIMPAN DATA IDENTITAS"):
                if rm and nama:
                    # LOGIKA UMUR: Anak (Thn & Bln), Dewasa (Thn saja)
                    delta = relativedelta(t_mrs, t_lhr)
                    if delta.years >= 19:
                        u_teks = f"{delta.years} Thn"
                    else:
                        u_teks = f"{delta.years} Thn {delta.months} Bln"
                    
                    imt_val = round(bb / ((tb/100)**2), 2) if bb > 0 and tb > 0 else 0
                    next_no = len(df_identitas) + 1
                    
                    new_row = pd.DataFrame([{
                        "no": next_no, "tgl_mrs": t_mrs.strftime("%Y-%m-%d"), "no_rm": rm, 
                        "ruang": rng, "no_kamar": str(no_kamar), "nama_pasien": nama, 
                        "umur": u_teks, "bb": bb, "tb": tb, "lila": lila, "ulna": ulna, 
                        "zscore": z_score, "imt": imt_val, "diagnosa_medis": d_medis, 
                        "skrining": skrining_gizi, "diet": diet, "input_by": st.session_state['username']
                    }])
                    updated_df = pd.concat([df_identitas, new_row], ignore_index=True)
                    conn.update(spreadsheet=URL_SHEETS, worksheet="Sheet1", data=updated_df)
                    st.success(f"✅ Data {nama} Berhasil Disimpan!"); st.cache_data.clear(); st.rerun()

    # --- TAB 2: DATA KLINIS / NCP (URUTAN A-K) ---
    with tab_ncp:
        st.markdown("<h4 style='color:#2D5A27;'>Input Data Klinis & Penunjang</h4>", unsafe_allow_html=True)
        if not df_identitas.empty:
            nama_pilih = st.selectbox("Pilih Pasien Dari Database:", options=df_identitas['nama_pasien'].tolist())
            row = df_identitas[df_identitas['nama_pasien'] == nama_pilih].iloc[0]
            
            with st.form("form_klinis"):
                st.info(f"📌 Pasien: {row['nama_pasien']} | RM: {row['no_rm']}")
                bio = st.text_area("Biokimia (Hasil Lab/Hasil Biokimia)")
                penunjang = st.text_area("Penunjang Lainnya")
                fk = st.text_area("Fisik / Klinis (F/K)")
                
                if st.form_submit_button("SIMPAN DATA KLINIS"):
                    next_no_ncp = len(df_ncp) + 1
                    new_ncp = pd.DataFrame([{
                        "no": next_no_ncp,                               # A
                        "tgl_input": datetime.now().strftime("%Y-%m-%d"),# B
                        "no_rm": row['no_rm'],                           # C
                        "ruang": row['ruang'],                           # D
                        "no_kamar": row['no_kamar'],                     # E
                        "nama_pasien": row['nama_pasien'],               # F
                        "diagnosa_medis": row['diagnosa_medis'],        # G
                        "biokimia": bio,                                 # H
                        "penunjang_lainnya": penunjang,                  # I
                        "fisik_klinis": fk,                              # J
                        "diet": row['diet']                              # K
                    }])
                    updated_ncp = pd.concat([df_ncp, new_ncp], ignore_index=True)
                    conn.update(spreadsheet=URL_SHEETS, worksheet="NCP", data=updated_ncp)
                    st.success(f"✅ Catatan Klinis baris #{next_no_ncp} Tersimpan!"); st.cache_data.clear(); st.rerun()
        else:
            st.warning("Silakan isi Tab Identitas terlebih dahulu.")

    # --- TAB 3: REKAP IDENTITAS (TAHUN 1900-2100) ---
    with tab2:
        st.markdown(f"<div class='metric-box'>📊 Database Pasien: <b>{len(df_identitas)}</b></div>", unsafe_allow_html=True)
        if not df_identitas.empty:
            df_identitas['tgl_mrs'] = pd.to_datetime(df_identitas['tgl_mrs'], errors='coerce')
            
            # Rentang Tahun 1900 - 2100
            tahun_skrg = datetime.now().year
            list_tahun = list(range(1900, 2101))
            
            f1, f2, f3 = st.columns(3)
            with f1: bul_p = st.selectbox("Filter Bulan", range(1, 13), index=datetime.now().month-1, format_func=lambda x: datetime(tahun_skrg, x, 1).strftime('%B'))
            with f2: tah_p = st.selectbox("Filter Tahun", list_tahun, index=list_tahun.index(tahun_skrg))
            with f3: rng_p = st.multiselect("Filter Ruangan", options=list_ruang, default=list_ruang)

            mask = (df_identitas['tgl_mrs'].dt.month == bul_p) & (df_identitas['tgl_mrs'].dt.year == tah_p) & (df_identitas['ruang'].isin(rng_p))
            df_filtered = df_identitas[mask].copy()

            st.dataframe(df_filtered, use_container_width=True, hide_index=True)
            
            # Download Excel Identitas
            out_id = BytesIO()
            with pd.ExcelWriter(out_id, engine='openpyxl') as writer:
                df_filtered.to_excel(writer, index=False, sheet_name='Identitas')
            st.download_button("📥 DOWNLOAD REKAP IDENTITAS", data=out_id.getvalue(), file_name=f"Rekap_Identitas_{bul_p}_{tah_p}.xlsx")
            
            st.divider()
            with st.expander("🗑️ Menu Hapus Data"):
                no_hapus = st.number_input("Masukkan No Urut yang ingin dihapus:", min_value=1, step=1)
                if st.button("KONFIRMASI HAPUS"):
                    df_new = df_identitas[df_identitas['no'] != no_hapus]
                    df_new['no'] = range(1, len(df_new) + 1) # Reset nomor urut
                    conn.update(spreadsheet=URL_SHEETS, worksheet="Sheet1", data=df_new)
                    st.success("Data telah dihapus."); st.cache_data.clear(); st.rerun()

    # --- TAB 4: REKAP KLINIS (URUTAN A-K) ---
    with tab_rekap_ncp:
        st.markdown(f"<div class='metric-box'>📜 Total Seluruh Catatan Klinis: <b>{len(df_ncp)}</b></div>", unsafe_allow_html=True)
        if not df_ncp.empty:
            st.dataframe(df_ncp, use_container_width=True, hide_index=True)
            
            # Download Excel NCP
            out_kl = BytesIO()
            with pd.ExcelWriter(out_kl, engine='openpyxl') as writer:
                df_ncp.to_excel(writer, index=False, sheet_name='Data_Klinis_NCP')
            st.download_button("📥 DOWNLOAD REKAP KLINIS NCP", data=out_kl.getvalue(), file_name="Rekap_Klinis_NCP.xlsx")
        else:
            st.info("Belum ada data klinis yang tersimpan.")
