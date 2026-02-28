import streamlit as st
import pandas as pd
try:
    from st_gsheets_connection import GSheetsConnection
except ModuleNotFoundError:
    try:
        from streamlit_gsheets_connection import GSheetsConnection
    except ModuleNotFoundError:
        from streamlit_gsheets import GSheetsConnection

from io import BytesIO
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- 1. PENGATURAN HALAMAN ---
st.set_page_config(page_title="Gizi Bangsal Ardilla", page_icon="🍊", layout="wide")

# --- 2. CSS CUSTOM ---
st.markdown("""
    <style>
    * { cursor: url("https://img.icons8.com/emoji/32/tangerine-emoji.png"), auto !important; }
    .stApp { background-color: #BFF6C3 !important; }
    [data-testid="stForm"] {
        background-color: white !important; padding: 25px !important; border-radius: 25px !important;
        box-shadow: 0px 10px 25px rgba(0,0,0,0.1); border: 2px solid #9BDBA1; max-width: 600px; margin: auto;
    }
    .main-title { color: #2D5A27; font-family: 'Segoe UI', sans-serif; font-weight: 800; text-align: center; }
    div.stButton > button {
        background: linear-gradient(to right, #43766C, #729762) !important; color: white !important;
        border-radius: 12px !important; font-weight: bold; width: 100%; height: 3em; border: none !important;
    }
    .metric-box {
        background-color: white; padding: 15px; border-radius: 15px; text-align: center;
        border: 2px solid #9BDBA1; margin-bottom: 20px; color: #2D5A27; font-size: 1.1em;
    }
    </style>
    """, unsafe_allow_html=True)

def warna_imt(val):
    try:
        val = float(val)
        if val <= 0: return ''
        if val < 18.5: return 'background-color: #F3C623; color: black;'
        elif 18.5 <= val < 25.0: return 'background-color: #9BDBA1; color: black;'
        elif 25.0 <= val < 27.0: return 'background-color: #FFA447; color: black;'
        else: return 'background-color: #FF6969; color: white;'
    except: return ''

# --- 3. LOGIKA LOGIN ---
if 'login_berhasil' not in st.session_state:
    st.session_state['login_berhasil'] = False
    st.session_state['username'] = ""

if not st.session_state['login_berhasil']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.form("login_form"):
        st.markdown("<h2 class='main-title'>LOGIN SISTEM GIZI</h2>", unsafe_allow_html=True)
        user_input = st.text_input("Username").lower().strip()
        pw_input = st.text_input("Password", type="password")
        if st.form_submit_button("MASUK"):
            users = {"ardilla": "melati123", "ahligizi1": "gizi123"}
            if user_input in users and pw_input == users[user_input]:
                st.session_state['login_berhasil'] = True
                st.session_state['username'] = user_input
                st.rerun()
            else: st.error("Username atau Password Salah!")
