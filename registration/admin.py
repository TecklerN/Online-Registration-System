from django.contrib import admin
from .models import Registration, DataBreach
from django.utils.html import format_html


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('organization_name', 'email', 'role', 'created_at', 'payment_status', 'approval_status')
    list_filter = ('role', 'payment_status', 'approval_status')  # You can filter by these
    search_fields = ('organization_name', 'email')

    actions = ['approve_selected', 'reject_selected']

    def approve_selected(self, request, queryset):
        queryset.update(approval_status='Approved')
    approve_selected.short_description = "Approve selected applications"

    def reject_selected(self, request, queryset):
        queryset.update(approval_status='Rejected')
    reject_selected.short_description = "Reject selected applications"


@admin.register(DataBreach)
class DataBreachAdmin(admin.ModelAdmin):
    list_display = (
        'organization_name',
        'description_preview',
        'formatted_date',
        'colored_status',
        'email_sent_icon'
    )

    def description_preview(self, obj):
        return obj.description[:60] + '...' if obj.description else ''
    description_preview.short_description = 'Description Preview'

    def colored_status(self, obj):
        color = {
            'Pending': 'orange',
            'Approved': 'green',
            'Rejected': 'red',
        }.get(obj.status, 'black')
        return format_html('<strong style="color:{};">{}</strong>', color, obj.status)
    colored_status.short_description = 'Status'

    def email_sent_icon(self, obj):
        if obj.email_sent:
            return format_html('<span style="color:green;">✔️</span>')
        return format_html('<span style="color:red;">❌</span>')
    email_sent_icon.short_description = 'Email Sent'

    def formatted_date(self, obj):
        return obj.date_reported.strftime('%b %d, %Y – %I:%M %p')
    formatted_date.short_description = 'Date Reported'
