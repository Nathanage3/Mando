from django.dispatch import receiver
from courses.signals import order_created
from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from core.models import User
import logging

logger = logging.getLogger(__name__)

@receiver(order_created)
def on_order_created(sender, **kwargs):
  print(kwargs['order'])


@receiver(post_save, sender=User)
def send_activation_email(sender, instance, created, **kwargs):
    if created:
        subject = "Activate Your Account"
        context = {
            'frontend_url': settings.FRONTEND_URL,
            'uid': instance.id,
            'token': 'dummy-token',  # Replace with actual token generation logic
        }
        email_body = render_to_string('courses/custom_activation_email.html', context)
        plain_message = f"Activate your account by visiting this link: {context['frontend_url']}/activate/{context['uid']}/{context['token']}"

        logger.debug(f"Email context: {context}")
        logger.debug(f"Rendered HTML email body: {email_body}")

        send_mail(
            subject=subject,
            message=plain_message,
            html_message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.email],
            fail_silently=False,
        )
        logger.info("Activation email sent successfully.")
