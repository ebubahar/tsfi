import streamlit as st
import pandas as pd
import io

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="CRF - TSFI & Diyafram USG", layout="wide")

# --- SİHİRBAZ VE VERİTABANI BAŞLATMA ---
if 'hasta_verileri' not in st.session_state:
    st.session_state['hasta_verileri'] = []

if 'step' not in st.session_state:
    st.session_state.step = 1

def next_step():
    if st.session_state.step < 10:
        st.session_state.step += 1

def prev_step():
    if st.session_state.step > 1:
        st.session_state.step -= 1

# --- ÜST NAVİGASYON ---
st.title("📋 OLGU RAPOR FORMU (CRF)")
st.subheader("TSFI Validasyonu ve Diyafram USG Çalışması")
st.progress(st.session_state.step / 10)

adımlar = ["1. Demografik", "2. Vitals/Yaralanma", "3. ISS", "4. USG", "5. CCI", 
           "6. MNA", "7. FRAIL", "8. TSFI (Hasta)", "9. TSFI (Yakını)", "10. Kayıt"]
st.caption(f"**Yan Yana 10 Sekmeli Görünüm | Mevcut Aşama:** {adımlar[st.session_state.step - 1]} ({st.session_state.step}/10)")
st.divider()

# ==========================================
# ADIM 1: KİMLİK VE DEMOGRAFİK BİLGİLER
# ==========================================
if st.session_state.step == 1:
    st.header("1. Hasta Kimlik ve Demografik Bilgileri")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("İsim Soyisim", key="isim_soyisim")
        st.text_input("TC Kimlik No", key="tc_kimlik")
    with col2:
        st.number_input("Yaş (Yıl)", min_value=0, max_value=120, step=1, key="yas")
        st.selectbox("Cinsiyet", ["Erkek", "Kadın", "Diğer"], key="cinsiyet")

# ==========================================
# ADIM 2: YARALANMA VE VİTAL BULGULAR
# ==========================================
elif st.session_state.step == 2:
    st.header("2. Yaralanma Özellikleri ve Vital Bulgular")
    
    col_y1, col_y2 = st.columns(2)
    with col_y1:
        y_turu = st.selectbox("Yaralanma Türü", ["Künt", "Delici", "Diğer"], key="y_turu")
        if y_turu == "Diğer":
            st.text_input("Lütfen 'Diğer' yaralanma türünü açıklayınız:", key="y_turu_diger")
    with col_y2:
        y_mek = st.selectbox("Yaralanma Mekanizması", ["Düşme", "Trafik Kazası", "Yüksekten Düşme", "Diğer"], key="y_mek")
        if y_mek == "Diğer":
            st.text_input("Lütfen 'Diğer' mekanizmayı açıklayınız:", key="y_mek_diger")
    
    st.markdown("---")
    st.subheader("GKS ve Vital Bulgular")
    
    col_g1, col_g2, col_g3, col_g4 = st.columns(4)
    with col_g1: gks_goz = st.number_input("GKS - Göz", min_value=1, max_value=4, value=4, key="gks_goz")
    with col_g2: gks_motor = st.number_input("GKS - Motor", min_value=1, max_value=6, value=6, key="gks_motor")
    with col_g3: gks_sozel = st.number_input("GKS - Sözel", min_value=1, max_value=5, value=5, key="gks_sozel")
    with col_g4:
        gks_toplam = gks_goz + gks_motor + gks_sozel
        st.info(f"**GKS Toplam:** {gks_toplam}")
        st.session_state['gks_toplam'] = gks_toplam

    st.markdown("<br>", unsafe_allow_html=True)
    col_v1, col_v2, col_v3 = st.columns(3)
    with col_v1:
        st.number_input("Nabız (/dk)", min_value=0, key="nabiz")
        solunum = st.number_input("Solunum (/dk)", min_value=0, value=16, key="solunum")
        st.number_input("Ateş (°C)", value=36.5, format="%.1f", key="ates")
    with col_v2:
        sbp = st.number_input("Sistolik TA (mmHg)", min_value=0, value=120, key="sbp")
        dbp = st.number_input("Diyastolik TA (mmHg)", min_value=0, value=80, key="dbp")
        # MAP Hesaplama: (Sistolik + 2*Diyastolik) / 3
        map_degeri = (sbp + 2 * dbp) / 3
        st.success(f"**🧮 Hesaplanan MAP:** {map_degeri:.1f} mmHg")
        st.session_state['map_degeri'] = map_degeri
    with col_v3:
        spo2 = st.number_input("SpO2 (%)", min_value=0, max_value=100, value=98, key="spo2")
        fio2 = st.number_input("FiO2 (%)", min_value=21, max_value=100, value=21, key="fio2")
        # ROX İndeksi Hesaplama: (SpO2 / FiO2(ondalık)) / Solunum Sayısı
        if solunum > 0:
            rox = (spo2 / (fio2 / 100.0)) / solunum
            st.success(f"**🧮 Hesaplanan ROX İndeksi:** {rox:.2f}")
            st.session_state['rox_indeksi'] = rox
        else:
            st.warning("ROX hesabı için solunum sayısı giriniz.")
            st.session_state['rox_indeksi'] = 0.0

