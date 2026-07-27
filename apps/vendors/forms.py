from django import forms
from apps.vendors.models import Musician, Caricaturist, Photographer

class MusicianSignupForm(forms.ModelForm):
    """Form for musicians to register as vendors"""
    password = forms.CharField(widget=forms.PasswordInput())
    password_confirm = forms.CharField(widget=forms.PasswordInput())
    
    class Meta:
        model = Musician
        fields = [
            'business_name',
            'bio',
            'profile_image',
            'experience_years',
            'instruments',
            'genres',
            'ensemble_size',
            'hourly_rate',
            'location',
            'phone',
            'website',
            'instagram',
            'facebook',
            'can_provide_sound_system',
        ]
        widgets = {
            'business_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Your Business Name',
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Tell us about yourself and your music',
                'rows': 4,
            }),
            'experience_years': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Years of Experience',
            }),
            'instruments': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'e.g., Piano, Violin, Guitar',
            }),
            'genres': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'e.g., Classical, Jazz, Pop',
            }),
            'ensemble_size': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Ensemble Size',
            }),
            'hourly_rate': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Hourly Rate (£)',
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Location/County',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Phone Number',
                'type': 'tel',
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Website (Optional)',
            }),
            'instagram': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Instagram Handle (Optional)',
            }),
            'facebook': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Facebook Page (Optional)',
            }),
            'can_provide_sound_system': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-purple-600',
            }),
        }

class CaricaturistSignupForm(forms.ModelForm):
    """Form for caricaturists to register as vendors"""
    password = forms.CharField(widget=forms.PasswordInput())
    password_confirm = forms.CharField(widget=forms.PasswordInput())
    
    class Meta:
        model = Caricaturist
        fields = [
            'business_name',
            'bio',
            'profile_image',
            'experience_years',
            'style',
            'medium',
            'hourly_rate',
            'location',
            'phone',
            'website',
            'instagram',
            'facebook',
            'rush_delivery_available',
            'turnaround_days',
        ]

class PhotographerSignupForm(forms.ModelForm):
    """Form for photographers to register as vendors"""
    password = forms.CharField(widget=forms.PasswordInput())
    password_confirm = forms.CharField(widget=forms.PasswordInput())
    
    class Meta:
        model = Photographer
        fields = [
            'business_name',
            'bio',
            'profile_image',
            'experience_years',
            'specialization',
            'editing_style',
            'hourly_rate',
            'location',
            'phone',
            'website',
            'instagram',
            'facebook',
            'has_second_shooter',
            'drone_available',
            'photos_included',
        ]
