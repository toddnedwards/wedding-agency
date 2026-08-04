from django import forms
from apps.vendors.models import Musician, Caricaturist, Photographer
from apps.accounts.models import CustomUser


ACT_TYPE_CHOICES = [
    ('wedding_band', 'Wedding Bands'),
    ('acoustic_solo_duo', 'Acoustic Solo/Duo'),
    ('wedding_dj', 'Wedding DJs'),
    ('saxophone_player', 'Saxophone Players'),
    ('pianist', 'Pianist'),
]

CARICATURIST_SERVICE_CHOICES = [
    ('live_event_caricatures', 'Live Event Caricatures'),
    ('digital_caricatures', 'Digital Caricatures'),
    ('traditional_paper_caricatures', 'Traditional Paper Caricatures'),
    ('guest_favors', 'Guest Favors / Take-Home Artwork'),
    ('custom_commissions', 'Custom Commissions'),
]

PHOTOGRAPHER_SERVICE_CHOICES = [
    ('ceremony_coverage', 'Ceremony Coverage'),
    ('full_day_coverage', 'Full Day Coverage'),
    ('engagement_shoots', 'Engagement Shoots'),
    ('drone_photography', 'Drone Photography'),
    ('second_shooter_package', 'Second Shooter Package'),
]

GENRE_CHOICES = [
    ('pop', 'Pop'),
    ('rock', 'Rock'),
    ('jazz', 'Jazz'),
    ('soul', 'Soul'),
    ('rnb', 'R&B'),
    ('funk', 'Funk'),
    ('classical', 'Classical'),
    ('blues', 'Blues'),
    ('folk', 'Folk'),
    ('indie', 'Indie'),
    ('electronic', 'Electronic'),
    ('afrobeats', 'Afrobeats'),
    ('reggae', 'Reggae'),
    ('latin', 'Latin'),
]


class BaseVendorSignupForm(forms.ModelForm):
    """Shared fields for all vendor signup forms"""
    LOCKED_PROFILE_FIELDS = {
        'first_name',
        'last_name',
        'email',
        'password',
        'password_confirm',
        'act_name',
        'stage_name',
        'act_types',
        'number_of_members',
        'home_county',
        'home_country',
    }

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20)
    password = forms.CharField(widget=forms.PasswordInput())
    password_confirm = forms.CharField(widget=forms.PasswordInput())
    act_types = forms.ChoiceField(
        choices=ACT_TYPE_CHOICES,
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        self.is_profile_edit = kwargs.pop('is_profile_edit', False)
        super().__init__(*args, **kwargs)

        # `phone` is a non-model form field, so set it explicitly from the instance.
        if 'phone' in self.fields and not self.is_bound and getattr(self, 'instance', None) is not None:
            self.fields['phone'].initial = getattr(self.instance, 'phone', '')

        optional_fields = {
            'website',
            'instagram',
            'facebook',
            'sound_system_details',
            'lighting_system_details',
            'sample_setlist',
        }

        for field_name, field in self.fields.items():
            if field_name in optional_fields or isinstance(field, forms.BooleanField):
                field.required = False
            else:
                field.required = True

        self.fields['first_name'].label = 'First Name'
        self.fields['last_name'].label = 'Last Name'
        self.fields['email'].label = 'Email Address'
        self.fields['phone'].label = 'Phone Number'
        self.fields['act_name'].label = 'Name of Act'
        self.fields['stage_name'].label = 'Stage / Professional Name (this is the name that will appear on our website)'
        self.fields['act_types'].label = 'Act Type'
        self.fields['number_of_members'].label = 'Number of Members'
        self.fields['home_county'].label = 'Act Home County'
        self.fields['home_country'].label = 'Act Home Country'
        self.fields['start_price'].label = 'Start Price'
        if not self.is_bound:
            self.fields['start_price'].initial = 0

        if self.is_profile_edit:
            for field_name in self.LOCKED_PROFILE_FIELDS:
                if field_name in self.fields:
                    self.fields.pop(field_name)

            if 'profile_image' in self.fields:
                self.fields['profile_image'].required = False

        if 'bio' in self.fields:
            self.fields['bio'].max_length = 250
            self.fields['bio'].widget.attrs.update({'maxlength': 250, 'rows': 7})

        text_fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'password',
            'password_confirm',
            'act_name',
            'stage_name',
            'number_of_members',
            'home_county',
            'home_country',
            'start_price',
        ]
        for field_name in text_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                })

        if 'first_name' in self.fields:
            self.fields['first_name'].widget.attrs.update({'placeholder': 'First Name'})
        if 'last_name' in self.fields:
            self.fields['last_name'].widget.attrs.update({'placeholder': 'Last Name'})
        if 'email' in self.fields:
            self.fields['email'].widget.attrs.update({'placeholder': 'Email Address'})
        if 'phone' in self.fields:
            self.fields['phone'].widget.attrs.update({'placeholder': 'Phone Number', 'type': 'tel'})
        if 'act_name' in self.fields:
            self.fields['act_name'].widget.attrs.update({'placeholder': 'Name of Act'})
        if 'stage_name' in self.fields:
            self.fields['stage_name'].widget.attrs.update({'placeholder': 'Stage / Professional Name'})
        if 'number_of_members' in self.fields:
            self.fields['number_of_members'].widget.attrs.update({'placeholder': 'Number of Members', 'min': 1})
        if 'home_county' in self.fields:
            self.fields['home_county'].widget.attrs.update({'placeholder': 'Act Home County'})
        if 'home_country' in self.fields:
            self.fields['home_country'].widget.attrs.update({'placeholder': 'Act Home Country'})
        if 'start_price' in self.fields:
            self.fields['start_price'].widget.attrs.update({'placeholder': '0', 'min': 0})

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if not self.is_profile_edit and password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Passwords do not match.')

        return cleaned_data

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            return email

        if not self.is_profile_edit and CustomUser.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists. Please log in instead.')

        return email

    def save(self, commit=True):
        vendor = super().save(commit=False)
        if 'act_types' in self.cleaned_data:
            selected_act_type = self.cleaned_data.get('act_types', '')
            if isinstance(selected_act_type, list):
                vendor.act_types = ', '.join(selected_act_type)
            else:
                vendor.act_types = selected_act_type or ''
        if 'act_name' in self.cleaned_data and self.cleaned_data.get('act_name'):
            vendor.business_name = self.cleaned_data.get('act_name')
        if 'stage_name' in self.cleaned_data and self.cleaned_data.get('stage_name'):
            vendor.business_name = self.cleaned_data.get('stage_name')
        if 'home_county' in self.cleaned_data and 'home_country' in self.cleaned_data:
            vendor.location = f"{self.cleaned_data.get('home_county')}, {self.cleaned_data.get('home_country')}"
        if 'start_price' in self.cleaned_data and self.cleaned_data.get('start_price') is not None:
            vendor.hourly_rate = self.cleaned_data.get('start_price')
        phone = self.cleaned_data.get('phone')
        if phone:
            vendor.phone = phone

        if commit:
            vendor.save()

        return vendor


