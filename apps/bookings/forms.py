from django import forms
from django.utils import timezone
from .models import Enquiry

class EnquiryForm(forms.ModelForm):
    """Form for customer to submit an enquiry"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'event_date' in self.fields:
            self.fields['event_date'].widget.attrs['min'] = timezone.localdate().isoformat()

    def clean_event_date(self):
        event_date = self.cleaned_data.get('event_date')
        if event_date and event_date < timezone.localdate():
            raise forms.ValidationError('Event date cannot be in the past.')
        return event_date
    
    class Meta:
        model = Enquiry
        fields = [
            'customer_name',
            'customer_email',
            'customer_phone',
            'event_date',
            'event_time',
            'event_type',
            'event_location',
            'venue_name',
            'county',
            'details',
            'special_requirements',
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Your Full Name',
            }),
            'customer_email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Your Email Address',
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Your Phone Number',
                'type': 'tel',
            }),
            'event_date': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'type': 'date',
            }),
            'event_time': forms.TimeInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'type': 'time',
            }),
            'event_type': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'e.g., Wedding, Birthday, Corporate Event',
            }),
            'event_location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Event Location/Address',
            }),
            'venue_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Venue Name (Optional)',
            }),
            'county': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'County/Region',
            }),
            'details': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Tell us about your event and what you\'re looking for',
                'rows': 4,
            }),
            'special_requirements': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Any special requirements or notes?',
                'rows': 3,
            }),
        }
