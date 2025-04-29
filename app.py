import streamlit as st
import pandas as pd
import joblib

st.set_page_config(page_title="Ev Fiyat Tahmini", layout="centered")

# Model, scaler ve kolonlar yükleniyor
model = joblib.load("xgb_streamlit_model.pkl")
scaler = joblib.load("scaler.pkl")
expected_columns = joblib.load("model_columns.pkl")

st.title("🏡 Ev Fiyat Tahmini Uygulaması")
st.write("Ev özelliklerini girerek tahmini satış fiyatını öğrenin.")

# ------------------------------ #
#          Yapı Bilgileri         #
# ------------------------------ #
with st.expander("🏠 Yapı Bilgileri"):
    col1, col2 = st.columns(2)
    with col1:
        overallqual = st.slider("Evin Genel Kalitesi (1-10)", 1, 10, 5)
        grlivarea_m2 = st.number_input("Yaşanabilir Üst Kat Alanı (m²)", 0, 10000, 140)
        lotarea_m2 = st.number_input("Arsa Alanı (m²)", 0, 10000, 700)
    with col2:
        house_age = st.number_input("Evin Yaşı (Yıl)", 0, 120, 30)
        since_remod = st.number_input("Yenilemeden Bu Yana Geçen Süre (Yıl)", 0, 100, 10)

# ------------------------------ #
#         Konfor Özellikleri      #
# ------------------------------ #
with st.expander("✨ Konfor Özellikleri"):
    col1, col2 = st.columns(2)
    with col1:
        total_bathrooms = st.number_input("Toplam Banyo Sayısı", 0.0, 5.0, 2.0, step=0.5)
        fireplaces = st.number_input("Şömine Sayısı", 0, 5, 1)
    with col2:
        centralair = st.selectbox("Merkezi Klima Var mı?", ["Evet", "Hayır"])
        haspool = st.selectbox("Havuz Var mı?", ["Evet", "Hayır"])
        heating = st.selectbox("Isıtma Tipi", ["Doğalgaz Merkezi", "Doğalgaz Bireysel", "Yerden Isıtma", "Duvar Tipi Isıtma"])

# ------------------------------ #
#           Garaj Bilgileri       #
# ------------------------------ #
with st.expander("🚗 Garaj Bilgileri"):
    col1, col2 = st.columns(2)
    with col1:
        garagecars = st.number_input("Garajda Park Edilebilecek Araç Sayısı", 0, 5, 1)
    with col2:
        garagetype = st.selectbox("Garaj Yapı Tipi", ["Bitişik Garaj", "Müstakil Garaj", "Bina İçi Garaj", "Garaj Yok"])

# ------------------------------ #
#       Dış Alan Özellikleri      #
# ------------------------------ #
with st.expander("🌳 Dış Alan Özellikleri"):
    col1, col2 = st.columns(2)
    with col1:
        total_outdoor_sf_m2 = st.number_input("Toplam Açık Alan (m²)", 0, 10000, 20)
    with col2:
        total_porch_sf_m2 = st.number_input("Veranda Alanı (m²)", 0, 10000, 10)

# ------------------------------ #
#     Lokasyon ve Yapı Tipleri    #
# ------------------------------ #
with st.expander("📍 Lokasyon ve Yapı Tipleri"):
    col1, col2 = st.columns(2)
    with col1:
        neighborhood = st.selectbox("Mahalle Grubu", ["Düşük Gelirli Bölge", "Orta Gelirli Bölge", "Lüks Bölge"])
        housestyle_group = st.selectbox("Ev Yapı Şekli", ["Tek Katlı", "Çok Katlı"])
    with col2:
        mszoning = st.selectbox("İmar Tipi", ["Düşük Yoğunluklu Konut", "Orta Yoğunluklu Konut", "Zengin Konut Bölgesi", "Yüksek Yoğunluklu Konut", "Ticari Alan"])
        foundation = st.selectbox("Temel Yapı Tipi", ["Betonarme", "Beton Blok", "Taş", "Ahşap"])

# ======================= #
#    İşlem ve Tahmin      #
# ======================= #

# Birim dönüşümleri
grlivarea = grlivarea_m2 / 0.092903
lotarea = lotarea_m2 / 0.092903
total_outdoor_sf = total_outdoor_sf_m2 / 0.092903
total_porch_sf = total_porch_sf_m2 / 0.092903

# Binary dönüşümler
centralair = 1 if centralair == "Evet" else 0
haspool = 1 if haspool == "Evet" else 0

# Mapping işlemleri
garagetype_map = {
    "Bitişik Garaj": 0,
    "Müstakil Garaj": 1,
    "Bina İçi Garaj": 2,
    "Garaj Yok": 3
}
mszoning_map = {
    "Düşük Yoğunluklu Konut": 0,
    "Orta Yoğunluklu Konut": 1,
    "Zengin Konut Bölgesi": 2,
    "Yüksek Yoğunluklu Konut": 3,
    "Ticari Alan (C)": 4
}
foundation_map = {
    "Betonarme": 0,
    "Beton Blok": 1,
    "Taş": 2,
    "Ahşap": 3
}
heating_map = {
    "Doğalgaz Merkezi": 0,
    "Doğalgaz Bireysel": 1,
    "Yerçekimi ile Isıtma": 2,
    "Duvar Tipi Isıtma": 3
}

garagetype = garagetype_map[garagetype]
mszoning = mszoning_map[mszoning]
foundation = foundation_map[foundation]
heating = heating_map[heating]

# One-hot encoding işlemleri
housestyle_group_Single = 1 if housestyle_group == "Tek Katlı" else 0
housestyle_group_Split = 1 if housestyle_group == "Çok Katlı" else 0
neighborhood_Low = 1 if neighborhood == "Düşük Gelirli Bölge" else 0
neighborhood_Mid = 1 if neighborhood == "Orta Gelirli Bölge" else 0
neighborhood_Luxury = 1 if neighborhood == "Lüks Bölge" else 0

# Veri çerçevesini oluştur
input_data = pd.DataFrame([{
    "overallqual": overallqual,
    "garagecars": garagecars,
    "fireplaces": fireplaces,
    "total_bathrooms": total_bathrooms,
    "grlivarea": grlivarea,
    "lotarea": lotarea,
    "house_age": house_age,
    "since_remod": since_remod,
    "total_outdoor_sf": total_outdoor_sf,
    "total_porch_sf": total_porch_sf,
    "centralair": centralair,
    "haspool": haspool,
    "garagetype": garagetype,
    "mszoning": mszoning,
    "foundation": foundation,
    "heating": heating,
    "housestyle_group_Single": housestyle_group_Single,
    "housestyle_group_Split": housestyle_group_Split,
    "neighborhood_Low": neighborhood_Low,
    "neighborhood_Mid": neighborhood_Mid,
    "neighborhood_Luxury": neighborhood_Luxury
}])

# Eksik kolonları tamamlama
for col in expected_columns:
    if col not in input_data.columns:
        input_data[col] = 0
input_data = input_data[expected_columns]

# Ölçekleme
input_scaled = scaler.transform(input_data)

# Tahmin
if st.button("Tahmini Fiyatı Hesapla"):
    prediction = model.predict(input_scaled)[0]

    # Özellik bazlı düzeltmeler
    if haspool:
        prediction *= 1.10
    if centralair:
        prediction *= 1.03
    if neighborhood_Luxury:
        prediction *= 1.05

    st.success(f"💰 Tahmini Ev Fiyatı: ${round(prediction):,}")
