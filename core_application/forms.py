# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import User, Student, Programme, School


class UserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        }),
        required=False
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        }),
        required=False
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 
            'phone', 'address', 'gender', 'date_of_birth', 
            'profile_picture', 'national_id'
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter username',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address',
                'required': True
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name',
                'required': True
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter address'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'national_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter national ID'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.is_update = kwargs.pop('is_update', False)
        super().__init__(*args, **kwargs)
        
        # Make required fields
        required_fields = ['username', 'email', 'first_name', 'last_name']
        for field_name in required_fields:
            self.fields[field_name].required = True
        
        # Make password fields required only for creation
        if not self.is_update:
            self.fields['password'].required = True
            self.fields['confirm_password'].required = True
        
        # Add empty choice for gender
        self.fields['gender'].choices = [('', 'Select Gender')] + list(User.GENDER_CHOICES)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if not self.is_update:
            if password and confirm_password and password != confirm_password:
                raise ValidationError("Passwords don't match")
        elif password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords don't match")

        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            qs = User.objects.filter(email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("A user with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            qs = User.objects.filter(username=username)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("A user with this username already exists.")
        return username

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data.get('date_of_birth')
        if date_of_birth:
            today = timezone.now().date()
            age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
            if age < 16:
                raise ValidationError("Student must be at least 16 years old.")
            if age > 80:
                raise ValidationError("Please check the date of birth.")
        return date_of_birth


class StudentForm(forms.ModelForm):
    # Remove the duplicate course field - we'll use programme directly
    
    class Meta:
        model = Student
        fields = [
            'registration_number', 'programme', 'current_year', 'current_semester',
            'admission_date', 'admission_type', 'sponsor_type', 'status',
            'guardian_name', 'guardian_phone', 'guardian_relationship', 'guardian_address',
            'emergency_contact', 'blood_group', 'medical_conditions',
            'expected_graduation_date', 'gpa'
        ]
        widgets = {
            'registration_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter student registration number',
                'required': True
            }),
            'programme': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'current_year': forms.NumberInput(attrs={
                'class': 'form-select',
                'required': True
            }),
            'current_semester': forms.NumberInput(attrs={
                'class': 'form-select',
                'required': True
            }),
            'admission_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'admission_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'sponsor_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'guardian_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter guardian full name',
                'required': True
            }),
            'guardian_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter guardian phone number',
                'required': True
            }),
            'guardian_relationship': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter relationship (e.g., Father, Mother, Guardian)',
                'required': True
            }),
            'guardian_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter guardian address'
            }),
            'emergency_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter emergency contact number',
                'required': True
            }),
            'blood_group': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter blood group (e.g., A+, B-, O+)'
            }),
            'medical_conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter any medical conditions or allergies (optional)'
            }),
            'expected_graduation_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'gpa': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '4',
                'placeholder': 'Enter GPA (0.00 - 4.00)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set up programme choices
        self.fields['programme'].queryset = Programme.objects.filter(is_active=True).order_by('name')
        self.fields['programme'].empty_label = "Select Programme"
        
        # Set up year choices - dynamic based on selected programme
        # Default to max 4 years, but will be updated via JavaScript based on programme selection
        year_choices = [('', 'Select Year')]
        for i in range(1, 5):  # 1 to 4 years
            year_choices.append((i, f'Year {i}'))
        self.fields['current_year'].choices = year_choices
        
        # Set up semester choices - dynamic based on programme's semesters_per_year
        semester_choices = [('', 'Select Semester')]
        for i in range(1, 4):  # 1 to 3 semesters (covers most cases)
            semester_choices.append((i, f'Semester {i}'))
        self.fields['current_semester'].choices = semester_choices
        
        # Set up other choice fields
        self.fields['admission_type'].choices = [('', 'Select Admission Type')] + list(Student.ADMISSION_TYPES)
        self.fields['sponsor_type'].choices = [('', 'Select Sponsor Type')] + list(Student.SPONSOR_TYPES)
        self.fields['status'].choices = [('', 'Select Status')] + list(Student.STATUS_CHOICES)
        
        # Make required fields
        required_fields = ['registration_number', 'programme', 'current_year', 'current_semester', 
                          'admission_date', 'guardian_name', 'guardian_phone', 'guardian_relationship', 
                          'emergency_contact']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True

        # If editing existing student, limit year/semester choices to programme's constraints
        if self.instance.pk and self.instance.programme:
            programme = self.instance.programme
            
            # Update year choices based on programme duration
            year_choices = [('', 'Select Year')]
            for i in range(1, programme.duration_years + 1):
                year_choices.append((i, f'Year {i}'))
            self.fields['current_year'].choices = year_choices
            
            # Update semester choices based on programme's semesters per year
            semester_choices = [('', 'Select Semester')]
            for i in range(1, programme.semesters_per_year + 1):
                semester_choices.append((i, f'Semester {i}'))
            self.fields['current_semester'].choices = semester_choices

    def clean_registration_number(self):
        registration_number = self.cleaned_data.get('registration_number')
        if registration_number:
            qs = Student.objects.filter(registration_number=registration_number)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("A student with this registration number already exists.")
        return registration_number

    def clean_gpa(self):
        gpa = self.cleaned_data.get('gpa')
        if gpa is not None and (gpa < 0 or gpa > 4):
            raise ValidationError("GPA must be between 0.00 and 4.00")
        return gpa

    def clean_admission_date(self):
        admission_date = self.cleaned_data.get('admission_date')
        if admission_date:
            today = timezone.now().date()
            
            # Check if admission date is not too old (e.g., more than 10 years ago)
            years_ago = today.year - admission_date.year
            if years_ago > 10:
                raise ValidationError("Admission date seems too old. Please verify.")
        return admission_date

    def clean_expected_graduation_date(self):
        expected_graduation_date = self.cleaned_data.get('expected_graduation_date')
        admission_date = self.cleaned_data.get('admission_date')
        programme = self.cleaned_data.get('programme')
        
        if expected_graduation_date and admission_date and programme:
            # Calculate expected graduation based on programme duration
            expected_years = programme.duration_years
            calculated_graduation = admission_date.replace(year=admission_date.year + expected_years)
            
            # Allow some flexibility (6 months before to 2 years after calculated date)
            min_date = calculated_graduation.replace(month=max(1, calculated_graduation.month - 6))
            max_date = calculated_graduation.replace(year=calculated_graduation.year + 2)
            
            if expected_graduation_date < min_date or expected_graduation_date > max_date:
                raise ValidationError(
                    f"Expected graduation date should be around {calculated_graduation.strftime('%Y-%m-%d')} "
                    f"based on the programme duration of {expected_years} years."
                )
        
        return expected_graduation_date

    def clean(self):
        cleaned_data = super().clean()
        programme = cleaned_data.get('programme')
        current_year = cleaned_data.get('current_year')
        current_semester = cleaned_data.get('current_semester')
        
        if programme and current_year and current_semester:
            # Validate year against programme duration
            if current_year > programme.duration_years:
                raise ValidationError(
                    f"Current year cannot exceed programme duration of {programme.duration_years} years."
                )
            
            # Validate semester against programme's semesters per year
            if current_semester > programme.semesters_per_year:
                raise ValidationError(
                    f"Current semester cannot exceed {programme.semesters_per_year} semesters per year "
                    f"for this programme."
                )
        
        return cleaned_data