# ==========================================
# ADIM 3: ISS (YARALANMA ŞİDDETİ SKORU)
# ==========================================
elif st.session_state.step == 3:
    st.header("3. Yaralanma Şiddeti Skoru (ISS) Hesaplaması")
    st.write("Kural: En ciddi yaralanan 3 bölgenin AIS (1-6) puanlarının kareleri toplamı. AIS 6 varsa ISS direkt 75'tir.")

    ais_options = [0, 1, 2, 3, 4, 5, 6]
    col_ais1, col_ais2, col_ais3 = st.columns([1, 1, 1.5])
    
    with col_ais1:
        ais_bb = st.selectbox("Baş ve Boyun AIS", ais_options, key="ais_bb")
        ais_yuz = st.selectbox("Yüz AIS", ais_options, key="ais_yuz")
        ais_gogus = st.selectbox("Göğüs AIS", ais_options, key="ais_gogus")
    with col_ais2:
        ais_karin = st.selectbox("Karın / Pelvik AIS", ais_options, key="ais_karin")
        ais_ekst = st.selectbox("Ekstremiteler AIS", ais_options, key="ais_ekst")
        ais_dis = st.selectbox("Dışsal AIS", ais_options, key="ais_dis")

    ais_listesi = [ais_bb, ais_yuz, ais_gogus, ais_karin, ais_ekst, ais_dis]
    if 6 in ais_listesi:
        iss_skoru = 75
    else:
        ais_sirali = sorted(ais_listesi, reverse=True)
        iss_skoru = sum([x**2 for x in ais_sirali[:3]])
    
    st.session_state['iss_skoru'] = iss_skoru
    
    with col_ais3:
        st.success(f"**🧮 Hesaplanan ISS Skoru:** {iss_skoru}")
        st.markdown("""
        **📌 ISS Puan Anlamları:**
        * **1 - 8 Puan:** Minör Yaralanma
        * **9 - 15 Puan:** Orta Derece Yaralanma
        * **16 - 24 Puan:** Ciddi (Ağır) Yaralanma
        * **25 - 49 Puan:** Çok Ciddi Yaralanma
        * **50 - 74 Puan:** Kritik Yaralanma
        * **75 Puan:** Ölümcül Yaralanma
        """)

# ==========================================
# ADIM 4: SAĞ DİYAFRAM USG (DTF OTO HESAP)
# ==========================================
elif st.session_state.step == 4:
    st.header("4. Sağ Diyafram USG Değerlendirmesi")
    st.caption("Not: Çalışma protokolü gereği sadece Sağ Diyafram ölçümleri alınmaktadır.")
    
    col_usg1, col_usg2 = st.columns(2)
    with col_usg1:
        sag_eksk = st.number_input("Sağ Diyafragmatik Ekskürsiyon (cm)", min_value=0.0, format="%.2f", key="sag_eksk")
        sag_end_insp = st.number_input("Sağ Kalınlık - End-İnspiryum (cm)", min_value=0.0, format="%.2f", key="sag_end_insp")
        sag_end_eksp = st.number_input("Sağ Kalınlık - End-Ekspiryum (cm)", min_value=0.0, format="%.2f", key="sag_end_eksp")
    with col_usg2:
        # DTF (Kalınlaşma Fraksiyonu) Hesaplama Formülü
        if sag_end_eksp > 0:
            dtf = ((sag_end_insp - sag_end_eksp) / sag_end_eksp) * 100
            st.success(f"**🧮 Sağ Kalınlaşma Fraksiyonu (DTF):** % {dtf:.1f}")
            st.session_state['sag_tf'] = dtf
        else:
            st.warning("DTF otomatik hesabı için End-Ekspiryum değeri 0'dan büyük olmalıdır.")
            st.session_state['sag_tf'] = 0.0
            
        st.text_input("USG Diğer Bulgular", key="usg_diger")

