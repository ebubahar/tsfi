import streamlit as st
import pandas as pd
import io

# Sayfa Yapılandırması
st.set_page_config(page_title="CRF - TSFI & Diyafram USG", layout="wide")
st.title("OLGU RAPOR FORMU (CRF) - TSFI Validasyonu ve Diyafram USG")

# Veritabanı (Session State) başlatma
if 'hasta_verileri' not in st.session_state:
    st.session_state['hasta_verileri'] = []

# --- 1. Hasta Kimlik ve Demografik Bilgileri ---
st.header("1. Hasta Kimlik ve Demografik Bilgileri")
col1, col2 = st.columns(2)
with col1:
    barkod = st.text_input("BARKOD / ÇALIŞMA NO")
    isim_soyisim = st.text_input("İsim Soyisim")
    tc_kimlik = st.text_input("TC Kimlik No")
with col2:
    yas = st.number_input("Yaş (Yıl)", min_value=0, max_value=120, step=1)
    cinsiyet = st.selectbox("Cinsiyet", ["Erkek", "Kadın", "Diğer"])

# --- 2. Yaralanma Özellikleri ve Vital Bulgular ---
st.header("2. Yaralanma Özellikleri ve Vital Bulgular")
col3, col4 = st.columns(2)
with col3:
    yaralanma_turu = st.selectbox("Yaralanma Türü", ["Künt", "Delici", "Diğer"])
    yaralanma_mekanizmasi = st.selectbox("Yaralanma Mekanizması", ["Düşme", "Trafik Kazası", "Yüksekten Düşme", "Diğer"])
with col4:
    st.subheader("GKS ve Vital Bulgular")
    gks_goz = st.number_input("GKS - Göz", min_value=1, max_value=4, value=4)
    gks_motor = st.number_input("GKS - Motor", min_value=1, max_value=6, value=6)
    gks_sozel = st.number_input("GKS - Sözel", min_value=1, max_value=5, value=5)
    gks_toplam = gks_goz + gks_motor + gks_sozel
    st.info(f"**Toplam GKS:** {gks_toplam}")

col_v1, col_v2, col_v3, col_v4, col_v5 = st.columns(5)
nabiz = col_v1.number_input("Nabız (/dk)", min_value=0)
solunum = col_v2.number_input("Solunum (/dk)", min_value=0)
ates = col_v3.number_input("Ateş (°C)", value=36.5, format="%.1f")
map_degeri = col_v4.number_input("MAP (mmHg)", min_value=0)
spo2 = col_v5.number_input("SpO2 (%)", min_value=0, max_value=100, value=98)

# --- 3. Yaralanma Şiddeti Skoru (ISS) ---
st.header("3. Yaralanma Şiddeti Skoru (ISS) Hesaplaması")
st.write("Kural: En ciddi yaralanan 3 bölgenin AIS (1-6) puanlarının kareleri toplamı. AIS 6 varsa ISS direkt 75'tir.")

ais_options = [0, 1, 2, 3, 4, 5, 6]
col_ais1, col_ais2 = st.columns(2)
with col_ais1:
    ais_bas_boyun = st.selectbox("Baş ve Boyun AIS", ais_options)
    ais_yuz = st.selectbox("Yüz AIS", ais_options)
    ais_gogus = st.selectbox("Göğüs AIS", ais_options)
with col_ais2:
    ais_karin = st.selectbox("Karın veya Pelvik AIS", ais_options)
    ais_ekstremite = st.selectbox("Ekstremiteler AIS", ais_options)
    ais_dissal = st.selectbox("Dışsal AIS", ais_options)

ais_listesi = [ais_bas_boyun, ais_yuz, ais_gogus, ais_karin, ais_ekstremite, ais_dissal]
if 6 in ais_listesi:
    iss_skoru = 75
else:
    ais_sirali = sorted(ais_listesi, reverse=True)
    iss_skoru = sum([x**2 for x in ais_sirali[:3]])
st.success(f"**Hesaplanan ISS Skoru:** {iss_skoru}")

# --- 4. Diyafram USG Değerlendirmesi ---
st.header("4. Diyafram USG Değerlendirmesi")
col_usg1, col_usg2 = st.columns(2)
with col_usg1:
    st.subheader("Sağ Diyafram")
    sag_ekskursiyon = st.number_input("Sağ Diyafragmatik Ekskürsiyon (cm)", min_value=0.0, format="%.2f")
    sag_end_insp = st.number_input("Sağ Kalınlık - End-İnspiryum (cm)", min_value=0.0, format="%.2f")
    sag_end_eksp = st.number_input("Sağ Kalınlık - End-Ekspiryum (cm)", min_value=0.0, format="%.2f")
    sag_tf = st.number_input("Sağ Kalınlaşma Fraksiyonu (TF) (%)", min_value=0.0, format="%.1f")
