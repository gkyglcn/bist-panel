# =====================================================================
# BIST100 GÜNLÜK EMİR VE STRATEJİ PANELİ (Yerel / Standalone Sürüm)
# =====================================================================
# Bu dosyayı bilgisayarınızda (terminal üzerinden 'streamlit run bist_panel.py' 
# komutuyla) çalıştırarak tarayıcınızda doğrudan yerel arayüze ulaşabilirsiniz.

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="BIST100 Algoritmik Sinyal Paneli", layout="wide")

st.title("🚀 BIST100 Günlük Alım ve Emir Paneli")
st.markdown("Bu panel, **EMA(20), EMA(50), EMA(200) ve RSI(14)** stratejisine göre güncel sinyal üreten hisseleri listeler.")

# Hafıza alanı (State)
if 'df_signals' not in st.session_state:
    st.session_state.df_signals = None

# Sidebar ayarları
st.sidebar.header("⚙️ Kontrol Paneli")
mode = st.sidebar.radio("Mod Seçimi:", ["Canlı Tarama (BIST)", "Test / Örnek Modu"])

if st.sidebar.button("🔄 Verileri Yükle / Tara"):
    with st.spinner("Piyasa verileri işleniyor, lütfen bekleyin..."):
        if mode == "Test / Örnek Modu":
            # Test verileri
            results = [
                {"Hisse": "THYAO.IS", "Kapanış": 285.50, "Alış": 285.50, "Stop-Loss (%4)": 274.08, "Hedef (%10)": 314.05, "RSI": 52.4},
                {"Hisse": "GARAN.IS", "Kapanış": 112.40, "Alış": 112.40, "Stop-Loss (%4)": 107.90, "Hedef (%10)": 123.64, "RSI": 48.1},
                {"Hisse": "AKBNK.IS", "Kapanış": 64.20, "Alış": 64.20, "Stop-Loss (%4)": 61.63, "Hedef (%10)": 70.62, "RSI": 45.6},
                {"Hisse": "EREGL.IS", "Kapanış": 51.80, "Alış": 51.80, "Stop-Loss (%4)": 49.73, "Hedef (%10)": 56.98, "RSI": 55.2}
            ]
        else:
            # Gerçek BIST Taraması
            tickers = [
                "AKBNK.IS", "ARCLK.IS", "ASELS.IS", "BIMAS.IS", "EKGYO.IS", "ENKAI.IS", "EREGL.IS", 
                "FROTO.IS", "GARAN.IS", "HALKB.IS", "ISCTR.IS", "KCHOL.IS", "KRDMD.IS", "PETKM.IS", 
                "PGSUS.IS", "SAHOL.IS", "SASA.IS", "SISE.IS", "TAVHL.IS", "TCELL.IS", "THYAO.IS", 
                "TOASO.IS", "TUPRS.IS", "VAKBN.IS", "VESTL.IS", "YKBNK.IS"
            ]
            results = []
            for t in tickers:
                try:
                    df = yf.download(t, period="6mo", interval="1d", auto_adjust=True, progress=False)
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    if len(df) > 200:
                        df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
                        df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
                        df["EMA200"] = df["Close"].ewm(span=200, adjust=False).mean()
                        
                        delta = df["Close"].diff()
                        gain = delta.clip(lower=0)
                        loss = -delta.clip(upper=0.0)
                        avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
                        avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
                        rs = avg_gain / avg_loss
                        df["RSI14"] = 100 - (100 / (1 + rs))
                        
                        last = df.iloc[-1]
                        trend_ok = last["EMA50"] > last["EMA200"]
                        dist = abs(last["Close"] - last["EMA20"]) / last["EMA20"]
                        near_ema = dist <= 0.02
                        rsi_ok = 40 <= last["RSI14"] <= 60
                        
                        if trend_ok and (near_ema or rsi_ok):
                            price = float(last["Close"])
                            sl = round(price * 0.96, 2)
                            tp = round(price * 1.10, 2)
                            results.append({
                                "Hisse": t,
                                "Kapanış": round(price, 2),
                                "Alış": round(price, 2),
                                "Stop-Loss (%4)": sl,
                                "Hedef (%10)": tp,
                                "RSI": round(float(last["RSI14"]), 1)
                            })
                except:
                    continue
        st.session_state.df_signals = pd.DataFrame(results)

# Sonuçları ekrana yazdırma
if st.session_state.df_signals is not None:
    if not st.session_state.df_signals.empty:
        st.success(f"Tarama tamamlandı! Toplam {len(st.session_state.df_signals)} hisse listeleniyor.")
        st.dataframe(st.session_state.df_signals, use_container_width=True)
    else:
        st.warning("Seçilen kriterlere uyan aktif sinyal bulunamadı.")
else:
    st.info("Sol menüden modu seçip butona basarak verileri yükleyebilirsiniz.")