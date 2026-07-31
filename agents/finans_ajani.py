"""
finans_ajani.py
----------------
Finansal Analiz Modu için fiyat verisini ve haberleri Anthropic (Claude) API
kullanarak birleştirip piyasa duygu durumu (sentiment) skoru ve sade dilde
bir özet üreten ajan (Özellik 5.4 — Piyasa Duygu Analizi, Özellik 5.5 — Sade
Dil Özeti).

Yatırım tavsiyesi / AL-SAT sinyali üretimi kesinlikle yasaktır; bu kural
sistem promptunda katı biçimde uygulanır.
"""

import json
import os

from dotenv import load_dotenv
from anthropic import Anthropic

# .env dosyasındaki ortam değişkenlerini yükle
load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Varsayılan model: en yetenekli Claude modeli
MODEL = "claude-opus-5"

SYSTEM_PROMPT = """\
Sen tarafsız bir finansal haber analisti ve piyasa yorumcususun.
Sana bir varlığın adı, güncel fiyat bilgisi ve o varlıkla ilgili haberler verilecek.

Görevlerin:
1. "sentiment_skoru": Verilen haberlerin genel tonuna bakarak -1 (çok negatif)
   ile +1 (çok pozitif) arasında ondalıklı bir sayı üret.
2. "sentiment_durumu": Skora göre şu üç etiketten birini seç:
   - skor >= 0.5  ise "Piyasa haberleri genel olarak olumlu"
   - -0.5 < skor < 0.5 ise "Piyasa haberleri karışık / nötr"
   - skor <= -0.5 ise "Piyasa haberleri genel olarak olumsuz"
3. "ozet": Fiyat verisini ve haberleri birleştirerek, kullanıcının kolayca
   anlayabileceği sade bir dilde 3-4 cümlelik bir özet yaz.

KESİN KURALLAR (istisnasız uygulanır):
- "Yatırım yapmalısınız", "almalısınız", "satmalısınız", "kaçırmayın" gibi
  tavsiye ifadeleri ASLA kullanılmaz.
- "Yükselecek", "düşecek", "hedef fiyat" gibi geleceğe dönük tahmin ifadeleri
  ASLA kullanılmaz.
- AL / SAT / BEKLE gibi sinyal etiketleri ASLA üretilmez.
- Sadece geçmişte ne olduğu ve haberlerin/verilerin ne söylediği anlatılır;
  yorum veya öneri eklenmez.

Yanıtını SADECE aşağıdaki formatta geçerli bir JSON nesnesi olarak ver.
Başka hiçbir açıklama, giriş cümlesi veya markdown kod bloğu ekleme:

{"sentiment_skoru": 0.2, "sentiment_durumu": "...", "ozet": "..."}
"""


def finansal_analiz_yap(varlik_adi: str, fiyat_bilgisi: dict, haberler: list[dict]) -> dict:
    """
    Fiyat bilgisini ve haberleri Claude'a göndererek piyasa duygu durumu
    skoru ve sade dilde bir özet üretir.

    Parametreler:
        varlik_adi (str): İncelenen varlığın adı (örn. "USD/TRY", "THYAO").
        fiyat_bilgisi (dict): Güncel fiyat/değişim bilgisi
            (örn. {"guncel_fiyat": 34.20, "gunluk_degisim_yuzde": 0.8}).
        haberler (list[dict]): "Kaynak" ve "Başlık" anahtarlarını içeren
            haber sözlükleri listesi (news_agent.haberleri_getir çıktısı).

    Dönüş:
        dict: {"sentiment_skoru": float, "sentiment_durumu": str, "ozet": str}
    """
    if not ANTHROPIC_API_KEY:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY bulunamadı. Lütfen .env dosyasına geçerli bir Anthropic API anahtarı ekleyin."
        )

    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    girdi = {
        "varlik": varlik_adi,
        "fiyat_bilgisi": fiyat_bilgisi,
        "haberler": haberler or [],
    }
    kullanici_mesaji = (
        "Aşağıdaki varlık, fiyat bilgisi ve haberleri analiz et:\n\n"
        f"{json.dumps(girdi, ensure_ascii=False, indent=2)}"
    )

    try:
        yanit = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": kullanici_mesaji}],
        )
    except Exception as hata:
        raise RuntimeError(f"Claude API isteği sırasında hata oluştu: {hata}") from hata

    yanit_metni = next((blok.text for blok in yanit.content if blok.type == "text"), "")

    try:
        sonuc = json.loads(yanit_metni)
    except json.JSONDecodeError as hata:
        raise ValueError(
            f"Claude'dan gelen yanıt geçerli bir JSON değil:\n{yanit_metni}"
        ) from hata

    return sonuc


if __name__ == "__main__":
    # Basit test: sahte fiyat verisi ve haberlerle USD/TRY analizi
    ornek_fiyat_bilgisi = {"guncel_fiyat": 34.20, "gunluk_degisim_yuzde": 0.8}
    ornek_haberler = [
        {"Kaynak": "Reuters", "Başlık": "TCMB faiz kararını açıkladı, piyasalar sakin"},
        {"Kaynak": "Bloomberg HT", "Başlık": "Dolar/TL güne yatay başladı"},
        {"Kaynak": "Anadolu Ajansı", "Başlık": "Merkez Bankası Para Politikası Kurulu toplandı"},
    ]

    try:
        sonuc = finansal_analiz_yap("USD/TRY", ornek_fiyat_bilgisi, ornek_haberler)
        print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Hata: {e}")
