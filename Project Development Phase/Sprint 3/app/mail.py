from config import MAIL_DEFAULT_SENDER, MAIL_API_KEY
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

sg = SendGridAPIClient(api_key = MAIL_API_KEY)

def send_mail(to_email, msg_title, msg_content):
    message = Mail(
        from_email = MAIL_DEFAULT_SENDER,
        to_emails = to_email,
        subject = msg_title,
        html_content = msg_content
    )
    sg.send(message)