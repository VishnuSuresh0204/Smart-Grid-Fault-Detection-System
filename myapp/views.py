
import math

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout as auth_logout
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import *


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_user_role(user):
    if user.is_superuser:
        return 'Admin'
    return user.user_type


def get_logged_user(request):
    user_id = request.session.get('userid')

    if not user_id:
        return None

    try:
        user = Login.objects.get(id=user_id, is_active=True)

        if request.session.get('usertype') != get_user_role(user):
            request.session.flush()
            return None

        return user

    except (Login.DoesNotExist, ValueError, TypeError):
        request.session.flush()
        return None


def require_role(request, allowed_roles):
    user = get_logged_user(request)

    if user and get_user_role(user) in allowed_roles:
        return user

    return None


def get_base_template(role):
    templates = {
        'Admin': 'ADMIN/commen.html',
        'Grid Operator': 'OPERATOR/commen.html',
        'Maintenance Technician': 'TECHNICIAN/commen.html',
    }
    return templates.get(role, 'home.html')


def create_fault_alert(prediction):
    """
    Create an alert for a fault prediction.

    Call this after a FaultPrediction has been saved.
    Existing alerts for the same prediction are not duplicated.
    """
    fault = (prediction.predicted_fault or '').strip().lower()

    normal_labels = {
        'normal',
        'no fault',
        'no_fault',
        'healthy',
        'no failure',
        'no_failure',
        'none',
    }

    if fault in normal_labels:
        return None

    alert, created = FaultAlert.objects.get_or_create(
        prediction=prediction,
        defaults={
            'title': f'Grid fault detected: {prediction.predicted_fault}',
            'message': (
                f'A possible grid fault was detected for '
                f'{prediction.measurement.grid_section.section_name}. '
                f'Severity: {prediction.severity}. '
                f'Please review the prediction and take appropriate action.'
            ),
            'status': 'New',
        }
    )

    return alert


def get_prediction_queryset():
    return FaultPrediction.objects.select_related(
        'measurement',
        'measurement__grid_section',
        'measurement__recorded_by',
    ).order_by('-analyzed_at')


# =========================================================
# HOME
# =========================================================

def home(request):
    return render(request, 'home.html')


# =========================================================
# LOGIN
# =========================================================

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is None or not user.is_active:
            messages.error(request, 'Invalid username or password.')
            return redirect('/login')

        if user.is_superuser:
            role = 'Admin'
        elif user.user_type in [
            'Grid Operator',
            'Maintenance Technician',
        ]:
            role = user.user_type
        else:
            messages.error(request, 'Invalid user role.')
            return redirect('/login')

        auth_login(request, user)

        request.session['userid'] = user.id
        request.session['username'] = user.username
        request.session['usertype'] = role

        if role == 'Admin':
            return redirect('/admin_home')

        if role == 'Grid Operator':
            return redirect('/operator_home')

        return redirect('/technician_home')

    return render(request, 'login.html')


# =========================================================
# LOGOUT
# =========================================================

def logout(request):
    auth_logout(request)
    request.session.flush()
    return redirect('/login')


# =========================================================
# GRID OPERATOR REGISTRATION
# =========================================================