# ==========================================
# ADIM 5: CCI
# ==========================================
elif st.session_state.step == 5:
    st.header("5. Charlson Comorbidity Index (CCI)")
    cci_items = {
        "Geçirilmiş MI": 1, "Konjestif Kalp Yt.": 1, "Periferik Vasküler H.": 1,
        "Serebrovasküler H.": 1, "Demans": 1, "Kronik Akciğer H.": 1, "Romatolojik H.": 1,
        "Peptik Ülser H.": 1, "Hafif Karaciğer H.": 1, "Diyabet": 1,
        "Hemipleji": 2, "Orta-Ağır Böbrek H.": 2, "Komplikasyonlu Diyabet": 2,
        "Metastazsız Kanser": 2, "Lösemi": 2, "Lenfoma": 2,
        "Orta-Ağır Karaciğer H.": 3, "Metastatik Solid Tümör": 6, "AIDS": 6
    }
    cci_skor = 0
    col_c1, col_c2, col_c3 = st.columns(3)
    for i, (hastalik, puan) in enumerate(cci_items.items()):
        with [col_c1, col_c2, col_c3][i % 3]:
            secili = st.checkbox(f"{hastalik} ({puan} Puan)", key=f"cci_{i}")
            if secili: cci_skor += puan
    st.success(f"**TOPLAM CCI SKORU:** {cci_skor}")
    st.session_state['cci_skor'] = cci_skor

# ==========================================
# ADIM 6: MNA
# ==========================================
elif st.session_state.step == 6:
    st.header("6. Mini Nütrisyonel Değerlendirme (MNA)")
    mna_a = st.selectbox("A. Besin alımında azalma?", {"0: Şiddetli düşüş":0, "1: Orta derece düşüş":1, "2: Düşüş yok":2}.items(), format_func=lambda x: x[0], key="mna_a")[1]
    mna_b = st.selectbox("B. Son 3 ay kilo kaybı?", {"0: >3 kg":0, "1: Bilinmiyor":1, "2: 1-3 kg arası":2, "3: Kilo kaybı yok":3}.items(), format_func=lambda x: x[0], key="mna_b")[1]
    mna_c = st.selectbox("C. Hareketlilik?", {"0: Yatağa bağımlı":0, "1: Evden çıkamaz":1, "2: Evden çıkabilir":2}.items(), format_func=lambda x: x[0], key="mna_c")[1]
    mna_d = st.selectbox("D. Psikolojik stres/akut hastalık?", {"0: Evet":0, "2: Hayır":2}.items(), format_func=lambda x: x[0], key="mna_d")[1]
    mna_e = st.selectbox("E. Nöropsikolojik problemler?", {"0: Ciddi bunama":0, "1: Hafif bunama":1, "2: Problem yok":2}.items(), format_func=lambda x: x[0], key="mna_e")[1]
    mna_f = st.selectbox("F. Vücut Kitle İndeksi (VKİ)?", {"0: <19":0, "1: 19-20.9":1, "2: 21-22.9":2, "3: ≥23":3}.items(), format_func=lambda x: x[0], key="mna_f")[1]
    mna_skor = mna_a + mna_b + mna_c + mna_d + mna_e + mna_f
    st.success(f"**MNA TARAMA SKORU:** {mna_skor} / 14")
    st.session_state['mna_skor'] = mna_skor

# ==========================================
# ADIM 7: FRAIL
# ==========================================
elif st.session_state.step == 7:
    st.header("7. FRAIL Ölçeği")
    frail_1 = st.selectbox("Yorgunluk", {"Her zaman / Çoğu zaman":1, "Bazen / Çok az / Hiçbir zaman":0}.items(), format_func=lambda x: x[0], key="frail_1")[1]
    frail_2 = st.selectbox("Direnç (Merdiven çıkma zorluğu)", {"Evet":1, "Hayır":0}.items(), format_func=lambda x: x[0], key="frail_2")[1]
    frail_3 = st.selectbox("Dolaşma (Yürüme zorluğu)", {"Evet":1, "Hayır":0}.items(), format_func=lambda x: x[0], key="frail_3")[1]
    frail_4 = st.selectbox("Hastalık (5 ve üzeri var mı?)", {"5-11 hastalık":1, "0-4 hastalık":0}.items(), format_func=lambda x: x[0], key="frail_4")[1]
    frail_5 = st.selectbox("Kilo Kaybı (Son 1 yılda >= %5)", {"Evet (≥%5)":1, "Hayır (<%5)":0}.items(), format_func=lambda x: x[0], key="frail_5")[1]
    frail_skor = frail_1 + frail_2 + frail_3 + frail_4 + frail_5
    st.success(f"**TOPLAM FRAIL SKORU:** {frail_skor} / 5")
    st.session_state['frail_skor'] = frail_skor

