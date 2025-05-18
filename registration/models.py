from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.conf import settings

# PDF file validator
def validate_document_file(value):
    if not value.name.endswith('.pdf'):
        raise ValidationError("Only PDF files are allowed for document uploads.")

# -------------------------------------------------------
# 🟢 Data Controller Model
# -------------------------------------------------------
class DataController(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    registration_number = models.CharField(max_length=50, unique=True)
    document = models.FileField(
        upload_to='documents/',
        validators=[validate_document_file],
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# -------------------------------------------------------
# 🟢 Registration Model
# -------------------------------------------------------
class Registration(models.Model):
    ROLE_CHOICES = [
        ('controller', 'Data Controller'),
        ('processor', 'Data Processor')
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
    ]

    APPROVAL_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    organization_name = models.CharField(max_length=255)
    email = models.EmailField()
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    payment_verified = models.BooleanField(default=False)
    payment_status = models.CharField(
        max_length=10, choices=PAYMENT_STATUS_CHOICES, default='Pending'
    )
    document = models.FileField(
        upload_to='documents/', 
        validators=[validate_document_file],
        null=True, 
        blank=True
    )
    # models.py
    rejection_reason = models.TextField(null=True, blank=True)

    approval_status = models.CharField(
        max_length=10, choices=APPROVAL_CHOICES, default='Pending'
    )

    def __str__(self):
        return self.organization_name

# -------------------------------------------------------
# 🟢 Data Breach Model with Email Notification
# -------------------------------------------------------
class DataBreach(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organization_name = models.CharField(max_length=255)
    description = models.TextField()
    date_occurred = models.DateField()
    supporting_documents = models.FileField(
        upload_to='documents/', 
        validators=[validate_document_file],
        blank=True, 
        null=True
    )
    actions_taken = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    date_reported = models.DateTimeField(auto_now_add=True)
    resolution_notes = models.TextField(blank=True, null=True)
    cause = models.TextField(blank=True, null=True)
    recommendations = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending'
    )
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)


    def save(self, *args, **kwargs):
        # Send email if status has changed
        if self.pk:
            old = DataBreach.objects.get(pk=self.pk)
            if old.status != self.status:
                subject = "📢 Update on Your Breach Report"
                message = (
                    f"Dear {self.user.username},\n\n"
                    f"The status of your breach report (dated {self.date_reported.date()}) "
                    f"has been updated to: {self.status.capitalize()}.\n\n"
                    f"Regards,\nPOTRAZ Team"
                )
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [self.user.email],
                    fail_silently=False
                )
                self.email_sent = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Breach by {self.organization_name} on {self.date_occurred}"
