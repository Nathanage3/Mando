from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from djoser.views import UserViewSet
from django.conf import settings
from django.http import JsonResponse
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from .tokens import account_activation_token
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import User
import logging
import uuid


logger = logging.getLogger(__name__)


class CustomUserViewSet(UserViewSet):
    """
    Custom User ViewSet to handle additional user-related actions.
    Inherits from Djoser's UserViewSet.
    """

    @action(detail=False, methods=['put'], permission_classes=[IsAuthenticated])
    def update_profile_picture(self, request):
        """
        Custom action to update the user's profile picture.
        """
        try:
            user = request.user
            profile_picture = request.FILES.get('profile_picture')

            if not profile_picture:
                return Response({'error': 'No profile picture uploaded'}, status=400)

            # You could add additional validation for file type or size here
            user.profile_picture = profile_picture
            user.save()

            logger.info(f"Profile picture updated for {user.email}")
            return Response({'status': 'Profile picture updated successfully'}, status=200)

        except Exception as e:
            logger.error(f"Error updating profile picture: {str(e)}")
            return Response({'error': str(e)}, status=500)

'''Adding new lines of codes'''

def signup(request):
    if request.method == 'POST':
        print("POST Data:", request.POST)  # Log the submitted data
        form = CustomUserCreationForm(request.POST)
        if not form.is_valid():
            print("Form is not valid")
            print("Form errors:", form.errors)
        else:
            print("Form is valid")
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            print("User saved successfully:", user)

            # Generate activation link
            frontend_url = settings.FRONTEND_URL
            activation_link = f"{frontend_url}/activate/{urlsafe_base64_encode(force_bytes(user.pk))}/{account_activation_token.make_token(user)}"
            print("Activation link:", activation_link)  # Debugging log

            # Send email confirmation
            subject = 'Activate your account for MandoSite #2'
            message = render_to_string('registration/account_activation_email.html', {
                'user': user,
                'activation_link': activation_link,
            })

            try:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=message,
                    from_email=settings.EMAIL_HOST_USER,
                    to=[user.email],
                )
                email.attach_alternative(message, "text/html")
                email.send()
                print("Email sent successfully.")  # Debugging log
            except Exception as e:
                print("Error sending email:", e)

            return redirect('account_activation_sent')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/signup.html', {'form': form})


def account_activation_sent(request):
    return JsonResponse({'message': 'Account activation email sent.'}, status=200)


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return JsonResponse({'error': 'Invalid activation link'}, status=400)

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return JsonResponse({'message': 'Account activated successfully. Please log in to access your account.'}, status=200)
    else:
        return JsonResponse({'error': 'Invalid activation token'}, status=400)

def account_activation_complete(request):
    return JsonResponse({'message': 'Account activation complete.'}, status=200)


@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({'message': 'CSRF cookie set'})