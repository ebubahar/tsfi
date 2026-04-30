import streamlit as st
import pandas as pd
import io

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="CRF - Akıllı Veri Giriş Sistemi", layout="wide")

# --- VERİ TABANI & HAFIZA (SESSION STATE) ANAHTARLARI ---
# Formdaki her alanın varsayılan değeri. (Sıfırlama işlemlerinde kullanılır)
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

# Başlangıç değişkenlerini Session State'e yükle
for k, v in KEYS.items():
    if k not in st.session_state:
        st.session_state[k] = v

if 'hasta_verileri' not in st.session_state:
    st.session_state['hasta_verileri'] = {} # Hızlı arama için TC kimliği anahtar yapıyoruz
if 'current_step' not in st.session_state:
    st.session_state['current_step'] = 0

# --- SİSTEM FONKSİYONLARI ---

def tc_bulundu_doldur():
    """Kullanıcı TC yazdığında eski verileri çağırır"""
    tc = st.session_state.tc_kimlik
    if tc in st.session_state.hasta_verileri:
        for k, v in st.session_state.hasta_verileri[tc].items():
            if k in KEYS:
                st.session_state[k] = v
        st.toast(f"✅ {tc} numaralı hastanın eski verileri yüklendi. Eksik kalanları tamamlayabilirsiniz!")

def skorlari_hesapla():
    """Tüm otomatik hesaplamaları yapar ve geriye sözlük döner"""
    # MAP
    map_val = (st.session_state.sistolik + 2 * st.session_state.diyastolik) / 3
    # ROX
    fio2_oran = st.session_state.fio2 / 100.0
    rox_val = (st.session_state.spo2 / fio2_oran) / st.session_state.solunum if st.session_state.solunum > 0 and fio2_oran > 0 else 0
    # DTF
    dtf_val = ((st.session_state.sag_end_insp - st.session_state.sag_end_eksp) / st.session_state.sag_end_eksp) * 100 if st.session_state.sag_end_eksp > 0 else 0
    
    # ISS
    ais_dict = {"0: Yok": 0, "1: Küçük": 1, "2: Orta": 2, "3: Ciddi (Hayatı Tehdit Etmeyen)": 3, "4: Ciddi (Hayatı Tehdit Eden)": 4, "5: Ağır (Kritik)": 5, "6: Maksimum (Muhtemelen Ölümcül)": 6}
    ais_vals = [ais_dict[st.session_state.ais_bas], ais_dict[st.session_state.ais_yuz], ais_dict[st.session_state.ais_gogus], ais_dict[st.session_state.ais_karin], ais_dict[st.session_state.ais_ekstremite], ais_dict[st.session_state.ais_dissal]]
    iss_val = 75 if 6 in ais_vals else sum(x**2 for x in sorted(ais_vals, reverse=True)[:3])
    
    # CCI
    cci_keys = [('cci_mi',1),('cci_kky',1),('cci_pvh',1),('cci_svo',1),('cci_demans',1),('cci_koah',1),('cci_rom',1),('cci_ulser',1),('cci_kc_hafif',1),('cci_dm',1),('cci_hemipleji',2),('cci_kby',2),('cci_dm_komp',2),('cci_kanser',2),('cci_losemi',2),('cci_lenfoma',2),('cci_kc_agir',3),('cci_metastaz',6),('cci_aids',6)]
    cci_val = sum(puan for key, puan in cci_keys if st.session_state[key])

    # MNA
    mna_val = int(st.session_state.mna_a[0]) + int(st.session_state.mna_b[0]) + int(st.session_state.mna_c[0]) + int(st.session_state.mna_d[0]) + int(st.session_state.mna_e[0]) + int(st.session_state.mna_f[0])
    
    # SORUNU ÇÖZEN SATIR: [-1] kullanılarak stringin içindeki son parantez alınıyor.
    def parse_score(val): return float(str(val).split("(")[-1].split(")")[0])
    
    # FRAIL
    frail_val = parse_score(st.session_state.frail_1) + parse_score(st.session_state.frail_2) + parse_score(st.session_state.frail_3) + parse_score(st.session_state.frail_4) + parse_score(st.session_state.frail_5)

    # TSFI Hasta & Yakın
    h_tsfi = sum([parse_score(st.session_state[k]) for k in ['h_kanser', 'h_kah', 'h_demans', 'h_kbakim', 'h_para', 'h_evisi', 'h_tuvalet', 'h_yurume', 'h_yararli', 'h_uzgun', 'h_caba', 'h_yalniz', 'h_dusme', 'h_cinsel', 'h_alb']])
    y_tsfi = sum([parse_score(st.session_state[k]) for k in ['y_kanser', 'y_kah', 'y_demans', 'y_kbakim', 'y_para', 'y_evisi', 'y_tuvalet', 'y_yurume', 'y_yararli', 'y_uzgun', 'y_caba', 'y_yalniz', 'y_dusme', 'y_cinsel', 'y_alb']])

    return {"MAP": map_val, "ROX": rox_val, "DTF (%)": dtf_val, "ISS": iss_val, "CCI": cci_val, "MNA": mna_val, "FRAIL": frail_val, "TSFI (Hasta)": h_tsfi, "TSFI (Yakın)": y_tsfi}

