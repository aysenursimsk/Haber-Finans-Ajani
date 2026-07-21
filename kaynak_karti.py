import streamlit as st


def kaynak_kartini_goster(
    kaynak: dict,
    index: int,
    favorilendi_mi: bool = False,
    kayitli_not: str = "",
    benzersiz_on_ek: str = "",
    not_ozelligi_aktif: bool = True,
):
    """
    Bir haber kaynağını kart formatında gösterir.

    kaynak dict'i şu alanları içermeli:
        - baslik (str)
        - kaynak_adi (str)
        - tarih (str)
        - link (str)
        - olgu_yorum_skoru (float, opsiyonel)   -> 0-1 arası (bias_analysis çıktısıyla aynı ölçek)
        - dogrulama_skoru (float, opsiyonel)    -> 0-1 arası
        - duygusal_yuzde (float, opsiyonel)     -> 0-100 arası

    favorilendi_mi: bu haberin şu an favori olup olmadığı (dışarıdan gelir).
    kayitli_not: bu haber için daha önce kaydedilmiş not (dışarıdan gelir).
    benzersiz_on_ek: farklı sorgular arasında widget key çakışmasını önlemek
        için (örn. aktif_kayit_id) — her sorgu için farklı bir değer verilmeli.
    not_ozelligi_aktif: False verilirse not ikonu/alanı hiç gösterilmez
        (örn. Finansal Mod'da notlar kalıcı kaydedilmediği için kapatılır).

    Dönüş değeri: {"favori_tiklandi_mi": bool|None, "yeni_not": str|None}
    Çağıran taraf bunları kalıcı olarak kaydetmekle sorumludur.
    """
    favori_tiklandi_mi = None
    yeni_not = None
    onek = f"{benzersiz_on_ek}_" if benzersiz_on_ek else ""

    with st.container(border=True):
        ust_sol, ust_sag = st.columns([5, 1])

        with ust_sol:
            st.markdown(f"**{kaynak['baslik']}**")
            st.caption(f"{kaynak['kaynak_adi']} · {kaynak['tarih']}")

        with ust_sag:
            favori_key = f"{onek}favori_{index}"

            if not_ozelligi_aktif:
                fav_col, not_col = st.columns(2)
            else:
                fav_col = st.container()

            with fav_col:
                yildiz = "⭐" if favorilendi_mi else "☆"
                if st.button(yildiz, key=favori_key, help="Favorile"):
                    favori_tiklandi_mi = not favorilendi_mi

            if not_ozelligi_aktif:
                not_key = f"{onek}not_ac_{index}"
                with not_col:
                    not_ikonu = "📝" if kayitli_not else "🗒️"
                    if st.button(not_ikonu, key=not_key, help="Not ekle/düzenle"):
                        st.session_state[f"{onek}not_ac_durum_{index}"] = not st.session_state.get(f"{onek}not_ac_durum_{index}", False)

        if not_ozelligi_aktif and st.session_state.get(f"{onek}not_ac_durum_{index}", False):
            girilen_not = st.text_area(
                "Notun",
                value=kayitli_not,
                key=f"{onek}not_metni_{index}",
                placeholder="Bu kaynakla ilgili notunu yaz...",
                label_visibility="collapsed",
            )
            if st.button("Notu Kaydet", key=f"{onek}not_kaydet_{index}"):
                yeni_not = girilen_not

        # Etiketler (0-1 ölçek: >= 0.6 belirgin, <= 0.4 tersi, arası dengeli)
        # Skorlar mevcut değilse (örn. Finansal Mod'da bias analizi yapılmıyor) bu bölüm atlanır.
        olgu_yorum = kaynak.get("olgu_yorum_skoru")
        dogrulama = kaynak.get("dogrulama_skoru")
        duygusal = kaynak.get("duygusal_yuzde")

        if olgu_yorum is not None and dogrulama is not None:
            etiket_col1, etiket_col2, _ = st.columns([2, 2, 3])

            with etiket_col1:
                if olgu_yorum >= 0.6:
                    st.markdown(":green[Olgu ağırlıklı]")
                elif olgu_yorum <= 0.4:
                    st.markdown(":orange[Yorum ağırlıklı]")
                else:
                    st.markdown(":gray[Dengeli]")

            with etiket_col2:
                if dogrulama >= 0.6:
                    st.markdown(":blue[Çok kaynaklı]")
                else:
                    st.markdown(":gray[Tek kaynaklı]")

            metrik_col, link_col = st.columns([3, 1])
            with metrik_col:
                st.caption(
                    f"Olgu/Yorum: **{olgu_yorum:.2f}**  ·  "
                    f"Doğrulama: **{dogrulama:.2f}**  ·  "
                    f"Duygusal: **%{(duygusal or 0):.0f}**"
                )
            with link_col:
                st.markdown(f"[Kaynağa git ↗]({kaynak['link']})")
        else:
            st.markdown(f"[Kaynağa git ↗]({kaynak['link']})")

    return {"favori_tiklandi_mi": favori_tiklandi_mi, "yeni_not": yeni_not}


def kaynak_listesini_goster(kaynaklar: list[dict]):
    """Birden fazla kaynağı sırayla kart formatında listeler."""
    for i, kaynak in enumerate(kaynaklar):
        kaynak_kartini_goster(kaynak, i)