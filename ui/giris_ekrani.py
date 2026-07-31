"""
giris_ekrani.py
----------------
Kullanıcı girişi ve kayıt formunu sidebar'da render eden arayüz bileşeni
(Özellik 6.1 — Hesap / Giriş Sistemi).
"""

import streamlit as st

from data.kullanici_yonetimi import giris_yap, kullanici_olustur


def giris_ekranini_goster() -> None:
    """
    Sidebar'da giriş / kayıt formunu gösterir. Başarılı işlemde
    st.session_state["kullanici"] doldurulur ve sayfa yeniden çalıştırılır.
    """
    st.sidebar.markdown("### 👤 Hesap")

    sekme_giris, sekme_kayit = st.sidebar.tabs(["Giriş Yap", "Kayıt Ol"])

    with sekme_giris:
        with st.form("giris_formu"):
            eposta = st.text_input("E-posta", key="giris_eposta")
            sifre = st.text_input("Şifre", type="password", key="giris_sifre")
            gonder = st.form_submit_button("Giriş Yap")

        if gonder:
            try:
                kullanici = giris_yap(eposta, sifre)
                if kullanici:
                    st.session_state["kullanici"] = kullanici
                    st.rerun()
                else:
                    st.error("E-posta veya şifre hatalı.")
            except Exception:
                st.error("😕 Giriş sırasında bir sorun oluştu. Lütfen tekrar deneyin.")

    with sekme_kayit:
        with st.form("kayit_formu"):
            yeni_eposta = st.text_input("E-posta", key="kayit_eposta")
            yeni_sifre = st.text_input("Şifre (en az 6 karakter)", type="password", key="kayit_sifre")
            kayit_gonder = st.form_submit_button("Hesap Oluştur")

        if kayit_gonder:
            try:
                kullanici = kullanici_olustur(yeni_eposta, yeni_sifre)
                st.session_state["kullanici"] = kullanici
                st.success("Hesabınız oluşturuldu, giriş yapıldı!")
                st.rerun()
            except ValueError as e:
                st.error(f"🚫 {e}")
            except Exception:
                st.error("😕 Kayıt sırasında bir sorun oluştu. Lütfen tekrar deneyin.")

    st.sidebar.caption(
        "Hesap açmadan da Genel Haber Modu'nu kullanabilirsiniz (misafir modu). "
        "Favoriler, alarm ve portföy için hesap gereklidir."
    )


def hesap_ozetini_goster() -> None:
    """Giriş yapmış kullanıcı için sidebar'da hoş geldin mesajı ve çıkış butonu gösterir."""
    kullanici = st.session_state.get("kullanici")
    st.sidebar.markdown("### 👤 Hesap")
    st.sidebar.write(f"Merhaba, **{kullanici['eposta']}**")
    if st.sidebar.button("Çıkış Yap"):
        del st.session_state["kullanici"]
        st.rerun()
