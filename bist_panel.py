import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="BIST100 Canlı Alım ve Emir Paneli", page_icon="📈", layout="wide"
)

# Mobil uyumlu şık tasarım ve tablo ayarları
st.markdown(
    """
    <style>
    .dataframe {font-size: 12px !important;}
    [data-testid="stHorizontalBlock"] {gap: 0rem;}
    .stExpander {background-color: #1e1e1e; border-radius: 8px; margin-bottom: 10px;}
    </style>
""",
    unsafe_allow_html=True,
)

st.title("🚀 BIST100 Canlı Alım ve Emir Paneli")
st.markdown(
    "Bu panel; canlı verilerle EMA(20) ve RSI(14) stratejisine göre sinyal"
    " üretir, emir ve stop seviyelerini hesaplar."
)

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
kar_al_orani = st.sidebar.slider("Kar Al (Hedef) Oranı (%)", 2.0, 20.0, 8.0, 0.5) / 100

if st.sidebar.button("🔄 Canlı Verileri Tara"):
  with st.spinner("Piyasadan canlı veriler taranıyor ve analiz ediliyor..."):
    sinyal_listesi = {}
    ham_veriler = {}

    data = yf.download(
        bist_hisseleri, period="1y", interval="1d", progress=False
    )["Close"]

    for hisse in bist_hisseleri:
      try:
        if hisse in data.columns:
          df = data[hisse].dropna()
          if len(df) > 200:
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
              temiz_ad = hisse.replace(".IS", "")
              stop_fiyat = son_fiyat * (1 - stop_loss_orani)
              hedef_fiyat = son_fiyat * (1 + kar_al_orani)

              sinyal_listesi[temiz_ad] = {
                  "Fiyat": round(son_fiyat, 2),
                  f"SL(%{int(stop_loss_orani*100)})": round(stop_fiyat, 2),
                  f"Hedef(%{int(kar_al_orani*100)})": round(hedef_fiyat, 2),
                  "RSI": round(son_rsi, 1),
              }
              # Grafik için son 60 günlük veriyi ve EMA'yı saklıyoruz
              gf_df = pd.DataFrame(
                  {"Fiyat": df.tail(60), "EMA20": ema20.tail(60)}
              )
              ham_veriler[temiz_ad] = gf_df
      except Exception as e:
        continue

    if sinyal_listesi:
      st.success(
          f"Tarama tamamlandı! Kriterlere uyan toplam {len(sinyal_listesi)} hisse"
          " listeleniyor."
      )

      # 1. Özet Tablo
      tablo_df = pd.DataFrame.from_dict(sinyal_listesi, orient="index")
      st.dataframe(tablo_df, use_container_width=True)

      st.markdown("---")
      st.subheader("📊 Hisse Bazlı Emir Detayları ve Grafikler")
      st.markdown(
          "Aşağıdan istediğin hisseyi seçerek detaylı emir maliyetlerini ve"
          " fiyat/EMA grafiğini inceleyebilirsin:"
      )

      # 2. Her hisse için ayrı açılır menü (Expander) ve Grafik
      for hisse_adi, detaylar in sinyal_listesi.items():
        with st.expander(f"📌 {hisse_adi} - Detaylar ve Grafik"):
          col1, col2 = st.columns(2)
          with col1:
            st.markdown(f"**Alış / Maliyet:** `{detaylar['Fiyat']} TL`")
            st.markdown(
                f"**Stop-Loss (Satış):**"
                f" `{detaylar[f'SL(%{int(stop_loss_orani*100)})']} TL`"
            )
          with col2:
            st.markdown(
                f"**Hedef (Satış):**"
                f" `{detaylar[f'Hedef(%{int(kar_al_orani*100)})']} TL`"
            )
            st.markdown(f"**RSI Değeri:** `{detaylar['RSI']}`")

          # Grafik Çizimi
          if hisse_adi in ham_veriler:
            st.line_chart(ham_veriler[hisse_adi])

    else:
      st.warning("Şu anki koşullarda filtreye uyan hisse bulunamadı.")