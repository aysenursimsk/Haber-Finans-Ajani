"""
sorgu_cache.py
--------------
Bölüm 7, Katman 3 — Sorgu Cache'i (performans amaçlı).

Aynı konu kısa bir süre içinde tekrar sorulursa, haber/analiz ajanlarına
(Tavily, Claude) yeniden gitmek yerine önceki sonucu döndürür. Bu katman
sadece performans içindir; Katman 2'deki (ChromaDB) kullanıcı tercih
hafızasıyla karıştırılmamalıdır — burada kullanıcı bazlı hiçbir bilgi
tutulmaz, sadece "konu -> son sonuç" eşlemesi tutulur.

Süreç içi (in-process) basit bir TTL cache'idir; harici bir servise ihtiyaç
duymaz. Streamlit tek bir sunucu sürecinde birden fazla kullanıcı oturumunu
aynı process üzerinde çalıştırdığı için, bu modül seviyesindeki sözlük tüm
kullanıcılar arasında paylaşılır.
"""

import re
import time
from threading import Lock

TTL_SANIYE = 30 * 60  # PRD Katman 3: "örn. 30 dakika"

_cache: dict[str, dict] = {}
_kilit = Lock()


def _anahtar_uret(konu: str) -> str:
    """Karşılaştırma için konuyu sadeleştirir (büyük/küçük harf, fazladan boşluk farkını yok sayar)."""
    return re.sub(r"\s+", " ", konu.strip().lower())


def cache_getir(konu: str) -> dict | None:
    """
    Verilen konu için hâlâ geçerli (TTL süresi dolmamış) bir cache kaydı varsa döndürür.

    Dönüş:
        dict {"kaydedilme_zamani": float, ...diğer alanlar} ya da kayıt yoksa/süresi
        dolmuşsa None.
    """
    anahtar = _anahtar_uret(konu)
    with _kilit:
        kayit = _cache.get(anahtar)
        if kayit is not None and time.time() - kayit["kaydedilme_zamani"] > TTL_SANIYE:
            del _cache[anahtar]
            kayit = None
    return kayit


def cache_kaydet(konu: str, **veri) -> None:
    """Bir sorgu sonucunu cache'e yazar (aynı konu için varsa üzerine yazılır)."""
    anahtar = _anahtar_uret(konu)
    with _kilit:
        _cache[anahtar] = {**veri, "kaydedilme_zamani": time.time()}


def cache_temizle(konu: str) -> None:
    """Belirtilen konunun cache kaydını siler (kullanıcı 'Yenile' dediğinde çağrılır)."""
    anahtar = _anahtar_uret(konu)
    with _kilit:
        _cache.pop(anahtar, None)
