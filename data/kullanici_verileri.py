"""
kullanici_verileri.py
-----------------------
Giriş yapmış kullanıcıya özel kalıcı veriler: favoriler (Özellik 6.2),
portföy (Özellik 5.7), fiyat alarmları (Özellik 5.6) ve sorgu geçmişi
(Bölüm 7 — Katman 2: Kullanıcı Tercih Hafızası) için CRUD işlemleri.
"""

import json
from collections import Counter
from datetime import datetime, timezone

from data.veritabani import baglanti_al, veritabanini_hazirla

# ============================= FAVORİLER =====================================


def favori_ekle(kullanici_id: int, tur: str, deger: str, ek_bilgi: str = None) -> None:
    """
    Bir haber konusunu veya finansal varlığı kullanıcının favorilerine ekler.

    Parametreler:
        tur (str): "haber_konusu" veya "finansal_varlik".
        deger (str): Konu metni veya varlık adı.
        ek_bilgi (str): Finansal varlıklar için ticker/kategori bilgisi (opsiyonel).
    """
    veritabanini_hazirla()
    with baglanti_al() as baglanti:
        mevcut = baglanti.execute(
            "SELECT id FROM favoriler WHERE kullanici_id = ? AND tur = ? AND deger = ?",
            (kullanici_id, tur, deger),
        ).fetchone()
        if mevcut:
            return  # zaten favorilerde
        baglanti.execute(
            "INSERT INTO favoriler (kullanici_id, tur, deger, ek_bilgi, eklenme_tarihi) VALUES (?, ?, ?, ?, ?)",
            (kullanici_id, tur, deger, ek_bilgi, datetime.now(timezone.utc).isoformat()),
        )


def favorileri_getir(kullanici_id: int, tur: str = None) -> list:
    """Kullanıcının favorilerini (isteğe bağlı türe göre filtrelenmiş) listeler."""
    veritabanini_hazirla()
    with baglanti_al() as baglanti:
        if tur:
            satirlar = baglanti.execute(
                "SELECT * FROM favoriler WHERE kullanici_id = ? AND tur = ? ORDER BY eklenme_tarihi DESC",
                (kullanici_id, tur),
            ).fetchall()
        else:
            satirlar = baglanti.execute(
                "SELECT * FROM favoriler WHERE kullanici_id = ? ORDER BY eklenme_tarihi DESC",
                (kullanici_id,),
            ).fetchall()
    return [dict(satir) for satir in satirlar]


def favori_sil(favori_id: int, kullanici_id: int) -> None:
    """Bir favoriyi siler (sadece sahibi silebilir)."""
    veritabanini_hazirla()
    with baglanti_al() as baglanti:
        baglanti.execute(
            "DELETE FROM favoriler WHERE id = ? AND kullanici_id = ?", (favori_id, kullanici_id)
        )


# ============================= PORTFÖY =======================================


