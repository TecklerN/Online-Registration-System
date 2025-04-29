from django.contrib import admin
from .models import Registration, DataBreach
from django.utils.html import format_html
from django.core.mail import send_mail


from django.core.mail import EmailMultiAlternatives
from django.utils.html import format_html
from django.conf import settings

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('organization_name', 'email', 'role', 'created_at', 'payment_status', 'approval_status')
    list_filter = ('role', 'payment_status', 'approval_status')
    search_fields = ('organization_name', 'email')

    actions = ['approve_selected', 'reject_selected']

    def approve_selected(self, request, queryset):
        for registration in queryset:
            registration.approval_status = 'Approved'
            registration.save()

            subject = "🎉 Registration Approved - POTRAZ"
            from_email = 'nyashateckler@gmail.com'
            to_email = [registration.email]

            text_content = f"Dear {registration.organization_name}, your registration has been approved."

            html_content = format_html(
                """
                <html>
                    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                        <div style="text-align:center; margin-bottom:20px;">
                            <img src="http://127.0.0.1:8000/static/images/potraz_logo.png.png" alt="POTRAZ Logo" width="150" />
                        </div>
                        <h2 style="color: #004aad;">🎉 Congratulations!</h2>
                        <p>Dear <strong>{}</strong>,</p>
                        <p>Your registration with <strong>POTRAZ</strong> has been <span style="color:green;"><strong>approved</strong></span>.</p>
                        <p>You may now access the system and services.</p>
                        <br/>
                        <p style="font-size: 12px; color: grey;">Best regards,<br/>POTRAZ Team</p>
                    </body>
                </html>
                """, registration.organization_name
            )

            msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
            msg.attach_alternative(html_content, "text/html")
            msg.send()

    approve_selected.short_description = "Approve selected applications and send beautiful email"

    def reject_selected(self, request, queryset):
        for registration in queryset:
            registration.approval_status = 'Rejected'
            registration.save()

            subject = "🚫 Registration Rejected - POTRAZ"
            from_email = 'nyashateckler@gmail.com'
            to_email = [registration.email]

            text_content = f"Dear {registration.organization_name}, your registration was rejected."

            html_content = format_html(
                """
                <html>
                    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                        <div style="text-align:center; margin-bottom:20px;">
                            <img src="http://127.0.0.1:8000/static/images/potraz_logo.png.png" width="150" />
                        </div>
                        <h2 style="color: red;">🚫 We're Sorry</h2>
                        <p>Dear <strong>{}</strong>,</p>
                        <p>Unfortunately, your registration with <strong>POTRAZ</strong> has been <span style="color:red;"><strong>rejected</strong></span>.</p>
                        <p>If you believe this was a mistake, please contact our team for assistance.</p>
                        <br/>
                        <p style="font-size: 12px; color: grey;">Best regards,<br/>POTRAZ Team</p>
                    </body>
                </html>
                """, registration.organization_name
            )

            msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
            msg.attach_alternative(html_content, "text/html")
            msg.send()

    reject_selected.short_description = "Reject selected applications and send beautiful email"



@admin.register(DataBreach)
class DataBreachAdmin(admin.ModelAdmin):
    list_display = (
        'organization_name',
        'description_preview',
        'formatted_date',
        'colored_status',
        'email_sent_icon'
    )

    list_filter = ('status', 'date_occurred')
    search_fields = ('organization_name', 'description')

    readonly_fields = (
        'user', 'organization_name', 'description',
        'date_occurred', 'created_at', 'date_reported',
        'email_sent'
    )

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
        if obj.email_sent:
            return format_html('<span style="color:green;">✔️</span>')
        return format_html('<span style="color:red;">❌</span>')
    email_sent_icon.short_description = 'Email Sent'

    def formatted_date(self, obj):
        return obj.date_reported.strftime('%b %d, %Y – %I:%M %p')
    formatted_date.short_description = 'Date Reported'
