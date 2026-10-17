
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout as auth_logout
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import *

# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def get_user_role(user):
    """Superusers are administrators; other users use user_type."""
    if user.is_superuser:
        return 'Admin'
    return user.user_type


def get_logged_user(request):
    """Validate the logged-in user against the database session."""

    if 'userid' not in request.session:
        return None

    try:
        user = Login.objects.get(
            id=request.session['userid'],
            is_active=True
        )

        if request.session.get('usertype') != get_user_role(user):
            request.session.flush()
            return None

        return user

    except Login.DoesNotExist:
        request.session.flush()
        return None


def require_role(request, allowed_roles):
    """Return the user if their role is allowed; otherwise return None."""

    user = get_logged_user(request)

    if user is None:
        return None

    if get_user_role(user) not in allowed_roles:
        return None

    return user


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

def home(request):
    return render(request, 'home.html')


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------

def login(request):

    if request.method == 'POST':

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None and user.is_active:

            # Admin accounts are created using createsuperuser.
            if user.is_superuser:
                role = 'Admin'

            elif user.user_type in [
                'Grid Operator',
                'Maintenance Technician'
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

            elif role == 'Grid Operator':
                return redirect('/operator_home')

            elif role == 'Maintenance Technician':
                return redirect('/technician_home')

        messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')


# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------

def logout(request):
    auth_logout(request)
    request.session.flush()
    return redirect('/login')


# ---------------------------------------------------------
# GRID OPERATOR REGISTRATION
# ---------------------------------------------------------

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
            employee_id, password, confirm_password
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
                    user_type='Grid Operator'
                )

                GridOperatorRegistration.objects.create(
                    user=user,
                    name=name,
                    email=email,
                    phone=phone,
                    address=address,
                    employee_id=employee_id,
                    profile_image=profile_image
                )

            messages.success(
                request,
                'Grid Operator registration successful. Please log in.'
            )
            return redirect('/login')

        except IntegrityError:
            messages.error(
                request,
                'Registration failed. Please try again.'
            )
            return redirect('/operator_registration')

    return render(request, 'operator_registration.html')


# ---------------------------------------------------------
# MAINTENANCE TECHNICIAN REGISTRATION
# ---------------------------------------------------------

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
        experience_years = request.POST.get('experience_years', '0')

        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        profile_image = request.FILES.get('profile_image')

        if not all([
            name, username, email, phone, address,
            employee_id, password, confirm_password
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
            experience_years = int(experience_years)
            if experience_years < 0:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(
                request,
                'Experience must be a valid non-negative number.'
            )
            return redirect('/technician_registration')

        try:
            with transaction.atomic():

                user = Login.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    user_type='Maintenance Technician'
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
                    profile_image=profile_image
                )

            messages.success(
                request,
                'Technician registration successful. Please log in.'
            )
            return redirect('/login')

        except IntegrityError:
            messages.error(
                request,
                'Registration failed. Please try again.'
            )
            return redirect('/technician_registration')

    return render(request, 'technician_registration.html')


# ---------------------------------------------------------
# ADMIN HOME
# ---------------------------------------------------------

def admin_home(request):

    user = require_role(request, ['Admin'])

    if user is None:
        messages.error(request, 'Please log in as an administrator.')
        return redirect('/login')

    context = {
        'total_operators': GridOperatorRegistration.objects.count(),
        'total_technicians': MaintenanceTechnicianRegistration.objects.count(),
        'total_grid_sections': GridSection.objects.count(),
        'total_measurements': ElectricalMeasurement.objects.count(),
        'total_predictions': FaultPrediction.objects.count(),
    }

    return render(request, 'ADMIN/home.html', context)


# ---------------------------------------------------------
# GRID OPERATOR HOME
# ---------------------------------------------------------

def operator_home(request):

    user = require_role(request, ['Grid Operator'])

    if user is None:
        return redirect('/login')

    try:
        operator = GridOperatorRegistration.objects.get(user=user)
    except GridOperatorRegistration.DoesNotExist:
        messages.error(request, 'Operator profile not found.')
        return redirect('/logout')

    measurements = ElectricalMeasurement.objects.filter(
        recorded_by=user
    ).select_related('grid_section').order_by('-recorded_at')[:10]

    return render(
        request,
        'OPERATOR/home.html',
        {
            'operator': operator,
            'measurements': measurements,
            'total_measurements': ElectricalMeasurement.objects.filter(
                recorded_by=user
            ).count(),
        }
    )


# ---------------------------------------------------------
# TECHNICIAN HOME
# ---------------------------------------------------------

def technician_home(request):

    user = require_role(request, ['Maintenance Technician'])

    if user is None:
        return redirect('/login')

    try:
        technician = MaintenanceTechnicianRegistration.objects.get(user=user)
    except MaintenanceTechnicianRegistration.DoesNotExist:
        messages.error(request, 'Technician profile not found.')
        return redirect('/logout')

    return render(
        request,
        'TECHNICIAN/home.html',
        {'technician': technician}
    )


# ---------------------------------------------------------
# GRID OPERATOR PROFILE
# ---------------------------------------------------------

def operator_profile(request):

    user = require_role(request, ['Grid Operator'])

    if user is None:
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
        {'user': user, 'profile': profile}
    )


