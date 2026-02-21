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

# --- 2. CSS CUSTOM ---
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
        box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNGSI LOGIKA GIZI ---

def warna_imt(val):
    try:
        val = float(val)
        if val <= 0: return ''
        if val < 18.5: return 'background-color: #F3C623; color: black;'   # Kuning
        elif 18.5 <= val < 25.0: return 'background-color: #9BDBA1; color: black;' # Hijau
        elif 25.0 <= val < 27.0: return 'background-color: #FFA447; color: black;' # Orange
        else: return 'background-color: #FF6969; color: white;'            # Merah
    except:
        return ''

def label_imt(val):
    try:
        val = float(val)
        if val <= 0: return ""
        if val < 18.5: return "Kurus (Underweight)"
        elif 18.5 <= val < 25.0: return "Normal"
        elif 25.0 <= val < 27.0: return "Overweight"
        else: return "Obesitas"
    except:
        return ""

def bersihkan_tabel(df):
    if df.empty: return df
    df = df.copy()
    
    # 1. Rapikan Tanggal & No RM
    for col in df.columns:
        if 'tgl' in col or 'tanggal' in col.lower():
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d-%m-%Y')
        elif col in ['no', 'no_rm', 'no_kamar']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int).astype(str).replace('0', '')

    # 2. KHUSUS IDENTITAS: Hitung IMT & Status Gizi
    if 'bb' in df.columns and 'tb' in df.columns:
        for col in ['bb', 'tb', 'lila', 'ulna']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Hitung IMT (Angka)
        df['imt_num'] = df.apply(lambda r: round(r['bb']/((r['tb']/100)**2), 2) if float(r['bb'])>0 and float(r['tb'])>0 else 0, axis=1)
        
        # Munculkan Teks Status Gizi
        df['status_gizi'] = df['imt_num'].apply(label_imt)
        
        # Format kolom IMT untuk tampilan
        df['imt'] = df['imt_num'].apply(lambda x: f"{float(x):.2f}")
        df = df.drop(columns=['imt_num']) 
            
    return df

# --- 3. LOGIKA LOGIN ---
if 'login_berhasil' not in st.session_state:
    st.session_state['login_berhasil'] = False
    st.session_state['username'] = ""

