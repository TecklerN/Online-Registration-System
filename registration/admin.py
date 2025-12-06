from django.contrib import admin
from django.utils.html import format_html
from django.core.mail import send_mail, EmailMultiAlternatives
from django.utils import timezone
from django.conf import settings
from .models import Registration, DataBreach
import random, string


# Define action functions first
@admin.action(description="Mark selected breaches as Reviewed and send email")
def mark_as_reviewed(modeladmin, request, queryset):
    for breach in queryset:
        breach.status = 'reviewed'
        breach.email_sent = True
        breach.email_sent_at = timezone.now()
        send_mail(
            "Breach Reviewed by POTRAZ",
            f"Dear {breach.user.username},\n\n"
            f"Your reported data breach has been reviewed.\n\n"
            f"Review Details:\nCause: {breach.cause or 'N/A'}\n"
            f"Resolution: {breach.resolution_notes or 'N/A'}\n"
            f"Recommendations: {breach.recommendations or 'N/A'}\n\n"
            f"Thank you for cooperating with POTRAZ.",
            settings.DEFAULT_FROM_EMAIL,
            [breach.user.email],
            fail_silently=False
        )
        breach.save()

@admin.action(description="Mark selected breaches as Resolved")
def mark_as_resolved(modeladmin, request, queryset):
    for breach in queryset:
        if breach.status != 'resolved':
            breach.status = 'resolved'
            breach.email_sent = True
            breach.email_sent_at = timezone.now()
            send_mail(
                "✅ Breach Resolved by POTRAZ",
                f"Dear {breach.user.username},\n\n"
                f"Your reported breach has been resolved successfully.\n\n"
                f"Cause: {breach.cause or 'N/A'}\n"
                f"Resolution: {breach.resolution_notes or 'N/A'}\n"
                f"Recommendations to Prevent Recurrence:\n{breach.recommendations or 'N/A'}\n\n"
                f"Regards,\nPOTRAZ Team",
                settings.DEFAULT_FROM_EMAIL,
                [breach.user.email],
                fail_silently=False
            )
            breach.save()

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('organization_name', 'email', 'role', 'created_at', 'payment_status', 'approval_status')
    list_filter = ('role', 'payment_status', 'approval_status')
    search_fields = ('organization_name', 'email')
    actions = ['approve_selected', 'reject_selected']
    


