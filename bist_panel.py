import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="BIST100 Canlı Alım ve Emir Paneli", page_icon="📈", layout="wide"
)

st.markdown(
    """
    <style>
    .dataframe {font-size: 12px !important;}
    [data-testid="stHorizontalBlock"] {gap: 0rem;}
    </style>
""",
    unsafe_allow_html=True,
)

st.title("🚀 BIST100 Canlı Alım ve Emir Paneli")
st.markdown(
    "Bu panel, seçilen BIST100 hisselerinin güncel verilerini çekerek"
    " EMA(20)/EMA(50)/EMA(200) ve RSI(14) stratejisine göre sinyal üretir."
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

if st.sidebar.button("🔄 Canlı Verileri Tara"):
  with st.spinner("Piyasadan canlı veriler taranıyor..."):
    sinyal_listesi = []
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
              stop_loss_fiyati = son_fiyat * (1 - stop_loss_orani)
              sinyal_listesi.append({
                  "Hisse": hisse.replace(".IS", ""),
                  "Fiyat": round(son_fiyat, 2),
                  f"SL(%{int(stop_loss_orani*100)})": round(
                      stop_loss_fiyati, 2
                  ),
                  "RSI": round(son_rsi, 1),
              })
      except Exception as e:
        continue

    if sinyal_listesi:
      sonuc_df = pd.DataFrame(sinyal_listesi)
      st.success(
          f"Tarama tamamlandı! Kriterlere uyan toplam {len(sonuc_df)} hisse"
          " listeleniyor."
      )
      st.dataframe(sonuc_df, use_container_width=True, hide_index=True)
    else:
      st.warning("Şu anki koşullarda filtreye uyan hisse bulunamadı.")
