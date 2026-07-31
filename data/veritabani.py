"""
veritabani.py
-------------
Uygulamanın kalıcı verilerini (kullanıcılar, favoriler, portföy, fiyat
alarmları, sorgu geçmişi) saklayan yerel SQLite veritabanı bağlantısı ve
şeması. Harici bir servise ihtiyaç duymaz; veritabanı dosyası proje
içinde `data/uygulama.db` olarak tutulur (git'e dahil edilmez).
"""

import sqlite3
from pathlib import Path

VERITABANI_YOLU = Path(__file__).parent / "uygulama.db"


def baglanti_al() -> sqlite3.Connection:
    """SQLite veritabanına bağlantı açar (satırlara sözlük gibi erişim sağlar)."""
    baglanti = sqlite3.connect(VERITABANI_YOLU, check_same_thread=False)
    baglanti.row_factory = sqlite3.Row
    return baglanti


def veritabanini_hazirla() -> None:
    """Uygulama ilk çalıştığında gerekli tabloları oluşturur (varsa dokunmaz)."""
    with baglanti_al() as baglanti:
        baglanti.executescript(
            """
            CREATE TABLE IF NOT EXISTS kullanicilar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                eposta TEXT UNIQUE NOT NULL,
                sifre_hash TEXT NOT NULL,
                olusturma_tarihi TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS favoriler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kullanici_id INTEGER NOT NULL,
                tur TEXT NOT NULL,
                deger TEXT NOT NULL,
                ek_bilgi TEXT,
                eklenme_tarihi TEXT NOT NULL,
                FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(id)
            );

            CREATE TABLE IF NOT EXISTS portfoy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kullanici_id INTEGER NOT NULL,
                varlik_adi TEXT NOT NULL,
                ticker TEXT NOT NULL,
                miktar REAL NOT NULL,
                maliyet_fiyati REAL NOT NULL,
                eklenme_tarihi TEXT NOT NULL,
                FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(id)
            );

            CREATE TABLE IF NOT EXISTS fiyat_alarmlari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kullanici_id INTEGER NOT NULL,
                varlik_adi TEXT NOT NULL,
                ticker TEXT NOT NULL,
                hedef_fiyat REAL NOT NULL,
                yon TEXT NOT NULL,
                tetiklendi INTEGER NOT NULL DEFAULT 0,
                olusturma_tarihi TEXT NOT NULL,
                FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(id)
            );

            CREATE TABLE IF NOT EXISTS sorgu_gecmisi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kullanici_id INTEGER NOT NULL,
                konu TEXT NOT NULL,
                tarih TEXT NOT NULL,
                FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(id)
            );

            CREATE TABLE IF NOT EXISTS takvim_hatirlatmalari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kullanici_id INTEGER NOT NULL,
                etkinlik_adi TEXT NOT NULL,
                etkinlik_tarihi TEXT NOT NULL,
                olusturma_tarihi TEXT NOT NULL,
                FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(id)
            );

            CREATE TABLE IF NOT EXISTS konu_alarmlari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kullanici_id INTEGER NOT NULL,
                konu TEXT NOT NULL,
                siklik TEXT NOT NULL DEFAULT 'anlik',
                gorulen_haber_urlleri TEXT NOT NULL DEFAULT '[]',
                son_kontrol_tarihi TEXT,
                olusturma_tarihi TEXT NOT NULL,
                FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(id)
            );
            """
        )
