import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="BIST100 Canlı Alım ve Emir Paneli", page_icon="📈", layout="wide"
)

# Mobil uyumlu şık tasarım için CSS
st.markdown(
    """
    <style>
    .dataframe {font-size: 12px !important;}
    </style>
""",
    unsafe_allow_html=True,
)

st.title("🚀 BIST100 Profesyonel Alım ve Grafik Paneli")
st.markdown(
    "Canlı tarama sonuçlarından bir hisse seçerek detaylı fiyat ve EMA"
    " grafiklerini inceleyebilirsiniz."
)

# Taranacak Başlıca BIST Hisseleri
bist_hisseleri = [
    "THYAO.IS",
    "GARAN.IS",
    "AKBNK.IS",
    "EREGL.IS",
    "KCHOL.IS",
    "BIMAS.IS",
    "TUPRS.IS",
    "ASELS.IS",
    "FROTO.IS",
    "SAHOL.IS",
    "YKBNK.IS",
    "SISE.IS",
    "PETKM.IS",
    "KRDMD.IS",
]

st.sidebar.header("Kontrol Paneli")
stop_loss_orani = (
    st.sidebar.slider("Stop-Loss Oranı (%)", 1.0, 10.0, 4.0, 0.5) / 100
)

# Verileri çekme ve işleme fonksiyonu
@st.cache_data(ttl=300)  # 5 dakika önbellek
def veri_tara():
  sinyal_listesi = []
  ham_veriler = {}
  data = yf.download(
      bist_hisseleri, period="6m", interval="1d", progress=False
  )["Close"]

  for hisse in bist_hisseleri:
    try:
      if hisse in data.columns:
        df = data[hisse].dropna()
        if len(df) > 50:
          ham_veriler[hisse] = df
          ema20 = df.ewm(span=20, adjust=False).mean()
          delta = df.diff()
          gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
          loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
          rs = gain / loss
          rsi = 100 - (100 / (1 + rs))

          son_fiyat = float(df.iloc[-1])
          son_ema20 = float(ema20.iloc[-1])
          son_rsi = float(rsi.iloc[-1])

          if son_fiyat > son_ema20 and 40 < son_rsi < 70:
            stop_loss_fiyati = son_fiyat * (1 - stop_loss_orani)
            sinyal_listesi.append({
                "Hisse": hisse.replace(".IS", ""),
                "Fiyat": round(son_fiyat, 2),
                f"SL(%{int(stop_loss_orani*100)})": round(stop_loss_fiyati, 2),
                "RSI": round(son_rsi, 1),
            })
    except:
      continue
  return pd.DataFrame(sinyal_listesi), ham_veriler


if st.sidebar.button("🔄 Canlı Verileri Tara ve Güncelle"):
  st.session_state["tara"] = True

if "tara" in st.session_state and st.session_state["tara"]:
  with st.spinner("Piyasa taranıyor ve veriler hazırlanıyor..."):
    df_sonuc, ham_Veri_sozlugu = veri_tara()

    if not df_sonuc.empty:
      st.success(
          f"Tarama tamamlandı! Kriterlere uyan toplam {len(df_sonuc)} hisse"
          " listeleniyor."
      )
      st.dataframe(df_sonuc, use_container_width=True, hide_index=True)

      st.markdown("---")
      st.subheader("📊 Hisse Teknik Grafik İncelemesi")

      # Kullanıcının listeden detayını görmek istediği hisseyi seçmesi için kutu
      secilen_hisse = st.selectbox(
          "Grafiğini incelemek istediğiniz hisseyi seçin:",
          df_sonuc["Hisse"].tolist(),
      )

      if secilen_hisse:
        hisse_tam_adi = secilen_hisse + ".IS"
        if hisse_tam_adi in ham_Veri_sozlugu:
          hisse_df = ham_Veri_sozlugu[hisse_tam_adi]

          # EMA Hesaplamaları
          ema20 = hisse_df.ewm(span=20, adjust=False).mean()
          ema50 = hisse_df.ewm(span=50, adjust=False).mean()

           grafik_df = pd.DataFrame({
              "Fiyat": hisse_df,
              "EMA 20": ema20,
              "EMA 50": ema50,
          })

          st.line_chart(grafik_df)
          st.caption(
              f"📌 {secilen_hisse} varlığına ait son dönem Fiyat ve Hareketli"
              " Ortalama (EMA) Grafiği"
          )
    else:
      st.warning("Şu anki koşullarda filtreye uyan hisse bulunamadı.")
else:
  st.info(
      "Sol menüdeki **'Canlı Verileri Tara ve Güncelle'** butonuna basarak"
      " analizi başlatın."
  )