"""
disa_aktarma.py
----------------
Özellik 5.9 / S2.10 — Dışa Aktarma. Görüntülenen analiz ekranını PDF rapor
olarak, haber/portföy verisini CSV olarak dışa aktarma işlevlerini sağlar.

Dil kuralları (Özellik 5.5 ile aynı, istisnasız): PDF raporlarına yatırım
tavsiyesi niteliğinde hiçbir ifade eklenmez; finansal raporlarda sabit yasal
uyarı metni her zaman yer alır.
"""

import io
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Streamlit/sunucu ortamında ekran gerektirmeyen backend
import matplotlib.pyplot as plt
from fpdf import FPDF

_FONT_YOLU = Path(__file__).parent.parent / "assets" / "DejaVuSans.ttf"

YASAL_UYARI = (
    "Bu icerik yalnizca bilgilendirme amaclidir. Yatirim tavsiyesi degildir. "
    "Yatirim kararlariniz icin lutfen lisansli bir yatirim danismanina basvurun."
)

# Marka renkleri (RGB) — uygulamanın "haber" temasıyla uyumlu
_KIRMIZI = (206, 32, 41)      # #CE2029 — başlık çubuğu, vurgular
_LACIVERT = (44, 62, 80)      # #2C3E50 — alt başlıklar
_ACIK_GRI = (242, 242, 242)   # #F2F2F2 — kart arkaplanları
_ORTA_GRI = (120, 120, 120)   # ikincil metin
_BEYAZ = (255, 255, 255)
_SIYAH = (30, 30, 30)


class _RaporPDF(FPDF):
    """Her sayfada otomatik sayfa numarası ve ince alt çizgi ekleyen temel sınıf."""

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(*_ACIK_GRI)
        self.line(15, self.get_y(), self.w - 15, self.get_y())
        self.set_font("DejaVu", "", 8)
        self.set_text_color(*_ORTA_GRI)
        self.cell(0, 10, f"Sayfa {self.page_no()}", align="C")


def _pdf_olustur() -> _RaporPDF:
    """Türkçe karakterleri destekleyen (DejaVuSans gömülü) boş bir PDF sayfası oluşturur."""
    pdf = _RaporPDF()
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.add_font("DejaVu", "", str(_FONT_YOLU))
    pdf.add_font("DejaVu", "B", str(_FONT_YOLU))
    pdf.set_font("DejaVu", size=11)
    return pdf


def _fiyat_grafigi_png_uret(fiyat_df: pd.DataFrame, gostergeler: list[str]) -> bytes:
    """
    Fiyat verisini (kapanış + seçili göstergeler) matplotlib ile bir PNG
    grafiğe çizer, PDF'e gömülebilecek şekilde bytes olarak döndürür.
    """
    fig, ax = plt.subplots(figsize=(7.2, 3.2), dpi=150)

    ax.plot(fiyat_df.index, fiyat_df["Kapanis"], color="#CE2029", linewidth=1.4, label="Kapanis")

    if "MA200 (200 Günlük Ort.)" in gostergeler and "MA200" in fiyat_df.columns:
        ax.plot(fiyat_df.index, fiyat_df["MA200"], color="#2C3E50", linewidth=1.0, label="MA200")

    if "Bollinger Bantları" in gostergeler and "Bollinger_Ust" in fiyat_df.columns:
        ax.plot(fiyat_df.index, fiyat_df["Bollinger_Ust"], color="#999999", linewidth=0.8,
                 linestyle="--", label="Bollinger Ust")
        ax.plot(fiyat_df.index, fiyat_df["Bollinger_Alt"], color="#999999", linewidth=0.8,
                 linestyle="--", label="Bollinger Alt")

    ax.set_facecolor("#FFFFFF")
    fig.patch.set_facecolor("#FFFFFF")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=7, loc="upper left", frameon=False)
    ax.grid(True, alpha=0.2)
    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png")
    plt.close(fig)
    buffer.seek(0)
    return buffer.read()