if not st.session_state['login_berhasil']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.form("login_form"):
        st.markdown("<h2 class='main-title'>LOGIN SISTEM GIZI</h2>", unsafe_allow_html=True)
        user_input = st.text_input("Username").lower()
        pw_input = st.text_input("Password", type="password")
        if st.form_submit_button("MASUK"):
            users = {"ardilla": "melati123", "ahligizi1": "gizi123"}
            if user_input in users and pw_input == users[user_input]:
                st.session_state['login_berhasil'] = True
                st.session_state['username'] = user_input
                st.toast('Selamat datang kembali!', icon='🍊')
                st.rerun()
            else: st.error("Username atau Password Salah!")
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
                t_lhr = st.date_input("Tanggal Lahir", value=datetime(1990, 1, 1), min_value=datetime(1900, 1, 1))
            with c2:
                rng = st.selectbox("Ruang Perawatan", list_ruang)
                no_kamar = st.text_input("Nomor Kamar (Wajib)")
                d_medis = st.text_input("Diagnosa Medis")
                skrining_gizi = st.selectbox("Hasil Skrining Gizi", ["Berisiko", "Tidak Berisiko"])
                diet = st.text_input("Jenis Diet Gizi")

            st.markdown("---")
            ca1, ca2, ca3, ca4 = st.columns(4)
            with ca1: bb = st.number_input("BB (kg)", min_value=0.0, step=0.1, format="%.2f")
            with ca2: tb = st.number_input("TB (cm)", min_value=0.0, step=0.1, format="%.2f")
            with ca3: lila = st.number_input("LILA (cm)", min_value=0.0, step=0.1, format="%.2f")
            with ca4: ulna = st.number_input("ULNA (cm)", min_value=0.0, step=0.1, format="%.2f")
            z_score = st.text_input("Z-Score (Khusus Anak)")
            
            if st.form_submit_button("SIMPAN DATA IDENTITAS"):
                if rm and nama:
                    delta = relativedelta(t_mrs, t_lhr)
                    u_teks = f"{delta.years} Thn" if delta.years >= 19 else f"{delta.years} Thn {delta.months} Bln"
                    imt_awal = round(bb / ((tb/100)**2), 2) if bb > 0 and tb > 0 else 0
                    
                    new_row = pd.DataFrame([{
                        "no": len(df_identitas) + 1, "tgl_mrs": t_mrs.strftime("%Y-%m-%d"), "no_rm": rm, 
                        "ruang": rng, "no_kamar": str(no_kamar), "nama_pasien": nama, 
                        "tgl_lahir": t_lhr.strftime("%Y-%m-%d"), "umur": u_teks, "bb": bb, "tb": tb, 
                        "lila": lila, "ulna": ulna, "zscore": z_score, "imt": imt_awal, 
                        "diagnosa_medis": d_medis, "skrining": skrining_gizi, "diet": diet, 
                        "input_by": st.session_state['username']
                    }])
                    conn.update(spreadsheet=URL_SHEETS, worksheet="Sheet1", data=pd.concat([df_identitas, new_row], ignore_index=True))
                    st.snow(); st.toast('Tersimpan!', icon='✅'); st.cache_data.clear(); st.rerun()

    # --- TAB 2: DATA KLINIS ---
    with tab_ncp:
        st.markdown("<h4 style='color:#2D5A27;'>Input Data Klinis</h4>", unsafe_allow_html=True)
        if not df_identitas.empty:
            list_p = df_identitas['nama_pasien'].tolist() if st.session_state['username'] == "ardilla" else df_identitas[df_identitas['input_by'] == st.session_state['username']]['nama_pasien'].tolist()
            if list_p:
                nama_pilih = st.selectbox("Pilih Pasien:", options=list_p)
                row = df_identitas[df_identitas['nama_pasien'] == nama_pilih].iloc[0]
                with st.form("form_klinis", clear_on_submit=True):
                    st.info(f"📌 {row['nama_pasien']} | RM: {row['no_rm']}")
                    bio = st.text_area("Biokimia")
                    penunjang = st.text_area("Penunjang")
                    fk = st.text_area("Fisik / Klinis")
                    if st.form_submit_button("SIMPAN DATA KLINIS"):
                        new_ncp = pd.DataFrame([{
                            "no": len(df_ncp) + 1, "tgl_input": datetime.now().strftime("%Y-%m-%d"),
                            "no_rm": row['no_rm'], "ruang": row['ruang'], "no_kamar": row['no_kamar'], 
                            "nama_pasien": row['nama_pasien'], "diagnosa_medis": row['diagnosa_medis'], 
                            "biokimia": bio, "penunjang_lainnya": penunjang, "fisik_klinis": fk, "diet": row['diet'],
                            "input_by": st.session_state['username']
                        }])
                        conn.update(spreadsheet=URL_SHEETS, worksheet="NCP", data=pd.concat([df_ncp, new_ncp], ignore_index=True))
                        st.snow(); st.toast('Tersimpan!', icon='❄️'); st.cache_data.clear(); st.rerun()

    # --- TAB 3: REKAP IDENTITAS ---
    with tab2:
        if not df_identitas.empty:
            df_view_raw = df_identitas if st.session_state['username'] == "ardilla" else df_identitas[df_identitas['input_by'] == st.session_state['username']]
            df_clean = bersihkan_tabel(df_view_raw)
            
            f1, f2, f3 = st.columns(3)
            with f1: bul_i = st.selectbox("Bulan", range(1, 13), index=datetime.now().month-1, key="b1")
            with f2: tah_i = st.selectbox("Tahun", range(2024, 2031), index=datetime.now().year-2024, key="t1")
            with f3: rng_i = st.multiselect("Ruangan", options=list_ruang, key="r1")
            
            df_clean['dt_obj'] = pd.to_datetime(df_clean['tgl_mrs'], format='%d-%m-%Y', errors='coerce')
            sel_rooms = rng_i if rng_i else list_ruang
            mask = (df_clean['dt_obj'].dt.month == bul_i) & (df_clean['dt_obj'].dt.year == tah_i) & (df_clean['ruang'].isin(sel_rooms))
            df_f = df_clean[mask].drop(columns=['dt_obj']).copy()

            st.markdown(f"<div class='metric-box'>📊 Terfilter: <b>{len(df_f)}</b> Pasien</div>", unsafe_allow_html=True)
            # Bagian ini memerlukan fungsi warna_imt
            st.dataframe(df_f.style.applymap(warna_imt, subset=['imt']), use_container_width=True, hide_index=True)
            
            out = BytesIO()
            with pd.ExcelWriter(out, engine='openpyxl') as writer: df_f.to_excel(writer, index=False)
            st.download_button("📥 DOWNLOAD IDENTITAS", data=out.getvalue(), file_name="Rekap_Identitas.xlsx")

    # --- TAB 4: REKAP KLINIS ---
    with tab_rekap_ncp:
        if not df_ncp.empty:
            df_view_k_raw = df_ncp if st.session_state['username'] == "ardilla" else df_ncp[df_ncp['input_by'] == st.session_state['username']]
            df_clean_k = bersihkan_tabel(df_view_k_raw)
            
            k1, k2, k3 = st.columns(3)
            with k1: bul_k = st.selectbox("Bulan (Klinis)", range(1, 13), index=datetime.now().month-1, key="b2")
            with k2: tah_k = st.selectbox("Tahun (Klinis)", range(2024, 2031), index=datetime.now().year-2024, key="t2")
            with k3: rng_k = st.multiselect("Ruangan (Klinis)", options=list_ruang, key="r2")

            df_clean_k['dt_obj'] = pd.to_datetime(df_clean_k['tgl_input'], format='%d-%m-%Y', errors='coerce')
            sel_rooms_k = rng_k if rng_k else list_ruang
            mask_k = (df_clean_k['dt_obj'].dt.month == bul_k) & (df_clean_k['dt_obj'].dt.year == tah_k) & (df_clean_k['ruang'].isin(sel_rooms_k))
            df_f_k = df_clean_k[mask_k].drop(columns=['dt_obj']).copy()

            st.markdown(f"<div class='metric-box'>📜 Catatan Klinis: <b>{len(df_f_k)}</b> Pasien</div>", unsafe_allow_html=True)
            st.dataframe(df_f_k, use_container_width=True, hide_index=True)
            
            out_k = BytesIO()
            with pd.ExcelWriter(out_k, engine='openpyxl') as writer: df_f_k.to_excel(writer, index=False)
            st.download_button("📥 DOWNLOAD KLINIS", data=out_k.getvalue(), file_name="Rekap_Klinis.xlsx")