def approve_selected(self, request, queryset):
    from django.contrib.auth.models import User

    for registration in queryset:
        registration.approval_status = 'Approved'
        registration.payment_verified = True

        password = None  # Initialize password variable
         # ✅ Check if the registration has an associated user
        if not hasattr(registration, 'user') or not registration.user:
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            user = User.objects.create_user(
                username=registration.email,
                password=password,
                email=registration.email
            )
            registration.user = user
        
            registration.save()
        else:
                password = "Use the password you received earlier."

        
        # Prepare login details based on whether we created a new user
        if password:
            login_details = f"""
            <p>Here are your login credentials:</p>
            <ul>
                <li><strong>Username:</strong> {registration.email}</li>
                <li><strong>Password:</strong> {password}</li>
            </ul>
            """
        else:
            login_details = """
            <p>Use your existing credentials to login.</p>
            """
        
        subject = "🎉 Registration Approved - POTRAZ"
        from_email = 'nyashateckler@gmail.com'
        to_email = [registration.email]

        text_content = f"Dear {registration.organization_name}, your registration has been approved."

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                    <div style="text-align:center; margin-bottom:20px;">
                        <img src="http://127.0.0.1:8000/static/images/potraz_logo.png" width="150" />
                    </div>
                    <h2 style="color: green;">🎉 Congratulations!</h2>
                    <p>Dear <strong>{registration.organization_name}</strong>,</p>
                    <p>Your registration with <strong>POTRAZ</strong> has been 
                    <span style="color:green;"><strong>approved</strong></span>.</p>
                    <p>{'Here are your login credentials:' if password else ''}</p>
                    <ul>
                        <li><strong>Username:</strong> {registration.email}</li>
                        <li><strong>Password:</strong> {password}</li>
                    </ul>
                    <p>You can log in here: 
                    <a href="http://127.0.0.1:8000/login">http://127.0.0.1:8000/login</a></p>
                    <br/>
                    <p>We look forward to your compliance and cooperation.</p>
                    <br/>
                    <p style="font-size: 12px; color: grey;">Best regards,<br/>POTRAZ Team</p>
                </body>
            </html>
        """
        msg = EmailMultiAlternatives(
                subject="🎉 Registration Approved - POTRAZ",
                body=f"Dear {registration.organization_name}, your registration has been approved.",
                from_email='nyashateckler@gmail.com',
                to=[registration.email],
                bcc=['nyashateckler@gmail.com']
            )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        self.message_user(request, f"{queryset.count()} registrations approved")
    approve_selected.short_description = "Approve selected organizations"


def reject_selected(self, request, queryset):
        for registration in queryset:
            registration.approval_status = 'Rejected'
            registration.save()

            subject = " Registration Rejected - POTRAZ"
            from_email = 'nyashateckler@gmail.com'
            to_email = [registration.email]

            text_content = f"Dear {registration.organization_name}, your registration was rejected."

            html_content = format_html(
                """
                <html>
                <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                    <div style="text-align:center; margin-bottom:20px;">
                        <img src="http://127.0.0.1:8000/static/images/potraz_logo.png" width="150" />
                    </div>
                    <h2 style="color: red;"> We're Sorry</h2>
                    <p>Dear <strong>{registration.organization_name}</strong>,</p>
                    <p>Unfortunately, your registration with <strong>POTRAZ</strong> has been 
                    <span style="color:red;"><strong>rejected</strong></span>.</p>
                    <p>Possible reasons include missing or invalid documents. Please verify and try again.</p>
                    <p>If you believe this was a mistake, contact our support team.</p>
                    <br/>
                    <p style="font-size: 12px; color: grey;">Best regards,<br/>POTRAZ Team</p>
                </body>
            </html>
                """, registration.organization_name
            )

            msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
            msg.attach_alternative(html_content, "text/html")
            msg.send()
        self.message_user(request, " Selected registrations rejected and email sent.")
reject_selected.short_description = "Reject selected applications and send email"

@admin.register(DataBreach)
class DataBreachAdmin(admin.ModelAdmin):
    list_display = (
        'organization_name', 'description_preview', 'formatted_date',
        'colored_status', 'email_sent_icon'
    )
    list_filter = ('status', 'date_occurred')
    search_fields = ('organization_name', 'description')
    readonly_fields = (
        'user', 'organization_name', 'description', 'date_occurred',
        'created_at', 'date_reported', 'email_sent'
    )
    actions = [mark_as_reviewed, mark_as_resolved]

    def description_preview(self, obj):
        return obj.description[:60] + '...' if obj.description else ''
    description_preview.short_description = 'Description Preview'

    def colored_status(self, obj):
        color = {
            'pending': 'orange',
            'reviewed': 'blue',
            'resolved': 'green',
        }.get(obj.status.lower(), 'black')
        return format_html('<strong style="color:{};">{}</strong>', color, obj.status.capitalize())
    colored_status.short_description = 'Status'

    def email_sent_icon(self, obj):
        return format_html('<span style="color:green;">✔️</span>') if obj.email_sent else format_html('<span style="color:red;">❌</span>')
    email_sent_icon.short_description = 'Email Sent'

    def formatted_date(self, obj):
        return obj.date_reported.strftime('%b %d, %Y – %I:%M %p')
    formatted_date.short_description = 'Date Reported'

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            subject = f"🛡️ POTRAZ - Breach Status Updated"
            message = f"""
Dear {obj.organization_name},

Your data breach report dated {obj.date_occurred} has been updated.

New Status: {obj.status.upper()}

If you have further questions, feel free to reach out.

Best regards,  
POTRAZ Team
"""
            send_mail(
                subject,
                message,
                'nyashateckler@gmail.com',
                [obj.user.email],
                fail_silently=True
            )
        super().save_model(request, obj, form, change)