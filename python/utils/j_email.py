import smtplib
from email.message import EmailMessage
import socket, os

class Email:
    def __init__(self, smtp_server, port=25, user=None, password=None, ssl=False):
        self.smtp_server = smtp_server
        self.port = port
        self.user = user
        self.password = password
        self.ssl = ssl

    def __connect(self):
        try:
            if self.ssl:
                return smtplib.SMTP_SSL(self.smtp_server, self.port)
            else:
                return smtplib.SMTP(self.smtp_server, self.port)
        except socket.gaierror as err:
            print(f'Could not connect to {self.smtp_server}. {err}')
            return 0
    
    def __disconnect(self, s):
        s.quit()

    def __compile_msg(self, from_addr, to_addr, subject, body, files):
        try:
            msg = EmailMessage()
            msg.set_content(body)
            msg['From'] = from_addr
            msg['To'] = to_addr
            msg['Subject'] = subject
            for file_name in files:
                file_name_without_path = os.path.basename(file_name)
                with open(file_name, 'r') as f:
                    msg.add_attachment(f.read(), filename=file_name_without_path)
            return msg
        except FileNotFoundError as err:
            logger.error(f"Failed to locate file. {err}")

    def send_mail(self, from_addr, to_addr, subject, body, files=[]):
        try:
            s = self.__connect()    
            if s:
                msg = self.__compile_msg(from_addr, to_addr, subject, body, files)
                s.send_message(msg)
                self.__disconnect(s)
                print("Message Sent")
        except Exception as err:
            print(f"Exception caugh : {err}")