def hastayi_kaydet(sessiz=False):
    """Mevcut durumu hesaplamaları yaparak veritabanına ekler"""
    tc = st.session_state.tc_kimlik
    if not tc:
        if not sessiz: st.warning("⚠️ Kaydetmek için önce TC Kimlik No girmelisiniz!")
        return False
    
    hasta_satiri = {k: st.session_state[k] for k in KEYS.keys()}
    hesaplamalar = skorlari_hesapla()
    hasta_satiri.update(hesaplamalar) # Otomatik skorları da excele geçmesi için ekle
    
    st.session_state.hasta_verileri[tc] = hasta_satiri
    if not sessiz: st.toast("💾 Verileriniz başarıyla kaydedildi!")
    return True

def yeni_hasta_baslat():
    """Eğer veri varsa kaydeder, sonra formu temizler"""
    if st.session_state.tc_kimlik:
        hastayi_kaydet(sessiz=True)
    for k, v in KEYS.items():
        st.session_state[k] = v
    st.session_state.current_step = 0
    st.rerun()

# --- ÜST PANEL (BAŞLIK VE YENİ HASTA) ---
col_top1, col_top2 = st.columns([8, 2])
with col_top1:
    st.title("📑 CRF Veri Giriş Sistemi")
with col_top2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ YENİ HASTA Ekle / Temizle", use_container_width=True):
        yeni_hasta_baslat()

# --- SEKMELER (NAVİGASYON) ---
adimlar = ["1. Demografi", "2. Yaralanma & Vital", "3. ISS Skoru", "4. Diyafram USG", "5. CCI Skoru", "6. MNA Tarama", "7. FRAIL Ölçeği", "8. TSFI (Hasta)", "9. TSFI (Yakını)", "10. Sonuç"]
st.session_state.current_step = adimlar.index(st.radio("Sekmeler:", adimlar, index=st.session_state.current_step, horizontal=True))
st.divider()

# ====== SEKME İÇERİKLERİ ======

if st.session_state.current_step == 0:
    st.header("1. Kimlik ve Demografi")
    st.text_input("TC Kimlik No (Yazınca eski veriler otomatik gelir)", key="tc_kimlik", on_change=tc_bulundu_doldur)
    st.text_input("İsim Soyisim", key="isim_soyisim")
    c1, c2 = st.columns(2)
    c1.number_input("Yaş", min_value=0, max_value=120, key="yas")
    c2.selectbox("Cinsiyet", ["Erkek", "Kadın", "Diğer"], key="cinsiyet")

