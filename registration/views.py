from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from .models import Registration, DataBreach
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from paynow import Paynow
from django.contrib.auth.models import User
import random
import string
from django.conf import settings
from .models import DataBreach
from .forms import BreachReportForm
from .forms import DataBreachForm
from django.core.mail import send_mail
from .models import Registration
from .forms import RegistrationForm
from django.shortcuts import get_object_or_404


# Paynow credentials (better to store them in settings.py)
PAYNOW_INTEGRATION_ID = settings.PAYNOW_INTEGRATION_ID
PAYNOW_INTEGRATION_KEY = settings.PAYNOW_INTEGRATION_KEY
PAYNOW_RESULT_URL = settings.PAYNOW_RESULT_URL  # Callback URL (for updating payment status)
PAYNOW_RETURN_URL = settings.PAYNOW_RETURN_URL  # Redirect user after payment

def initiate_payment(request, order_id):  
    order = get_object_or_404(Registration, id=order_id)

    paynow = Paynow(PAYNOW_INTEGRATION_ID, PAYNOW_INTEGRATION_KEY, PAYNOW_RESULT_URL, PAYNOW_RETURN_URL)

    # Create payment
    payment = paynow.create_payment(f"Order-{order.id}", order.email)
    payment.add("Registration Fee", 10.00)  # Ensure `amount_due` exists in your model

    # Send payment request to Paynow
    response = paynow.send(payment)

    if response.success:
        return redirect(response.redirect_url)  # Redirect user to Paynow payment options
    else:
        return render(request, "payment_failed.html", {'order': order})  # Show error if Paynow fails





def login_success(request):
    return redirect('report_breach')



def home(request):
    return render(request, 'home.html')

def homepage(request):
    return render(request, 'homepage.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            try:
                reg = Registration.objects.get(user=user)
                if reg.approval_status == "Approved":
                    login(request, user)
                    return redirect('dashboard')
                else:
                    messages.error(request, "⏳ Your account is still pending approval.")
            except Registration.DoesNotExist:
                messages.error(request, "Registration record not found.")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'registration/login.html')



def user_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('homepage')


def payment_success(request):
    return render(request, 'payment_success.html')


def register(request):
    print("📥 Register view accessed with method:", request.method)
    registration = None

    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            registration = form.save()
            print("✅ Registration saved:", registration)

            # ✅ Auto-create user account
            username = registration.email
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

            user = User.objects.create_user(username=username, password=password)
            user.email = registration.email
            user.save()

            # ✅ Send email with both registration confirmation & login credentials
            subject = "✅ Registration Received & Login Details - POTRAZ"
            message = f"""
Dear {registration.organization_name},

Thank you for registering with POTRAZ.

Your registration has been successfully received and is currently under review.

🧾 Submitted Role: {registration.role}

✅ Your login credentials:
Username: {username}
Password: {password}

Login here: http://127.0.0.1:8000/login

Best regards,  
POTRAZ Team
"""
            send_mail(
                subject,
                message,
                'nyashateckler@gmail.com',  # Or use a noreply@potraz.gov.zw if you have one
                [registration.email],
                fail_silently=False,
            )

            messages.success(request, '🎉 Registration successful! Login credentials have been emailed.')
            return render(request, 'confirmation.html')

        else:
            print("❌ Form errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form, 'registration': registration})



def confirmation(request):
    return render(request, 'confirmation.html')


@csrf_exempt
def payment_update(request):
    if request.method == 'POST':
        payment_data = request.POST
        print("💳 Payment Data Received:", payment_data)
        # TODO: Update payment status in database
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'failed'}, status=400)


@login_required
def dashboard(request):
    registrations = Registration.objects.all()
    return render(request, 'dashboard.html', {'registrations': registrations})


@login_required
def user_dashboard(request):
    registrations = Registration.objects.filter(email=request.user.email)
    return render(request, 'dashboard.html', {'registrations': registrations})


def make_payment(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id)

    # Mock payment process (replace with real payment gateway integration)
    payment_success = True  # Simulate a successful payment

    if payment_success:
        registration.payment_status = "Paid"
        registration.save()
        messages.success(request, "Payment successful!")
        return redirect('home')

    messages.error(request, "Payment failed. Please try again.")
    return redirect('register')



# Ensure only POTRAZ staff can access the panel
def is_potraz_staff(user):
    return user.is_authenticated and user.is_staff  # Adjust if you have specific roles

@login_required

def admin_dashboard(request):
    query = request.GET.get('query', '')

    # Filter registrations based on search query
    pending_registrations = Registration.objects.filter(approval_status="Pending", payment_verified=True)
    approved_registrations = Registration.objects.filter(approval_status="Approved", payment_verified=True)
    rejected_registrations = Registration.objects.filter(approval_status="Rejected", payment_verified=True)

    if query:
        pending_registrations = pending_registrations.filter(organization_name__icontains=query) | pending_registrations.filter(email__icontains=query)
        approved_registrations = approved_registrations.filter(organization_name__icontains=query) | approved_registrations.filter(email__icontains=query)
        rejected_registrations = rejected_registrations.filter(organization_name__icontains=query) | rejected_registrations.filter(email__icontains=query)

    return render(request, 'admin_dashboard.html', {
        'pending_registrations': pending_registrations,
        'approved_registrations': approved_registrations,
        'rejected_registrations': rejected_registrations,
    })


