from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        # Workaround for a known djongo/MongoDB limitation: Django's default
        # user_logged_in signal tries to update the user's last_login field
        # right after authentication, and djongo sometimes loses track of
        # the document's primary key on that specific update, raising:
        #   ValueError: Cannot force an update in save() with no primary key.
        # Disabling this one signal avoids the crash. It only means the
        # last_login timestamp won't auto-update — everything else (login,
        # sessions, permissions) is unaffected.
        from django.contrib.auth.signals import user_logged_in
        from django.contrib.auth.models import update_last_login
        user_logged_in.disconnect(update_last_login)
