from django.db import models


class AcademicYear(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g. "2026–2027"
    is_current = models.BooleanField(default=False)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.name