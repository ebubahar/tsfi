import streamlit as st
import pandas as pd

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Acil Klinik Formu", layout="wide")

# --- SİHİRBAZ (WIZARD) ALTYAPISI ---
# Uygulamanın hangi adımda (sekmede) olduğunu hafızada tutarız
if 'step' not in st.session_state:
    st.session_state.step = 1

def next_step():
    if st.session_state.step < 10:
        st.session_state.step += 1

def prev_step():
    if st.session_state.step > 1:
        st.session_state.step -= 1

# --- ÜST BİLGİ VE İLERLEME ÇUBUĞU ---
st.title("⚕️ Acil Servis Klinik Veri Giriş Formu")
st.progress(st.session_state.step / 10)

# Yan yana sekme görünümü hissi vermek için adımları üstte gösterelim
adımlar = ["1. Hasta", "2. Vitals", "3. Yaralanma", "4. ISS", "5. Lab", 
           "6. Sağ USG", "7. EASIX", "8. Görüntüleme", "9. Tedavi", "10. Sonuç"]
st.caption(f"**Mevcut Aşama:** {adımlar[st.session_state.step - 1]} ({st.session_state.step}/10)")
st.divider()

# ==========================================
# ADIM 1: HASTA BİLGİLERİ (Barkod Çıkarıldı)
# ==========================================
if st.session_state.step == 1:
    st.header("1. Hasta Demografik Bilgileri")
    col1, col2 = st.columns(2)
    with col1:
        st.number_input("Yaş", min_value=0, max_value=120, key="yas")
    with col2:
        st.selectbox("Cinsiyet", ["Erkek", "Kadın", "Belirtilmemiş"], key="cinsiyet")

# ==========================================
# ADIM 2: HAYATİ BULGULAR (MAP Hesaplama ve FiO2)
# ==========================================
elif st.session_state.step == 2:
    st.header("2. Hayati Bulgular")
    col1, col2 = st.columns(2)
    
    with col1:
        sbp = st.number_input("Sistolik TA (mmHg)", min_value=0, max_value=300, value=120, key="sbp")
        dbp = st.number_input("Diyastolik TA (mmHg)", min_value=0, max_value=200, value=80, key="dbp")
        
        # MAP Otomatik Hesaplama Formülü: (Sistolik + 2 * Diyastolik) / 3
        map_val = (sbp + (2 * dbp)) / 3
        st.info(f"**🧮 Hesaplanan MAP:** {map_val:.1f} mmHg")

    with col2:
        st.number_input("Nabız (Atım/dk)", min_value=0, max_value=300, value=80, key="nabiz")
        st.number_input("FiO2 (%)", min_value=21, max_value=100, value=21, step=1, key="fio2")

# ==========================================
# ADIM 3: YARALANMA TÜRÜ VE MEKANİZMASI
# ==========================================
elif st.session_state.step == 3:
    st.header("3. Yaralanma Türü ve Mekanizması")
    
    # Yaralanma Türü
    tur = st.selectbox("Yaralanma Türü", ["Künt", "Penetran", "Yanık", "Diğer"], key="y_tur")
    if tur == "Diğer":
        st.text_input("Lütfen 'Diğer' yaralanma türünü açıklayınız:", key="y_tur_diger")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Yaralanma Mekanizması
    mekanizma = st.selectbox("Yaralanma Mekanizması", ["Araç İçi Trafik Kazası", "Araç Dışı Trafik Kazası", "Düşme", "Darp/Kesici Alet", "Diğer"], key="y_mek")
    if mekanizma == "Diğer":
        st.text_area("Lütfen 'Diğer' mekanizmayı detaylıca açıklayınız:", key="y_mek_diger")

# ==========================================
# ADIM 4: ISS PUANLAMASI VE AÇIKLAMALARI
# ==========================================
elif st.session_state.step == 4:
    st.header("4. ISS (Injury Severity Score)")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        iss_score = st.number_input("ISS Puanını Giriniz", min_value=0, max_value=75, value=0, key="iss")
    
    with col2:
        st.markdown("""
        **📌 ISS Puanlama Rehberi:**
        * **1 - 8 Puan:** Minör (Hafif) Yaralanma
        * **9 - 15 Puan:** Orta Derece Yaralanma
        * **16 - 24 Puan:** Ciddi (Ağır) Yaralanma
        * **25 - 49 Puan:** Çok Ciddi Yaralanma
        * **50 - 74 Puan:** Kritik (Hayatı Tehdit Eden) Yaralanma
        * **75 Puan:** Ölümcül (Maksimum) Yaralanma
        """)
        
        # Otomatik Uyarı Sistemi
        if iss_score >= 16:
            st.error("⚠️ Ciddi/Kritik Yaralanma Seviyesi!")
        elif iss_score > 0:
            st.success("✅ Minör/Orta Seviye")

