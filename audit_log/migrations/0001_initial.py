import django.db.models.deletion
import django_mongodb_backend.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', django_mongodb_backend.fields.ObjectIdAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('CREATE', 'Create'), ('UPDATE', 'Update'), ('DELETE', 'Delete'), ('LOGIN', 'Login'), ('OTHER', 'Other')], max_length=20)),
                ('model_name', models.CharField(max_length=100)),
                ('record_id', models.CharField(blank=True, max_length=100, null=True)),
                ('record_repr', models.CharField(blank=True, help_text='String representation of the record', max_length=255, null=True)),
                ('changes', models.TextField(blank=True, help_text='JSON or descriptive text of what changed', null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-timestamp']},
        ),
    ]
