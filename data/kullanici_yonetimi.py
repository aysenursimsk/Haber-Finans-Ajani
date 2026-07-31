"""
kullanici_yonetimi.py
----------------------
Kullanıcı kaydı, girişi ve şifre doğrulama işlemlerini yürütür.
Şifreler asla düz metin olarak saklanmaz; bcrypt ile hashlenir (Özellik 6.1).
"""

import re
from datetime import datetime, timezone

import bcrypt

from data.veritabani import baglanti_al, veritabanini_hazirla

EPOSTA_DESENI = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def kullanici_olustur(eposta: str, sifre: str) -> dict:
    """
    Yeni bir kullanıcı hesabı oluşturur.

    Parametreler:
        eposta (str): Kullanıcının e-posta adresi (benzersiz olmalı).
        sifre (str): Düz metin şifre (fonksiyon içinde hashlenip saklanır).

    Dönüş:
        dict: Oluşturulan kullanıcının {"id", "eposta"} bilgisi.
    """
    eposta = (eposta or "").strip().lower()
    if not EPOSTA_DESENI.match(eposta):
        raise ValueError("Lütfen geçerli bir e-posta adresi girin.")
    if not sifre or len(sifre) < 6:
        raise ValueError("Şifre en az 6 karakter olmalıdır.")

    veritabanini_hazirla()
    sifre_hash = bcrypt.hashpw(sifre.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    with baglanti_al() as baglanti:
        mevcut = baglanti.execute(
            "SELECT id FROM kullanicilar WHERE eposta = ?", (eposta,)
        ).fetchone()
        if mevcut:
            raise ValueError("Bu e-posta adresiyle zaten bir hesap var.")

        imlec = baglanti.execute(
            "INSERT INTO kullanicilar (eposta, sifre_hash, olusturma_tarihi) VALUES (?, ?, ?)",
            (eposta, sifre_hash, datetime.now(timezone.utc).isoformat()),
        )
        return {"id": imlec.lastrowid, "eposta": eposta}


def giris_yap(eposta: str, sifre: str) -> dict:
    """
    Kullanıcı giriş bilgilerini doğrular.

    Dönüş:
        dict veya None: Doğrulama başarılıysa {"id", "eposta"}; başarısızsa None.
    """
    eposta = (eposta or "").strip().lower()
    if not eposta or not sifre:
        return None

    veritabanini_hazirla()
    with baglanti_al() as baglanti:
        satir = baglanti.execute(
            "SELECT id, eposta, sifre_hash FROM kullanicilar WHERE eposta = ?", (eposta,)
        ).fetchone()

    if satir is None:
        return None

    if bcrypt.checkpw(sifre.encode("utf-8"), satir["sifre_hash"].encode("utf-8")):
        return {"id": satir["id"], "eposta": satir["eposta"]}

    return None
