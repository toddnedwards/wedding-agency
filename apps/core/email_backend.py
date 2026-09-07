import smtplib
import socket

from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend


class IPv4SMTP(smtplib.SMTP):
    def _get_socket(self, host, port, timeout):
        ipv4_address = socket.gethostbyname(host)
        return socket.create_connection((ipv4_address, port), timeout, self.source_address)


class EmailBackend(SMTPEmailBackend):
    connection_class = IPv4SMTP