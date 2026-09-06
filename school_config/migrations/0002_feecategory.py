import django_mongodb_backend.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('school_config', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeeCategory',
            fields=[
                ('id', django_mongodb_backend.fields.ObjectIdAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
