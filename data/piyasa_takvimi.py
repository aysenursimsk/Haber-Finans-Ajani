"""
piyasa_takvimi.py
------------------
Finansal takvim olaylarını (TCMB PPK toplantıları, TÜİK enflasyon açıklamaları,
önemli şirket bilanço tarihleri gibi) listeleyen veri katmanı (Özellik 5.8).

ÖNEMLİ — Ekip için not: Aşağıdaki tarihler YER TUTUCUDUR ve otomatik olarak
bugünün tarihine göre üretilir (TCMB PPK yaklaşık 6 haftada bir, TÜİK enflasyon
açıklaması her ayın 3'ünde yapılır — bu genel örüntüler doğrudur, ancak KESİN
tarihler değildir). Gerçek tarihler TCMB (tcmb.gov.tr) ve TÜİK'in resmi yayın
takviminden alınıp `SABIT_TAKVIM_OLAYLARI` listesine elle girilmelidir.

Sistem bu olayların SONUCUNU asla tahmin etmez; sadece tarih/olay bilgisini sunar.
"""

from datetime import date, datetime, timedelta

# Ekip, gerçek tarihler netleştikçe bu listeyi TCMB/TÜİK'in resmi takviminden
# güncellenmiş, kesin tarihlerle doldurmalıdır. Boş bırakılırsa sadece aşağıdaki
# otomatik üretilen yer tutucu olaylar gösterilir.
SABIT_TAKVIM_OLAYLARI = [
    # Örnek: {"etkinlik_adi": "TCMB PPK Toplantısı", "kategori": "Makro - Faiz Kararı",
    #         "tarih": "2026-08-20", "aciklama": "..."},
]


def _yer_tutucu_olaylari_uret(ileri_ay_sayisi: int = 3) -> list:
    """
    Gerçek tarihler girilene kadar kullanılacak, bugüne göre otomatik üretilen
    örnek takvim olayları. TCMB PPK için ~6 haftalık, TÜİK enflasyon açıklaması
    için ayın 3'ü örüntüsü kullanılır — bunlar genel örüntülerdir, kesin resmi
    tarih değildir.
    """
    bugun = date.today()
    olaylar = []

    # TÜİK Enflasyon Açıklaması — her ayın 3'ü (yaklaşık örüntü)
    for ay_ofset in range(ileri_ay_sayisi + 1):
        hedef_ay = bugun.month - 1 + ay_ofset
        hedef_yil = bugun.year + hedef_ay // 12
        hedef_ay = hedef_ay % 12 + 1
        try:
            tuik_tarihi = date(hedef_yil, hedef_ay, 3)
        except ValueError:
            continue
        if tuik_tarihi >= bugun:
            olaylar.append(
                {
                    "etkinlik_adi": "TÜİK Enflasyon (TÜFE/ÜFE) Açıklaması",
                    "kategori": "Makro - Enflasyon",
                    "tarih": tuik_tarihi.isoformat(),
                    "aciklama": (
                        "Türkiye İstatistik Kurumu aylık tüketici ve üretici fiyat "
                        "endeksi açıklaması (yaklaşık tarih — kesin tarih için TÜİK "
                        "yayın takvimine bakınız)."
                    ),
                }
            )

    # TCMB PPK Toplantısı — yaklaşık 6 haftalık aralıklarla (genel örüntü)
    ilk_toplanti = bugun + timedelta(days=14)
    for i in range(3):
        toplanti_tarihi = ilk_toplanti + timedelta(weeks=6 * i)
        olaylar.append(
            {
                "etkinlik_adi": "TCMB PPK Toplantısı",
                "kategori": "Makro - Faiz Kararı",
                "tarih": toplanti_tarihi.isoformat(),
                "aciklama": (
                    "Türkiye Cumhuriyet Merkez Bankası Para Politikası Kurulu faiz "
                    "kararı toplantısı (yaklaşık tarih — kesin tarih için TCMB resmi "
                    "duyuru takvimine bakınız)."
                ),
            }
        )

    return olaylar


def takvim_olaylarini_getir(sadece_gelecek: bool = True) -> list:
    """
    Finansal takvim olaylarını tarihe göre sıralı döndürür.

    Parametreler:
        sadece_gelecek (bool): True ise sadece bugün ve sonrasındaki olaylar döner.

    Dönüş:
        list[dict]: Her biri "etkinlik_adi", "kategori", "tarih" (date), "aciklama"
            ve "kalan_gun" (int) anahtarlarını içeren olay sözlükleri, tarihe göre artan sırada.
    """
    bugun = date.today()
    ham_olaylar = list(SABIT_TAKVIM_OLAYLARI) + _yer_tutucu_olaylari_uret()

    olaylar = []
    for ham in ham_olaylar:
        etkinlik_tarihi = datetime.strptime(ham["tarih"], "%Y-%m-%d").date()
        if sadece_gelecek and etkinlik_tarihi < bugun:
            continue
        olaylar.append(
            {
                **ham,
                "tarih": etkinlik_tarihi,
                "kalan_gun": (etkinlik_tarihi - bugun).days,
            }
        )

    return sorted(olaylar, key=lambda olay: olay["tarih"])


if __name__ == "__main__":
    for olay in takvim_olaylarini_getir():
        print(f"{olay['tarih']} ({olay['kalan_gun']} gün) — {olay['etkinlik_adi']}")