def _satir(pdf: _RaporPDF, h: float, metin: str, kalin: bool = False, punto: int = 10,
           renk: tuple = _SIYAH) -> None:
    """
    Bir satır/paragraf yazar ve imleci HER ZAMAN garantili olarak sol kenara
    sıfırlar (fpdf2'de art arda multi_cell çağrılarının imleci sağda
    bırakıp genişliği negatife düşürmesini önlemek için).
    """
    pdf.set_font("DejaVu", "B" if kalin else "", punto)
    pdf.set_text_color(*renk)
    pdf.multi_cell(0, h, metin)
    pdf.set_x(pdf.l_margin)


def _baslik_cubugu(pdf: _RaporPDF, baslik: str, alt_baslik: str = "") -> None:
    """Sayfanın en üstüne, marka renginde bir başlık çubuğu çizer."""
    genislik = pdf.w
    pdf.set_fill_color(*_KIRMIZI)
    pdf.rect(0, 0, genislik, 28, style="F")

    pdf.set_xy(15, 8)
    pdf.set_font("DejaVu", "B", 17)
    pdf.set_text_color(*_BEYAZ)
    pdf.cell(genislik - 30, 8, "YZTA NEWS", align="L")

    pdf.set_xy(15, 17)
    pdf.set_font("DejaVu", "", 10)
    pdf.cell(genislik - 30, 6, baslik, align="L")

    pdf.set_xy(15, 35)
    pdf.set_text_color(*_SIYAH)
    if alt_baslik:
        pdf.set_font("DejaVu", "", 9)
        pdf.set_text_color(*_ORTA_GRI)
        pdf.cell(genislik - 30, 6, alt_baslik, align="L")
        pdf.set_x(pdf.l_margin)
        pdf.ln(10)
    else:
        pdf.ln(4)


def _bolum_basligi(pdf: _RaporPDF, metin: str) -> None:
    """Lacivert, dolu arkaplanlı bir bölüm başlığı çizer (örn. 'Kısaca Ne Oldu?')."""
    pdf.ln(3)
    pdf.set_x(pdf.l_margin)
    pdf.set_fill_color(*_LACIVERT)
    pdf.set_text_color(*_BEYAZ)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 9, f"  {metin}", fill=True, align="L")
    pdf.set_x(pdf.l_margin)
    pdf.ln(11)
    pdf.set_text_color(*_SIYAH)


def _paragraf(pdf: _RaporPDF, metin: str, punto: int = 10) -> None:
    """Açık gri kart arkaplanlı bir paragraf metni yazar."""
    pdf.set_font("DejaVu", "", punto)
    pdf.set_fill_color(*_ACIK_GRI)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 6, metin, fill=True)
    pdf.set_x(pdf.l_margin)
    pdf.ln(3)


def _kaynak_karti(pdf: _RaporPDF, baslik: str, kaynak: str, tarih: str, url: str,
                   metrik_metni: str = "") -> None:
    """Tek bir haber kaynağını, üst çizgili bir kart olarak çizer."""
    pdf.set_draw_color(*_ACIK_GRI)
    pdf.set_x(pdf.l_margin)
    pdf.set_font("DejaVu", "B", 10)
    pdf.set_text_color(*_SIYAH)
    pdf.multi_cell(0, 6, baslik, border="T")
    pdf.set_x(pdf.l_margin)

    pdf.set_font("DejaVu", "", 8)
    pdf.set_text_color(*_ORTA_GRI)
    pdf.multi_cell(0, 5, f"{kaynak}  -  {tarih}")
    pdf.set_x(pdf.l_margin)

    if metrik_metni:
        pdf.set_font("DejaVu", "", 8)
        pdf.set_text_color(*_LACIVERT)
        pdf.multi_cell(0, 5, metrik_metni)
        pdf.set_x(pdf.l_margin)

    pdf.set_font("DejaVu", "", 8)
    pdf.set_text_color(*_KIRMIZI)
    pdf.multi_cell(0, 5, url)
    pdf.set_x(pdf.l_margin)
    pdf.ln(2)


