
from django.db import models
from django.contrib.auth.models import AbstractUser


# ==========================================
# 1. LOGIN
# ==========================================

class Login(AbstractUser):

    user_type = models.CharField(max_length=50, blank=True)

    view_pass = models.CharField(
        max_length=255,
        blank=True
    )

    def __str__(self):
        return self.username


# ==========================================
# 2. GRID OPERATOR REGISTRATION
# ==========================================

class GridOperatorRegistration(models.Model):

    user = models.OneToOneField(
        Login,
        on_delete=models.CASCADE,
        related_name='operator_profile'
    )

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()

    employee_id = models.CharField(
        max_length=50,
        unique=True
    )

    profile_image = models.FileField(
        upload_to='operator_profiles/',
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ==========================================
# 3. MAINTENANCE TECHNICIAN REGISTRATION
# ==========================================

class MaintenanceTechnicianRegistration(models.Model):

    user = models.OneToOneField(
        Login,
        on_delete=models.CASCADE,
        related_name='technician_profile'
    )

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()

    employee_id = models.CharField(
        max_length=50,
        unique=True
    )

    qualification = models.CharField(
        max_length=200,
        blank=True
    )

    specialization = models.CharField(
        max_length=200,
        blank=True
    )

    experience_years = models.PositiveIntegerField(default=0)

    profile_image = models.FileField(
        upload_to='technician_profiles/',
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name