with col_usg2:
    st.subheader("Sol Diyafram")
    sol_ekskursiyon = st.number_input("Sol Diyafragmatik Ekskürsiyon (cm)", min_value=0.0, format="%.2f")
    sol_end_insp = st.number_input("Sol Kalınlık - End-İnspiryum (cm)", min_value=0.0, format="%.2f")
    sol_end_eksp = st.number_input("Sol Kalınlık - End-Ekspiryum (cm)", min_value=0.0, format="%.2f")
    sol_tf = st.number_input("Sol Kalınlaşma Fraksiyonu (TF) (%)", min_value=0.0, format="%.1f")
usg_diger = st.text_input("USG Diğer Bulgular")

# --- 5. Charlson Comorbidity Index (CCI) ---
st.header("5. Charlson Comorbidity Index (CCI)")
cci_items = {
    "Geçirilmiş Miyokard İnfarktüsü": 1, "Konjestif Kalp Yetmezliği": 1, "Periferik Vasküler Hastalık": 1,
    "Serebrovasküler Hastalık": 1, "Demans": 1, "Kronik Akciğer Hastalığı": 1, "Romatolojik Hastalık": 1,
    "Peptik Ülser Hastalığı": 1, "Hafif Karaciğer Hastalığı": 1, "Diyabet": 1,
    "Hemipleji": 2, "Orta-Ağır Böbrek Hastalığı": 2, "Kronik Komplikasyonlu Diyabet": 2,
    "Metastazsız Kanser": 2, "Lösemi": 2, "Lenfoma": 2,
    "Orta-Ağır Karaciğer Hastalığı": 3,
    "Metastatik Solid Tümör": 6, "AIDS": 6
}
cci_skor = 0
cci_secimler = {}
col_c1, col_c2, col_c3 = st.columns(3)
for i, (hastalik, puan) in enumerate(cci_items.items()):
    with [col_c1, col_c2, col_c3][i % 3]:
        secili_mi = st.checkbox(f"{hastalik} ({puan} Puan)")
        cci_secimler[hastalik] = secili_mi
        if secili_mi:
            cci_skor += puan
st.success(f"**TOPLAM CCI SKORU:** {cci_skor}")

# --- 6. MNA Tarama Formu ---
st.header("6. Mini Nütrisyonel Değerlendirme (MNA)")
mna_a = st.selectbox("A. Besin alımında azalma?", {"0: Şiddetli düşüş":0, "1: Orta derece düşüş":1, "2: Düşüş yok":2}.items(), format_func=lambda x: x[0])[1]
mna_b = st.selectbox("B. Son 3 ay kilo kaybı?", {"0: >3 kg":0, "1: Bilinmiyor":1, "2: 1-3 kg arası":2, "3: Kilo kaybı yok":3}.items(), format_func=lambda x: x[0])[1]
mna_c = st.selectbox("C. Hareketlilik?", {"0: Yatağa bağımlı":0, "1: Evden çıkamaz":1, "2: Evden çıkabilir":2}.items(), format_func=lambda x: x[0])[1]
mna_d = st.selectbox("D. Psikolojik stres/akut hastalık?", {"0: Evet":0, "2: Hayır":2}.items(), format_func=lambda x: x[0])[1]
mna_e = st.selectbox("E. Nöropsikolojik problemler?", {"0: Ciddi bunama":0, "1: Hafif bunama":1, "2: Problem yok":2}.items(), format_func=lambda x: x[0])[1]
mna_f = st.selectbox("F. Vücut Kitle İndeksi (VKİ)?", {"0: <19":0, "1: 19-20.9":1, "2: 21-22.9":2, "3: ≥23":3}.items(), format_func=lambda x: x[0])[1]
mna_skor = mna_a + mna_b + mna_c + mna_d + mna_e + mna_f
st.success(f"**MNA TARAMA SKORU:** {mna_skor} / 14")

