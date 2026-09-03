from djongo import models


class Student(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("graduated", "Graduated"),
        ("withdrawn", "Withdrawn"),
    ]

    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]

    _id = models.ObjectIdField(primary_key=True)

    # Temporary reference until Dev1 School model is available
    school_id = models.CharField(max_length=24, blank=True)

    student_number = models.CharField(max_length=50, unique=True)
    admission_number = models.CharField(max_length=50, unique=True)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        blank=True,
    )

    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    profile_picture = models.CharField(max_length=500, blank=True)
    notes = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name


class Enrollment(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("completed", "Completed"),
        ("withdrawn", "Withdrawn"),
    ]

    _id = models.ObjectIdField(primary_key=True)

    # References stored temporarily as Mongo ObjectId strings
    student_id = models.CharField(max_length=24)
    academic_year_id = models.CharField(max_length=24, blank=True)
    grade_id = models.CharField(max_length=24, blank=True)
    classroom_id = models.CharField(max_length=24, blank=True)

    enrollment_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    def __str__(self):
        return self.student_id


class Guardian(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
    ]

    RELATIONSHIP_CHOICES = [
        ("father", "Father"),
        ("mother", "Mother"),
        ("legal_guardian", "Legal Guardian"),
        ("other", "Other"),
    ]

    _id = models.ObjectIdField(primary_key=True)

    school_id = models.CharField(
        max_length=24,
        blank=True,
    )

    first_name = models.CharField(
        max_length=100,
    )

    last_name = models.CharField(
        max_length=100,
    )

    relationship = models.CharField(
        max_length=30,
        choices=RELATIONSHIP_CHOICES,
    )

    phone = models.CharField(
        max_length=30,
    )

    email = models.EmailField(
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name


class StudentGuardian(models.Model):
    """
    Links students and guardians.

    A student can have multiple guardians,
    and one guardian can belong to multiple students.
    """

    _id = models.ObjectIdField(primary_key=True)

    student_id = models.CharField(
        max_length=24,
    )

    guardian_id = models.CharField(
        max_length=24,
    )

    is_primary = models.BooleanField(
        default=False,
    )

    def __str__(self):
        return f"{self.student_id} - {self.guardian_id}"