class MusicianSignupForm(BaseVendorSignupForm):
    """Form for musicians to register as vendors"""

    genres = forms.MultipleChoiceField(
        choices=GENRE_CHOICES,
        widget=forms.SelectMultiple(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
            'size': 8,
        }),
        help_text='Choose up to 5 genres (Ctrl/Cmd + click to select multiple).',
    )

    class Meta:
        model = Musician
        fields = [
            'act_name',
            'stage_name',
            'act_types',
            'number_of_members',
            'home_county',
            'home_country',
            'start_price',
            'profile_image',
            'bio',
            'experience_years',
            'instruments',
            'genres',
            'sample_setlist',
            'website',
            'instagram',
            'facebook',
            'can_provide_sound_system',
            'sound_system_details',
            'can_provide_lighting_system',
            'lighting_system_details',
        ]
        widgets = {
            'act_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Name of Act',
            }),
            'stage_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Stage Name / Act Name',
            }),
            'number_of_members': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Number of Members',
                'min': 1,
            }),
            'home_county': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Act Home County',
            }),
            'home_country': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Act Home Country',
            }),
            'start_price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': '0',
                'min': 0,
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Tell us about yourself and your music',
                'rows': 7,
                'maxlength': 250,
            }),
            'experience_years': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Years of Experience',
            }),
            'instruments': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'e.g., Piano, Violin, Guitar',
            }),
            'sample_setlist': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'e.g., Mr. Brightside\nValerie\nCan\'t Help Falling in Love',
                'rows': 6,
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
            'sound_system_details': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'If yes, please tell us about your setup',
                'rows': 3,
            }),
            'can_provide_lighting_system': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-purple-600',
            }),
            'lighting_system_details': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': 'If yes, please tell us about your lighting setup',
                'rows': 3,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_profile_edit and 'genres' in self.fields:
            self.fields.pop('genres')

        if 'genres' in self.fields:
            self.fields['genres'].label = 'Genres'
        if 'can_provide_sound_system' in self.fields:
            self.fields['can_provide_sound_system'].label = 'Can provide sound system?'
        if 'sample_setlist' in self.fields:
            self.fields['sample_setlist'].label = 'Sample Setlist'
            self.fields['sample_setlist'].required = False
        if 'sound_system_details' in self.fields:
            self.fields['sound_system_details'].label = 'If yes, please tell us about your setup'
            self.fields['sound_system_details'].required = False
        if 'can_provide_lighting_system' in self.fields:
            self.fields['can_provide_lighting_system'].label = 'Can provide lighting system?'
        if 'lighting_system_details' in self.fields:
            self.fields['lighting_system_details'].label = 'If yes, please tell us about your lighting setup'
            self.fields['lighting_system_details'].required = False

    def clean_genres(self):
        genres = self.cleaned_data.get('genres', [])
        if len(genres) > 5:
            raise forms.ValidationError('Please select up to 5 genres.')
        return genres

    def save(self, commit=True):
        vendor = super().save(commit=False)
        selected_genres = self.cleaned_data.get('genres', [])
        vendor.genres = ', '.join(selected_genres)

        if commit:
            vendor.save()

        return vendor