else:
    # --- 4. KONEKSI DATA ---
    conn = st.connection("gsheets", type=GSheetsConnection)
    list_ruang = ["Anna", "Maria", "Fransiskus", "Teresa", "Monika", "Clement", "ICU/ICCU"]
    user_aktif = st.session_state['username'].lower()

    # Ambil data terbaru
    df_identitas = conn.read(worksheet="Sheet1", ttl=0).fillna('')
    df_ncp = conn.read(worksheet="NCP", ttl=0).fillna('')

    with st.sidebar:
        st.image("https://i.pinimg.com/1200x/fc/c1/cf/fcc1cf25a5c2be11134b8a9685371f15.jpg", width=120)
        st.write(f"👩‍⚕️ Hallo: **{user_aktif.upper()}**")
        if st.button("Logout"):
            st.session_state['login_berhasil'] = False
            st.rerun()

    st.markdown(f"<h1 class='main-title'>Manajemen Bangsal - {user_aktif.upper()}</h1>", unsafe_allow_html=True)
    tab1, tab_ncp, tab2, tab_rekap_ncp = st.tabs(["➕ Identitas", "📝 Data Klinis", "📊 Rekap Identitas", "📜 Rekap Klinis"])

    # --- TAB 1: INPUT IDENTITAS ---
    with tab1:
        with st.form("form_identitas", clear_on_submit=True):
            st.markdown("<h4 style='color:#2D5A27;'>Form Identitas & Skrining</h4>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                t_mrs = st.date_input("Tanggal MRS", value=datetime.now())
                rm = st.text_input("Nomor Rekam Medis (Wajib)")
                nama = st.text_input("Nama Lengkap Pasien (Wajib)")
                t_lhr = st.date_input("Tanggal Lahir", value=datetime(1990, 1, 1))
            with c2:
                rng = st.selectbox("Ruang Perawatan", list_ruang)
                no_kamar = st.text_input("Nomor Kamar")
                d_medis = st.text_input("Diagnosa Medis")
                skrining_gizi = st.selectbox("Hasil Skrining Gizi", ["Berisiko", "Tidak Berisiko"])
                diet = st.text_input("Jenis Diet Gizi")

            st.markdown("---")
            ca1, ca2, ca3, ca4 = st.columns(4)
            with ca1: bb = st.number_input("BB (kg)", min_value=0.0, step=0.1)
            with ca2: tb = st.number_input("TB (cm)", min_value=0.0, step=0.1)
            with ca3: lila = st.number_input("LILA (cm)", min_value=0.0, step=0.1)
            with ca4: ulna = st.number_input("ULNA (cm)", min_value=0.0, step=0.1)
            
            if st.form_submit_button("SIMPAN DATA IDENTITAS"):
                if rm and nama:
                    delta = relativedelta(t_mrs, t_lhr)
                    u_teks = f"{delta.years} Thn"
                    imt_val = round(bb / ((tb/100)**2), 2) if bb > 0 and tb > 0 else 0
                    
                    new_id = pd.DataFrame([{
                        "tgl_mrs": t_mrs.strftime("%Y-%m-%d"), "no_rm": rm, "nama_pasien": nama,
                        "ruang": rng, "no_kamar": no_kamar, "umur": u_teks, "bb": bb, "tb": tb,
                        "lila": lila, "ulna": ulna, "imt": imt_val, "diagnosa_medis": d_medis,
                        "skrining": skrining_gizi, "diet": diet, "input_by": user_aktif
                    }])
                    # Penting: reset_index agar urutan di Google Sheets tetap rapi
                    df_identitas = pd.concat([df_identitas, new_id], ignore_index=True).reset_index(drop=True)
                    conn.update(worksheet="Sheet1", data=df_identitas)
                    st.success("Identitas Tersimpan!"); st.rerun()
                else: st.error("No RM dan Nama Wajib diisi!")

    # --- TAB 2: DATA KLINIS ---
    with tab_ncp:
        # Filter dropdown pasien hanya yang diinput oleh user ini (Kecuali ardilla)
        df_p_user = df_identitas[df_identitas['input_by'].str.lower() == user_aktif] if user_aktif != "ardilla" else df_identitas
        list_p = df_p_user['nama_pasien'].tolist()
        
        if list_p:
            nama_pilih = st.selectbox("Pilih Pasien:", options=list_p)
            row_p = df_p_user[df_p_user['nama_pasien'] == nama_pilih].iloc[0]
            with st.form("form_klinis"):
                st.info(f"📌 Pasien: {row_p['nama_pasien']} | RM: {row_p['no_rm']}")
                bio = st.text_area("Biokimia")
                fk = st.text_area("Fisik / Klinis")
                if st.form_submit_button("SIMPAN DATA KLINIS"):
                    new_ncp = pd.DataFrame([{
                        "tgl_input": datetime.now().strftime("%Y-%m-%d"), "no_rm": row_p['no_rm'],
                        "nama_pasien": row_p['nama_pasien'], "ruang": row_p['ruang'],
                        "biokimia": bio, "fisik_klinis": fk, "input_by": user_aktif
                    }])
                    df_ncp = pd.concat([df_ncp, new_ncp], ignore_index=True).reset_index(drop=True)
                    conn.update(worksheet="NCP", data=df_ncp)
                    st.success("Data Klinis Tersimpan!"); st.rerun()
        else: st.warning("Belum ada data pasien.")

    # --- TAB 3: REKAP IDENTITAS ---
    with tab2:
        st.subheader("📊 Filter Identitas")
        f1, f2, f3 = st.columns(3)
        with f1: bul_i = st.selectbox("Bulan", range(1, 13), index=datetime.now().month-1, key="bi")
        with f2: tah_i = st.selectbox("Tahun", range(2024, 2031), index=0, key="ti")
        with f3: rng_i = st.multiselect("Ruangan", list_ruang)

        df_identitas['tgl_dt'] = pd.to_datetime(df_identitas['tgl_mrs'], errors='coerce')
        mask_i = (df_identitas['tgl_dt'].dt.month == bul_i) & (df_identitas['tgl_dt'].dt.year == tah_i)
        if rng_i: mask_i = mask_i & (df_identitas['ruang'].isin(rng_i))
        if user_aktif != "ardilla": mask_i = mask_i & (df_identitas['input_by'].str.lower() == user_aktif)
        
        df_f_i = df_identitas[mask_i].copy()
        if not df_f_i.empty:
            for idx, row in df_f_i.iterrows():
                with st.expander(f"👤 {row['nama_pasien']} ({row['ruang']})"):
                    if st.button("🗑️ Hapus Pasien", key=f"del_id_{idx}"):
                        df_identitas = df_identitas.drop(idx).reset_index(drop=True)
                        conn.update(worksheet="Sheet1", data=df_identitas.drop(columns=['tgl_dt']))
                        st.warning("Terhapus!"); st.rerun()
            st.dataframe(df_f_i.drop(columns=['tgl_dt']).style.applymap(warna_imt, subset=['imt']), use_container_width=True)
        else: st.info("Tidak ada data.")

    # --- TAB 4: REKAP KLINIS ---
    with tab_rekap_ncp:
        st.subheader("📜 Rekap Klinis")
        k1, k2 = st.columns(2)
        with k1: bul_k = st.selectbox("Bulan", range(1, 13), index=datetime.now().month-1, key="bk")
        with k2: tah_k = st.selectbox("Tahun", range(2024, 2031), index=0, key="tk")

        df_ncp['tgl_dt_k'] = pd.to_datetime(df_ncp['tgl_input'], errors='coerce')
        mask_k = (df_ncp['tgl_dt_k'].dt.month == bul_k) & (df_ncp['tgl_dt_k'].dt.year == tah_k)
        if user_aktif != "ardilla": mask_k = mask_k & (df_ncp['input_by'].str.lower() == user_aktif)
        
        df_f_k = df_ncp[mask_k].copy()
        if not df_f_k.empty:
            st.dataframe(df_f_k.drop(columns=['tgl_dt_k']), use_container_width=True, hide_index=True)
            # Tombol Download Excel
            out = BytesIO()
            with pd.ExcelWriter(out, engine='openpyxl') as writer:
                df_f_k.drop(columns=['tgl_dt_k']).to_excel(writer, index=False)
            st.download_button("📥 Download Excel", data=out.getvalue(), file_name=f"Rekap_Klinis_{bul_k}_{tah_k}.xlsx")
        else: st.info("Data klinis kosong untuk bulan ini.")
