
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



# ==========================================
# 4. GRID SECTION
# ==========================================

class GridSection(models.Model):

    section_name = models.CharField(max_length=100, unique=True)
    section_code = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=200)

    voltage_rating = models.FloatField()
    current_rating = models.FloatField()

    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.section_name


# ==========================================
# 5. ELECTRICAL MEASUREMENT
# ==========================================

class ElectricalMeasurement(models.Model):

    grid_section = models.ForeignKey(
        GridSection,
        on_delete=models.CASCADE,
        related_name='measurements'
    )

    voltage = models.FloatField()
    current = models.FloatField()
    frequency = models.FloatField()
    active_power = models.FloatField()
    reactive_power = models.FloatField(default=0)
    power_factor = models.FloatField(null=True, blank=True)

    input_source = models.CharField(
        max_length=50,
        default='Manual'
    )

    recorded_by = models.ForeignKey(
        Login,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_measurements'
    )

    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.grid_section.section_name} - {self.id}"


# ==========================================
# 6. FAULT PREDICTION
# ==========================================

class FaultPrediction(models.Model):

    measurement = models.ForeignKey(
        ElectricalMeasurement,
        on_delete=models.CASCADE,
        related_name='predictions'
    )

    model_name = models.CharField(
        max_length=100,
        default='Hugging Face ML Model'
    )

    model_version = models.CharField(
        max_length=50,
        blank=True
    )

    predicted_fault = models.CharField(max_length=100)

    confidence_score = models.FloatField(
        null=True,
        blank=True
    )

    severity = models.CharField(
        max_length=50,
        default='Low'
    )

    explanation = models.TextField(blank=True)

    verification_status = models.CharField(
        max_length=50,
        default='Pending'
    )

    analyzed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.predicted_fault