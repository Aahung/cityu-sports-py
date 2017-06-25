__author__ = 'Hung'

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class Mailer:
    def __init__(self):
        pass

    @staticmethod
    def send(receiver, sender='', subject='', message='', reply=''):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = ", ".join(receiver)
        msg['Reply-to'] = reply
        msg.attach(MIMEText(message, 'html'))
        try:
            server = smtplib.SMTP_SSL('', 465)
            server.ehlo()
            server.login('', '')
            server.sendmail(sender, receiver, msg.as_string())
            server.quit()
        except Exception, ex:
            server.quit()
            pass