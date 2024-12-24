# courses/emails.py
from django.conf import settings
from django.template.loader import render_to_string
from djoser.email import ActivationEmail
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)

class CustomActivationEmail(ActivationEmail):
    template_name = 'courses/custom_activation_email.html'
    token_generator = PasswordResetTokenGenerator()

    @staticmethod
    def get_subject():
        return "Activate Your Account"

    @staticmethod
    def send_manual_email(user):
        try:
            token = CustomActivationEmail.token_generator.make_token(user)
            subject = CustomActivationEmail.get_subject()
            context = {
                'frontend_url': settings.FRONTEND_URL,
                'uid': user.id,
                'token': token,
            }

            logger.debug(f"Email context: {context}")

            email_body = render_to_string('courses/custom_activation_email.html', context)
            plain_message = f"Activate your account by visiting this link: {context['frontend_url']}/activate/{context['uid']}/{context['token']}"

            logger.debug(f"Rendered HTML email body: {email_body}")
            logger.debug(f"Plain email body: {plain_message}")
            logger.debug(f"Sending email with subject: {subject}, to: {user.email}")

            send_mail(
                subject=subject,
                message=plain_message,
                html_message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info("Activation email sent successfully.")

        except Exception as e:
            logger.error(f"Error sending activation email: {e}")
            raise