def genel_analiz_pdf_uret(konu: str, tldr: str, bias_analysis: dict, haberler: list[dict]) -> bytes:
    """
    Genel Haber Modu analiz ekranını (TL;DR + bias analizi + kaynak listesi) PDF olarak üretir.

    Dönüş:
        bytes: İndirilebilir PDF dosyasının ham içeriği.
    """
    pdf = _pdf_olustur()
    _baslik_cubugu(pdf, "Haber Analiz Raporu", f"Konu: {konu}")

    _bolum_basligi(pdf, "Kisaca Ne Oldu?")
    _paragraf(pdf, tldr or "Ozet olusturulamadi.")

    if bias_analysis:
        _bolum_basligi(pdf, "Bakis Acisi Haritasi")
        _satir(
            pdf, 5,
            "Asagidaki degerler siyasi bir yargi icermez, sadece metnin "
            "olculebilir yazim ozelliklerini yansitir.",
            punto=8, renk=_ORTA_GRI,
        )
        pdf.ln(2)
        for kaynak, metrikler in bias_analysis.items():
            if not isinstance(metrikler, dict):
                continue
            _satir(pdf, 6, kaynak, kalin=True, punto=10, renk=_SIYAH)
            _satir(
                pdf, 5,
                f"Olgu/Yorum: {metrikler.get('olgu_yorum_skoru', 0):.2f}   "
                f"Dogrulama: {metrikler.get('dogrulama_skoru', 0):.2f}   "
                f"Atif turu: {metrikler.get('atif_turu', 'belirtilmemis')}   "
                f"Duygusal: %{metrikler.get('duygusal_yuzde', 0):.0f}",
                punto=9, renk=_LACIVERT,
            )
            pdf.ln(2)

    if haberler:
        _bolum_basligi(pdf, f"Kaynak Haberler ({len(haberler)} adet)")
        for haber in haberler:
            _kaynak_karti(
                pdf,
                haber.get("Başlık", "Başlık yok"),
                haber.get("Kaynak", "Bilinmiyor"),
                haber.get("Tarih", ""),
                haber.get("URL", ""),
            )

    return bytes(pdf.output())


def finansal_analiz_pdf_uret(
    varlik_adi: str,
    fiyat_bilgisi: dict,
    finansal_analiz: dict,
    haberler: list[dict],
    fiyat_df: pd.DataFrame | None = None,
    gostergeler: list[str] | None = None,
) -> bytes:
    """
    Finansal Analiz Modu ekranını (fiyat özeti + grafik + duygu skoru +
    sade dil özeti + haber listesi) PDF olarak üretir. Sabit yasal uyarı
    metni her zaman eklenir.

    fiyat_df / gostergeler verilirse, fiyat grafiği de PDF'e resim olarak
    gömülür; verilmezse bu bölüm atlanır (geriye dönük uyumluluk için
    opsiyonel tutuldu).

    Dönüş:
        bytes: İndirilebilir PDF dosyasının ham içeriği.
    """
    pdf = _pdf_olustur()
    _baslik_cubugu(pdf, "Finansal Analiz Raporu", f"Varlik: {varlik_adi}")

    _bolum_basligi(pdf, "Fiyat Ozeti")
    degisim = fiyat_bilgisi.get("gunluk_degisim_yuzde", 0)
    _paragraf(
        pdf,
        f"Guncel fiyat: {fiyat_bilgisi.get('guncel_fiyat', '-')}     "
        f"Gunluk degisim: %{degisim:+.2f}"
    )

    if fiyat_df is not None and not fiyat_df.empty:
        _bolum_basligi(pdf, "Fiyat Grafigi")
        try:
            grafik_png = _fiyat_grafigi_png_uret(fiyat_df, gostergeler or [])
            pdf.set_x(pdf.l_margin)
            pdf.image(io.BytesIO(grafik_png), w=pdf.w - 30)
            pdf.ln(3)
        except Exception:
            _satir(pdf, 5, "Grafik olusturulamadi.", punto=9, renk=_ORTA_GRI)

    _bolum_basligi(pdf, "Piyasa Duygu Durumu")
    _paragraf(
        pdf,
        f"Skor: {finansal_analiz.get('sentiment_skoru', 0):+.2f}     "
        f"Durum: {finansal_analiz.get('sentiment_durumu', 'Belirlenemedi')}"
    )

    _bolum_basligi(pdf, "Sade Dil Ozeti")
    _paragraf(pdf, finansal_analiz.get("ozet", "Ozet olusturulamadi."))

    if haberler:
        _bolum_basligi(pdf, f"Ilgili Haberler ({len(haberler)} adet)")
        for haber in haberler:
            _kaynak_karti(
                pdf,
                haber.get("Başlık", "Başlık yok"),
                haber.get("Kaynak", "Bilinmiyor"),
                haber.get("Tarih", ""),
                haber.get("URL", ""),
            )

    pdf.ln(4)
    pdf.set_x(pdf.l_margin)
    pdf.set_fill_color(*_ACIK_GRI)
    pdf.set_font("DejaVu", "B", 8)
    pdf.set_text_color(*_ORTA_GRI)
    pdf.multi_cell(0, 5, f"Yasal Uyari: {YASAL_UYARI}", fill=True)
    pdf.set_x(pdf.l_margin)

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


