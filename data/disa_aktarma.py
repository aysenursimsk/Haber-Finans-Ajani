"""
disa_aktarma.py
----------------
Özellik 5.9 / S2.10 — Dışa Aktarma. Görüntülenen analiz ekranını PDF rapor
olarak, portföy verisini CSV olarak dışa aktarma işlevlerini sağlar.

Dil kuralları (Özellik 5.5 ile aynı, istisnasız): PDF raporlarına yatırım
tavsiyesi niteliğinde hiçbir ifade eklenmez; finansal raporlarda sabit yasal
uyarı metni her zaman yer alır.
"""

import io
from pathlib import Path

import pandas as pd
from fpdf import FPDF

_FONT_YOLU = Path(__file__).parent.parent / "assets" / "DejaVuSans.ttf"

YASAL_UYARI = (
    "Bu icerik yalnizca bilgilendirme amaclidir. Yatirim tavsiyesi degildir. "
    "Yatirim kararlariniz icin lutfen lisansli bir yatirim danismanina basvurun."
)


def _pdf_olustur() -> FPDF:
    """Türkçe karakterleri destekleyen (DejaVuSans gömülü) boş bir PDF sayfası oluşturur."""
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("DejaVu", "", str(_FONT_YOLU))
    pdf.add_font("DejaVu", "B", str(_FONT_YOLU))
    pdf.set_font("DejaVu", size=11)
    return pdf


def _yaz(pdf: FPDF, h: float, metin: str, kalin: bool = False, punto: int = 11) -> None:
    """
    Bir satır/paragraf yazar ve imleci her zaman sol kenara sıfırlar.

    `multi_cell` çağrısından sonra fpdf2 imleci sağ kenarda bırakır; bir
    sonraki `multi_cell` çağrısı bunu sıfırlamazsa "yeterli yatay alan yok"
    hatası fırlatır. `pdf.ln(0)` çağrısı imleci dikey konumu değiştirmeden
    sol kenara döndürür.
    """
    pdf.set_font("DejaVu", "B" if kalin else "", punto)
    pdf.multi_cell(0, h, metin)
    pdf.ln(0)


def genel_analiz_pdf_uret(konu: str, tldr: str, bias_analysis: dict, haberler: list[dict]) -> bytes:
    """
    Genel Haber Modu analiz ekranını (TL;DR + bias analizi + kaynak listesi) PDF olarak üretir.

    Dönüş:
        bytes: İndirilebilir PDF dosyasının ham içeriği.
    """
    pdf = _pdf_olustur()
    _yaz(pdf, 10, f"Haber Analizi: {konu}", kalin=True, punto=15)
    pdf.ln(2)

    _yaz(pdf, 8, "Kisaca Ne Oldu?", kalin=True, punto=12)
    _yaz(pdf, 6, tldr or "Ozet olusturulamadi.")
    pdf.ln(2)

    if bias_analysis:
        _yaz(pdf, 8, "Bakis Acisi Haritasi (Bias Analizi)", kalin=True, punto=12)
        _yaz(
            pdf, 6,
            "Asagidaki degerler siyasi bir yargi icermez, sadece metnin "
            "olculebilir yazim ozelliklerini yansitir."
        )
        for kaynak, metrikler in bias_analysis.items():
            if not isinstance(metrikler, dict):
                continue
            _yaz(pdf, 6, kaynak, kalin=True, punto=11)
            _yaz(
                pdf, 6,
                f"  Olgu/Yorum: {metrikler.get('olgu_yorum_skoru', 0):.2f}  ·  "
                f"Dogrulama: {metrikler.get('dogrulama_skoru', 0):.2f}  ·  "
                f"Atif turu: {metrikler.get('atif_turu', 'belirtilmemis')}  ·  "
                f"Duygusal: %{metrikler.get('duygusal_yuzde', 0):.0f}",
                punto=10,
            )
            pdf.ln(1)
        pdf.ln(2)

    if haberler:
        _yaz(pdf, 8, f"Kaynak Haberler ({len(haberler)} adet)", kalin=True, punto=12)
        for haber in haberler:
            _yaz(pdf, 6, haber.get("Başlık", "Başlık yok"), kalin=True, punto=10)
            _yaz(
                pdf, 5,
                f"{haber.get('Kaynak', 'Bilinmiyor')} · {haber.get('Tarih', '')} · {haber.get('URL', '')}",
                punto=9,
            )
            pdf.ln(1)

    return bytes(pdf.output())


def finansal_analiz_pdf_uret(
    varlik_adi: str,
    fiyat_bilgisi: dict,
    finansal_analiz: dict,
    haberler: list[dict],
) -> bytes:
    """
    Finansal Analiz Modu ekranını (fiyat özeti + duygu skoru + sade dil özeti +
    haber listesi) PDF olarak üretir. Sabit yasal uyarı metni her zaman eklenir.

    Dönüş:
        bytes: İndirilebilir PDF dosyasının ham içeriği.
    """
    pdf = _pdf_olustur()
    _yaz(pdf, 10, f"Finansal Analiz: {varlik_adi}", kalin=True, punto=15)
    pdf.ln(2)

    _yaz(pdf, 8, "Fiyat Ozeti", kalin=True, punto=12)
    _yaz(
        pdf, 6,
        f"Guncel fiyat: {fiyat_bilgisi.get('guncel_fiyat', '-')}   "
        f"Gunluk degisim: %{fiyat_bilgisi.get('gunluk_degisim_yuzde', 0):+.2f}"
    )
    pdf.ln(2)

    _yaz(pdf, 8, "Piyasa Duygu Durumu", kalin=True, punto=12)
    _yaz(
        pdf, 6,
        f"Skor: {finansal_analiz.get('sentiment_skoru', 0):+.2f}   "
        f"({finansal_analiz.get('sentiment_durumu', 'Belirlenemedi')})"
    )
    pdf.ln(2)

    _yaz(pdf, 8, "Sade Dil Ozeti", kalin=True, punto=12)
    _yaz(pdf, 6, finansal_analiz.get("ozet", "Ozet olusturulamadi."))
    pdf.ln(2)

    if haberler:
        _yaz(pdf, 8, f"Ilgili Haberler ({len(haberler)} adet)", kalin=True, punto=12)
        for haber in haberler:
            _yaz(pdf, 6, haber.get("Başlık", "Başlık yok"), kalin=True, punto=10)
            _yaz(
                pdf, 5,
                f"{haber.get('Kaynak', 'Bilinmiyor')} · {haber.get('Tarih', '')} · {haber.get('URL', '')}",
                punto=9,
            )
            pdf.ln(1)

    pdf.ln(4)
    _yaz(pdf, 5, YASAL_UYARI, kalin=True, punto=9)

    return bytes(pdf.output())


def portfoy_csv_uret(portfoy_kayitlari: list[dict]) -> bytes:
    """
    Portföy kayıtlarını CSV olarak üretir (Excel'de doğru Türkçe karakter
    gösterimi için UTF-8 BOM eklenir).

    Parametreler:
        portfoy_kayitlari: `data.kullanici_verileri.portfoyu_getir` çıktısı.

    Dönüş:
        bytes: İndirilebilir CSV dosyasının ham içeriği.
    """
    df = pd.DataFrame(portfoy_kayitlari)
    if df.empty:
        df = pd.DataFrame(columns=["varlik_adi", "ticker", "miktar", "maliyet_fiyati", "eklenme_tarihi"])
    else:
        df = df[["varlik_adi", "ticker", "miktar", "maliyet_fiyati", "eklenme_tarihi"]]

    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8-sig")