class CaricaturistSignupForm(BaseVendorSignupForm):
    """Form for caricaturists to register as vendors"""

    act_types = forms.ChoiceField(
        choices=CARICATURIST_SERVICE_CHOICES,
        widget=forms.RadioSelect,
        help_text='Select your primary caricature service.',
    )

    class Meta:
        model = Caricaturist
        fields = [
            'act_name',
            'stage_name',
            'act_types',
            'number_of_members',
            'home_county',
            'home_country',
            'start_price',
            'profile_image',
            'bio',
            'experience_years',
            'style',
            'medium',
            'website',
            'instagram',
            'facebook',
            'rush_delivery_available',
            'turnaround_days',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'act_name' in self.fields:
            self.fields['act_name'].label = 'Your Name (private)'
            self.fields['act_name'].widget.attrs.update({'placeholder': 'Your Name'})
        if 'stage_name' in self.fields:
            self.fields['stage_name'].label = 'Professional / Brand Name (this is the name that will appear on our website)'
            self.fields['stage_name'].widget.attrs.update({'placeholder': 'Professional / Brand Name'})
        if 'act_types' in self.fields:
            self.fields['act_types'].label = 'Caricature Services'
        if 'number_of_members' in self.fields:
            self.fields['number_of_members'].label = 'Number of Artists in Your Team'
        if 'style' in self.fields:
            self.fields['style'].label = 'Drawing Style'
        if 'medium' in self.fields:
            self.fields['medium'].label = 'Mediums You Use'
        if 'rush_delivery_available' in self.fields:
            self.fields['rush_delivery_available'].label = 'Do you offer rush booking or delivery?'
        if 'turnaround_days' in self.fields:
            self.fields['turnaround_days'].label = 'Typical Turnaround Time (Days)'


class PhotographerSignupForm(BaseVendorSignupForm):
    """Form for photographers to register as vendors"""

    act_types = forms.MultipleChoiceField(
        choices=PHOTOGRAPHER_SERVICE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        help_text='Select all photography services you offer.',
    )

    class Meta:
        model = Photographer
        fields = [
            'act_name',
            'stage_name',
            'act_types',
            'number_of_members',
            'home_county',
            'home_country',
            'start_price',
            'profile_image',
            'bio',
            'experience_years',
            'specialization',
            'editing_style',
            'website',
            'instagram',
            'facebook',
            'has_second_shooter',
            'drone_available',
            'photos_included',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'act_name' in self.fields:
            self.fields['act_name'].label = 'Your Name (private)'
            self.fields['act_name'].widget.attrs.update({'placeholder': 'Your Name'})
        if 'stage_name' in self.fields:
            self.fields['stage_name'].label = 'Professional / Brand Name (this is the name that will appear on our website)'
            self.fields['stage_name'].widget.attrs.update({'placeholder': 'Professional / Brand Name'})
        if 'act_types' in self.fields:
            self.fields['act_types'].label = 'Photography Services'
        if 'number_of_members' in self.fields:
            self.fields['number_of_members'].label = 'Team Size'
        if 'specialization' in self.fields:
            self.fields['specialization'].label = 'Primary Photography Specialization'
        if 'editing_style' in self.fields:
            self.fields['editing_style'].label = 'Editing Style'
        if 'has_second_shooter' in self.fields:
            self.fields['has_second_shooter'].label = 'Do you offer a second shooter?'
        if 'drone_available' in self.fields:
            self.fields['drone_available'].label = 'Do you offer drone coverage?'
        if 'photos_included' in self.fields:
            self.fields['photos_included'].label = 'Number of Photos Included (Starting Package)'