# ---------------------------------------------------------
# TECHNICIAN PROFILE
# ---------------------------------------------------------

def technician_profile(request):

    user = require_role(request, ['Maintenance Technician'])

    if user is None:
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
        experience_years = request.POST.get('experience_years', '0')

        if name:
            profile.name = name

        if phone:
            profile.phone = phone

        if address:
            profile.address = address

        profile.qualification = qualification
        profile.specialization = specialization

        try:
            experience_years = int(experience_years)
            if experience_years < 0:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(
                request,
                'Enter a valid non-negative experience value.'
            )
            return redirect('/technician_profile')

        profile.experience_years = experience_years

        if request.FILES.get('profile_image'):
            profile.profile_image = request.FILES['profile_image']

        profile.save()

        messages.success(request, 'Profile updated successfully.')
        return redirect('/technician_profile')

    return render(
        request,
        'TECHNICIAN/profile.html',
        {'user': user, 'profile': profile}
    )


# ---------------------------------------------------------
# ADMIN - VIEW GRID OPERATORS
# ---------------------------------------------------------

def view_operators(request):

    user = require_role(request, ['Admin'])

    if user is None:
        return redirect('/login')

    operators = GridOperatorRegistration.objects.select_related(
        'user'
    ).order_by('-id')

    return render(
        request,
        'ADMIN/view_operators.html',
        {'operators': operators}
    )


# ---------------------------------------------------------
# ADMIN - VIEW TECHNICIANS
# ---------------------------------------------------------

def view_technicians(request):

    user = require_role(request, ['Admin'])

    if user is None:
        return redirect('/login')

    technicians = MaintenanceTechnicianRegistration.objects.select_related(
        'user'
    ).order_by('-id')

    return render(
        request,
        'ADMIN/view_technicians.html',
        {'technicians': technicians}
    )


# ---------------------------------------------------------
# ADMIN - GRID SECTIONS
# ---------------------------------------------------------

def manage_grid_sections(request):

    user = require_role(request, ['Admin'])

    if user is None:
        return redirect('/login')

    if request.method == 'POST':

        section_name = request.POST.get('section_name', '').strip()
        section_code = request.POST.get('section_code', '').strip()
        location = request.POST.get('location', '').strip()
        description = request.POST.get('description', '').strip()

        try:
            voltage_rating = float(request.POST.get('voltage_rating', ''))
            current_rating = float(request.POST.get('current_rating', ''))

            if voltage_rating <= 0 or current_rating <= 0:
                raise ValueError

        except (ValueError, TypeError):
            messages.error(
                request,
                'Voltage and current ratings must be positive numbers.'
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
                description=description
            )
            messages.success(request, 'Grid section added successfully.')

        except IntegrityError:
            messages.error(
                request,
                'Section name or section code already exists.'
            )

        return redirect('/manage_grid_sections')

    sections = GridSection.objects.all().order_by('-id')

    return render(
        request,
        'ADMIN/manage_grid_sections.html',
        {'sections': sections}
    )


# ---------------------------------------------------------
# GRID OPERATOR - RECORD ELECTRICAL MEASUREMENT
# ---------------------------------------------------------

def add_measurement(request):

    user = require_role(request, ['Grid Operator'])

    if user is None:
        return redirect('/login')

    sections = GridSection.objects.filter(is_active=True).order_by(
        'section_name'
    )

    if request.method == 'POST':

        section_id = request.POST.get('grid_section')

        try:
            section = GridSection.objects.get(
                id=section_id,
                is_active=True
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

            power_factor_input = request.POST.get('power_factor', '').strip()
            power_factor = (
                float(power_factor_input)
                if power_factor_input else None
            )

            values = [
                voltage, current, frequency,
                active_power, reactive_power
            ]

            if not all(
                __import__('math').isfinite(value) for value in values
            ):
                raise ValueError

            if power_factor is not None:
                if not __import__('math').isfinite(power_factor):
                    raise ValueError
                if not 0 <= power_factor <= 1:
                    raise ValueError

            if voltage < 0 or current < 0 or frequency <= 0:
                raise ValueError

        except (ValueError, TypeError):
            messages.error(
                request,
                'Enter valid readings. Power factor must be between 0 and 1.'
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
            recorded_by=user
        )

        messages.success(
            request,
            'Electrical measurement saved successfully.'
        )
        return redirect('/measurement_history')

    return render(
        request,
        'OPERATOR/add_measurement.html',
        {'sections': sections}
    )


# ---------------------------------------------------------
# MEASUREMENT HISTORY
# ---------------------------------------------------------

def measurement_history(request):

    user = get_logged_user(request)

    if user is None:
        return redirect('/login')

    measurements = ElectricalMeasurement.objects.select_related(
        'grid_section', 'recorded_by'
    ).order_by('-recorded_at')

    role = get_user_role(user)

    if role == 'Grid Operator':
        measurements = measurements.filter(recorded_by=user)

    elif role not in ['Admin']:
        messages.error(request, 'You are not allowed to view measurements.')
        return redirect('/login')

    base_template = 'ADMIN/commen.html' if role == 'Admin' else 'OPERATOR/commen.html'

    return render(
        request,
        'measurements/history.html',
        {
            'measurements': measurements,
            'base_template': base_template,
            'user_role': role
        }
    )


# ---------------------------------------------------------
# FAULT PREDICTION HISTORY
# ---------------------------------------------------------

def prediction_history(request):

    user = get_logged_user(request)

    if user is None:
        return redirect('/login')

    predictions = FaultPrediction.objects.select_related(
        'measurement',
        'measurement__grid_section',
        'measurement__recorded_by'
    ).order_by('-analyzed_at')

    role = get_user_role(user)

    if role == 'Grid Operator':
        predictions = predictions.filter(
            measurement__recorded_by=user
        )

    elif role not in ['Admin', 'Maintenance Technician']:
        return redirect('/login')

    if role == 'Admin':
        base_template = 'ADMIN/commen.html'
    elif role == 'Grid Operator':
        base_template = 'OPERATOR/commen.html'
    else:
        base_template = 'TECHNICIAN/commen.html'

    return render(
        request,
        'predictions/history.html',
        {
            'predictions': predictions,
            'base_template': base_template,
            'user_role': role
        }
    )


# ---------------------------------------------------------
# FAULT PREDICTION DETAIL
# ---------------------------------------------------------

def prediction_detail(request, prediction_id):

    user = get_logged_user(request)

    if user is None:
        return redirect('/login')

    prediction = get_object_or_404(
        FaultPrediction.objects.select_related(
            'measurement',
            'measurement__grid_section',
            'measurement__recorded_by'
        ),
        id=prediction_id
    )

    role = get_user_role(user)

    # Operators can view only predictions for their own readings.
    if role == 'Grid Operator':
        if prediction.measurement.recorded_by_id != user.id:
            messages.error(request, 'You cannot view this prediction.')
            return redirect('/prediction_history')

    elif role not in ['Admin', 'Maintenance Technician']:
        return redirect('/login')

    if role == 'Admin':
        base_template = 'ADMIN/commen.html'
    elif role == 'Grid Operator':
        base_template = 'OPERATOR/commen.html'
    else:
        base_template = 'TECHNICIAN/commen.html'

    return render(
        request,
        'predictions/detail.html',
        {
            'prediction': prediction,
            'base_template': base_template,
            'user_role': role
        }
    )
