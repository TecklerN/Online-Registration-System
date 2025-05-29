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
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime
from django.conf import settings
from django.utils.timezone import now 
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
    return user.is_authenticated and user.is_staff  

@login_required
def admin_dashboard(request):
    query = request.GET.get('query', '')

    pending_registrations = Registration.objects.filter(approval_status="Pending", payment_verified=True)
    approved_registrations = Registration.objects.filter(approval_status="Approved")
    rejected_registrations = Registration.objects.filter(approval_status="Rejected")

    if query:
        pending_registrations = pending_registrations.filter(
            organization_name__icontains=query) | pending_registrations.filter(email__icontains=query)
        approved_registrations = approved_registrations.filter(
            organization_name__icontains=query) | approved_registrations.filter(email__icontains=query)
        rejected_registrations = rejected_registrations.filter(
            organization_name__icontains=query) | rejected_registrations.filter(email__icontains=query)

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

    # ✅ Make sure a user exists
    user = User.objects.filter(email=registration.email).first()

    if user:
        # 🔐 Generate secure password reset email
        subject = "🎉 Registration Approved - Set Your Password"
        message = f"""
        Dear {registration.organization_name},

🎉 Congratulations! Your registration with POTRAZ has been approved.

You may now access the online system and its full set of services. To begin, please set your password using the link below:

🔐 Set Your Password: http://127.0.0.1:8000/reset/{urlsafe_base64_encode(force_bytes(user.pk))}/{default_token_generator.make_token(user)}/

Please do this within the next 24 hours to secure your account.

If you encounter any issues, feel free to contact us at support@potraz.gov.zw.

Best regards,  
POTRAZ Registration Team  
🌐 www.potraz.gov.zw
"""
        email_template_name = "registration/password_reset_email.html"
        context = {
            "email": user.email,
            "domain": "127.0.0.1:8000",
            "site_name": "POTRAZ",
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "user": user,
            "token": default_token_generator.make_token(user),
            "protocol": "http",
        }
        email_body = render_to_string(email_template_name, context)

        send_mail(subject, email_body, 'nyashateckler@gmail.com', [user.email], fail_silently=False)

    messages.success(request, " Registration approved & email sent!")
    return redirect('admin_dashboard')

@login_required
def reject_registration(request, reg_id):
    registration = get_object_or_404(Registration, id=reg_id)
    
    if request.method == 'POST':
        reason = request.POST.get('rejection_reason')
        registration.approval_status = 'Rejected'
        registration.rejection_reason = reason
        registration.save()

        # 📧 Send Rejection Email
        subject = " Registration Rejected  POTRAZ"
        message = f"""
Dear {registration.organization_name},

Thank you for submitting your registration to the POTRAZ Online Registration System.

After careful review, we regret to inform you that your registration has been **rejected** due to the following reason:

❗ {reason or 'Missing or invalid documentation.'}

We kindly advise you to review your submission and ensure all required documents are authentic, complete, and properly formatted before reapplying.

If you believe this decision was made in error or you need further clarification, please contact our team at: support@potraz.gov.zw.

We appreciate your interest in complying with the national data governance standards.

Best regards,  
POTRAZ Registration Team  
www.potraz.gov.zw
"""
        send_mail(
            subject,
            message,
            'nyashateckler@gmail.com',
            [registration.email],
            fail_silently=False,
        )

        messages.error(request, " Registration rejected & email sent!")
        return redirect('admin_dashboard')

    return render(request, 'admin/reject_reason_form.html', {'registration': registration})

   
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
                send_mail(subject, message, 'nyashateckler@gmail.com', [request.user.email])
                breach.email_sent = True
                breach.email_sent_at = now()
            except Exception as e:
                print(" Failed to send email:", e)
                breach.email_sent = False

            breach.save()

            messages.success(request, "✅ Breach report submitted successfully!")
            return render(request, 'breach_confirmation.html')
        else:
            print(" Breach form errors:", form.errors)
            messages.error(request, "Please correct the errors.")
    else:
        form = DataBreachForm()

    return render(request, 'report_breach.html', {'form': form})


@login_required
def breach_reports_admin(request):
    reports = DataBreach.objects.all().order_by('-date_occurred')
    return render(request, 'admin_breach_reports.html', {'reports': reports})




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

@login_required
def update_breach(request, breach_id):
    breach = get_object_or_404(DataBreach, id=breach_id)

    if request.method == 'POST':
        old_status = breach.status
        new_status = request.POST.get('status')
        resolution_notes = request.POST.get('resolution_notes')  
        cause = request.POST.get('cause')  
        recommendations = request.POST.get('recommendations')  

        breach.status = new_status
        breach.resolution_notes = resolution_notes
        breach.cause = cause
        breach.recommendations = recommendations
        breach.save()

        if old_status != 'resolved' and new_status == 'resolved':
            subject = "✅ Data Breach Resolved - POTRAZ"
            message = (
                f"Dear {breach.organization_name},\n\n"
                f"Thank you for reporting the data breach that occurred on {breach.date_occurred}.\n\n"
                f"We have reviewed and resolved the issue. Please find the summary below:\n\n"
                f"📌 **Cause**: {cause}\n"
                f"🔧 **How it was resolved**: {resolution_notes}\n"
                f"✅ **Recommendations**: {recommendations}\n\n"
                f"Status: {breach.status}\n\n"
                f"If you need more help, feel free to reach out.\n\nBest regards,\nPOTRAZ Cybersecurity Unit"
            )
            send_mail(subject, message, 'your-email@gmail.com', [breach.user.email])
            messages.success(request, "Resolved email sent successfully.")

        else:
            messages.success(request, "Breach status updated successfully.")

        return redirect('breach_reports_admin')

    return render(request, 'update_breach.html', {'breach': breach})


def update_breach_status(request, breach_id):
    breach = get_object_or_404(BreachReport, pk=breach_id)
    
    if request.method == 'POST':
        form = BreachStatusForm(request.POST, instance=breach)
        if form.is_valid():
            updated_breach = form.save()

            # Only send email if status is resolved
            if updated_breach.status == 'resolved':
                subject = "✅ Your Data Breach Report Has Been Resolved"
                from_email = "noreply@potraz.gov.zw"
                to_email = [updated_breach.email]  # assuming breach has an email field

                context = {
                    'organization_name': updated_breach.organization_name,
                    'description': updated_breach.description,
                    'date_occurred': updated_breach.date_occurred,
                    'cause': updated_breach.cause,
                    'resolution_notes': updated_breach.resolution_notes,
                    'recommendations': updated_breach.recommendations,
                    'current_year': datetime.now().year,
                }

                html_content = render_to_string('emails/breach_resolved_email.html', context)
                text_content = strip_tags(html_content)

                email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
                email.attach_alternative(html_content, "text/html")
                email.send()

            messages.success(request, "Breach status updated successfully.")
            return redirect('view_breaches')
    else:
        form = BreachStatusForm(instance=breach)

    return render(request, 'update_breach_status.html', {'form': form, 'breach': breach})
