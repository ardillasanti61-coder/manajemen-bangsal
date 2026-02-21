import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from io import BytesIO
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- 1. PENGATURAN HALAMAN ---
st.set_page_config(
    page_title="Gizi Bangsal Ardilla", 
    page_icon="🍊", 
    layout="wide"
)

# URL Google Sheet
URL_SHEETS = "https://docs.google.com/spreadsheets/d/1oPJUfBl5Ht74IUbt_Qv8XzG51bUmpCwJ_FL7iBO6UR0/edit"

# --- 2. CSS CUSTOM (Tema Hijau Gizi) ---
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
        border: 2px solid #9BDBA1; margin-bottom: 20px; color: #2D5A27; font-size: 1.1em;
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
                st.toast('Selamat datang kembali!', icon='🍊')
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

    # Ambil Data Terbaru
    df_identitas = conn.read(spreadsheet=URL_SHEETS, worksheet="Sheet1", ttl=0).fillna('')
    df_ncp = conn.read(spreadsheet=URL_SHEETS, worksheet="NCP", ttl=0).fillna('')

    # --- TAB 1: INPUT IDENTITAS ---
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
                    st.toast('Sedang menyiapkan data...', icon='🍊')
                    with st.spinner('Menyimpan ke Cloud...'):
                        delta = relativedelta(t_mrs, t_lhr)
                        u_teks = f"{delta.years} Thn" if delta.years >= 19 else f"{delta.years} Thn {delta.months} Bln"
                        imt_val = round(bb / ((tb/100)**2), 2) if bb > 0 and tb > 0 else 0
                        
                        new_row = pd.DataFrame([{
                            "no": len(df_identitas) + 1, "tgl_mrs": t_mrs.strftime("%Y-%m-%d"), "no_rm": rm, 
                            "ruang": rng, "no_kamar": str(no_kamar), "nama_pasien": nama, 
                            "umur": u_teks, "bb": bb, "tb": tb, "lila": lila, "ulna": ulna, 
                            "zscore": z_score, "imt": imt_val, "diagnosa_medis": d_medis, 
                            "skrining": skrining_gizi, "diet": diet, "input_by": st.session_state['username']
                        }])
                        updated_df = pd.concat([df_identitas, new_row], ignore_index=True)
                        conn.update(spreadsheet=URL_SHEETS, worksheet="Sheet1", data=updated_df)
                    st.snow()
                    st.toast(f'Data {nama} Berhasil Tersimpan!', icon='✅')
                    st.cache_data.clear(); st.rerun()

    # --- TAB 2: DATA KLINIS ---
    with tab_ncp:
        st.markdown("<h4 style='color:#2D5A27;'>Input Data Klinis & Penunjang</h4>", unsafe_allow_html=True)
        if not df_identitas.empty:
            nama_pilih = st.selectbox("Pilih Pasien Dari Database:", options=df_identitas['nama_pasien'].tolist())
            row = df_identitas[df_identitas['nama_pasien'] == nama_pilih].iloc[0]
            with st.form("form_klinis"):
                st.info(f"📌 Pasien: {row['nama_pasien']} | RM: {row['no_rm']}")
                bio = st.text_area("Biokimia (Hasil Lab)")
                penunjang = st.text_area("Penunjang Lainnya")
                fk = st.text_area("Fisik / Klinis (F/K)")
                if st.form_submit_button("SIMPAN DATA KLINIS"):
                    st.toast('Mengunggah data klinis...', icon='📝')
                    with st.spinner('Menghubungkan ke server...'):
                        new_ncp = pd.DataFrame([{
                            "no": len(df_ncp) + 1, "tgl_input": datetime.now().strftime("%Y-%m-%d"),
                            "no_rm": row['no_rm'], "ruang": row['ruang'], "no_kamar": row['no_kamar'], 
                            "nama_pasien": row['nama_pasien'], "diagnosa_medis": row['diagnosa_medis'], 
                            "biokimia": bio, "penunjang_lainnya": penunjang, "fisik_klinis": fk, "diet": row['diet']
                        }])
                        updated_ncp = pd.concat([df_ncp, new_ncp], ignore_index=True)
                        conn.update(spreadsheet=URL_SHEETS, worksheet="NCP", data=updated_ncp)
                    st.snow()
                    st.toast('Catatan klinis tersimpan!', icon='❄️')
                    st.cache_data.clear(); st.rerun()

    # Pengaturan Filter Global
    tahun_skrg = datetime.now().year
    list_tahun = list(range(1900, 2101))

    # --- TAB 3: REKAP IDENTITAS ---
    with tab2:
        if not df_identitas.empty:
            df_identitas['tgl_mrs'] = pd.to_datetime(df_identitas['tgl_mrs'], errors='coerce')
            f1, f2, f3 = st.columns(3)
            with f1: bul_i = st.selectbox("Filter Bulan", range(1, 13), index=datetime.now().month-1, format_func=lambda x: datetime(tahun_skrg, x, 1).strftime('%B'))
            with f2: tah_i = st.selectbox("Filter Tahun", list_tahun, index=list_tahun.index(tahun_skrg))
            with f3: rng_i = st.multiselect("Filter Ruangan", options=list_ruang, default=list_ruang)

            mask_i = (df_identitas['tgl_mrs'].dt.month == bul_i) & (df_identitas['tgl_mrs'].dt.year == tah_i) & (df_identitas['ruang'].isin(rng_i))
            df_f_i = df_identitas[mask_i].copy()
            
            # Counter Data Identitas
            st.markdown(f"<div class='metric-box'>📊 Pasien Terfilter: <b>{len(df_f_i)}</b> | Total Database: <b>{len(df_identitas)}</b></div>", unsafe_allow_html=True)
            
            st.dataframe(df_f_i, use_container_width=True, hide_index=True)
            
            out_i = BytesIO()
            with pd.ExcelWriter(out_i, engine='openpyxl') as writer:
                df_f_i.to_excel(writer, index=False, sheet_name='Identitas')
            st.download_button("📥 DOWNLOAD REKAP IDENTITAS", data=out_i.getvalue(), file_name=f"Rekap_Identitas_{bul_i}_{tah_i}.xlsx")
            
            st.divider()
            with st.expander("🗑️ Hapus Data Identitas"):
                no_h = st.number_input("Masukkan No Urut Identitas yang ingin dihapus:", min_value=1, step=1, key="del_id")
                if st.button("HAPUS DATA IDENTITAS"):
                    with st.spinner('Menghapus...'):
                        df_new = df_identitas[df_identitas['no'] != no_h]
                        df_new['no'] = range(1, len(df_new) + 1)
                        conn.update(spreadsheet=URL_SHEETS, worksheet="Sheet1", data=df_new)
                    st.toast('Data berhasil dihapus', icon='🗑️')
                    st.cache_data.clear(); st.rerun()

    # --- TAB 4: REKAP KLINIS ---
    with tab_rekap_ncp:
        if not df_ncp.empty:
            df_ncp['tgl_input'] = pd.to_datetime(df_ncp['tgl_input'], errors='coerce')
            k1, k2, k3 = st.columns(3)
            with k1: bul_k = st.selectbox("Filter Bulan (Klinis)", range(1, 13), index=datetime.now().month-1, format_func=lambda x: datetime(tahun_skrg, x, 1).strftime('%B'))
            with k2: tah_k = st.selectbox("Filter Tahun (Klinis)", list_tahun, index=list_tahun.index(tahun_skrg))
            with k3: rng_k = st.multiselect("Filter Ruangan (Klinis)", options=list_ruang, default=list_ruang)

            mask_k = (df_ncp['tgl_input'].dt.month == bul_k) & (df_ncp['tgl_input'].dt.year == tah_k) & (df_ncp['ruang'].isin(rng_k))
            df_f_k = df_ncp[mask_k].copy()
            
            # Counter Data Klinis
            st.markdown(f"<div class='metric-box'>📜 Catatan Terfilter: <b>{len(df_f_k)}</b> | Total Database: <b>{len(df_ncp)}</b></div>", unsafe_allow_html=True)
            
            st.dataframe(df_f_k, use_container_width=True, hide_index=True)
            
            out_k = BytesIO()
            with pd.ExcelWriter(out_k, engine='openpyxl') as writer:
                df_f_k.to_excel(writer, index=False, sheet_name='Klinis')
            st.download_button("📥 DOWNLOAD REKAP KLINIS", data=out_k.getvalue(), file_name=f"Rekap_Klinis_{bul_k}_{tah_k}.xlsx")

            st.divider()
            with st.expander("🗑️ Menu Hapus Catatan Klinis"):
                no_h_k = st.number_input("Masukkan No Urut Klinis yang ingin dihapus:", min_value=1, step=1, key="del_klinis")
                if st.button("HAPUS CATATAN KLINIS"):
                    with st.spinner('Menghapus...'):
                        df_new_ncp = df_ncp[df_ncp['no'] != no_h_k]
                        df_new_ncp['no'] = range(1, len(df_new_ncp) + 1)
                        conn.update(spreadsheet=URL_SHEETS, worksheet="NCP", data=df_new_ncp)
                    st.toast('Catatan berhasil dihapus!', icon='🗑️')
                    st.cache_data.clear(); st.rerun()
