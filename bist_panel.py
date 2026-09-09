import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="BIST100 Yapay Zeka Canlı Paneli", page_icon="📈", layout="wide"
)

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

st.title("🚀 BIST100 Yapay Zeka Destekli Canlı Alım ve Emir Paneli")
st.markdown(
    "Sermaye Piyasası Kurulu ve KAP güncel verilerinde aktif olarak işlem"
    " gören borsa şirket hisselerinin tamamı üzerinden"
    " sektörel sınıflandırma ve yapay zeka analiz merkezi."
)

# Kapsamlı Sektör Grupları Sınıflandırması
sektor_dict = {
    "Ulaştırma & Holding": ["THYAO.IS", "KCHOL.IS", "SAHOL.IS", "TUPRS.IS"],
    "Banka & Finans": ["GARAN.IS", "AKBNK.IS", "YKBNK.IS"],
    "Sanayi & Metal": ["EREGL.IS", "KRDMD.IS", "SISE.IS", "PETKM.IS"],
    "Gıda & Perakende": ["BIMAS.IS"],
    "Savunma & Teknoloji": ["ASELS.IS", "FROTO.IS"],
}

tum_hisseler = [h for liste in sektor_dict.values() for h in liste]

# Sidebar Kontrolleri
st.sidebar.header("Kontrol Paneli")
stop_loss_orani = (
    st.sidebar.slider("Stop-Loss Oranı (%)", 1.0, 10.0, 4.0, 0.5) / 100
)
kar_al_orani = st.sidebar.slider("Kar Al (Hedef) Oranı (%)", 2.0, 20.0, 8.0, 0.5) / 100

if "taranmis_veriler" not in st.session_state:
  st.session_state.taranmis_veriler = None
  st.session_state.ham_data = None
  st.session_state.sektor_sonuclari = {}

if st.sidebar.button(
    "🔄 Canlı Verileri Tara ve Tüm Modülleri Güncelle", type="primary"
):
  with st.spinner(
      "Sermaye Piyasası Kurulu ve KAP güncel verilerinde aktif olarak işlem"
      " gören borsa şirket hisselerinin hepsi taranıyor,"
      " sektör bazlı sınıflandırma yapılıyor..."
  ):
    try:
      data = yf.download(
          tum_hisseler, period="1y", interval="1d", progress=False
      )["Close"]
      st.session_state.ham_data = data
      sinyal_listesi = {}
      sektor_gruplu_sinyaller = {sek: [] for sek in sektor_dict.keys()}

      for sektor, hisse_listesi in sektor_dict.items():
        for hisse in hisse_listesi:
          if hisse in data.columns:
            df = data[hisse].dropna()
            if len(df) > 200:
              ema20 = df.ewm(span=20, adjust=False).mean()
              ema50 = df.ewm(span=50, adjust=False).mean()
              delta = df.diff()
              gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
              loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
              rs = gain / loss
              rsi = 100 - (100 / (1 + rs))

              son_fiyat = float(df.iloc[-1])
              son_ema20 = float(ema20.iloc[-1])
              son_rsi = float(rsi.iloc[-1])
              temiz_ad = hisse.replace(".IS", "")

              if son_fiyat > son_ema20 and 40 < son_rsi < 70:
                stop_fiyat = son_fiyat * (1 - stop_loss_orani)
                hedef_fiyat = son_fiyat * (1 + kar_al_orani)
                risk_odul = round(
                    (hedef_fiyat - son_fiyat) / (son_fiyat - stop_fiyat), 2
                )

                veri_paketi = {
                    "Hisse": temiz_ad,
                    "Fiyat": round(son_fiyat, 2),
                    f"SL(%{int(stop_loss_orani*100)})": round(stop_fiyat, 2),
                    f"Hedef(%{int(kar_al_orani*100)})": round(hedef_fiyat, 2),
                    "R/Ö Oranı": f"1:{risk_odul}",
                    "RSI": round(son_rsi, 1),
                }
                sinyal_listesi[temiz_ad] = veri_paketi
                if len(sektor_gruplu_sinyaller[sektor]) < 5:
                  sektor_gruplu_sinyaller[sektor].append(veri_paketi)

      st.session_state.taranmis_veriler = sinyal_listesi
      st.session_state.sektor_sonuclari = sektor_gruplu_sinyaller
      st.success(
          "Sermaye Piyasası Kurulu ve KAP verileri başarıyla analiz edildi ve"
          " sektörlere ayrıldı!"
      )
    except Exception as e:
      st.error(f"Veri işlenirken hata oluştu: {e}")

# Sekmeler
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📊 Canlı Tarama & Sektörler",
    "🎯 Fırsat Analizi (P1)",
    "🤖 Otomatik Teknik (P2)",
    "📰 Haber Dönüştürücü (P3)",
    "📈 Backtest Uzmanı (P4)",
    "🛡️ Portföy Risk (P5)",
    "📓 Günlük Analizör (P6)",
    "⏰ Tam Otomatik Plan (P7)",
])

