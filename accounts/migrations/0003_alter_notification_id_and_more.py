import django_mongodb_backend.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "accounts",
            "0002_notification_notificationpreference",
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # MongoDB already has its immutable _id field.
            # Do not attempt to rename or alter it physically.
            database_operations=[],

            # Update Django's migration state so it matches
            # the project's ObjectIdAutoField configuration.
            state_operations=[
                migrations.AlterField(
                    model_name="notification",
                    name="id",
                    field=(
                        django_mongodb_backend.fields.ObjectIdAutoField(
                            auto_created=True,
                            primary_key=True,
                            serialize=False,
                            verbose_name="ID",
                        )
                    ),
                ),

                migrations.AlterField(
                    model_name="notificationpreference",
                    name="id",
                    field=(
                        django_mongodb_backend.fields.ObjectIdAutoField(
                            auto_created=True,
                            primary_key=True,
                            serialize=False,
                            verbose_name="ID",
                        )
                    ),
                ),
            ],
        ),
    ]