# ==========================================
# ADIM 8 & 9 İÇİN TSFI HESAPLAMA FONKSİYONU
# ==========================================
def tsfi_hesapla_form(prefix):
    st.subheader("Eşlik Eden Hastalıklar")
    kanser = st.selectbox("Kanser", {"Yok (0)":0, "Evet (1)":1}.items(), format_func=lambda x: x[0], key=f"{prefix}_kanser")[1]
    kah = st.selectbox("Koroner Arter", {"Yok (0)":0, "İlaç tedavisi (0.25)":0.25, "PCI (0.5)":0.5, "CABG (0.75)":0.75, "MI (1)":1}.items(), format_func=lambda x: x[0], key=f"{prefix}_kah")[1]
    demans = st.selectbox("Demans", {"Yok (0)":0, "Hafif (0.25)":0.25, "Orta (0.5)":0.5, "Ağır (1)":1}.items(), format_func=lambda x: x[0], key=f"{prefix}_demans")[1]
    
    st.subheader("Günlük Yaşam Aktiviteleri")
    k_bakim = st.selectbox("Kişisel bakımda yardım", {"Hayır (0)":0, "Evet (1)":1}.items(), format_func=lambda x: x[0], key=f"{prefix}_kbakim")[1]
    para = st.selectbox("Para yönetimi yardım", {"Hayır (0)":0, "Evet (1)":1}.items(), format_func=lambda x: x[0], key=f"{prefix}_para")[1]
    ev_isi = st.selectbox("Ev işleri yardım", {"Hayır (0)":0, "Evet (1)":1}.items(), format_func=lambda x: x[0], key=f"{prefix}_evisi")[1]
    tuvalet = st.selectbox("Tuvalet yardım", {"Hayır (0)":0, "Evet (1)":1}.items(), format_func=lambda x: x[0], key=f"{prefix}_tuvalet")[1]
    yurume = st.selectbox("Yürürken yardım", {"Yok (0)":0, "Baston (0.75)":0.75, "Yürüteç (0.5)":0.5, "Tekerlekli sandalye (1)":1}.items(), format_func=lambda x: x[0], key=f"{prefix}_yurume")[1]
    
    st.subheader("Sağlık Tutumu (Kendini daha az...)")
    tut_secenek = {"Hiçbir zaman (0)":0, "Bazen (0.5)":0.5, "Çoğu zaman (1)":1}
    yararli = st.selectbox("Yararlı hissetme", tut_secenek.items(), format_func=lambda x: x[0], key=f"{prefix}_yararli")[1]
    uzgun = st.selectbox("Üzgün hissetme", tut_secenek.items(), format_func=lambda x: x[0], key=f"{prefix}_uzgun")[1]
    caba = st.selectbox("Çaba harcama", tut_secenek.items(), format_func=lambda x: x[0], key=f"{prefix}_caba")[1]
    yalniz = st.selectbox("Yalnız hissetme", tut_secenek.items(), format_func=lambda x: x[0], key=f"{prefix}_yalniz")[1]
    dusme = st.selectbox("Düşmeler", {"Yok (0)":0, "Var, son 1 ayda değil (0.5)":0.5, "Son 1 ayda (1)":1}.items(), format_func=lambda x: x[0], key=f"{prefix}_dusme")[1]
    
    st.subheader("Fonksiyon ve Beslenme")
    cinsel = st.selectbox("Cinsel olarak aktif", {"Evet (0)":0, "Hayır (1)":1}.items(), format_func=lambda x: x[0], key=f"{prefix}_cinsel")[1]
    albumin = st.selectbox("Albümin", {"≥3g/dl (0)":0, "<3g/dl (1)":1}.items(), format_func=lambda x: x[0], key=f"{prefix}_alb")[1]
    
    tsfi_toplam = sum([kanser, kah, demans, k_bakim, para, ev_isi, tuvalet, yurume, yararli, uzgun, caba, yalniz, dusme, cinsel, albumin])
    frailty_indeks = tsfi_toplam / 15.0
    durum = "Frail (>0.25)" if frailty_indeks > 0.25 else "Non-frail (≤0.25)"
    
    st.info(f"**{prefix} TSFI Skoru:** {tsfi_toplam} / 15  |  **İndeks:** {frailty_indeks:.2f}  |  **Durum:** {durum}")
    st.session_state[f'{prefix}_skor'] = tsfi_toplam
    st.session_state[f'{prefix}_indeks'] = frailty_indeks
    st.session_state[f'{prefix}_durum'] = durum

