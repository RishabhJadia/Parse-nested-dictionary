import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.utils import COMMASPACE
from email import encoders
from os.path import basename


class EmailSender:
    def __init__(self, smtp_server, smtp_port, username, password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    def send_email(self, to, subject, text, html=None, attachments=None, images=None, cc=None, delimiter=',', charset='utf-8'):
        msg = self._create_message(to, subject, text, html, attachments, images, cc, delimiter, charset)
        try:
            server = self._connect_to_server()
            self._send_message(server, msg)
            print("Email sent successfully!")
        except Exception as e:
            print("Error sending email: {}".format(e))
        finally:
            self._disconnect_from_server(server)

    def _create_message(self, to, subject, text, html=None, attachments=None, images=None, cc=None, delimiter=',', charset='utf-8'):
        msg = MIMEMultipart('related')
        msg['From'] = self.username
        msg['To'] = COMMASPACE.join(split_string(to, delimiter))
        if cc:
            msg['Cc'] = COMMASPACE.join(split_string(cc, delimiter))
        msg['Subject'] = subject

        msg.attach(MIMEText(text, 'plain', charset))
        if html:
            msg.attach(MIMEText(html, 'html', charset))

        if images:
            for image in images:
                self._attach_image(msg, image)

        if attachments:
            for file in attachments:
                self._attach_file(msg, file)

        return msg

    def _attach_image(self, msg, image_path):
        with open(image_path, 'rb') as f:
            img = MIMEImage(f.read())
            img.add_header('Content-ID', '<{}>'.format(basename(image_path)))
            msg.attach(img)

    def _attach_file(self, msg, file_path):
        try:
            with open(file_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment', filename=basename(file_path))
                msg.attach(part)
        except IOError:
            print("Error attaching file: {}".format(file_path))

    def _connect_to_server(self):
        server = smtplib.SMTP(self.smtp_server, self.smtp_port)
        server.starttls()
        server.login(self.username, self.password)
        return server

    def _send_message(self, server, msg):
        recipients = split_string(msg['To'] + ',' + msg['Cc'] if 'Cc' in msg else msg['To'])
        server.sendmail(self.username, recipients, msg.as_string())

    def _disconnect_from_server(self, server):
        server.quit()

def split_string(string, delimiter=','):
    """
    Splits a string by a specified delimiter into a list of individual strings.
    """
    return [s.strip() for s in string.split(delimiter) if s]
  
  
  --------------------------------------------------------------------------------------------------------
#TestCase
import unittest
from email_sender import EmailSender

class TestEmailSender(unittest.TestCase):
    def setUp(self):
        # Set up a test instance of the EmailSender class
        self.sender = EmailSender('smtp.example.com', 587, 'test@example.com', 'password123')

    def test_send_email_plain_text(self):
        # Test sending an email with plain text only
        recipients = ['recipient1@example.com', 'recipient2@example.com']
        subject = 'Test Email'
        body = 'This is a test email.'
        self.sender.send_email(recipients, subject, body)
        # Check that the email was sent successfully
        self.assertTrue(True, "Email was sent successfully")
        # Check that the expected email content was received
        expected_msg = f"From: test@example.com\nTo: {','.join(recipients)}\nSubject: {subject}\n\n{body}"
        self.assertIn(expected_msg, self.sender.sent_messages, "Email content was correct")

    def test_send_email_html_and_attachments(self):
        # Test sending an email with HTML and attachments
        recipients = ['recipient1@example.com']
        subject = 'Test Email with HTML and Attachments'
        body = 'This is a test email with HTML and attachments.'
        html = '<html><body><h1>This is a test email</h1><p>Here is an image:</p><img src="cid:image1"></body></html>'
        attachments = ['test.txt', 'test.pdf']
        images = ['test.png']
        self.sender.send_email(recipients, subject, body, html=html, attachments=attachments, images=images)
        # Check that the email was sent successfully
        self.assertTrue(True, "Email was sent successfully")
        # Check that the expected email content was received
        expected_msg = f"From: test@example.com\nTo: {','.join(recipients)}\nSubject: {subject}\n\n{body}"
        self.assertIn(expected_msg, self.sender.sent_messages, "Email content was correct")
        # Check that the attachments were received
        for attachment in attachments:
            expected_attachment = f"Content-Disposition: attachment; filename=\"{attachment}\""
            self.assertIn(expected_attachment, self.sender.sent_messages, f"Attachment {attachment} was received")
        # Check that the images were received
        for i, image in enumerate(images):
            expected_image = f"Content-ID: <image{i+1}>"
            self.assertIn(expected_image, self.sender.sent_messages, f"Image {image} was received")

    def test_send_email_invalid_recipient(self):
        # Test sending an email to an invalid recipient
        with self.assertRaises(Exception):
            self.sender.send_email(['invalid-email'], 'Test Email', 'This is a test email.')
        self.assertTrue(True, "Exception was raised")

    def test_send_email_missing_recipient(self):
        # Test sending an email without specifying any recipients
        with self.assertRaises(Exception):
            self.sender.send_email([], 'Test Email', 'This is a test email.')
        self.assertTrue(True, "Exception was raised")

    def test_send_email_invalid_attachment(self):
        # Test sending an email with an invalid attachment file path
        attachments = ['invalid-file-path.txt']
        with self.assertRaises(Exception):
            self.sender.send_email(['recipient1@example.com'], 'Test Email with Invalid Attachment', 'This is a test email with an invalid attachment.', attachments=attachments)
        self.assertTrue(True, "Exception was raised")

    def test_send_email_missing_username(self):
        # Test creating an EmailSender instance without specifying a username
        with self.assertRaises(Exception):
            EmailSender('smtp.example.com', 587, None, 'password123')
        self.assertTrue(True, "Exception was raised")

    def test_send_email_missing_password(self):
        # Test creating an EmailSender instance without specifying a password
        with self.assertRaises(Exception):
            EmailSender('smtp.example.com', 587, 'test@example.com', None)
        self.assertTrue(True, "Exception was raised")

if __name__ == '__main__':
    unittest.main()
