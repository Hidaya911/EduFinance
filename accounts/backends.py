from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class EmailBackend(ModelBackend):
    """
    Authenticates using the email field instead of username.

    Your login form sends the value the user typed in the "Email address"
    box as POST field 'username' (that's just Django's AuthenticationForm
    field name — it doesn't mean it's matched against the username column).
    This backend takes that value and looks the user up by email instead.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()

        if username is None or password is None:
            return None

        try:
            user = UserModel.objects.get(email__iexact=username)
        except UserModel.DoesNotExist:
            # Run the default password hasher anyway to avoid leaking
            # via response-time whether an email exists in the system.
            UserModel().set_password(password)
            return None
        except UserModel.MultipleObjectsReturned:
            user = UserModel.objects.filter(email__iexact=username).order_by('id').first()

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None