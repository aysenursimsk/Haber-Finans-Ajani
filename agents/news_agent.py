"""
news_agent.py
-------------
Kullanıcının girdiği bir konu hakkında internetten güncel haberleri toplayan ajan.

Bu modül Tavily API'yi kullanarak son 24-72 saat içinde yayınlanmış haberleri arar
ve her haberi standart bir sözlük (dictionary) yapısında döndürür:
    {"Kaynak": ..., "Başlık": ..., "Tarih": ..., "URL": ...}
"""

import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from tavily import TavilyClient

# .env dosyasındaki ortam değişkenlerini yükle
load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


def _kaynak_adini_cikar(url: str) -> str:
    """Verilen URL'den okunabilir bir kaynak (site) adı çıkarır."""
    try:
        netloc = urlparse(url).netloc
        # "www." önekini temizle
        return netloc.replace("www.", "") if netloc else "Bilinmiyor"
    except Exception:
        return "Bilinmiyor"


def haberleri_getir(konu: str, gun_araligi: int = 3, max_sonuc: int = 15) -> list[dict]:
    """
    Belirtilen konu hakkında son `gun_araligi` gün içinde yayınlanmış haberleri getirir.

    Parametreler:
        konu (str): Aranacak haber konusu (örn. "Yapay Zeka").
        gun_araligi (int): Kaç gün öncesine kadar haber aranacağı (varsayılan 3 gün / 72 saat).
        max_sonuc (int): Getirilecek maksimum haber sayısı (5 ile 15 arasında sınırlandırılır).

    Dönüş:
        list[dict]: Her biri "Kaynak", "Başlık", "Tarih" ve "URL" anahtarlarına sahip
                    haber sözlüklerinden oluşan liste.
    """
    if not konu or not konu.strip():
        raise ValueError("Aranacak konu boş olamaz.")

    if not TAVILY_API_KEY:
        raise EnvironmentError(
            "TAVILY_API_KEY bulunamadı. Lütfen .env dosyasına geçerli bir Tavily API anahtarı ekleyin."
        )

    # Sonuç sayısını 5-15 aralığında sınırla (görev gereksinimi)
    max_sonuc = max(5, min(15, max_sonuc))

    client = TavilyClient(api_key=TAVILY_API_KEY)

    try:
        yanit = client.search(
            query=konu,
            topic="news",       # haber odaklı arama
            days=gun_araligi,   # son N gün içindeki haberler
            max_results=max_sonuc,
            include_answer=False,
        )
    except Exception as hata:
        raise RuntimeError(f"Tavily API araması sırasında hata oluştu: {hata}") from hata

    haberler = []
    for sonuc in yanit.get("results", []):
        haberler.append(
            {
                "Kaynak": _kaynak_adini_cikar(sonuc.get("url", "")),
                "Başlık": sonuc.get("title", "Başlık bulunamadı"),
                "Tarih": sonuc.get("published_date", "Tarih bulunamadı"),
                "URL": sonuc.get("url", ""),
            }
        )

    return haberler


if __name__ == "__main__":
    # Basit test: "Yapay Zeka" konusu hakkında haberleri getir ve ekrana yazdır
    ornek_konu = "Yapay Zeka"
    try:
        sonuclar = haberleri_getir(ornek_konu)
        print(f"'{ornek_konu}' konusu için {len(sonuclar)} haber bulundu:\n")
        for i, haber in enumerate(sonuclar, start=1):
            print(f"{i}. {haber['Başlık']}")
            print(f"   Kaynak : {haber['Kaynak']}")
            print(f"   Tarih  : {haber['Tarih']}")
            print(f"   URL    : {haber['URL']}\n")
    except Exception as e:
        print(f"Hata: {e}")