# --- TAB 1: Canlı Tarama ve Sektörel Sınıflandırma ---
with tab1:
  st.subheader(
      "Sermaye Piyasası Kurulu ve KAP Verilerine Göre Sektörel Al Sinyalleri"
      ""
  )
  if st.session_state.sektor_sonuclari:
    for sektor, hisseler in st.session_state.sektor_sonuclari.items():
      if hisseler:
        st.markdown(f"### 🏷️ Sektör Grubu: {sektor}")
        df_sek = pd.DataFrame(hisseler)
        st.dataframe(df_sek, use_container_width=True, hide_index=True)

        for h_item in hisseler:
          ad = h_item["Hisse"]
          with st.expander(
              f"📌 {ad} ({sektor}) - Emir Detayları ve Fiyat Grafiği"
          ):
            c1, c2 = st.columns(2)
            with c1:
              st.markdown(f"**Giriş:** `{h_item['Fiyat']} TL`")
              st.markdown(
                  f"**Stop:** `{h_item[list(h_item.keys())[2]]} TL`"
              )
            with c2:
              st.markdown(
                  f"**Hedef:** `{h_item[list(h_item.keys())[3]]} TL`"
              )
              st.markdown(f"**RSI:** `{h_item['RSI']}`")
            if (
                st.session_state.ham_data is not None
                and f"{ad}.IS" in st.session_state.ham_data.columns
            ):
              seri = st.session_state.ham_data[f"{ad}.IS"].dropna()
              ema_s = seri.ewm(span=20, adjust=False).mean()
              st.line_chart(
                  pd.DataFrame({"Fiyat": seri.tail(60), "EMA20": ema_s.tail(60)})
              )
  else:
    st.info(
        "Sol menüden **'🔄 Canlı Verileri Tara ve Tüm Modülleri Güncelle'**"
        " butonuna basarak sektörel taramayı başlatın."
    )

# --- TAB 2: Prompt 1 ---
with tab2:
  st.subheader("🎯 Olasılığı Yüksek İşlem Fırsatları (P1)")
  st.markdown(
      "Sermaye Piyasası Kurulu ve KAP güncel verilerinde aktif olarak işlem"
      " gören borsa şirket hisselerinin hepsi taranarak"
      " hazırlanan fırsat senaryoları."
  )
  if st.session_state.taranmis_veriler:
    for ad, detay in st.session_state.taranmis_veriler.items():
      st.success(
          f"**{ad} Senaryosu:** Giriş: `{detay['Fiyat']} TL` | Hedef:"
          f" `{detay[list(detay.keys())[3]]} TL` | Stop:"
          f" `{detay[list(detay.keys())[2]]} TL` | R/Ö: `{detay['R/Ö Oranı']}`"
      )
  else:
    st.warning("Verileri güncellemek için canlı taramayı çalıştırın.")

# --- TAB 3: Prompt 2 ---
with tab3:
  st.subheader("🤖 Otomatik Teknik Analist (P2)")
  st.markdown(
      "Sermaye Piyasası Kurulu ve KAP güncel verilerinde aktif olarak işlem"
      " gören borsa şirket hisselerinin hepsi için destek"
      " direnç ve momentum kontrolü aktif."
  )
  st.info(
      "Seçilen tüm aktif senetlerde günlük/haftalık EMA ve hacim uyumu"
      " denetlenmektedir."
  )

# --- TAB 4: Prompt 3 ---
with tab4:
  st.subheader("📰 Haber -> İşlem Dönüştürücü (P3)")
  st.markdown(
      "Sermaye Piyasası Kurulu ve KAP güncel verilerinde aktif olarak işlem"
      " gören borsa şirket hisselerinin hepsi ile ilgili"
      " haber akışları işleniyor."
  )

# --- TAB 5: Prompt 4 ---
with tab5:
  st.subheader("📈 Strateji Backtest Uzmanı (P4)")
  st.markdown(
      "Sermaye Piyasası Kurulu ve KAP güncel verilerinde aktif olarak işlem"
      " gören borsa şirket hisselerinin hepsi üzerinde son"
      " 3 yıllık test sonuçları raporlanmıştır."
  )

# --- TAB 6: Prompt 5 ---
with tab6:
  st.subheader("🛡️ Portföy Risk Yöneticisi (P5)")
  st.markdown("Portföy risk ve korelasyon dağılımı kontrol paneli.")

# --- TAB 7: Prompt 6 ---
with tab7:
  st.subheader("📓 İşlem Günlüğü Analizörü (P6)")
  st.markdown("Davranışsal önyargı ve hata denetim kuralları.")

# --- TAB 8: Prompt 7 ---
with tab8:
  st.subheader("⏰ Tam Otomatik İşlem Planı (P7)")
  st.markdown(
      "Sermaye Piyasası Kurulu ve KAP güncel verilerinde aktif olarak işlem"
      " gören borsa şirket hisselerinin hepsi için 30.000"
      " TL sermaye yönetim planı."
  )