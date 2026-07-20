import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

def mail_gonder(alici_mail, konu, html_icerik):
    """Gmail üzerinden HTML formatlı mail gönderir. Başarılıysa (True, mesaj), değilse (False, hata) döner.
    Şifreler .streamlit/secrets.toml'dan okunur (sunucuda Streamlit Cloud panelinden)."""
    try:
        gonderen = st.secrets["GONDEREN_MAIL"]
        sifre = st.secrets["UYGULAMA_SIFRESI"]
    except Exception:
        return False, "Mail ayarları bulunamadı: .streamlit/secrets.toml içinde GONDEREN_MAIL ve UYGULAMA_SIFRESI tanımlı olmalı."

    try:
        mesaj = MIMEMultipart("alternative")
        mesaj["Subject"] = konu
        mesaj["From"] = gonderen
        mesaj["To"] = alici_mail
        mesaj.attach(MIMEText(html_icerik, "html"))

        # Gmail'in güvenli sunucusuna bağlan ve gönder
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as sunucu:
            sunucu.login(gonderen, sifre)
            sunucu.sendmail(gonderen, alici_mail, mesaj.as_string())

        return True, "Mail başarıyla gönderildi."
    except Exception as e:
        return False, f"Mail gönderilemedi: {e}"