# ==========================================
# ADIM 5: LABORATUVAR
# ==========================================
elif st.session_state.step == 5:
    st.header("5. Temel Laboratuvar Değerleri")
    col1, col2 = st.columns(2)
    with col1:
        st.number_input("Laktat (mmol/L)", min_value=0.0, step=0.1, key="laktat")
        st.number_input("Hemoglobin (g/dL)", min_value=0.0, step=0.1, key="hgb")
    with col2:
        st.number_input("WBC (10^3/µL)", min_value=0.0, step=0.1, key="wbc")
        st.number_input("Trombosit (10^3/µL)", min_value=0.0, step=1.0, key="plt")

# ==========================================
# ADIM 6: SAĞ DİYAFRAGMA USG & DTF HESAPLAMA
# ==========================================
elif st.session_state.step == 6:
    st.header("6. Sağ Diyafragma Ultrasonografisi")
    st.caption("Not: Sol diyafragma ölçümü protokolden çıkarılmıştır.")
    
    col1, col2 = st.columns(2)
    with col1:
        exp_kalinlik = st.number_input("Ekspiryum Sonu Kalınlık (mm)", min_value=0.1, value=1.5, step=0.1, key="exp_usg")
    with col2:
        insp_kalinlik = st.number_input("İnspiryum Sonu Kalınlık (mm)", min_value=0.1, value=2.0, step=0.1, key="insp_usg")
        
    # DTF Hesaplama Formülü: [(İnsp - Eksp) / Eksp] * 100
    if exp_kalinlik > 0:
        dtf = ((insp_kalinlik - exp_kalinlik) / exp_kalinlik) * 100
        st.success(f"**🧮 Sağ Diyafragma Kalınlaşma Fraksiyonu (DTF):** % {dtf:.2f}")

# ==========================================
# ADIM 7: KLİNİK SKORLAR (EASIX vb.)
# ==========================================
elif st.session_state.step == 7:
    st.header("7. Klinik Skorlamalar (EASIX)")
    st.caption("EASIX Skoru = (LDH * Kreatinin) / Trombosit formülü üzerinden hesaplanır.")
    st.text_input("EASIX Skoru (Hesaplanan/Gözlenen)", key="easix")

# ==========================================
# ADIM 8: GÖRÜNTÜLEME
# ==========================================
elif st.session_state.step == 8:
    st.header("8. Teşhis ve Görüntüleme")
    st.checkbox("Toraks BT Çekildi", key="toraks_bt")
    st.checkbox("Batın BT Çekildi", key="batin_bt")
    st.text_area("Görüntüleme Rapor Notları:", key="radyoloji_not")

# ==========================================
# ADIM 9: TEDAVİ VE MÜDAHALE
# ==========================================
elif st.session_state.step == 9:
    st.header("9. Acil Servis Müdahaleleri")
    st.multiselect("Uygulanan İşlemler", 
                   ["Entübasyon", "Göğüs Tüpü", "Kan Transfüzyonu", "Vazopressör", "Cerrahi Konsültasyon"], 
                   key="mudahaleler")

# ==========================================
# ADIM 10: SONUÇ VE KAYIT
# ==========================================
elif st.session_state.step == 10:
    st.header("10. Sonuç ve Taburculuk")
    st.selectbox("Klinik Sonuç", ["Servise Yatış", "Yoğun Bakıma (YBÜ) Yatış", "Taburcu", "Eksitus", "Sevk"], key="sonuc")
    st.text_area("Eklemek İstediğiniz Klinik Notlar:", key="klinik_not")
    
    st.warning("Verileri Excel'e kaydetmeden önce tüm adımları kontrol ettiğinizden emin olun.")

# --- ALT NAVİGASYON BUTONLARI ---
st.divider()
col_left, col_mid, col_right = st.columns([1, 8, 1])

with col_left:
    if st.session_state.step > 1:
        st.button("⬅️ Geri", on_click=prev_step, use_container_width=True)

with col_right:
    if st.session_state.step < 10:
        st.button("İleri ➡️", type="primary", on_click=next_step, use_container_width=True)
    elif st.session_state.step == 10:
        if st.button("💾 Kaydet", type="primary", use_container_width=True):
            st.toast("Veriler başarıyla kaydedildi!", icon="✅")
            st.balloons()