elif st.session_state.current_step == 1:
    st.header("2. Yaralanma & Vital Bulgular")
    c1, c2 = st.columns(2)
    with c1:
        st.selectbox("Yaralanma Türü", ["Künt", "Delici", "Diğer"], key="yar_turu_secim")
        if st.session_state.yar_turu_secim == "Diğer": st.text_input("Diğer sebebi nedir?", key="yar_turu_detay")
    with c2:
        st.selectbox("Yaralanma Mekanizması", ["Düşme", "Trafik Kazası", "Yüksekten Düşme", "Diğer"], key="yar_mek_secim")
        if st.session_state.yar_mek_secim == "Diğer": st.text_input("Mekanizma diğer açıklaması", key="yar_mek_detay")
    
    st.subheader("Vital Bulgular")
    v1, v2, v3, v4, v5, v6, v7 = st.columns(7)
    v1.number_input("Sistolik TA", min_value=0, key="sistolik")
    v2.number_input("Diyastolik", min_value=0, key="diyastolik")
    v3.number_input("Nabız", min_value=0, key="nabiz")
    v4.number_input("Solunum", min_value=1, key="solunum")
    v5.number_input("Ateş", format="%.1f", key="ates")
    v6.number_input("SpO2", min_value=0, max_value=100, key="spo2")
    v7.number_input("FiO2 (%)", min_value=21, max_value=100, key="fio2")

    oto = skorlari_hesapla()
    st.info(f"⚡ **Otomatik Hesaplamalar:** GKS ({st.session_state.gks_goz+st.session_state.gks_motor+st.session_state.gks_sozel}) | **MAP:** {oto['MAP']:.1f} mmHg | **ROX İndeksi:** {oto['ROX']:.2f}")
    
    st.subheader("GKS")
    g1, g2, g3 = st.columns(3)
    g1.number_input("Göz", min_value=1, max_value=4, key="gks_goz")
    g2.number_input("Motor", min_value=1, max_value=6, key="gks_motor")
    g3.number_input("Sözel", min_value=1, max_value=5, key="gks_sozel")

elif st.session_state.current_step == 2:
    st.header("3. ISS (Yaralanma Şiddeti Skoru)")
    opt = ["0: Yok", "1: Küçük", "2: Orta", "3: Ciddi (Hayatı Tehdit Etmeyen)", "4: Ciddi (Hayatı Tehdit Eden)", "5: Ağır (Kritik)", "6: Maksimum (Muhtemelen Ölümcül)"]
    c1, c2 = st.columns(2)
    c1.selectbox("Baş ve Boyun", opt, key="ais_bas")
    c1.selectbox("Yüz", opt, key="ais_yuz")
    c1.selectbox("Göğüs", opt, key="ais_gogus")
    c2.selectbox("Karın / Pelvik", opt, key="ais_karin")
    c2.selectbox("Ekstremiteler", opt, key="ais_ekstremite")
    c2.selectbox("Dışsal", opt, key="ais_dissal")
    st.success(f"**Güncel ISS Puanı:** {skorlari_hesapla()['ISS']}")

elif st.session_state.current_step == 3:
    st.header("4. Diyafram USG Değerlendirmesi (Sağ)")
    c1, c2, c3 = st.columns(3)
    c1.number_input("Ekskürsiyon (cm)", min_value=0.0, format="%.2f", key="sag_ekskursiyon")
    c2.number_input("End-Ekspiryum Kalınlık (cm)", min_value=0.01, format="%.2f", key="sag_end_eksp")
    c3.number_input("End-İnspiryum Kalınlık (cm)", min_value=0.0, format="%.2f", key="sag_end_insp")
    st.text_area("Diğer USG Bulguları", key="usg_diger")
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
        with [c1, c2, c3][i % 3]: st.checkbox(label, key=h_key)
    st.success(f"**Mevcut CCI Skoru:** {skorlari_hesapla()['CCI']}")

