import json
import os
import streamlit as st
import pandas as pd
import io
import gspread
from google.oauth2.service_account import Credentials
import json  # JSON kütüphanesini doğru yere, en tepeye ekledik!

# --- GOOGLE SHEETS AYARLARI ---
# Aşağıdaki SHEET_ID kısmına Google E-Tablonun linkindeki uzun ID'yi yapıştır.
SHEET_ID = '1uxRGNOZIMRYmVqP7se8BkohF5Lj_x7eKtS60cxSl76g' 

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="CRF - Bulut Senkronizasyonlu Sistem", layout="wide")

# --- VARSAYILAN DEĞERLER (KEYS) ---
KEYS = {
    'tc_kimlik': '', 'isim_soyisim': '', 'yas': 0, 'cinsiyet': 'Erkek',
    'yar_turu_secim': 'Künt', 'yar_turu_detay': '', 'yar_mek_secim': 'Düşme', 'yar_mek_detay': '',
    'gks_goz': 4, 'gks_motor': 6, 'gks_sozel': 5,
    'sistolik': 120, 'diyastolik': 80, 'nabiz': 80, 'ates': 36.5,
    'solunum': 16, 'spo2': 98, 'fio2': 21,
    'ais_bas': "0: Yok", 'ais_yuz': "0: Yok", 'ais_gogus': "0: Yok", 'ais_karin': "0: Yok", 'ais_ekstremite': "0: Yok", 'ais_dissal': "0: Yok",
    'sag_ekskursiyon': 0.0, 'sag_end_eksp': 0.20, 'sag_end_insp': 0.30, 'usg_diger': '',
    'cci_mi': False, 'cci_kky': False, 'cci_pvh': False, 'cci_svo': False, 'cci_demans': False, 'cci_koah': False,
    'cci_rom': False, 'cci_ulser': False, 'cci_kc_hafif': False, 'cci_dm': False, 'cci_hemipleji': False,
    'cci_kby': False, 'cci_dm_komp': False, 'cci_kanser': False, 'cci_losemi': False, 'cci_lenfoma': False,
    'cci_kc_agir': False, 'cci_metastaz': False, 'cci_aids': False,
    'mna_a': "2: Düşüş yok", 'mna_b': "3: Kilo kaybı yok", 'mna_c': "2: Evden dışarı çıkabilir", 'mna_d': "2: Hayır", 'mna_e': "2: Hiçbir psikolojik problem yok", 'mna_f': "3: VKİ 23 ve üzeri",
    'frail_1': "Bazen / Çok az / Hiçbir zaman (0)", 'frail_2': "Hayır (0)", 'frail_3': "Hayır (0)", 'frail_4': "0-4 hastalık (0)", 'frail_5': "Hayır (<%5) (0)",
    'h_kanser': "Yok (0)", 'h_kah': "Yok (0)", 'h_demans': "Yok (0)", 'h_kbakim': "Hayır (0)", 'h_para': "Hayır (0)", 'h_evisi': "Hayır (0)", 'h_tuvalet': "Hayır (0)", 'h_yurume': "Yok (0)", 'h_yararli': "Hiçbir zaman (0)", 'h_uzgun': "Hiçbir zaman (0)", 'h_caba': "Hiçbir zaman (0)", 'h_yalniz': "Hiçbir zaman (0)", 'h_dusme': "Yok (0)", 'h_cinsel': "Evet (0)", 'h_alb': "≥3g/dl (0)",
    'y_kanser': "Yok (0)", 'y_kah': "Yok (0)", 'y_demans': "Yok (0)", 'y_kbakim': "Hayır (0)", 'y_para': "Hayır (0)", 'y_evisi': "Hayır (0)", 'y_tuvalet': "Hayır (0)", 'y_yurume': "Yok (0)", 'y_yararli': "Hiçbir zaman (0)", 'y_uzgun': "Hiçbir zaman (0)", 'y_caba': "Hiçbir zaman (0)", 'y_yalniz': "Hiçbir zaman (0)", 'y_dusme': "Yok (0)", 'y_cinsel': "Evet (0)", 'y_alb': "≥3g/dl (0)",
    'morbidite': 'Hayır', 'morbidite_turu': '', 'taburculuk': 'Eve'
}

