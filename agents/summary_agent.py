"""
summary_agent.py
----------------
Haber toplayıcıdan (news_agent) gelen haber listesini Anthropic (Claude) API
kullanarak analiz eden ajan.

Bu modül, verilen haber listesini Claude'a gönderir ve şu iki bilgiyi içeren
bir JSON sözlüğü döndürür:
    - "tldr": Tüm kaynakları sentezleyen tarafsız, tek paragraflık özet.
    - "bias_analysis": Her kaynağın başlığını 1 (tamamen olgu) ile
      10 (tamamen yorum) arasında puanlayan bir sözlük.
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

# Claude'a verilecek sistem talimatı: tarafsızlık ve JSON formatı zorunluluğu
SYSTEM_PROMPT = """\
Sen tarafsız bir haber analisti ve medya okuryazarlığı uzmanısın.
Sana bir KONU ve o konu için toplanmış bir haber listesi verilecek. Her haberin
"Kaynak" ve "Başlık" bilgisi olacak.

ÖNEMLİ: Haber listesi bir arama motorundan geliyor ve bazı haberler KONU ile
alakasız olabilir (arama motoru yeterli sonuç bulamadığında alakasız/genel
gündem haberleri döndürebilir). İlk işin, her haberin başlığının KONU ile
gerçekten ilgili olup olmadığını değerlendirmek.

Görevlerin:
1. "tldr":
   - Eğer haberlerin çoğu KONU ile gerçekten ilgiliyse: sadece ilgili
     kaynakları sentezleyen, tarafsız, tek paragraflık bir "Kısaca Ne Oldu?"
     özeti yaz. Bu özet kesinlikle yönlendirme, yorum veya kendi görüşünü
     içermemeli; sadece kaynaklarda ortak olan olguları anlat.
   - Eğer haberlerin çoğu (yarısından fazlası) KONU ile alakasızsa: SADECE
     şunu yaz: "'{KONU}' konusuyla ilgili yeterli/güncel haber bulunamadı.
     Arama sonuçları alakasız içerik döndürdü."

2. "bias_analysis": SADECE KONU ile gerçekten ilgili olan haberlerin
   başlığını ayrı ayrı, aşağıdaki 4 ölçülebilir metin özelliğine göre
   değerlendir (siyasi/ideolojik yargı DEĞİL, sadece metin analizi).
   Alakasız haberleri bias_analysis'e hiç dahil etme.
   - "olgu_yorum_skoru": 0.0 (tamamen olgu/veri) ile 1.0 (tamamen yorum/görüş) arası bir sayı.
   - "dogrulama_skoru": 0.0 (tek kaynağa dayanıyor) ile 1.0 (birden fazla kaynak/tanık doğrulamış) arası bir sayı.
   - "atif_turu": Başlık resmi bir açıklamaya mı, anonim bir kaynağa mı, yoksa
     başka bir habere mi dayanıyor? Kısaca belirt (örn. "resmi açıklama",
     "anonim kaynak", "başka habere dayalı", "belirtilmemiş").
   - "duygusal_yuzde": Başlıktaki duygusal yüklü kelime/sıfat/abartı oranını
     0-100 arası bir yüzde olarak tahmin et.
   Anahtar olarak haberin "Kaynak" adını kullan.

Yanıtını SADECE aşağıdaki formatta geçerli bir JSON nesnesi olarak ver.
Başka hiçbir açıklama, giriş cümlesi veya markdown kod bloğu ekleme:

{"tldr": "...", "bias_analysis": {"Kaynak1": {"olgu_yorum_skoru": 0.3, "dogrulama_skoru": 0.5, "atif_turu": "resmi açıklama", "duygusal_yuzde": 10}}}
"""

def haberleri_analiz_et(haberler: list[dict], konu: str) -> dict:
    """
    Verilen haber listesini Claude API'ye gönderip analiz sonucunu döndürür.

    Parametreler:
        haberler (list[dict]): Her biri en azından "Kaynak" ve "Başlık"
            anahtarlarını içeren haber sözlüklerinden oluşan liste
            (örn. [{"Kaynak": "BBC", "Başlık": "...", "URL": "..."}]).

    Dönüş:
        dict: {"tldr": str, "bias_analysis": {kaynak_adı: puan}} yapısında sözlük.
    """
    if not haberler:
        raise ValueError("Analiz edilecek haber listesi boş olamaz.")

    if not ANTHROPIC_API_KEY:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY bulunamadı. Lütfen .env dosyasına geçerli bir Anthropic API anahtarı ekleyin."
        )

    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    # Haber listesini modelin okuyabileceği bir metne dönüştür
    haber_metni = json.dumps(haberler, ensure_ascii=False, indent=2)
    kullanici_mesaji = f"KONU: {konu}\n\nAşağıdaki haber listesini analiz et:\n\n{haber_metni}"

    try:
        yanit = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": kullanici_mesaji}],
        )
    except Exception as hata:
        raise RuntimeError(f"Claude API isteği sırasında hata oluştu: {hata}") from hata

    # Yanıttaki metin bloğunu bul
    yanit_metni = next((blok.text for blok in yanit.content if blok.type == "text"), "")

    try:
        sonuc = json.loads(yanit_metni)
    except json.JSONDecodeError as hata:
        raise ValueError(
            f"Claude'dan gelen yanıt geçerli bir JSON değil:\n{yanit_metni}"
        ) from hata

    return sonuc


if __name__ == "__main__":
    # Test: aynı olay hakkında 3 farklı üslupta (tarafsız / abartılı / ortalama) sahte haber
    ornek_haberler = [
        {
            "Kaynak": "Reuters",
            "Başlık": "Merkez Bankası politika faizini değiştirmedi",
            "URL": "https://example.com/reuters-haber",
        },
        {
            "Kaynak": "ŞokHaber",
            "Başlık": "İNANILMAZ! Merkez Bankası'nın faiz kararı herkesi şaşkına çevirdi, işte perde arkası!",
            "URL": "https://example.com/sokhaber-haber",
        },
        {
            "Kaynak": "Anadolu Ajansı",
            "Başlık": "Merkez Bankası Para Politikası Kurulu faiz oranını sabit tuttu, piyasalar karışık tepki verdi",
            "URL": "https://example.com/aa-haber",
        },
    ]

    try:
        sonuc = haberleri_analiz_et(ornek_haberler, konu="Merkez Bankası faiz kararı")
        print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Hata: {e}")
