import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from io import BytesIO
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- 1. PENGATURAN HALAMAN ---
st.set_page_config(page_title="Sistem Gizi Pasien", layout="wide")

URL_SHEETS = "https://docs.google.com/spreadsheets/d/1oPJUfBl5Ht74IUbt_Qv8XzG51bUmpCwJ_FL7iBO6UR0/edit"

# --- 2. CSS CUSTOM ---
st.markdown("""
    <style>
    * { cursor: url("https://img.icons8.com/emoji/32/tangerine-emoji.png"), auto !important; }
    .stApp { background-color: #BFF6C3 !important; }
    [data-testid="stForm"] {
        background-color: white !important; padding: 25px !important; border-radius: 30px !important;
        box-shadow: 0px 15px 35px rgba(0,0,0,0.1); border: 2px solid #9BDBA1; max-width: 500px; margin: 2% auto !important;
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
    # Koneksi ke GSheets
    conn = st.connection("gsheets", type=GSheetsConnection)

    with st.sidebar:
        st.image("https://i.pinimg.com/1200x/fc/c1/cf/fcc1cf25a5c2be11134b8a9685371f15.jpg", width=120)
        st.write(f"👩‍⚕️ Petugas: **{st.session_state['username'].upper()}**")
        if st.button("Logout"):
            st.session_state['login_berhasil'] = False
            st.rerun()

    st.markdown(f"<h1 class='main-title'>Manajemen Bangsal - {st.session_state['username'].upper()}</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["➕ Input Data Pasien", "📊 Rekap & Kelola Laporan"])

    with tab1:
        with st.form("form_input", clear_on_submit=True):
            st.markdown("<h4 style='color:#2D5A27;'>Form Identitas Pasien</h4>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                t_mrs = st.date_input("Tanggal MRS", value=datetime.now())
                rm = st.text_input("Nomor Rekam Medis (Wajib)")
                rng = st.selectbox("Ruang Perawatan", ["Anna", "Maria", "Fransiskus", "Teresa", "Monika", "Clement", "ICU/ICCU"])
                # No Kamar sebagai text_input agar tidak ada koma otomatis
                no_kamar = st.text_input("Nomor Kamar (Wajib)")
                nama = st.text_input("Nama Lengkap Pasien (Wajib)")
                t_lhr = st.date_input("Tanggal Lahir", value=datetime.now())
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
                    
                    if imt_val >= 27: st_gizi = "Obesitas"
                    elif 25 <= imt_val < 27: st_gizi = "Overweight"
                    elif 18.5 <= imt_val < 25: st_gizi = "Normal"
                    elif 0 < imt_val < 18.5: st_gizi = "Kurus"
                    else: st_gizi = "Data Tidak Lengkap"

                    try:
                        existing_data = conn.read(spreadsheet=URL_SHEETS, ttl=0).dropna(how='all')
                        
                        # Memastikan no_kamar disimpan sebagai string murni
                        new_row = pd.DataFrame([{
                            "tgl_mrs": t_mrs.strftime("%Y-%m-%d"), "no_rm": rm, "ruang": rng, 
                            "no_kamar": str(no_kamar), "nama_pasien": nama,
                            "tgl_lahir": t_lhr.strftime("%Y-%m-%d"), "umur": u_teks, "bb": bb, "tb": tb, "imt": imt_val,
                            "status_gizi": st_gizi, "zscore": z_manual, "diagnosa_medis": d_medis,
                            "skrining_gizi": skrng_gizi, "diet": diet, "input_by": st.session_state['username']
                        }])
                        
                        updated_df = pd.concat([existing_data, new_row], ignore_index=True)
                        conn.update(spreadsheet=URL_SHEETS, data=updated_df)
                        
                        st.success(f"✅ Tersimpan! Pasien: {nama}")
                        st.balloons()
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"Gagal Simpan. Error: {e}")
                else:
                    st.warning("Nomor RM dan Nama Lengkap wajib diisi!")

    with tab2:
        df_full = conn.read(spreadsheet=URL_SHEETS, ttl=0).fillna('')
        
        if not df_full.empty:
            df_full['tgl_mrs'] = pd.to_datetime(df_full['tgl_mrs'], errors='coerce')
            df_full = df_full.dropna(subset=['tgl_mrs']) 
            
            st.markdown("### 📊 Filter & Download")
            c_f1, c_f2, c_f3 = st.columns(3)
            with c_f1:
                bulan_pilih = st.selectbox("Bulan", range(1, 13), index=datetime.now().month-1, format_func=lambda x: datetime(2026, x, 1).strftime('%B'))
            with c_f2:
                tahun_pilih = st.number_input("Tahun", value=datetime.now().year)
            with c_f3:
                ruang_pilih = st.multiselect("Ruangan", options=sorted(df_full['ruang'].unique().tolist()))

            # Filter Data
            df_res = df_full[(df_full['tgl_mrs'].dt.month == bulan_pilih) & (df_full['tgl_mrs'].dt.year == tahun_pilih)]
            if ruang_pilih:
                df_res = df_res[df_res['ruang'].isin(ruang_pilih)]

            # --- PENAMBAHAN NOMOR URUT VISUAL ---
            df_display = df_res.copy()
            # Membuat kolom No di paling kiri (1, 2, 3...)
            df_display.insert(0, 'No', range(1, 1 + len(df_display)))

            # Menampilkan jumlah total pasien hasil filter
            st.write(f"📌 **Total Pasien Terdaftar: {len(df_res)}**")

            # Fungsi Warna Gizi
            def warna_gizi(val):
                if val == 'Obesitas': return 'background-color: #FF7676'
                elif val == 'Overweight': return 'background-color: #FFD966'
                elif val == 'Normal': return 'background-color: #A9D18E'
                elif val == 'Kurus': return 'background-color: #9BCFE0'
                return ''

            # Tampilkan tabel (No Kamar dipaksa jadi string agar koma hilang)
            if 'no_kamar' in df_display.columns:
                df_display['no_kamar'] = df_display['no_kamar'].astype(str).replace('\.0', '', regex=True)

            st.dataframe(df_display.style.map(warna_gizi, subset=['status_gizi']), use_container_width=True, hide_index=True)

            if not df_res.empty:
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_export = df_res.copy()
                    df_export['tgl_mrs'] = df_export['tgl_mrs'].dt.strftime('%Y-%m-%d')
                    df_export.to_excel(writer, index=False, sheet_name='Laporan')
                    
                    ws = writer.sheets['Laporan']
                    last_row_xl = len(df_res) + 4
                    ws.cell(row=last_row_xl, column=2, value="Kepala Ruangan,")
                    ws.cell(row=last_row_xl, column=6, value="Kepala Instalasi Gizi,")
                    ws.cell(row=last_row_xl+4, column=2, value="( ____________________ )")
                    ws.cell(row=last_row_xl+4, column=6, value="( ____________________ )")

                st.download_button(
                    label="📥 DOWNLOAD EXCEL",
                    data=output.getvalue(),
                    file_name=f"Laporan_Gizi_{bulan_pilih}_{tahun_pilih}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.info("Belum ada data di Google Sheets.")
