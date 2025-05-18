from django import forms
from .models import DataBreach  
from .models import Registration

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ['organization_name', 'email', 'role', 'document']  # Include the document field

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['document'].required = True  # Make the file upload mandatory


class BreachReportForm(forms.ModelForm):
    class Meta:
        model = DataBreach
        fields =  [
            'organization_name',
            'date_occurred',
            'description',
            'actions_taken',
            'supporting_documents',
        ]
        widgets = {
            'date_occurred': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'impact': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'actions_taken': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'supporting_documents': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class DataBreachForm(forms.ModelForm):
    class Meta:
        model = DataBreach
        fields = ['organization_name', 'date_occurred', 'description']
        widgets = {
            'date_occurred': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'organization_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class BreachStatusForm(forms.ModelForm):
    class Meta:
        model = DataBreach
        fields = ['status', 'cause', 'resolution_notes', 'recommendations']
        widgets = {
            'cause': forms.Textarea(attrs={'rows': 2}),
            'resolution_notes': forms.Textarea(attrs={'rows': 2}),
            'recommendations': forms.Textarea(attrs={'rows': 2}),
        }


