"""
finans_verisi.py
-----------------
yfinance kullanarak finansal varlıklar için fiyat verisi çeken ve
teknik göstergeleri (RSI, MACD, Bollinger Bantları, MA200, Stokastik
osilatör, temel destek/direnç seviyeleri) hesaplayan yardımcı fonksiyonlar.
"""

import pandas as pd
import yfinance as yf

# MA200 gibi uzun vadeli göstergeleri doğru hesaplayabilmek için, ekranda
# gösterilen zaman diliminden bağımsız olarak her zaman en az bu kadar
# günlük geçmiş veri çekilir.
MIN_GECMIS_GUN = 250

# Ürün tanım dokümanındaki (Özellik 5.1) hazır varlık kategorileri.
# "ticker": yfinance sembolü, "sorgu": haber aramasında kullanılacak arama metni.
VARLIK_LISTESI = {
    "Döviz": {
        "USD/TRY": {"ticker": "TRY=X", "sorgu": "dolar kuru TCMB USD TRY"},
        "EUR/TRY": {"ticker": "EURTRY=X", "sorgu": "euro kuru TCMB EUR TRY"},
        "GBP/TRY": {"ticker": "GBPTRY=X", "sorgu": "sterlin kuru GBP TRY"},
    },
    "Emtia": {
        "Altın (Ons)": {"ticker": "GC=F", "sorgu": "altın ons fiyatı"},
        "Gümüş": {"ticker": "SI=F", "sorgu": "gümüş fiyatı"},
    },
    "Borsa Endeksi": {
        "BIST 100": {"ticker": "XU100.IS", "sorgu": "BIST 100 endeksi Borsa İstanbul"},
        "BIST 30": {"ticker": "XU030.IS", "sorgu": "BIST 30 endeksi Borsa İstanbul"},
    },
}

# Serbest sembol girilen kategoriler (Özellik 5.1 — bireysel hisse / kripto para)
SERBEST_SEMBOL_KATEGORILERI = {
    "Borsa - Hisse Senedi": {"ticker_eki": ".IS", "sorgu_sablonu": "{sembol} hissesi haberleri"},
    "Kripto Para": {"ticker_eki": "-USD", "sorgu_sablonu": "{sembol} kripto para haberleri"},
}


def fiyat_verisi_getir(ticker: str, gun_sayisi: int = 90) -> pd.DataFrame:
    """
    Verilen yfinance ticker'ı için fiyat verisini çeker.

    Parametreler:
        ticker (str): yfinance sembolü (örn. "THYAO.IS", "BTC-USD", "TRY=X").
        gun_sayisi (int): Ekranda gösterilecek gün sayısı (7, 30 veya 90).

    Dönüş:
        pd.DataFrame: "Acilis", "Yuksek", "Dusuk", "Kapanis" sütunlarını içeren,
            tarih indeksli bir DataFrame. MA200 gibi göstergeler doğru
            hesaplanabilsin diye gösterim penceresinden daha uzun bir
            geçmişle çekilir; ekranda gösterirken son `gun_sayisi` satır alınmalıdır.
    """
    if not ticker or not ticker.strip():
        raise ValueError("Geçerli bir varlık sembolü belirtilmedi.")

    cekilecek_gun = max(gun_sayisi, MIN_GECMIS_GUN)

    try:
        veri = yf.Ticker(ticker).history(period=f"{cekilecek_gun}d")
    except Exception as hata:
        raise RuntimeError(f"'{ticker}' için fiyat verisi çekilirken hata oluştu: {hata}") from hata

    if veri is None or veri.empty:
        raise ValueError(f"'{ticker}' sembolü için fiyat verisi bulunamadı.")

    veri = veri.rename(
        columns={"Open": "Acilis", "High": "Yuksek", "Low": "Dusuk", "Close": "Kapanis"}
    )
    return veri[["Acilis", "Yuksek", "Dusuk", "Kapanis"]]


def teknik_gostergeleri_hesapla(veri: pd.DataFrame) -> pd.DataFrame:
    """
    Verilen fiyat DataFrame'ine teknik gösterge sütunları ekler:
    RSI, MACD (+ sinyal çizgisi), Bollinger Bantları, MA200, Stokastik %K/%D.

    Parametreler:
        veri (pd.DataFrame): "Kapanis", "Yuksek", "Dusuk" sütunlarını içeren fiyat verisi.

    Dönüş:
        pd.DataFrame: Orijinal veriye gösterge sütunları eklenmiş hali.
    """
    df = veri.copy()

    # --- RSI (14 günlük) ---
    degisim = df["Kapanis"].diff()
    kazanc = degisim.clip(lower=0)
    kayip = -degisim.clip(upper=0)
    ort_kazanc = kazanc.rolling(window=14).mean()
    ort_kayip = kayip.rolling(window=14).mean()
    rs = ort_kazanc / ort_kayip
    df["RSI"] = 100 - (100 / (1 + rs))

    # --- MACD (12-26 günlük EMA farkı, 9 günlük sinyal çizgisi) ---
    ema12 = df["Kapanis"].ewm(span=12, adjust=False).mean()
    ema26 = df["Kapanis"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_Sinyal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    # --- Bollinger Bantları (20 günlük ortalama ± 2 standart sapma) ---
    orta_bant = df["Kapanis"].rolling(window=20).mean()
    std_sapma = df["Kapanis"].rolling(window=20).std()
    df["Bollinger_Orta"] = orta_bant
    df["Bollinger_Ust"] = orta_bant + (2 * std_sapma)
    df["Bollinger_Alt"] = orta_bant - (2 * std_sapma)

    # --- MA200 (200 günlük hareketli ortalama) ---
    df["MA200"] = df["Kapanis"].rolling(window=200).mean()

    # --- Stokastik Osilatör (14 günlük %K, 3 günlük %D) ---
    en_dusuk_14 = df["Dusuk"].rolling(window=14).min()
    en_yuksek_14 = df["Yuksek"].rolling(window=14).max()
    df["Stokastik_K"] = 100 * (df["Kapanis"] - en_dusuk_14) / (en_yuksek_14 - en_dusuk_14)
    df["Stokastik_D"] = df["Stokastik_K"].rolling(window=3).mean()

    return df


def destek_direnc_hesapla(veri: pd.DataFrame, pencere: int = 20) -> tuple:
    """
    Son `pencere` günün en düşük ve en yüksek fiyatlarına dayanan basit
    bir destek/direnç seviyesi hesaplar (temel düzey — Özellik 5.2).

    Dönüş:
        tuple: (destek_seviyesi, direnc_seviyesi)
    """
    son_veri = veri.tail(pencere)
    destek = son_veri["Dusuk"].min()
    direnc = son_veri["Yuksek"].max()
    return float(destek), float(direnc)


if __name__ == "__main__":
    # Basit test: USD/TRY için son 30 günlük veri ve göstergeler
    try:
        df = fiyat_verisi_getir("TRY=X", gun_sayisi=30)
        df = teknik_gostergeleri_hesapla(df)
        destek, direnc = destek_direnc_hesapla(df)
        print(df.tail(5)[["Kapanis", "RSI", "MACD", "MA200"]])
        print(f"\nDestek: {destek:.4f}  ·  Direnç: {direnc:.4f}")
    except Exception as e:
        print(f"Hata: {e}")
