"""
router.py
---------
Kullanıcının girdiği serbest metin konuyu analiz edip, bunun bir finansal
varlığa mı yoksa genel bir haber konusuna mı karşılık geldiğine karar veren
modül. Sonucuna göre app.py, haber ajanı veya finans ajanı akışını tetikler.
"""

import re
from data.finans_verisi import VARLIK_LISTESI


def _normalize(metin: str) -> str:
    """Karşılaştırma için metni sadeleştirir: küçük harfe çevirir, boşluk/noktalama farklarını yok sayar."""
    return re.sub(r"[^a-z0-9çğıöşü]", "", metin.lower())

def konu_varlik_eslestir(konu: str):
    konu_normalize = _normalize(konu)
    for kategori, varliklar in VARLIK_LISTESI.items():
        for varlik_adi, bilgi in varliklar.items():
            varlik_normalize = _normalize(varlik_adi)
            if varlik_normalize in konu_normalize or konu_normalize in varlik_normalize:
                return kategori, varlik_adi, bilgi["ticker"], bilgi["sorgu"]
    return None