def haberler_csv_uret(haberler: list[dict], bias_analysis: dict | None = None) -> bytes:
    """
    Bir haber listesini (Genel Haber Modu ya da Finansal Analiz Modu) CSV
    olarak üretir. bias_analysis verilirse, olgu/yorum ve doğrulama skorları
    da (varsa) ek sütun olarak eklenir.

    Dönüş:
        bytes: İndirilebilir CSV dosyasının ham içeriği (UTF-8 BOM'lu).
    """
    satirlar = []
    for haber in haberler:
        satir = {
            "Baslik": haber.get("Başlık", ""),
            "Kaynak": haber.get("Kaynak", ""),
            "Tarih": haber.get("Tarih", ""),
            "URL": haber.get("URL", ""),
        }
        if bias_analysis:
            metrikler = bias_analysis.get(haber.get("Kaynak", ""), {})
            if isinstance(metrikler, dict):
                satir["Olgu_Yorum_Skoru"] = metrikler.get("olgu_yorum_skoru", "")
                satir["Dogrulama_Skoru"] = metrikler.get("dogrulama_skoru", "")
                satir["Atif_Turu"] = metrikler.get("atif_turu", "")
                satir["Duygusal_Yuzde"] = metrikler.get("duygusal_yuzde", "")
        satirlar.append(satir)

    df = pd.DataFrame(satirlar)
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8-sig")


def fiyat_verisi_csv_uret(fiyat_df: pd.DataFrame) -> bytes:
    """
    Fiyat/teknik gösterge tablosunu (tarih, kapanış, MA200, Bollinger,
    RSI, MACD, Stokastik vb. — DataFrame'de ne varsa) CSV olarak üretir.

    Türkçe Excel/Google Sheets ile uyumlu olması için noktalı virgül (;)
    sütun ayracı ve virgül (,) ondalık işareti kullanılır — aksi halde
    Türkçe yerel ayarlı programlar ondalık noktayı binlik ayracı sanıp
    sayıları yanlış (çok büyük) gösterebilir. Sayılar okunabilirlik için
    4 ondalık basamağa yuvarlanır.

    Parametreler:
        fiyat_df: `data.finans_verisi.fiyat_verisi_getir` /
            `teknik_gostergeleri_hesapla` çıktısı (index tarih).

    Dönüş:
        bytes: İndirilebilir CSV dosyasının ham içeriği (UTF-8 BOM'lu).
    """
    df = fiyat_df.copy()
    df.index.name = "Tarih"
    sayisal_sutunlar = df.select_dtypes(include="number").columns
    df[sayisal_sutunlar] = df[sayisal_sutunlar].round(4)

    buffer = io.StringIO()
    df.to_csv(buffer, index=True, sep=";", decimal=",")
    return buffer.getvalue().encode("utf-8-sig")