# --- 7. FRAIL Ölçeği ---
st.header("7. FRAIL Ölçeği")
frail_1 = st.selectbox("Yorgunluk", {"Her zaman / Çoğu zaman":1, "Bazen / Çok az / Hiçbir zaman":0}.items(), format_func=lambda x: x[0])[1]
frail_2 = st.selectbox("Direnç (Merdiven çıkma zorluğu)", {"Evet":1, "Hayır":0}.items(), format_func=lambda x: x[0])[1]
frail_3 = st.selectbox("Dolaşma (Yürüme zorluğu)", {"Evet":1, "Hayır":0}.items(), format_func=lambda x: x[0])[1]
frail_4 = st.selectbox("Hastalık (5 ve üzeri var mı?)", {"5-11 hastalık":1, "0-4 hastalık":0}.items(), format_func=lambda x: x[0])[1]
frail_5 = st.selectbox("Kilo Kaybı (Son 1 yılda >= %5)", {"Evet (≥%5)":1, "Hayır (<%5)":0}.items(), format_func=lambda x: x[0])[1]
frail_skor = frail_1 + frail_2 + frail_3 + frail_4 + frail_5
st.success(f"**TOPLAM FRAIL SKORU:** {frail_skor} / 5")

# --- TSFI HESAPLAMA FONKSİYONU ---
def tsfi_hesapla(prefix):
    st.subheader("Eşlik Eden Hastalıklar")
    kanser = st.selectbox(f"Kanser ({prefix})", {"Yok (0)":0, "Evet (1)":1}.items(), format_func=lambda x: x[0], key=f"{prefix}_kanser")[1]
    kah = st.selectbox(f"Koroner Arter ({prefix})", {"Yok (0)":0, "İlaç tedavisi (0.25)":0.25, "PCI (0.5)":0.5, "CABG (0.75)":0.75, "MI (1)":1}.items(), format_func=lambda x: x[0], key=f"{prefix}_kah")[1]
    demans = st.selectbox(f"Demans ({prefix})", {"Yok (0)":0, "Hafif (0.25)":0.25, "Orta (0.5)":0.5, "Ağır (1)":1}.items(), format_func=lambda x: x[0], key=f"{prefix}_demans")[1]
    
    st.subheader("Günlük Yaşam Aktiviteleri")
    k_bakim = st.selectbox(f"Kişisel bakımda yardım ({prefix})", {"Hayır (0)":0, "Evet (1)":1}.items(), format_func=lambda x: x[0], key=f"{prefix}_kbakim")[1]
    para = st.selectbox(f"Para yönetimi yardım ({prefix})", {"Hayır (0)":0, "Evet (1)":1}.items(), format_func=lambda x: x[0], key=f"{prefix}_para")[1]
    ev_isi = st.selectbox(f"Ev işleri yardım ({prefix})", {"Hayır (0)":0, "Evet (1)":1}.items(), format_func=lambda x: x[0], key=f"{prefix}_evisi")[1]
    tuvalet = st.selectbox(f"Tuvalet yardım ({prefix})", {"Hayır (0)":0, "Evet (1)":1}.items(), format_func=lambda x: x[0], key=f"{prefix}_tuvalet")[1]
    yurume = st.selectbox(f"Yürürken yardım ({prefix})", {"Yok (0)":0, "Baston (0.75)":0.75, "Yürüteç (0.5)":0.5, "Tekerlekli sandalye (1)":1}.items(), format_func=lambda x: x[0], key=f"{prefix}_yurume")[1]
    
    st.subheader("Sağlık Tutumu (Kendini daha az...)")
    tut_secenek = {"Hiçbir zaman (0)":0, "Bazen (0.5)":0.5, "Çoğu zaman (1)":1}
    yararli = st.selectbox(f"Yararlı hissetme ({prefix})", tut_secenek.items(), format_func=lambda x: x[0], key=f"{prefix}_yararli")[1]
    uzgun = st.selectbox(f"Üzgün hissetme ({prefix})", tut_secenek.items(), format_func=lambda x: x[0], key=f"{prefix}_uzgun")[1]
    caba = st.selectbox(f"Çaba harcama ({prefix})", tut_secenek.items(), format_func=lambda x: x[0], key=f"{prefix}_caba")[1]
    yalniz = st.selectbox(f"Yalnız hissetme ({prefix})", tut_secenek.items(), format_func=lambda x: x[0], key=f"{prefix}_yalniz")[1]
    dusme = st.selectbox(f"Düşmeler ({prefix})", {"Yok (0)":0, "Var, son 1 ayda değil (0.5)":0.5, "Son 1 ayda (1)":1}.items(), format_func=lambda x: x[0], key=f"{prefix}_dusme")[1]
    
    st.subheader("Fonksiyon ve Beslenme")
    cinsel = st.selectbox(f"Cinsel olarak aktif ({prefix})", {"Evet (0)":0, "Hayır (1)":1}.items(), format_func=lambda x: x[0], key=f"{prefix}_cinsel")[1]
    albumin = st.selectbox(f"Albümin ({prefix})", {"≥3g/dl (0)":0, "<3g/dl (1)":1}.items(), format_func=lambda x: x[0], key=f"{prefix}_alb")[1]
    
    tsfi_toplam = sum([kanser, kah, demans, k_bakim, para, ev_isi, tuvalet, yurume, yararli, uzgun, caba, yalniz, dusme, cinsel, albumin])
    frailty_indeks = tsfi_toplam / 15.0
    durum = "Frail (>0.25)" if frailty_indeks > 0.25 else "Non-frail (≤0.25)"
    
    st.info(f"**{prefix} TSFI Skoru:** {tsfi_toplam} / 15  |  **İndeks:** {frailty_indeks:.2f}  |  **Durum:** {durum}")
    return tsfi_toplam, frailty_indeks, durum

