from django.dispatch import receiver
from courses.signals import order_created
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from core.models import User, UserActivationToken
import uuid
import logging


@receiver(order_created)
def on_order_created(sender, **kwargs):
  print(kwargs['order'])

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def send_activation_email(sender, instance, created, **kwargs):
    if created:  # Only trigger on new user creation
        token = uuid.uuid4()  # Generate token
        user_activation_token = UserActivationToken.objects.create(user=instance, token=token)
        logger.debug(f"UserActivationToken created: {user_activation_token}")
        subject = "Activate Your Account for Mando Website"
        context = {
            'frontend_url': settings.FRONTEND_URL,
            'uid': instance.pk,
            'token': token,
        }

        email_body = render_to_string('courses/custom_activation_email.html', context)
        plain_message = f"Activate your account by visiting this link: {context['frontend_url']}/activate/{context['uid']}/{context['token']}"

        # Send the activation email
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=email_body,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[instance.email],
            fail_silently=False,
        )

        logger.info(f"Activation email sent to {instance.email}.")