@login_required
def approve_registration(request, reg_id):
    registration = get_object_or_404(Registration, id=reg_id)
    registration.payment_verified = 'True'
    registration.approval_status = 'Approved'
    registration.save()

    # 📧 Send Approval Email
    subject = "🎉 Registration Approved!"
    message = f"Dear {registration.organization_name},\n\nYour registration has been approved by POTRAZ. You can now access all services.\n\nBest Regards,\nPOTRAZ Team"
    send_mail(subject, message, 'nyashateckler@gmail.com', [registration.email])

    messages.success(request, "✅ Registration approved & email sent!")
    return redirect('admin_dashboard')

@login_required
def reject_registration(request, reg_id):
    registration = get_object_or_404(Registration, id=reg_id)
    registration.approval_status = 'Rejected'
    registration.save()  

    # 📧 Send Rejection Email
    subject = "❌ Registration Rejected"
    message = f"Dear {registration.organization_name},\n\nUnfortunately, your registration was rejected by POTRAZ.\nIf you believe this was a mistake, please contact support.\n\nBest Regards,\nPOTRAZ Team"
    send_mail(subject, message, 'your-email@gmail.com', [registration.email])

    messages.error(request, "❌ Registration rejected & email sent!")
    return redirect('admin_dashboard')

@login_required
def report_breach(request):
    if request.method == 'POST':
        form = DataBreachForm(request.POST, request.FILES)
        if form.is_valid():
            breach = form.save(commit=False)
            breach.user = request.user

            # 💌 Confirmation Email
            subject = "✅ Data Breach Report Received"
            message = (
                f"Dear {breach.organization_name},\n\n"
                f"We have received your data breach report dated {breach.date_occurred}.\n\n"
                f"Details: {breach.description}\n\n"
                f"Our team will review and get back to you if needed.\n\nBest regards,\nPOTRAZ Team"
            )

            try:
                send_mail(subject, message, 'your-email@gmail.com', [request.user.email])
                breach.email_sent = True
                breach.email_sent_at = now()
            except Exception as e:
                print("❌ Failed to send email:", e)
                breach.email_sent = False

            breach.save()

            messages.success(request, "✅ Breach report submitted successfully!")
            return render(request, 'breach_confirmation.html')
        else:
            print("❌ Breach form errors:", form.errors)
            messages.error(request, "Please correct the errors.")
    else:
        form = DataBreachForm()

    return render(request, 'report_breach.html', {'form': form})


@login_required
def breach_reports_admin(request):
    reports = DataBreach.objects.all().order_by('-date_occurred')
    return render(request, 'admin_breach_reports.html', {'reports': reports})


@login_required
def report_breach(request):
    if request.method == 'POST':
        form = DataBreachForm(request.POST)
        if form.is_valid():
            breach = form.save(commit=False)
            breach.user = request.user  # Assign user
            breach.save()
            # 💌 Send confirmation email to the user
            subject = "✅ Data Breach Report Received"
            message = (
                f"Dear {breach.organization_name},\n\n"
                f"We have received your data breach report dated {breach.date_occurred}.\n\n"
                f"Details: {breach.description}\n\n"
                f"Our team will review and get back to you if needed.\n\nBest regards,\nPOTRAZ Team"
            )
            send_mail(subject, message, 'your-email@gmail.com', [request.user.email])
            messages.success(request, "✅ Breach report submitted successfully!")
            return render(request, "breach_confirmation.html")

        else:
            messages.error(request, "Please correct the form errors.")
    else:
        form = DataBreachForm()

    return render(request, 'report_breach.html', {'form': form})


@login_required
def my_breaches(request):
    breaches = DataBreach.objects.filter(user=request.user).order_by('-date_reported')
    return render(request, 'my_breaches.html', {'breaches': breaches})


@login_required
@staff_member_required
def reports_summary(request):
    # 📋 Registration Stats
    total_registrations = Registration.objects.count()
    approved = Registration.objects.filter(approval_status="Approved").count()
    pending = Registration.objects.filter(approval_status="Pending").count()
    rejected = Registration.objects.filter(approval_status="Rejected").count()

    # 🛡️ Breach Reports Stats
    total_breaches = DataBreach.objects.count()
    breach_pending = DataBreach.objects.filter(status="pending").count()
    breach_reviewed = DataBreach.objects.filter(status="reviewed").count()
    breach_resolved = DataBreach.objects.filter(status="resolved").count()

    # 🕒 Latest Activity
    latest_breach = DataBreach.objects.order_by('-date_reported').first()
    latest_reg = Registration.objects.order_by('-created_at').first()

    return render(request, "admin_reports_summary.html", {
        # Registration data
        "total_registrations": total_registrations,
        "approved": approved,
        "pending": pending,
        "rejected": rejected,

        # Breach data
        "total_breaches": total_breaches,
        "breach_pending": breach_pending,
        "breach_reviewed": breach_reviewed,
        "breach_resolved": breach_resolved,

        # Latest records
        "latest_breach": latest_breach,
        "latest_reg": latest_reg,
    })



@staff_member_required
def update_breach_status(request, breach_id):
    breach = get_object_or_404(DataBreach, id=breach_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        breach.status = new_status
        breach.save()

        messages.success(request, f"Status updated to {new_status}.")
        return redirect('breach_reports_admin')

    return render(request, 'update_breach_status.html', {'breach': breach})