# --- 8 & 9. TSFI (Hasta ve Yakını) ---
st.header("8 & 9. TSFI (Travma Spesifik Frailty İndeksi)")
tab1, tab2 = st.tabs(["1. Ölçüm (Hasta - Kendisi)", "2. Ölçüm (Hasta Yakını)"])
with tab1:
    tsfi_hasta_skor, tsfi_hasta_indeks, tsfi_hasta_durum = tsfi_hesapla("HASTA")
with tab2:
    tsfi_yakini_skor, tsfi_yakini_indeks, tsfi_yakini_durum = tsfi_hesapla("YAKIN")

# --- 10. Klinik Sonlanımlar ---
st.header("10. Klinik Sonlanımlar")
morbidite = st.selectbox("Morbidite (Komplikasyon) Gelişimi", ["Hayır", "Evet"])
morbidite_turu = st.text_input("Morbidite Türü (Varsa)")
taburculuk = st.selectbox("Taburculuk Durumu", ["Eve", "Servise", "Yoğun Bakıma", "Exitus"])

# --- Veri Kaydetme ve Excel İndirme ---
st.markdown("---")
if st.button("💾 Hastayı Kaydet ve Verisetine Ekle", use_container_width=True):
    yeni_kayit = {
        "Barkod": barkod, "İsim Soyisim": isim_soyisim, "TC": tc_kimlik, "Yaş": yas, "Cinsiyet": cinsiyet,
        "Yaralanma Türü": yaralanma_turu, "Mekanizma": yaralanma_mekanizmasi,
        "GKS Toplam": gks_toplam, "Nabız": nabiz, "Solunum": solunum, "Ateş": ates, "MAP": map_degeri, "SpO2": spo2,
        "ISS Skoru": iss_skoru,
        "Sağ Ekskürsiyon": sag_ekskursiyon, "Sağ TF": sag_tf, "Sol Ekskürsiyon": sol_ekskursiyon, "Sol TF": sol_tf,
        "CCI Skoru": cci_skor,
        "MNA Skoru": mna_skor,
        "FRAIL Skoru": frail_skor,
        "TSFI Hasta Skoru": tsfi_hasta_skor, "TSFI Hasta İndeks": tsfi_hasta_indeks, "TSFI Hasta Durum": tsfi_hasta_durum,
        "TSFI Yakını Skoru": tsfi_yakini_skor, "TSFI Yakını İndeks": tsfi_yakini_indeks, "TSFI Yakını Durum": tsfi_yakini_durum,
        "Morbidite": morbidite, "Taburculuk": taburculuk
    }
    st.session_state['hasta_verileri'].append(yeni_kayit)
    st.success(f"{isim_soyisim} isimli hastanın verileri başarıyla eklendi! Toplam hasta sayısı: {len(st.session_state['hasta_verileri'])}")

# Kaydedilen Verileri Gösterme ve Excel Export
if st.session_state['hasta_verileri']:
    st.subheader("Kaydedilen Veriler Önizleme")
    df = pd.DataFrame(st.session_state['hasta_verileri'])
    st.dataframe(df)

    # Excel'e çevirme işlemi (Hafızada)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="CRF_Verileri")
    
    st.download_button(
        label="📥 Tüm Verileri Excel Olarak İndir",
        data=buffer.getvalue(),
        file_name="TSFI_Calisma_Veriseti.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )