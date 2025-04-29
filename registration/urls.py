from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import homepage
from .views import update_breach_status
from .views import reports_summary
from .views import report_breach
from .views import initiate_payment
from django.contrib.auth import views as auth_views
from .views import admin_dashboard, approve_registration, reject_registration


urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('admin/breach/update/<int:breach_id>/', update_breach_status, name='update_breach_status'),
    path('confirmation/', views.confirmation, name='confirmation'),
    path('reports-summary/', reports_summary, name='reports_summary'),
    path('reports-summary/', views.reports_summary, name='reports_summary'),
    path('my-breaches/', views.my_breaches, name='my_breaches'),
    path('admin/breach-reports/', views.breach_reports_admin, name='breach_reports_admin'),
    path("report-breach/", report_breach, name="report_breach"),
    path('admin_dashboard/', admin_dashboard, name='admin_dashboard'),
    path('approve/<int:reg_id>/', approve_registration, name='approve_registration'),
    path('reject/<int:reg_id>/', reject_registration, name='reject_registration'),
    path('pay/<int:order_id>/', initiate_payment, name='initiate_payment'),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('make-payment/<int:registration_id>/', views.make_payment, name='make_payment'),
    path('payment-update/', views.payment_update, name='payment_update'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('accounts/', include('django.contrib.auth.urls')),  # Built-in authentication views
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
