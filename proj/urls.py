"""
URL configuration for proj project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from myapp import views
urlpatterns = [
    path('admin/', admin.site.urls),
path('', views.home, name='home'),

    # Authentication
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),

    # Registration
    path(
        'operator_registration',
        views.operator_registration,
        name='operator_registration'
    ),
    path(
        'technician_registration',
        views.technician_registration,
        name='technician_registration'
    ),

    # Dashboards
    path('admin_home', views.admin_home, name='admin_home'),
    path('operator_home', views.operator_home, name='operator_home'),
    path('technician_home', views.technician_home, name='technician_home'),

    # Profiles
    path('operator_profile', views.operator_profile, name='operator_profile'),
    path('technician_profile', views.technician_profile, name='technician_profile'),

    # Admin management
    path('view_operators', views.view_operators, name='view_operators'),
    path('view_technicians', views.view_technicians, name='view_technicians'),
    path('manage_grid_sections', views.manage_grid_sections, name='manage_grid_sections'),

    # Measurements & Telemetry
    path('add_measurement', views.add_measurement, name='add_measurement'),
    path('measurement_history', views.measurement_history, name='measurement_history'),

    # Fault Predictions
    path('prediction_history', views.prediction_history, name='prediction_history'),
    path('prediction_detail/<int:prediction_id>', views.prediction_detail, name='prediction_detail'),

    # Fault Alerts
    path('fault_alert_history', views.fault_alert_history, name='fault_alert_history'),
    path('acknowledge_fault_alert/<int:alert_id>', views.acknowledge_fault_alert, name='acknowledge_fault_alert'),
    path('resolve_fault_alert/<int:alert_id>', views.resolve_fault_alert, name='resolve_fault_alert'),

    # Maintenance Management
    path('assign_maintenance', views.assign_maintenance, name='assign_maintenance'),
    path('maintenance_records', views.maintenance_records, name='maintenance_records'),
    path('update_maintenance_status/<int:record_id>', views.update_maintenance_status, name='update_maintenance_status'),
]
