import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import gizli_ayarlar

def mail_gonder(alici_mail, konu, html_icerik):
    """Gmail üzerinden HTML formatlı mail gönderir. Başarılıysa (True, mesaj), değilse (False, hata) döner."""
    try:
        mesaj = MIMEMultipart("alternative")
        mesaj["Subject"] = konu
        mesaj["From"] = gizli_ayarlar.GONDEREN_MAIL
        mesaj["To"] = alici_mail
        mesaj.attach(MIMEText(html_icerik, "html"))

        # Gmail'in güvenli sunucusuna bağlan ve gönder
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as sunucu:
            sunucu.login(gizli_ayarlar.GONDEREN_MAIL, gizli_ayarlar.UYGULAMA_SIFRESI)
            sunucu.sendmail(gizli_ayarlar.GONDEREN_MAIL, alici_mail, mesaj.as_string())

        return True, "Mail başarıyla gönderildi."
    except Exception as e:
        return False, f"Mail gönderilemedi: {e}"