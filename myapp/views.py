from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.db import IntegrityError, transaction

from .models import (
    Login,
    GridOperatorRegistration,
    MaintenanceTechnicianRegistration
)


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

            if user.user_type not in [
                'Admin',
                'Grid Operator',
                'Maintenance Technician'
            ]:
                messages.error(request, 'Invalid user type')
                return redirect('/login')

            # Django authentication session
            auth_login(request, user)

            # Custom session values
            request.session['userid'] = user.id
            request.session['username'] = user.username
            request.session['usertype'] = user.user_type

            # Role-based redirection
            if user.user_type == 'Admin':
                return redirect('/admin_home')

            elif user.user_type == 'Grid Operator':
                return redirect('/operator_home')

            elif user.user_type == 'Maintenance Technician':
                return redirect('/technician_home')

        messages.error(request, 'Invalid username or password')

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
            name, username, email, phone,
            address, employee_id, password, confirm_password
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
            messages.error(request, 'Registration failed. Please try again.')
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
            name, username, email, phone,
            address, employee_id, password, confirm_password
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
            messages.error(request, 'Registration failed. Please try again.')
            return redirect('/technician_registration')

    return render(request, 'technician_registration.html')


# ---------------------------------------------------------
# SESSION VALIDATION
# ---------------------------------------------------------

def get_logged_user(request):

    if 'userid' not in request.session:
        return None

    try:
        user = Login.objects.get(
            id=request.session['userid'],
            is_active=True
        )

        # Confirm that the session role still matches the database
        if request.session.get('usertype') != user.user_type:
            request.session.flush()
            return None

        return user

    except Login.DoesNotExist:
        request.session.flush()
        return None


# ---------------------------------------------------------
# ADMIN HOME
# ---------------------------------------------------------

def admin_home(request):

    user = get_logged_user(request)

    if user is None:
        return redirect('/login')

    if user.user_type != 'Admin':
        return redirect('/login')

    total_operators = GridOperatorRegistration.objects.count()
    total_technicians = MaintenanceTechnicianRegistration.objects.count()

    return render(
        request,
        'ADMIN/home.html',
        {
            'total_operators': total_operators,
            'total_technicians': total_technicians,
        }
    )


# ---------------------------------------------------------
# GRID OPERATOR HOME
# ---------------------------------------------------------

def operator_home(request):

    user = get_logged_user(request)

    if user is None:
        return redirect('/login')

    if user.user_type != 'Grid Operator':
        return redirect('/login')

    try:
        operator = GridOperatorRegistration.objects.get(user=user)
    except GridOperatorRegistration.DoesNotExist:
        messages.error(request, 'Operator profile not found.')
        return redirect('/login')

    return render(
        request,
        'OPERATOR/home.html',
        {
            'operator': operator
        }
    )


# ---------------------------------------------------------
# TECHNICIAN HOME
# ---------------------------------------------------------

def technician_home(request):

    user = get_logged_user(request)

    if user is None:
        return redirect('/login')

    if user.user_type != 'Maintenance Technician':
        return redirect('/login')

    try:
        technician = MaintenanceTechnicianRegistration.objects.get(
            user=user
        )
    except MaintenanceTechnicianRegistration.DoesNotExist:
        messages.error(request, 'Technician profile not found.')
        return redirect('/login')

    return render(
        request,
        'TECHNICIAN/home.html',
        {
            'technician': technician
        }
    )


# ---------------------------------------------------------
# GRID OPERATOR PROFILE
# ---------------------------------------------------------

def operator_profile(request):

    user = get_logged_user(request)

    if user is None:
        return redirect('/login')

    if user.user_type != 'Grid Operator':
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
        {
            'user': user,
            'profile': profile
        }
    )


# ---------------------------------------------------------
# TECHNICIAN PROFILE
# ---------------------------------------------------------

def technician_profile(request):

    user = get_logged_user(request)

    if user is None:
        return redirect('/login')

    if user.user_type != 'Maintenance Technician':
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

            profile.experience_years = experience_years

        except (ValueError, TypeError):
            messages.error(
                request,
                'Enter a valid non-negative experience value.'
            )
            return redirect('/technician_profile')

        if request.FILES.get('profile_image'):
            profile.profile_image = request.FILES['profile_image']

        profile.save()

        messages.success(request, 'Profile updated successfully.')
        return redirect('/technician_profile')

    return render(
        request,
        'TECHNICIAN/profile.html',
        {
            'user': user,
            'profile': profile
        }
    )


# ---------------------------------------------------------
# ADMIN - VIEW GRID OPERATORS
# ---------------------------------------------------------

def view_operators(request):

    user = get_logged_user(request)

    if user is None:
        return redirect('/login')

    if user.user_type != 'Admin':
        return redirect('/login')

    operators = GridOperatorRegistration.objects.all().order_by('-id')

    return render(
        request,
        'ADMIN/view_operators.html',
        {
            'operators': operators
        }
    )


# ---------------------------------------------------------
# ADMIN - VIEW TECHNICIANS
# ---------------------------------------------------------

def view_technicians(request):

    user = get_logged_user(request)

    if user is None:
        return redirect('/login')

    if user.user_type != 'Admin':
        return redirect('/login')

    technicians = MaintenanceTechnicianRegistration.objects.all().order_by('-id')

    return render(
        request,
        'ADMIN/view_technicians.html',
        {
            'technicians': technicians
        }
    )