# ==========================================
# ADIM 8: TSFI (HASTA)
# ==========================================
elif st.session_state.step == 8:
    st.header("8. TSFI (Travma Spesifik Frailty İndeksi) - Hasta Kendisi")
    tsfi_hesapla_form("HASTA")

# ==========================================
# ADIM 9: TSFI (YAKINI)
# ==========================================
elif st.session_state.step == 9:
    st.header("9. TSFI (Travma Spesifik Frailty İndeksi) - Hasta Yakını")
    tsfi_hesapla_form("YAKIN")

# ==========================================
# ADIM 10: SONLANIMLAR VE KAYIT
# ==========================================
elif st.session_state.step == 10:
    st.header("10. Klinik Sonlanımlar ve Kayıt İşlemi")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.selectbox("Morbidite (Komplikasyon) Gelişimi", ["Hayır", "Evet"], key="morbidite")
        st.text_input("Morbidite Türü (Varsa)", key="morbidite_turu")
    with col_s2:
        st.selectbox("Taburculuk Durumu", ["Eve", "Servise", "Yoğun Bakıma", "Exitus"], key="taburculuk")

    st.markdown("---")
    
    if st.button("💾 Hastayı Kaydet ve Verisetine Ekle", use_container_width=True, type="primary"):
        yeni_kayit = {
            "İsim Soyisim": st.session_state.get('isim_soyisim', ''), 
            "TC": st.session_state.get('tc_kimlik', ''), 
            "Yaş": st.session_state.get('yas', 0), 
            "Cinsiyet": st.session_state.get('cinsiyet', ''),
            "Yaralanma Türü": st.session_state.get('y_turu', ''),
            "Yaralanma Türü Detay": st.session_state.get('y_turu_diger', ''),
            "Mekanizma": st.session_state.get('y_mek', ''),
            "Mekanizma Detay": st.session_state.get('y_mek_diger', ''),
            "GKS Toplam": st.session_state.get('gks_toplam', 0), 
            "Nabız": st.session_state.get('nabiz', 0), 
            "Solunum": st.session_state.get('solunum', 0), 
            "Ateş": st.session_state.get('ates', 0), 
            "Sistolik TA": st.session_state.get('sbp', 0),
            "Diyastolik TA": st.session_state.get('dbp', 0),
            "MAP (Oto)": st.session_state.get('map_degeri', 0), 
            "SpO2": st.session_state.get('spo2', 0),
            "FiO2 (%)": st.session_state.get('fio2', 21),
            "ROX İndeksi (Oto)": st.session_state.get('rox_indeksi', 0),
            "ISS Skoru (Oto)": st.session_state.get('iss_skoru', 0),
            "Sağ Ekskürsiyon": st.session_state.get('sag_eksk', 0), 
            "Sağ DTF (%)": st.session_state.get('sag_tf', 0),
            "CCI Skoru": st.session_state.get('cci_skor', 0),
            "MNA Skoru": st.session_state.get('mna_skor', 0),
            "FRAIL Skoru": st.session_state.get('frail_skor', 0),
            "TSFI Hasta Skoru": st.session_state.get('HASTA_skor', 0), 
            "TSFI Hasta İndeks": st.session_state.get('HASTA_indeks', 0),
            "TSFI Yakını Skoru": st.session_state.get('YAKIN_skor', 0), 
            "TSFI Yakını İndeks": st.session_state.get('YAKIN_indeks', 0),
            "Morbidite": st.session_state.get('morbidite', ''), 
            "Morbidite Detay": st.session_state.get('morbidite_turu', ''),
            "Taburculuk": st.session_state.get('taburculuk', '')
        }
        st.session_state['hasta_verileri'].append(yeni_kayit)
        st.success(f"✅ Veriler başarıyla eklendi! Toplam kayıt: {len(st.session_state['hasta_verileri'])}")
        st.balloons()

    # Veri İndirme Bölümü
    if st.session_state['hasta_verileri']:
        st.subheader("Kaydedilen Veriler Önizleme")
        df = pd.DataFrame(st.session_state['hasta_verileri'])
        st.dataframe(df)

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

# --- ALT NAVİGASYON (İLERİ/GERİ BUTONLARI) ---
st.divider()
col_left, col_mid, col_right = st.columns([1, 8, 1])

with col_left:
    if st.session_state.step > 1:
        st.button("⬅️ Geri", on_click=prev_step, use_container_width=True)

with col_right:
    if st.session_state.step < 10:
        st.button("İleri ➡️", type="primary", on_click=next_step, use_container_width=True)