elif st.session_state.current_step == 5:
    st.header("6. MNA Tarama")
    st.selectbox("A. Besin alımında azalma", ["0: Şiddetli düşüş", "1: Orta derece düşüş", "2: Düşüş yok"], key="mna_a")
    st.selectbox("B. Kilo kaybı durumu", ["0: >3 kg", "1: Bilinmiyor", "2: 1-3 kg arası", "3: Kilo kaybı yok"], key="mna_b")
    st.selectbox("C. Hareketlilik", ["0: Yatağa bağımlı", "1: Evden çıkamaz", "2: Evden dışarı çıkabilir"], key="mna_c")
    st.selectbox("D. Psikolojik stres / Akut hastalık", ["0: Evet", "2: Hayır"], key="mna_d")
    st.selectbox("E. Nöropsikolojik", ["0: Ciddi bunama", "1: Hafif bunama", "2: Hiçbir psikolojik problem yok"], key="mna_e")
    st.selectbox("F. VKİ", ["0: <19", "1: 19-20.9", "2: 21-22.9", "3: VKİ 23 ve üzeri"], key="mna_f")
    st.success(f"**MNA Skoru:** {skorlari_hesapla()['MNA']}")

elif st.session_state.current_step == 6:
    st.header("7. FRAIL Ölçeği")
    st.selectbox("Yorgunluk", ["Her zaman / Çoğu zaman (1)", "Bazen / Çok az / Hiçbir zaman (0)"], key="frail_1")
    st.selectbox("Direnç (Merdiven)", ["Evet (1)", "Hayır (0)"], key="frail_2")
    st.selectbox("Dolaşma (Yürüme)", ["Evet (1)", "Hayır (0)"], key="frail_3")
    st.selectbox("Hastalık (>5)", ["5-11 hastalık (1)", "0-4 hastalık (0)"], key="frail_4")
    st.selectbox("Kilo Kaybı (>=%5)", ["Evet (≥%5) (1)", "Hayır (<%5) (0)"], key="frail_5")
    st.success(f"**FRAIL Skoru:** {skorlari_hesapla()['FRAIL']}")

elif st.session_state.current_step in [7, 8]:
    prefix = "h_" if st.session_state.current_step == 7 else "y_"
    kim = "HASTA (KENDİSİ)" if st.session_state.current_step == 7 else "HASTA YAKINI"
    st.header(f"{st.session_state.current_step + 1}. TSFI - {kim}")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Hastalıklar & Günlük Yaşam")
        st.selectbox("Kanser", ["Yok (0)", "Evet (1)"], key=f"{prefix}kanser")
        st.selectbox("Koroner Arter H.", ["Yok (0)", "İlaç tedavisi (0.25)", "PCI (0.5)", "CABG (0.75)", "MI (1)"], key=f"{prefix}kah")
        st.selectbox("Demans", ["Yok (0)", "Hafif (0.25)", "Orta (0.5)", "Ağır (1)"], key=f"{prefix}demans")
        st.selectbox("Kişisel Bakım Yardım", ["Hayır (0)", "Evet (1)"], key=f"{prefix}kbakim")
        st.selectbox("Para Yönetimi", ["Hayır (0)", "Evet (1)"], key=f"{prefix}para")
        st.selectbox("Ev İşleri", ["Hayır (0)", "Evet (1)"], key=f"{prefix}evisi")
        st.selectbox("Tuvalet İhtiyacı", ["Hayır (0)", "Evet (1)"], key=f"{prefix}tuvalet")
        st.selectbox("Yürürken Yardım", ["Yok (0)", "Baston (0.75)", "Yürüteç (0.5)", "Tekerlekli sandalye (1)"], key=f"{prefix}yurume")
    with c2:
        st.subheader("Psikolojik, Beslenme & Fonksiyon")
        tut = ["Hiçbir zaman (0)", "Bazen (0.5)", "Çoğu zaman (1)"]
        st.selectbox("Daha az yararlı hissetme", tut, key=f"{prefix}yararli")
        st.selectbox("Üzgün hissetme", tut, key=f"{prefix}uzgun")
        st.selectbox("Çaba harcama hissi", tut, key=f"{prefix}caba")
        st.selectbox("Yalnız hissetme", tut, key=f"{prefix}yalniz")
        st.selectbox("Düşmeler", ["Yok (0)", "Var, son 1 ayda değil (0.5)", "Son 1 ayda (1)"], key=f"{prefix}dusme")
        st.selectbox("Cinsel olarak aktif", ["Evet (0)", "Hayır (1)"], key=f"{prefix}cinsel")
        st.selectbox("Albümin", ["≥3g/dl (0)", "<3g/dl (1)"], key=f"{prefix}alb")

    skor = skorlari_hesapla()["TSFI (Hasta)" if prefix == "h_" else "TSFI (Yakın)"]
    st.success(f"**Hesaplanan TSFI Puanı:** {skor} / 15 | **İndeks:** {(skor/15):.2f}")

elif st.session_state.current_step == 9:
    st.header("10. Sonuç ve Klinik Sonlanımlar")
    st.selectbox("Morbidite Gelişimi?", ["Hayır", "Evet"], key="morbidite")
    if st.session_state.morbidite == "Evet": st.text_input("Türü:", key="morbidite_turu")
    st.selectbox("Taburculuk Durumu", ["Eve", "Servise", "Yoğun Bakıma", "Exitus"], key="taburculuk")

# --- ALT YÖNLENDİRME & KAYDET BUTONLARI ---
st.markdown("<br><br>", unsafe_allow_html=True)
col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

with col_btn1:
    if st.session_state.current_step > 0:
        if st.button("⬅️ Önceki Sayfa", use_container_width=True):
            hastayi_kaydet(sessiz=True) # Sayfa değişirken arkadan yedekle
            st.session_state.current_step -= 1
            st.rerun()

with col_btn2:
    if st.button("💾 GÜNCEL SAYFAYI KAYDET", use_container_width=True):
        hastayi_kaydet()

with col_btn3:
    if st.session_state.current_step < len(adimlar) - 1:
        if st.button("Sonraki Sayfa ➡️", use_container_width=True):
            hastayi_kaydet(sessiz=True) # Sayfa değişirken arkadan yedekle
            st.session_state.current_step += 1
            st.rerun()

# --- EXCEL VE VERİ YÖNETİMİ ALANI ---
st.divider()
st.header("🗂️ Kayıtlı Hastalar (Canlı Tablo Düzenleme)")
st.write("Aşağıdaki tablo Excel mantığıyla çalışır. **Değerleri doğrudan üstüne tıklayıp değiştirebilir** veya **satırları silebilirsin**. İşlemin bitince aşağıdaki güncellemeyi kaydet butonuna basmayı unutma!")

if st.session_state.hasta_verileri:
    df = pd.DataFrame(list(st.session_state.hasta_verileri.values()))
    
    # TC Sütununu en başa alalım ki rahat görünsün
    if 'tc_kimlik' in df.columns:
        cols = ['tc_kimlik'] + [c for c in df.columns if c != 'tc_kimlik']
        df = df[cols]
    
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="veri_editoru")
    
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        if st.button("🔄 Tabloda Yaptığım Silme/Değişiklik İşlemlerini Sisteme Kaydet", use_container_width=True):
            yeni_veritabani = {}
            for index, row in edited_df.iterrows():
                yeni_veritabani[row['tc_kimlik']] = row.to_dict()
            st.session_state.hasta_verileri = yeni_veritabani
            st.success("Tablodaki güncellemeler sisteme yansıtıldı!")
            st.rerun()
            
    with col_dl2:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            edited_df.to_excel(writer, index=False, sheet_name="Tam_Veriseti")
        st.download_button("📥 Tabloyu EXCEL Olarak İndir", data=buffer.getvalue(), file_name="TSFI_Calisma_Veriseti.xlsx", use_container_width=True)
else:
    st.info("Sistemde henüz kaydedilmiş hasta bulunmuyor. Kayıt yaptıkça veriler burada Excel tablosu olarak belirecektir.")