def operator_registration(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        employee_id = request.POST.get('employee_id', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        profile_image = request.FILES.get('profile_image')

        if not all([
            name, username, email, phone, address,
            employee_id, password, confirm_password,
        ]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('/operator_registration')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('/operator_registration')

        if Login.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('/operator_registration')

        if Login.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return redirect('/operator_registration')

        if GridOperatorRegistration.objects.filter(
            employee_id=employee_id
        ).exists():
            messages.error(request, 'Employee ID already exists.')
            return redirect('/operator_registration')

        try:
            with transaction.atomic():
                user = Login.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    user_type='Grid Operator',
                )

                GridOperatorRegistration.objects.create(
                    user=user,
                    name=name,
                    email=email,
                    phone=phone,
                    address=address,
                    employee_id=employee_id,
                    profile_image=profile_image,
                )

            messages.success(
                request,
                'Grid Operator registration successful. Please log in.',
            )
            return redirect('/login')

        except IntegrityError:
            messages.error(request, 'Registration failed. Please try again.')
            return redirect('/operator_registration')

    return render(request, 'operator_registration.html')


# =========================================================
# MAINTENANCE TECHNICIAN REGISTRATION
# =========================================================

def technician_registration(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        employee_id = request.POST.get('employee_id', '').strip()

        qualification = request.POST.get('qualification', '').strip()
        specialization = request.POST.get('specialization', '').strip()
        experience_input = request.POST.get('experience_years', '0')

        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        profile_image = request.FILES.get('profile_image')

        if not all([
            name, username, email, phone, address,
            employee_id, password, confirm_password,
        ]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('/technician_registration')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('/technician_registration')

        if Login.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('/technician_registration')

        if Login.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return redirect('/technician_registration')

        if MaintenanceTechnicianRegistration.objects.filter(
            employee_id=employee_id
        ).exists():
            messages.error(request, 'Employee ID already exists.')
            return redirect('/technician_registration')

        try:
            experience_years = int(experience_input)
            if experience_years < 0:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(
                request,
                'Experience must be a valid non-negative number.',
            )
            return redirect('/technician_registration')

        try:
            with transaction.atomic():
                user = Login.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    user_type='Maintenance Technician',
                )

                MaintenanceTechnicianRegistration.objects.create(
                    user=user,
                    name=name,
                    email=email,
                    phone=phone,
                    address=address,
                    employee_id=employee_id,
                    qualification=qualification,
                    specialization=specialization,
                    experience_years=experience_years,
                    profile_image=profile_image,
                )

            messages.success(
                request,
                'Technician registration successful. Please log in.',
            )
            return redirect('/login')

        except IntegrityError:
            messages.error(request, 'Registration failed. Please try again.')
            return redirect('/technician_registration')

    return render(request, 'technician_registration.html')


# =========================================================
# ADMIN DASHBOARD
# =========================================================

def admin_home(request):
    user = require_role(request, ['Admin'])

    if not user:
        messages.error(request, 'Please log in as an administrator.')
        return redirect('/login')

    context = {
        'total_operators': GridOperatorRegistration.objects.count(),
        'total_technicians': MaintenanceTechnicianRegistration.objects.count(),
        'total_grid_sections': GridSection.objects.count(),
        'total_measurements': ElectricalMeasurement.objects.count(),
        'total_predictions': FaultPrediction.objects.count(),
        'total_alerts': FaultAlert.objects.count(),
        'new_alerts': FaultAlert.objects.filter(status='New').count(),
        'total_maintenance_records': MaintenanceRecord.objects.count(),
        'open_maintenance': MaintenanceRecord.objects.filter(
            status='Open'
        ).count(),
        'in_progress_maintenance': MaintenanceRecord.objects.filter(
            status='In Progress'
        ).count(),
        'completed_maintenance': MaintenanceRecord.objects.filter(
            status='Completed'
        ).count(),
    }

    return render(request, 'ADMIN/home.html', context)


# =========================================================
# GRID OPERATOR DASHBOARD
# =========================================================

def operator_home(request):
    user = require_role(request, ['Grid Operator'])

    if not user:
        return redirect('/login')

    try:
        operator = GridOperatorRegistration.objects.get(user=user)
    except GridOperatorRegistration.DoesNotExist:
        messages.error(request, 'Operator profile not found.')
        return redirect('/logout')

    measurements = ElectricalMeasurement.objects.filter(
        recorded_by=user
    ).select_related('grid_section').order_by('-recorded_at')[:10]

    predictions = get_prediction_queryset().filter(
        measurement__recorded_by=user
    )[:10]

    context = {
        'operator': operator,
        'measurements': measurements,
        'predictions': predictions,
        'total_measurements': ElectricalMeasurement.objects.filter(
            recorded_by=user
        ).count(),
        'total_predictions': FaultPrediction.objects.filter(
            measurement__recorded_by=user
        ).count(),
        'total_alerts': FaultAlert.objects.filter(
            prediction__measurement__recorded_by=user
        ).count(),
    }

    return render(request, 'OPERATOR/home.html', context)


# =========================================================
# TECHNICIAN DASHBOARD
# =========================================================

def technician_home(request):
    user = require_role(request, ['Maintenance Technician'])

    if not user:
        return redirect('/login')

    try:
        technician = MaintenanceTechnicianRegistration.objects.get(user=user)
    except MaintenanceTechnicianRegistration.DoesNotExist:
        messages.error(request, 'Technician profile not found.')
        return redirect('/logout')

    maintenance_records = MaintenanceRecord.objects.filter(
        technician=user
    ).select_related(
        'prediction',
        'prediction__measurement',
        'prediction__measurement__grid_section',
    ).order_by('-assigned_at')

    context = {
        'technician': technician,
        'maintenance_records': maintenance_records,
        'total_assigned': maintenance_records.count(),
        'open_tasks': maintenance_records.filter(status='Open').count(),
        'in_progress_tasks': maintenance_records.filter(
            status='In Progress'
        ).count(),
        'completed_tasks': maintenance_records.filter(
            status='Completed'
        ).count(),
        'recent_alerts': FaultAlert.objects.filter(
            prediction__in=get_prediction_queryset(),
        ).order_by('-created_at')[:5],
    }

    return render(request, 'TECHNICIAN/home.html', context)


# =========================================================
# GRID OPERATOR PROFILE
# =========================================================

def operator_profile(request):
    user = require_role(request, ['Grid Operator'])

    if not user:
        return redirect('/login')

    try:
        profile = GridOperatorRegistration.objects.get(user=user)
    except GridOperatorRegistration.DoesNotExist:
        messages.error(request, 'Profile not found.')
        return redirect('/operator_home')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()

        if name:
            profile.name = name
        if phone:
            profile.phone = phone
        if address:
            profile.address = address

        if request.FILES.get('profile_image'):
            profile.profile_image = request.FILES['profile_image']

        profile.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('/operator_profile')

    return render(
        request,
        'OPERATOR/profile.html',
        {'user': user, 'profile': profile},
    )


# =========================================================
# TECHNICIAN PROFILE
# =========================================================

def technician_profile(request):
    user = require_role(request, ['Maintenance Technician'])

    if not user:
        return redirect('/login')

    try:
        profile = MaintenanceTechnicianRegistration.objects.get(user=user)
    except MaintenanceTechnicianRegistration.DoesNotExist:
        messages.error(request, 'Profile not found.')
        return redirect('/technician_home')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        qualification = request.POST.get('qualification', '').strip()
        specialization = request.POST.get('specialization', '').strip()
        experience_input = request.POST.get('experience_years', '0')

        if name:
            profile.name = name
        if phone:
            profile.phone = phone
        if address:
            profile.address = address

        try:
            experience_years = int(experience_input)
            if experience_years < 0:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(
                request,
                'Enter a valid non-negative experience value.',
            )
            return redirect('/technician_profile')

        profile.qualification = qualification
        profile.specialization = specialization
        profile.experience_years = experience_years

        if request.FILES.get('profile_image'):
            profile.profile_image = request.FILES['profile_image']

        profile.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('/technician_profile')

    return render(
        request,
        'TECHNICIAN/profile.html',
        {'user': user, 'profile': profile},
    )


# =========================================================
# ADMIN - VIEW GRID OPERATORS
# =========================================================

def view_operators(request):
    if not require_role(request, ['Admin']):
        return redirect('/login')

    operators = GridOperatorRegistration.objects.select_related(
        'user'
    ).order_by('-id')

    return render(
        request,
        'ADMIN/view_operators.html',
        {'operators': operators},
    )


# =========================================================
# ADMIN - VIEW TECHNICIANS
# =========================================================

def view_technicians(request):
    if not require_role(request, ['Admin']):
        return redirect('/login')

    technicians = MaintenanceTechnicianRegistration.objects.select_related(
        'user'
    ).order_by('-id')

    return render(
        request,
        'ADMIN/view_technicians.html',
        {'technicians': technicians},
    )


# =========================================================
# ADMIN - MANAGE GRID SECTIONS
# =========================================================

def manage_grid_sections(request):
    if not require_role(request, ['Admin']):
        return redirect('/login')

    if request.method == 'POST':
        section_name = request.POST.get('section_name', '').strip()
        section_code = request.POST.get('section_code', '').strip()
        location = request.POST.get('location', '').strip()
        description = request.POST.get('description', '').strip()

        try:
            voltage_rating = float(request.POST.get('voltage_rating', ''))
            current_rating = float(request.POST.get('current_rating', ''))

            if (
                not math.isfinite(voltage_rating)
                or not math.isfinite(current_rating)
                or voltage_rating <= 0
                or current_rating <= 0
            ):
                raise ValueError

        except (ValueError, TypeError):
            messages.error(
                request,
                'Voltage and current ratings must be positive numbers.',
            )
            return redirect('/manage_grid_sections')

        if not all([section_name, section_code, location]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('/manage_grid_sections')

        try:
            GridSection.objects.create(
                section_name=section_name,
                section_code=section_code,
                location=location,
                voltage_rating=voltage_rating,
                current_rating=current_rating,
                description=description,
            )
            messages.success(request, 'Grid section added successfully.')

        except IntegrityError:
            messages.error(
                request,
                'Section name or section code already exists.',
            )

        return redirect('/manage_grid_sections')

    sections = GridSection.objects.all().order_by('-id')

    return render(
        request,
        'ADMIN/manage_grid_sections.html',
        {'sections': sections},
    )


# =========================================================
# GRID OPERATOR - RECORD ELECTRICAL MEASUREMENT
# =========================================================

def add_measurement(request):
    user = require_role(request, ['Grid Operator'])

    if not user:
        return redirect('/login')

    sections = GridSection.objects.filter(
        is_active=True
    ).order_by('section_name')

    if request.method == 'POST':
        section_id = request.POST.get('grid_section')

        try:
            section = GridSection.objects.get(
                id=section_id,
                is_active=True,
            )
        except (GridSection.DoesNotExist, ValueError, TypeError):
            messages.error(request, 'Please select a valid grid section.')
            return redirect('/add_measurement')

        try:
            voltage = float(request.POST.get('voltage', ''))
            current = float(request.POST.get('current', ''))
            frequency = float(request.POST.get('frequency', ''))
            active_power = float(request.POST.get('active_power', ''))
            reactive_power = float(
                request.POST.get('reactive_power') or 0
            )

            power_factor_input = request.POST.get(
                'power_factor', ''
            ).strip()

            power_factor = (
                float(power_factor_input)
                if power_factor_input else None
            )

            values = [
                voltage,
                current,
                frequency,
                active_power,
                reactive_power,
            ]

            if not all(math.isfinite(value) for value in values):
                raise ValueError

            if voltage < 0 or current < 0 or frequency <= 0:
                raise ValueError

            if power_factor is not None:
                if not math.isfinite(power_factor):
                    raise ValueError
                if not 0 <= power_factor <= 1:
                    raise ValueError

        except (ValueError, TypeError):
            messages.error(
                request,
                'Enter valid readings. Power factor must be between 0 and 1.',
            )
            return redirect('/add_measurement')

        ElectricalMeasurement.objects.create(
            grid_section=section,
            voltage=voltage,
            current=current,
            frequency=frequency,
            active_power=active_power,
            reactive_power=reactive_power,
            power_factor=power_factor,
            input_source='Manual',
            recorded_by=user,
        )

        messages.success(
            request,
            'Electrical measurement saved successfully.',
        )
        return redirect('/measurement_history')

    return render(
        request,
        'OPERATOR/add_measurement.html',
        {'sections': sections},
    )


# =========================================================
# MEASUREMENT HISTORY
# =========================================================

def measurement_history(request):
    user = get_logged_user(request)

    if not user:
        return redirect('/login')

    role = get_user_role(user)

    measurements = ElectricalMeasurement.objects.select_related(
        'grid_section',
        'recorded_by',
    ).order_by('-recorded_at')

    if role == 'Grid Operator':
        measurements = measurements.filter(recorded_by=user)
    elif role != 'Admin':
        messages.error(request, 'You are not allowed to view measurements.')
        return redirect('/login')

    return render(
        request,
        'measurements/history.html',
        {
            'measurements': measurements,
            'base_template': get_base_template(role),
            'user_role': role,
        },
    )


# =========================================================
# FAULT PREDICTION HISTORY
# =========================================================

def prediction_history(request):
    user = get_logged_user(request)

    if not user:
        return redirect('/login')

    role = get_user_role(user)
    predictions = get_prediction_queryset()

    if role == 'Grid Operator':
        predictions = predictions.filter(measurement__recorded_by=user)
    elif role not in ['Admin', 'Maintenance Technician']:
        return redirect('/login')

    return render(
        request,
        'predictions/history.html',
        {
            'predictions': predictions,
            'base_template': get_base_template(role),
            'user_role': role,
        },
    )


# =========================================================
# FAULT PREDICTION DETAIL
# =========================================================

def prediction_detail(request, prediction_id):
    user = get_logged_user(request)

    if not user:
        return redirect('/login')

    prediction = get_object_or_404(
        get_prediction_queryset(),
        id=prediction_id,
    )

    role = get_user_role(user)

    if role == 'Grid Operator':
        if prediction.measurement.recorded_by_id != user.id:
            messages.error(request, 'You cannot view this prediction.')
            return redirect('/prediction_history')
    elif role not in ['Admin', 'Maintenance Technician']:
        return redirect('/login')

    alerts = prediction.alerts.order_by('-created_at')
    maintenance_records = prediction.maintenance_records.select_related(
        'technician'
    ).order_by('-assigned_at')

    return render(
        request,
        'predictions/detail.html',
        {
            'prediction': prediction,
            'alerts': alerts,
            'maintenance_records': maintenance_records,
            'base_template': get_base_template(role),
            'user_role': role,
        },
    )


# =========================================================
# FAULT ALERT HISTORY
# =========================================================

def fault_alert_history(request):
    user = get_logged_user(request)

    if not user:
        return redirect('/login')

    role = get_user_role(user)

    alerts = FaultAlert.objects.select_related(
        'prediction',
        'prediction__measurement',
        'prediction__measurement__grid_section',
        'prediction__measurement__recorded_by',
        'acknowledged_by',
    ).order_by('-created_at')

    if role == 'Grid Operator':
        alerts = alerts.filter(
            prediction__measurement__recorded_by=user
        )
    elif role not in ['Admin', 'Maintenance Technician']:
        return redirect('/login')

    return render(
        request,
        'alerts/history.html',
        {
            'alerts': alerts,
            'base_template': get_base_template(role),
            'user_role': role,
        },
    )


# =========================================================
# ACKNOWLEDGE FAULT ALERT
# =========================================================

def acknowledge_fault_alert(request, alert_id):
    user = get_logged_user(request)

    if not user:
        return redirect('/login')

    if request.method != 'POST':
        return redirect('/fault_alert_history')

    role = get_user_role(user)

    if role not in ['Admin', 'Maintenance Technician']:
        messages.error(
            request,
            'You are not allowed to acknowledge this alert.',
        )
        return redirect('/fault_alert_history')

    alert = get_object_or_404(FaultAlert, id=alert_id)

    if alert.status == 'Resolved':
        messages.warning(request, 'This alert has already been resolved.')
        return redirect('/fault_alert_history')

    alert.acknowledged_by = user
    alert.acknowledged_at = timezone.now()
    alert.status = 'Acknowledged'
    alert.save(update_fields=[
        'acknowledged_by',
        'acknowledged_at',
        'status',
    ])

    messages.success(request, 'Fault alert acknowledged.')
    return redirect('/fault_alert_history')


# =========================================================
# RESOLVE FAULT ALERT - ADMIN
# =========================================================

def resolve_fault_alert(request, alert_id):
    user = require_role(request, ['Admin'])

    if not user:
        return redirect('/login')

    if request.method != 'POST':
        return redirect('/fault_alert_history')

    alert = get_object_or_404(FaultAlert, id=alert_id)

    if alert.status != 'Resolved':
        alert.status = 'Resolved'
        alert.resolved_at = timezone.now()

        if alert.acknowledged_by is None:
            alert.acknowledged_by = user
            alert.acknowledged_at = timezone.now()

        alert.save(update_fields=[
            'status',
            'resolved_at',
            'acknowledged_by',
            'acknowledged_at',
        ])

    messages.success(request, 'Fault alert resolved.')
    return redirect('/fault_alert_history')


# =========================================================
# ADMIN - ASSIGN MAINTENANCE TASK
# =========================================================

def assign_maintenance(request):
    user = require_role(request, ['Admin'])

    if not user:
        return redirect('/login')

    if request.method == 'POST':
        prediction_id = request.POST.get('prediction_id')
        technician_id = request.POST.get('technician')
        problem_description = request.POST.get(
            'problem_description', ''
        ).strip()

        if not all([
            prediction_id,
            technician_id,
            problem_description,
        ]):
            messages.error(
                request,
                'Select a prediction and technician, and enter the problem.',
            )
            return redirect('/assign_maintenance')

        prediction = get_object_or_404(
            FaultPrediction,
            id=prediction_id,
        )

        technician_profile = get_object_or_404(
            MaintenanceTechnicianRegistration.objects.select_related('user'),
            id=technician_id,
        )

        try:
            with transaction.atomic():
                record = MaintenanceRecord.objects.create(
                    prediction=prediction,
                    technician=technician_profile.user,
                    problem_description=problem_description,
                    status='Open',
                )

                # Ensure an alert exists for this prediction.
                create_fault_alert(prediction)

            messages.success(
                request,
                f'Maintenance task #{record.id} assigned successfully.',
            )
            return redirect('/maintenance_records')

        except IntegrityError:
            messages.error(
                request,
                'Unable to assign the maintenance task. Please try again.',
            )
            return redirect('/assign_maintenance')

    predictions = get_prediction_queryset()
    technicians = MaintenanceTechnicianRegistration.objects.select_related(
        'user'
    ).order_by('name')

    return render(
        request,
        'maintenance/assign.html',
        {
            'predictions': predictions,
            'technicians': technicians,
        },
    )


# =========================================================
# MAINTENANCE RECORDS
# Admin: all records
# Technician: only assigned records
# =========================================================

def maintenance_records(request):
    user = get_logged_user(request)

    if not user:
        return redirect('/login')

    role = get_user_role(user)

    records = MaintenanceRecord.objects.select_related(
        'prediction',
        'prediction__measurement',
        'prediction__measurement__grid_section',
        'technician',
    ).order_by('-assigned_at')

    if role == 'Maintenance Technician':
        records = records.filter(technician=user)
    elif role != 'Admin':
        messages.error(
            request,
            'You are not allowed to view maintenance records.',
        )
        return redirect('/login')

    return render(
        request,
        'maintenance/records.html',
        {
            'records': records,
            'base_template': get_base_template(role),
            'user_role': role,
        },
    )


# =========================================================
# TECHNICIAN - UPDATE MAINTENANCE TASK
# =========================================================

def update_maintenance_status(request, record_id):
    user = require_role(request, ['Maintenance Technician'])

    if not user:
        return redirect('/login')

    if request.method != 'POST':
        return redirect('/maintenance_records')

    record = get_object_or_404(
        MaintenanceRecord,
        id=record_id,
        technician=user,
    )

    new_status = request.POST.get('status', '').strip()
    action_taken = request.POST.get('action_taken', '').strip()

    allowed_statuses = ['Open', 'In Progress', 'Completed']

    if new_status not in allowed_statuses:
        messages.error(request, 'Please select a valid maintenance status.')
        return redirect('/maintenance_records')

    if new_status == 'Completed' and not action_taken:
        messages.error(
            request,
            'Describe the action taken before completing the task.',
        )
        return redirect('/maintenance_records')

    record.status = new_status
    record.action_taken = action_taken

    if new_status == 'Completed':
        if record.completed_at is None:
            record.completed_at = timezone.now()
    else:
        record.completed_at = None

    record.save(update_fields=[
        'status',
        'action_taken',
        'completed_at',
    ])

    messages.success(request, 'Maintenance task updated successfully.')
    return redirect('/maintenance_records')