def portfoye_ekle(kullanici_id: int, varlik_adi: str, ticker: str, miktar: float, maliyet_fiyati: float) -> None:
    """Kullanıcının portföyüne yeni bir varlık kaydı ekler."""
    veritabanini_hazirla()
    with baglanti_al() as baglanti:
        baglanti.execute(
            """INSERT INTO portfoy (kullanici_id, varlik_adi, ticker, miktar, maliyet_fiyati, eklenme_tarihi)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (kullanici_id, varlik_adi, ticker, miktar, maliyet_fiyati, datetime.now(timezone.utc).isoformat()),
        )


def portfoyu_getir(kullanici_id: int) -> list:
    """Kullanıcının portföyündeki tüm kayıtları listeler."""
    veritabanini_hazirla()
    with baglanti_al() as baglanti:
        satirlar = baglanti.execute(
            "SELECT * FROM portfoy WHERE kullanici_id = ? ORDER BY eklenme_tarihi DESC", (kullanici_id,)
        ).fetchall()
    return [dict(satir) for satir in satirlar]


def portfoy_kaydi_sil(kayit_id: int, kullanici_id: int) -> None:
    """Portföyden bir kaydı siler (sadece sahibi silebilir)."""
    veritabanini_hazirla()
    with baglanti_al() as baglanti:
        baglanti.execute(
            "DELETE FROM portfoy WHERE id = ? AND kullanici_id = ?", (kayit_id, kullanici_id)
        )


# =========================== FİYAT ALARMLARI =================================


def alarm_kur(kullanici_id: int, varlik_adi: str, ticker: str, hedef_fiyat: float, yon: str) -> None:
    """
    Bir varlık için fiyat alarmı kurar.

    Parametreler:
        yon (str): "ustune_ciktiginda" veya "altina_dustugunde".
    """
    veritabanini_hazirla()
    with baglanti_al() as baglanti:
        baglanti.execute(
            """INSERT INTO fiyat_alarmlari
               (kullanici_id, varlik_adi, ticker, hedef_fiyat, yon, tetiklendi, olusturma_tarihi)
               VALUES (?, ?, ?, ?, ?, 0, ?)""",
            (kullanici_id, varlik_adi, ticker, hedef_fiyat, yon, datetime.now(timezone.utc).isoformat()),
        )


def alarmlari_getir(kullanici_id: int, sadece_aktif: bool = False) -> list:
    """Kullanıcının fiyat alarmlarını listeler."""
    veritabanini_hazirla()
    with baglanti_al() as baglanti:
        if sadece_aktif:
            satirlar = baglanti.execute(
                "SELECT * FROM fiyat_alarmlari WHERE kullanici_id = ? AND tetiklendi = 0 ORDER BY olusturma_tarihi DESC",
                (kullanici_id,),
            ).fetchall()
        else:
            satirlar = baglanti.execute(
                "SELECT * FROM fiyat_alarmlari WHERE kullanici_id = ? ORDER BY olusturma_tarihi DESC",
                (kullanici_id,),
            ).fetchall()
    return [dict(satir) for satir in satirlar]


def alarmi_tetiklendi_isaretle(alarm_id: int) -> None:
    """Bir alarmı tetiklenmiş olarak işaretler (tekrar tekrar bildirim gitmesin diye)."""
    veritabanini_hazirla()
    with baglanti_al() as baglanti:
        baglanti.execute("UPDATE fiyat_alarmlari SET tetiklendi = 1 WHERE id = ?", (alarm_id,))


def alarm_sil(alarm_id: int, kullanici_id: int) -> None:
    """Bir fiyat alarmını siler (sadece sahibi silebilir)."""
    veritabanini_hazirla()
    with baglanti_al() as baglanti:
        baglanti.execute(
            "DELETE FROM fiyat_alarmlari WHERE id = ? AND kullanici_id = ?", (alarm_id, kullanici_id)
        )


# =========================== SORGU GEÇMİŞİ / HAFIZA ===========================


def sorgu_kaydet(kullanici_id: int, konu: str) -> None:
    """Kullanıcının yaptığı bir sorguyu geçmişe kaydeder (Katman 2 — tercih hafızası için)."""
    veritabanini_hazirla()
    with baglanti_al() as baglanti:
        baglanti.execute(
            "INSERT INTO sorgu_gecmisi (kullanici_id, konu, tarih) VALUES (?, ?, ?)",
            (kullanici_id, konu, datetime.now(timezone.utc).isoformat()),
        )


def hatirlatma_ekle(kullanici_id: int, etkinlik_adi: str, etkinlik_tarihi) -> None:
    """
    Bir piyasa takvimi olayı için hatırlatma kaydeder (Özellik 5.8 — Bildirim).

    Parametreler:
        etkinlik_tarihi (date veya str): Olayın tarihi (ISO formatına çevrilerek saklanır).
    """
    veritabanini_hazirla()
    tarih_metni = etkinlik_tarihi.isoformat() if hasattr(etkinlik_tarihi, "isoformat") else str(etkinlik_tarihi)
    with baglanti_al() as baglanti:
        mevcut = baglanti.execute(
            """SELECT id FROM takvim_hatirlatmalari
               WHERE kullanici_id = ? AND etkinlik_adi = ? AND etkinlik_tarihi = ?""",
            (kullanici_id, etkinlik_adi, tarih_metni),
        ).fetchone()
        if mevcut:
            return  # zaten hatırlatma kurulmuş
        baglanti.execute(
            """INSERT INTO takvim_hatirlatmalari (kullanici_id, etkinlik_adi, etkinlik_tarihi, olusturma_tarihi)
               VALUES (?, ?, ?, ?)""",
            (kullanici_id, etkinlik_adi, tarih_metni, datetime.now(timezone.utc).isoformat()),
        )


def hatirlatmalari_getir(kullanici_id: int) -> list:
    """Kullanıcının kurduğu piyasa takvimi hatırlatmalarını listeler."""
    veritabanini_hazirla()
    with baglanti_al() as baglanti:
        satirlar = baglanti.execute(
            "SELECT * FROM takvim_hatirlatmalari WHERE kullanici_id = ? ORDER BY etkinlik_tarihi ASC",
            (kullanici_id,),
        ).fetchall()
    return [dict(satir) for satir in satirlar]


def hatirlatma_sil(hatirlatma_id: int, kullanici_id: int) -> None:
    """Bir takvim hatırlatmasını siler (sadece sahibi silebilir)."""
    veritabanini_hazirla()
    with baglanti_al() as baglanti:
        baglanti.execute(
            "DELETE FROM takvim_hatirlatmalari WHERE id = ? AND kullanici_id = ?", (hatirlatma_id, kullanici_id)
        )


def sik_sorulan_konuyu_getir(kullanici_id: int, son_gun: int = 7, min_tekrar: int = 3) -> str:
    """
    Kullanıcının son `son_gun` gün içinde en az `min_tekrar` kez sorduğu bir
    konu varsa döndürür (Bölüm 7, Katman 2 — "THYAO için yeni haberler var"
    tarzı kişiselleştirilmiş öneri için kullanılır).

    Dönüş:
        str veya None: En sık sorulan konu (eşiği geçiyorsa), yoksa None.
    """
    veritabanini_hazirla()
    esik_zaman = datetime.now(timezone.utc).timestamp() - (son_gun * 86400)

    with baglanti_al() as baglanti:
        satirlar = baglanti.execute(
            "SELECT konu, tarih FROM sorgu_gecmisi WHERE kullanici_id = ?", (kullanici_id,)
        ).fetchall()

    son_konular = [
        satir["konu"]
        for satir in satirlar
        if datetime.fromisoformat(satir["tarih"]).timestamp() >= esik_zaman
    ]

    if not son_konular:
        return None

    en_sik, tekrar_sayisi = Counter(son_konular).most_common(1)[0]
    return en_sik if tekrar_sayisi >= min_tekrar else None


# ========================= KONU/HABER ALARMLARI (Özellik 4.6) ================


def konu_alarmi_kur(kullanici_id: int, konu: str, siklik: str = "anlik") -> None:
    """
    Bir konuyu haber alarmı için takibe alır.

    Parametreler:
        siklik (str): "anlik", "gunluk" veya "kapali".
    """
    veritabanini_hazirla()
    with baglanti_al() as baglanti:
        mevcut = baglanti.execute(
            "SELECT id FROM konu_alarmlari WHERE kullanici_id = ? AND konu = ?",
            (kullanici_id, konu),
        ).fetchone()
        if mevcut:
            return  # zaten takip ediliyor
        baglanti.execute(
            """INSERT INTO konu_alarmlari (kullanici_id, konu, siklik, olusturma_tarihi)
               VALUES (?, ?, ?, ?)""",
            (kullanici_id, konu, siklik, datetime.now(timezone.utc).isoformat()),
        )


def konu_alarmlarini_getir(kullanici_id: int) -> list:
    """Kullanıcının takip ettiği konu/haber alarmlarını listeler."""
    veritabanini_hazirla()
    with baglanti_al() as baglanti:
        satirlar = baglanti.execute(
            "SELECT * FROM konu_alarmlari WHERE kullanici_id = ? ORDER BY olusturma_tarihi DESC",
            (kullanici_id,),
        ).fetchall()
    return [dict(satir) for satir in satirlar]


def konu_alarmi_sil(alarm_id: int, kullanici_id: int) -> None:
    """Bir konu/haber alarmını siler (sadece sahibi silebilir)."""
    veritabanini_hazirla()
    with baglanti_al() as baglanti:
        baglanti.execute(
            "DELETE FROM konu_alarmlari WHERE id = ? AND kullanici_id = ?", (alarm_id, kullanici_id)
        )


def konu_alarmi_gorulenleri_guncelle(alarm_id: int, haber_urlleri: list) -> None:
    """
    Bir konu alarmının "görülen haberler" listesini ve son kontrol zamanını
    günceller (yeni haber tespiti sonraki kontrolde bu listeyle karşılaştırılır).
    """
    veritabanini_hazirla()
    with baglanti_al() as baglanti:
        baglanti.execute(
            "UPDATE konu_alarmlari SET gorulen_haber_urlleri = ?, son_kontrol_tarihi = ? WHERE id = ?",
            (json.dumps(haber_urlleri, ensure_ascii=False), datetime.now(timezone.utc).isoformat(), alarm_id),
        )