# --- SİSTEM BAŞLATMA ---
for k, v in KEYS.items():
    if k not in st.session_state:
        st.session_state[k] = v

if 'current_step' not in st.session_state:
    st.session_state['current_step'] = 0


# --- GOOGLE SHEETS FONKSİYONLARI ---
@st.cache_resource
def get_gsheet_client():
    """Dosya yolunu zorla tespit eden akıllı bağlantı"""
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # KODUN BULUNDUĞU TAM KLASÖRÜ BUL (Örn: C:\Users\ebuba\Desktop\ACİL TIP\tsfi_streamlit.io)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, 'google_credentials.json')
    
    try:
        # 1. Önce senin bilgisayarındaki o tam yoldan okumayı dener
        creds = Credentials.from_service_account_file(json_path, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e_local:
        # 2. Eğer dosyayı bulamazsa veya bulutta çalışıyorsak, Streamlit Secrets kasasına bakar
        try:
            creds_dict = json.loads(st.secrets["google_json"])
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            return gspread.authorize(creds)
        except Exception as e_cloud:
            # 3. İkisi de başarısız olursa ekrana tam olarak nerelere baktığını yazdırır!
            st.error(f"🛑 GİZLİ ANAHTAR BULUNAMADI!")
            st.write(f"**Lokalde aradığım tam yol:** `{json_path}`")
            st.write(f"**Lokal Hata:** `{e_local}`")
            raise Exception("Kimlik doğrulama dosyası bulunamadığı için işlem durduruldu.")def veriyi_cek(tc_no):
    """Buluttan TC ile hasta arar, bulursa ekrana çeker"""
    if not tc_no: return False
    try:
        client = get_gsheet_client()
        sh = client.open_by_key(SHEET_ID)
        worksheet = sh.get_worksheet(0) # İlk sayfa (Sheet1)
        
        records = worksheet.get_all_records() # Tüm veriyi indir
        for row in records:
            # TC kimlik numarasını string olarak eşleştir
            if str(row.get('tc_kimlik', '')) == str(tc_no):
                # Bulunan hastanın verilerini hafızaya (Session State) yükle
                for k in KEYS.keys():
                    if k in row:
                        st.session_state[k] = row[k]
                return True # Veri başarıyla çekildi
        return False # TC bulunamadı
    except Exception as e:
        st.error(f"⚠️ Buluttan veri çekerken bağlantı hatası oluştu. Lütfen JSON dosyasını ve İnternet bağlantınızı kontrol edin. Detay: {e}")
        return False

def veriyi_bul_veya_ekle(data_dict):
    """Buluta veriyi yazar. Hasta varsa üstüne yazar, yoksa yeni satır açar"""
    client = get_gsheet_client()
    sh = client.open_by_key(SHEET_ID)
    worksheet = sh.get_worksheet(0)
    
    # Eğer tablo tamamen boşsa önce başlıkları (Header) yaz
    if worksheet.row_count == 0 or not worksheet.row_values(1):
        worksheet.append_row(list(data_dict.keys()))
        
    records = worksheet.get_all_records()
    df = pd.DataFrame(records)
    
    tc = str(data_dict['tc_kimlik'])
    yeni_satir = list(data_dict.values())
    
    # Hasta daha önce kaydedilmiş mi kontrol et
    if not df.empty and 'tc_kimlik' in df.columns and tc in df['tc_kimlik'].astype(str).values:
        # Varsa ilgili satırı bul ve güncelle
        idx = df[df['tc_kimlik'].astype(str) == tc].index[0] + 2 # Header ve 0-index kayması
        worksheet.update(f"A{idx}", [yeni_satir])
    else:
        # Yoksa en alt satıra yeni kayıt olarak ekle
        worksheet.append_row(yeni_satir)

# --- TC KİMLİK DEĞİŞİM TETİKLEYİCİSİ ---
def tc_degisti_kontrol():
    """Kullanıcı TC yazıp Enter'a bastığında bu fonksiyon tetiklenir"""
    yeni_tc = st.session_state.tc_kimlik_input
    st.session_state.tc_kimlik = yeni_tc
    
    if yeni_tc:
        st.toast("⏳ Google Sheets bulutunda aranıyor...")
        bulundu_mu = veriyi_cek(yeni_tc)
        if bulundu_mu:
            st.toast("✅ CİHAZLAR ARASI SENKRONİZASYON BAŞARILI! Diğer cihazdan girilen veriler ekrana yüklendi.")
        else:
            st.toast("ℹ️ Bu TC'ye ait kayıt bulunamadı. Yeni bir kayıt oluşturuluyor.")

# --- HESAPLAMA VE KAYDETME FONKSİYONLARI ---
def skorlari_hesapla():
    gks_val = st.session_state.gks_goz + st.session_state.gks_motor + st.session_state.gks_sozel
    map_val = (st.session_state.sistolik + 2 * st.session_state.diyastolik) / 3
    fio2_oran = st.session_state.fio2 / 100.0
    rox_val = (st.session_state.spo2 / fio2_oran) / st.session_state.solunum if st.session_state.solunum > 0 and fio2_oran > 0 else 0
    dtf_val = ((st.session_state.sag_end_insp - st.session_state.sag_end_eksp) / st.session_state.sag_end_eksp) * 100 if st.session_state.sag_end_eksp > 0 else 0
    
    ais_dict = {"0: Yok": 0, "1: Küçük": 1, "2: Orta": 2, "3: Ciddi (Hayatı Tehdit Etmeyen)": 3, "4: Ciddi (Hayatı Tehdit Eden)": 4, "5: Ağır (Kritik)": 5, "6: Maksimum (Muhtemelen Ölümcül)": 6}
    ais_vals = [ais_dict[st.session_state.ais_bas], ais_dict[st.session_state.ais_yuz], ais_dict[st.session_state.ais_gogus], ais_dict[st.session_state.ais_karin], ais_dict[st.session_state.ais_ekstremite], ais_dict[st.session_state.ais_dissal]]
    iss_val = 75 if 6 in ais_vals else sum(x**2 for x in sorted(ais_vals, reverse=True)[:3])
    
    cci_keys = [('cci_mi',1),('cci_kky',1),('cci_pvh',1),('cci_svo',1),('cci_demans',1),('cci_koah',1),('cci_rom',1),('cci_ulser',1),('cci_kc_hafif',1),('cci_dm',1),('cci_hemipleji',2),('cci_kby',2),('cci_dm_komp',2),('cci_kanser',2),('cci_losemi',2),('cci_lenfoma',2),('cci_kc_agir',3),('cci_metastaz',6),('cci_aids',6)]
    cci_val = sum(puan for key, puan in cci_keys if st.session_state[key])

    mna_val = int(st.session_state.mna_a[0]) + int(st.session_state.mna_b[0]) + int(st.session_state.mna_c[0]) + int(st.session_state.mna_d[0]) + int(st.session_state.mna_e[0]) + int(st.session_state.mna_f[0])
    
    def parse_score(val): return float(str(val).split("(")[-1].split(")")[0])
    frail_val = parse_score(st.session_state.frail_1) + parse_score(st.session_state.frail_2) + parse_score(st.session_state.frail_3) + parse_score(st.session_state.frail_4) + parse_score(st.session_state.frail_5)

    h_tsfi = sum([parse_score(st.session_state[k]) for k in ['h_kanser', 'h_kah', 'h_demans', 'h_kbakim', 'h_para', 'h_evisi', 'h_tuvalet', 'h_yurume', 'h_yararli', 'h_uzgun', 'h_caba', 'h_yalniz', 'h_dusme', 'h_cinsel', 'h_alb']])
    y_tsfi = sum([parse_score(st.session_state[k]) for k in ['y_kanser', 'y_kah', 'y_demans', 'y_kbakim', 'y_para', 'y_evisi', 'y_tuvalet', 'y_yurume', 'y_yararli', 'y_uzgun', 'y_caba', 'y_yalniz', 'y_dusme', 'y_cinsel', 'y_alb']])

    return {"GKS_Toplam": gks_val, "MAP": map_val, "ROX": rox_val, "DTF (%)": dtf_val, "ISS": iss_val, "CCI": cci_val, "MNA": mna_val, "FRAIL": frail_val, "TSFI (Hasta)": h_tsfi, "TSFI (Yakın)": y_tsfi}

def hastayi_kaydet(sessiz=False):
    tc = st.session_state.tc_kimlik
    if not tc:
        if not sessiz: st.warning("⚠️ Buluta kaydetmek için önce 1. Sekmeden TC Kimlik No girmelisiniz!")
        return False
    
    hasta_satiri = {k: st.session_state[k] for k in KEYS.keys()}
    hasta_satiri.update(skorlari_hesapla()) 
    
    try:
        if not sessiz: st.info("☁️ Veriler Google Sheets bulutuna gönderiliyor...")
        veriyi_bul_veya_ekle(hasta_satiri)
        if not sessiz: st.success("💾 Verileriniz Google Sheets'e KALICI olarak kaydedildi!")
        return True
    except Exception as e:
        st.error(f"❌ Google Sheets Kayıt Hatası: Lütfen Secrets alanını kontrol edin. Detay: {e}")
        return False

def yeni_hasta_baslat():
    # Mevcut ekrandakini buluta at ve ekranı sıfırla
    if st.session_state.tc_kimlik:
        hastayi_kaydet(sessiz=True) 
    for k, v in KEYS.items():
        st.session_state[k] = v
    st.session_state.tc_kimlik_input = ''
    st.session_state.current_step = 0
    st.rerun()

def render_selectbox(label, options, state_key):
    idx = options.index(st.session_state[state_key]) if st.session_state[state_key] in options else 0
    st.session_state[state_key] = st.selectbox(label, options, index=idx)

# --- ÜST PANEL ---
col_top1, col_top2 = st.columns([8, 2])
with col_top1:
    st.title("☁️ CRF Bulut Senkronizasyon Sistemi")
    st.write("Cihazlar arası eşzamanlı çalışma aktif. Herhangi bir cihazdan TC girdiğinizde mevcut veriler otomatik çekilir.")
with col_top2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ YENİ HASTA (Ekranı Sıfırla)", use_container_width=True):
        yeni_hasta_baslat()

# --- SEKMELER & NAVİGASYON ---
adimlar = ["1. Demografi", "2. Yaralanma & Vital", "3. ISS", "4. USG", "5. CCI", "6. MNA", "7. FRAIL", "8. TSFI (H)", "9. TSFI (Y)", "10. Sonuç"]
new_step_name = st.radio("Sekmeler (İlerleme Durumu):", adimlar, index=st.session_state.current_step, horizontal=True)

if adimlar.index(new_step_name) != st.session_state.current_step:
    hastayi_kaydet(sessiz=True) # Sekme değiştikçe arkadan buluta at
    st.session_state.current_step = adimlar.index(new_step_name)
    st.rerun()
st.divider()

# ====== SEKME İÇERİKLERİ ======

if st.session_state.current_step == 0:
    st.header("1. Kimlik ve Demografi")
    # TC değiştiğinde tc_degisti_kontrol fonsiyonu buluttan veriyi çeker!
    st.text_input("TC Kimlik No (Yazıp Enter'a basın, diğer cihazdaki veriler çekilsin)", value=st.session_state.tc_kimlik, key="tc_kimlik_input", on_change=tc_degisti_kontrol)
    st.session_state.isim_soyisim = st.text_input("İsim Soyisim", value=st.session_state.isim_soyisim)
    c1, c2 = st.columns(2)
    st.session_state.yas = c1.number_input("Yaş", min_value=0, max_value=120, value=int(st.session_state.yas))
    with c2: render_selectbox("Cinsiyet", ["Erkek", "Kadın", "Diğer"], 'cinsiyet')

elif st.session_state.current_step == 1:
    st.header("2. Yaralanma & Vital Bulgular")
    c1, c2 = st.columns(2)
    with c1:
        render_selectbox("Yaralanma Türü", ["Künt", "Delici", "Diğer"], 'yar_turu_secim')
        if st.session_state.yar_turu_secim == "Diğer": 
            st.session_state.yar_turu_detay = st.text_input("Diğer sebebi nedir?", value=st.session_state.yar_turu_detay)
    with c2:
        render_selectbox("Yaralanma Mekanizması", ["Düşme", "Trafik Kazası", "Yüksekten Düşme", "Diğer"], 'yar_mek_secim')
        if st.session_state.yar_mek_secim == "Diğer": 
            st.session_state.yar_mek_detay = st.text_input("Mekanizma diğer açıklaması", value=st.session_state.yar_mek_detay)
    
    st.divider()
    st.subheader("Vital Bulgular")
    v1, v2, v3, v4, v5, v6, v7 = st.columns(7)
    st.session_state.sistolik = v1.number_input("Sistolik TA", min_value=0, value=int(st.session_state.sistolik))
    st.session_state.diyastolik = v2.number_input("Diyastolik", min_value=0, value=int(st.session_state.diyastolik))
    st.session_state.nabiz = v3.number_input("Nabız", min_value=0, value=int(st.session_state.nabiz))
    st.session_state.solunum = v4.number_input("Solunum", min_value=1, value=int(st.session_state.solunum))
    st.session_state.ates = v5.number_input("Ateş", value=float(st.session_state.ates), format="%.1f", step=0.1)
    st.session_state.spo2 = v6.number_input("SpO2", min_value=0, max_value=100, value=int(st.session_state.spo2))
    st.session_state.fio2 = v7.number_input("FiO2 (%)", min_value=21, max_value=100, value=int(st.session_state.fio2))

    st.subheader("GKS (Glasgow Koma Skoru)")
    g1, g2, g3 = st.columns(3)
    st.session_state.gks_goz = g1.number_input("Göz", min_value=1, max_value=4, value=int(st.session_state.gks_goz))
    st.session_state.gks_motor = g2.number_input("Motor", min_value=1, max_value=6, value=int(st.session_state.gks_motor))
    st.session_state.gks_sozel = g3.number_input("Sözel", min_value=1, max_value=5, value=int(st.session_state.gks_sozel))
    
    oto = skorlari_hesapla()
    st.info(f"⚡ **Otomatik Hesaplamalar:** GKS Toplamı: **{oto['GKS_Toplam']}** | MAP: **{oto['MAP']:.1f} mmHg** | ROX İndeksi: **{oto['ROX']:.2f}**")

elif st.session_state.current_step == 2:
    st.header("3. ISS (Yaralanma Şiddeti Skoru)")
    opt = ["0: Yok", "1: Küçük", "2: Orta", "3: Ciddi (Hayatı Tehdit Etmeyen)", "4: Ciddi (Hayatı Tehdit Eden)", "5: Ağır (Kritik)", "6: Maksimum (Muhtemelen Ölümcül)"]
    c1, c2 = st.columns(2)
    with c1:
        render_selectbox("Baş ve Boyun", opt, 'ais_bas')
        render_selectbox("Yüz", opt, 'ais_yuz')
        render_selectbox("Göğüs", opt, 'ais_gogus')
    with c2:
        render_selectbox("Karın / Pelvik", opt, 'ais_karin')
        render_selectbox("Ekstremiteler", opt, 'ais_ekstremite')
        render_selectbox("Dışsal", opt, 'ais_dissal')
    st.success(f"**Güncel ISS Puanı:** {skorlari_hesapla()['ISS']}")

elif st.session_state.current_step == 3:
    st.header("4. Diyafram USG Değerlendirmesi (Sağ)")
    c1, c2, c3 = st.columns(3)
    st.session_state.sag_ekskursiyon = c1.number_input("Ekskürsiyon (cm)", min_value=0.0, format="%.2f", step=0.1, value=float(st.session_state.sag_ekskursiyon))
    st.session_state.sag_end_eksp = c2.number_input("End-Ekspiryum Kalınlık", min_value=0.01, format="%.2f", step=0.05, value=float(st.session_state.sag_end_eksp))
    st.session_state.sag_end_insp = c3.number_input("End-İnspiryum Kalınlık", min_value=0.0, format="%.2f", step=0.05, value=float(st.session_state.sag_end_insp))
    st.session_state.usg_diger = st.text_area("Diğer USG Bulguları", value=st.session_state.usg_diger)
    st.success(f"**Otomatik Kalınlaşma Fraksiyonu (DTF):** %{skorlari_hesapla()['DTF (%)']:.1f}")

elif st.session_state.current_step == 4:
    st.header("5. Charlson Comorbidity Index (CCI)")
    hastaliklar = [
        ("Miyokard İnfarktüsü (1)", 'cci_mi'), ("Kalp Yetmezliği (1)", 'cci_kky'), ("Periferik Vasküler (1)", 'cci_pvh'), 
        ("Serebrovasküler (1)", 'cci_svo'), ("Demans (1)", 'cci_demans'), ("KOAH (1)", 'cci_koah'), 
        ("Romatolojik (1)", 'cci_rom'), ("Peptik Ülser (1)", 'cci_ulser'), ("Hafif Karaciğer H. (1)", 'cci_kc_hafif'), 
        ("Diyabet (1)", 'cci_dm'), ("Hemipleji (2)", 'cci_hemipleji'), ("Böbrek Hastalığı (2)", 'cci_kby'), 
        ("Komplikasyonlu DM (2)", 'cci_dm_komp'), ("Kanser (2)", 'cci_kanser'), ("Lösemi (2)", 'cci_losemi'), 
        ("Lenfoma (2)", 'cci_lenfoma'), ("Ağır Karaciğer H. (3)", 'cci_kc_agir'), ("Metastaz (6)", 'cci_metastaz'), ("AIDS (6)", 'cci_aids')
    ]
    c1, c2, c3 = st.columns(3)
    for i, (label, h_key) in enumerate(hastaliklar):
        with [c1, c2, c3][i % 3]: 
            val = st.session_state[h_key]
            if isinstance(val, str): val = val.upper() == 'TRUE'
            st.session_state[h_key] = st.checkbox(label, value=val)
    st.success(f"**Mevcut CCI Skoru:** {skorlari_hesapla()['CCI']}")

elif st.session_state.current_step == 5:
    st.header("6. MNA Tarama")
    render_selectbox("A. Besin alımında azalma", ["0: Şiddetli düşüş", "1: Orta derece düşüş", "2: Düşüş yok"], 'mna_a')
    render_selectbox("B. Kilo kaybı durumu", ["0: >3 kg", "1: Bilinmiyor", "2: 1-3 kg arası", "3: Kilo kaybı yok"], 'mna_b')
    render_selectbox("C. Hareketlilik", ["0: Yatağa bağımlı", "1: Evden çıkamaz", "2: Evden dışarı çıkabilir"], 'mna_c')
    render_selectbox("D. Psikolojik stres / Akut hastalık", ["0: Evet", "2: Hayır"], 'mna_d')
    render_selectbox("E. Nöropsikolojik", ["0: Ciddi bunama", "1: Hafif bunama", "2: Hiçbir psikolojik problem yok"], 'mna_e')
    render_selectbox("F. VKİ", ["0: <19", "1: 19-20.9", "2: 21-22.9", "3: VKİ 23 ve üzeri"], 'mna_f')
    st.success(f"**MNA Skoru:** {skorlari_hesapla()['MNA']}")

elif st.session_state.current_step == 6:
    st.header("7. FRAIL Ölçeği")
    render_selectbox("Yorgunluk", ["Her zaman / Çoğu zaman (1)", "Bazen / Çok az / Hiçbir zaman (0)"], 'frail_1')
    render_selectbox("Direnç (Merdiven)", ["Evet (1)", "Hayır (0)"], 'frail_2')
    render_selectbox("Dolaşma (Yürüme)", ["Evet (1)", "Hayır (0)"], 'frail_3')
    render_selectbox("Hastalık (>5)", ["5-11 hastalık (1)", "0-4 hastalık (0)"], 'frail_4')
    render_selectbox("Kilo Kaybı (>=%5)", ["Evet (≥%5) (1)", "Hayır (<%5) (0)"], 'frail_5')
    st.success(f"**FRAIL Skoru:** {skorlari_hesapla()['FRAIL']}")

elif st.session_state.current_step in [7, 8]:
    prefix = "h_" if st.session_state.current_step == 7 else "y_"
    kim = "HASTA (KENDİSİ)" if st.session_state.current_step == 7 else "HASTA YAKINI"
    st.header(f"{st.session_state.current_step + 1}. TSFI - {kim}")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Hastalıklar & Günlük Yaşam")
        render_selectbox("Kanser", ["Yok (0)", "Evet (1)"], f'{prefix}kanser')
        render_selectbox("Koroner Arter H.", ["Yok (0)", "İlaç tedavisi (0.25)", "PCI (0.5)", "CABG (0.75)", "MI (1)"], f'{prefix}kah')
        render_selectbox("Demans", ["Yok (0)", "Hafif (0.25)", "Orta (0.5)", "Ağır (1)"], f'{prefix}demans')
        render_selectbox("Kişisel Bakım Yardım", ["Hayır (0)", "Evet (1)"], f'{prefix}kbakim')
        render_selectbox("Para Yönetimi", ["Hayır (0)", "Evet (1)"], f'{prefix}para')
        render_selectbox("Ev İşleri", ["Hayır (0)", "Evet (1)"], f'{prefix}evisi')
        render_selectbox("Tuvalet İhtiyacı", ["Hayır (0)", "Evet (1)"], f'{prefix}tuvalet')
        render_selectbox("Yürürken Yardım", ["Yok (0)", "Baston (0.75)", "Yürüteç (0.5)", "Tekerlekli sandalye (1)"], f'{prefix}yurume')
    with c2:
        st.subheader("Psikolojik, Beslenme & Fonksiyon")
        tut = ["Hiçbir zaman (0)", "Bazen (0.5)", "Çoğu zaman (1)"]
        render_selectbox("Daha az yararlı hissetme", tut, f'{prefix}yararli')
        render_selectbox("Üzgün hissetme", tut, f'{prefix}uzgun')
        render_selectbox("Çaba harcama hissi", tut, f'{prefix}caba')
        render_selectbox("Yalnız hissetme", tut, f'{prefix}yalniz')
        render_selectbox("Düşmeler", ["Yok (0)", "Var, son 1 ayda değil (0.5)", "Son 1 ayda (1)"], f'{prefix}dusme')
        render_selectbox("Cinsel olarak aktif", ["Evet (0)", "Hayır (1)"], f'{prefix}cinsel')
        render_selectbox("Albümin", ["≥3g/dl (0)", "<3g/dl (1)"], f'{prefix}alb')

    skor = skorlari_hesapla()["TSFI (Hasta)" if prefix == "h_" else "TSFI (Yakın)"]
    st.success(f"**Hesaplanan TSFI Puanı:** {skor} / 15 | **İndeks:** {(skor/15):.2f}")

elif st.session_state.current_step == 9:
    st.header("10. Sonuç ve Klinik Sonlanımlar")
    render_selectbox("Morbidite Gelişimi?", ["Hayır", "Evet"], 'morbidite')
    if st.session_state.morbidite == "Evet": 
        st.session_state.morbidite_turu = st.text_input("Türü:", value=st.session_state.morbidite_turu)
    render_selectbox("Taburculuk Durumu", ["Eve", "Servise", "Yoğun Bakıma", "Exitus"], 'taburculuk')

# --- ALT YÖNLENDİRME & KAYDET BUTONLARI ---
st.markdown("<br><br>", unsafe_allow_html=True)
col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

with col_btn1:
    if st.session_state.current_step > 0:
        if st.button("⬅️ Geri (Önceki Sayfa)", use_container_width=True):
            hastayi_kaydet(sessiz=True) 
            st.session_state.current_step -= 1
            st.rerun()

with col_btn2:
    if st.button("💾 GÜNCEL VERİLERİ GOOGLE SHEETS'E GÖNDER", use_container_width=True):
        hastayi_kaydet(sessiz=False)

with col_btn3:
    if st.session_state.current_step < len(adimlar) - 1:
        if st.button("İleri (Sonraki Sayfa) ➡️", use_container_width=True):
            hastayi_kaydet(sessiz=True) 
            st.session_state.current_step += 1
            st.rerun()
