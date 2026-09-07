import smtplib
import socket

from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend


class IPv4SMTP(smtplib.SMTP):
    def _get_socket(self, host, port, timeout):
        ipv4_address = socket.gethostbyname(host)
        return socket.create_connection((ipv4_address, port), timeout, self.source_address)


class IPv4SMTPSSL(smtplib.SMTP_SSL):
    def _get_socket(self, host, port, timeout):
        ipv4_address = socket.gethostbyname(host)
        new_socket = socket.create_connection((ipv4_address, port), timeout, self.source_address)
        return self.context.wrap_socket(new_socket, server_hostname=host)


class EmailBackend(SMTPEmailBackend):
    @property
    def connection_class(self):
        return IPv4SMTPSSL if self.use_ssl else IPv4SMTP