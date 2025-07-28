# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import User, Student, Programme, School

# forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import User

class UserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
        required=False,
        help_text="Leave blank to keep current password on update."
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
        required=False,
        help_text="Re-enter password to confirm."
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 
            'phone', 'address', 'gender', 'date_of_birth', 
            'profile_picture', 'national_id'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.is_update = kwargs.pop('is_update', False)
        self.user_type = kwargs.pop('user_type', 'instructor')  # Default to instructor
        super().__init__(*args, **kwargs)

        # Password fields required only on create
        if not self.is_update:
            self.fields['password'].required = True
            self.fields['confirm_password'].required = True

        # Add gender placeholder
        self.fields['gender'].choices = [('', 'Select Gender')] + list(User.GENDER_CHOICES)

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
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = timezone.now().date()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 16:
                raise ValidationError("User must be at least 16 years old.")
            if age > 80:
                raise ValidationError("Please check the date of birth.")
        return dob

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password or confirm_password:
            if password != confirm_password:
                raise ValidationError("Passwords do not match.")

            if not self.is_update and len(password) < 8:
                raise ValidationError("Password must be at least 8 characters.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')

        if password:
            user.set_password(password)

        # Automatically set user type only on creation
        if not user.pk or not user.user_type:
            user.user_type = self.user_type

        if commit:
            user.save()
        return user



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
    


from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Instructor, School

User = get_user_model()

# class UserForm(forms.ModelForm):
#     """Form for User model fields"""
#     password = forms.CharField(
#         widget=forms.PasswordInput(attrs={'class': 'form-control'}),
#         required=False,
#         help_text="Leave blank to keep current password (for updates)"
#     )
#     confirm_password = forms.CharField(
#         widget=forms.PasswordInput(attrs={'class': 'form-control'}),
#         required=False,
#         help_text="Confirm password"
#     )
    
#     class Meta:
#         model = User
#         fields = [
#             'username', 'first_name', 'last_name', 'email', 'phone',
#             'address', 'gender', 'date_of_birth', 'profile_picture', 'national_id'
#         ]
#         widgets = {
#             'username': forms.TextInput(attrs={'class': 'form-control'}),
#             'first_name': forms.TextInput(attrs={'class': 'form-control'}),
#             'last_name': forms.TextInput(attrs={'class': 'form-control'}),
#             'email': forms.EmailInput(attrs={'class': 'form-control'}),
#             'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+254...'}),
#             'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#             'gender': forms.Select(attrs={'class': 'form-select'}),
#             'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
#             'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
#             'national_id': forms.TextInput(attrs={'class': 'form-control'}),
#         }
    
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Make password required only for new users
#         if not self.instance.pk:
#             self.fields['password'].required = True
#             self.fields['confirm_password'].required = True
        
#         # Add required asterisk to required fields
#         for field_name, field in self.fields.items():
#             if field.required:
#                 field.widget.attrs['required'] = True
#                 if 'class' in field.widget.attrs:
#                     field.widget.attrs['class'] += ' required'
    
#     def clean(self):
#         cleaned_data = super().clean()
#         password = cleaned_data.get('password')
#         confirm_password = cleaned_data.get('confirm_password')
        
#         # Password validation for new users or when password is being changed
#         if password or confirm_password:
#             if password != confirm_password:
#                 raise ValidationError("Passwords don't match.")
            
#             if len(password) < 8:
#                 raise ValidationError("Password must be at least 8 characters long.")
        
#         return cleaned_data
    
#     def save(self, commit=True):
#         user = super().save(commit=False)
#         password = self.cleaned_data.get('password')
        
#         if password:
#             user.set_password(password)
        
#         # Set user type for instructors
#         if not user.user_type:
#             user.user_type = 'instructor'
        
#         if commit:
#             user.save()
#         return user


class InstructorForm(forms.ModelForm):
    """Form for Instructor model fields"""
    
    class Meta:
        model = Instructor
        fields = [
            'employee_number', 'school', 'designation', 'employment_type',
            'qualifications', 'specialization', 'professional_registration',
            'experience_years', 'clinical_experience_years', 'salary',
            'joining_date', 'contract_end_date', 'is_active'
        ]
        widgets = {
            'employee_number': forms.TextInput(attrs={'class': 'form-control'}),
            'school': forms.Select(attrs={'class': 'form-select'}),
            'designation': forms.Select(attrs={'class': 'form-select'}),
            'employment_type': forms.Select(attrs={'class': 'form-select'}),
            'qualifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'professional_registration': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'clinical_experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contract_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter active schools only
        self.fields['school'].queryset = School.objects.filter(is_active=True).order_by('name')
        
        # Set initial values
        if not self.instance.pk:
            self.fields['is_active'].initial = True
            self.fields['experience_years'].initial = 0
            self.fields['clinical_experience_years'].initial = 0
        
        # Add help text
        self.fields['employee_number'].help_text = "Unique employee identification number"
        self.fields['qualifications'].help_text = "Educational qualifications and certifications"
        self.fields['professional_registration'].help_text = "Professional body registration number (if applicable)"
        self.fields['contract_end_date'].help_text = "Required for contract and part-time employees"
        
        # Conditional required fields based on employment type
        if self.instance.pk and self.instance.employment_type in ['contract', 'part_time']:
            self.fields['contract_end_date'].required = True
    
    def clean_employee_number(self):
        employee_number = self.cleaned_data['employee_number']
        
        # Check for uniqueness (excluding current instance)
        existing = Instructor.objects.filter(employee_number=employee_number)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise ValidationError("An instructor with this employee number already exists.")
        
        return employee_number
    
    def clean(self):
        cleaned_data = super().clean()
        employment_type = cleaned_data.get('employment_type')
        contract_end_date = cleaned_data.get('contract_end_date')
        joining_date = cleaned_data.get('joining_date')
        
        # Validate contract end date for contract employees
        if employment_type in ['contract', 'part_time'] and not contract_end_date:
            raise ValidationError("Contract end date is required for contract and part-time employees.")
        
        # Validate date logic
        if joining_date and contract_end_date and joining_date >= contract_end_date:
            raise ValidationError("Contract end date must be after joining date.")
        
        return cleaned_data


class InstructorSearchForm(forms.Form):
    """Form for instructor search and filtering"""
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, employee number, email...'
        })
    )
    
    school = forms.ModelChoiceField(
        queryset=School.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label="All Schools",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    designation = forms.ChoiceField(
        choices=[('', 'All Designations')] + list(Instructor.DESIGNATION_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    employment_type = forms.ChoiceField(
        choices=[('', 'All Employment Types')] + list(Instructor.EMPLOYMENT_TYPES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status = forms.ChoiceField(
        choices=[
            ('', 'All Status'),
            ('active', 'Active'),
            ('inactive', 'Inactive'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class BulkActionForm(forms.Form):
    """Form for bulk actions on instructors"""
    ACTION_CHOICES = [
        ('', 'Select Action'),
        ('activate', 'Activate Selected'),
        ('deactivate', 'Deactivate Selected'),
        ('delete', 'Delete Selected'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    instructor_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    def clean_instructor_ids(self):
        ids = self.cleaned_data['instructor_ids']
        if not ids:
            raise ValidationError("No instructors selected.")
        return ids.split(',')


class InstructorImportForm(forms.Form):
    """Form for importing instructors from CSV/Excel"""
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        }),
        help_text="Upload CSV or Excel file with instructor data"
    )
    
    update_existing = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Update existing instructors with matching employee numbers"
    )
    
    def clean_file(self):
        file = self.cleaned_data['file']
        
        # Validate file size (max 5MB)
        if file.size > 5 * 1024 * 1024:
            raise ValidationError("File size cannot exceed 5MB.")
        
        # Validate file extension
        allowed_extensions = ['.csv', '.xlsx', '.xls']
        if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
            raise ValidationError("Only CSV and Excel files are allowed.")
        
        return file
    
from django import forms
from .models import School

class SchoolForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add form-control class to all fields except checkbox
        for field_name, field in self.fields.items():
            if field_name != 'is_active':
                field.widget.attrs['class'] = 'form-control'
            if field_name == 'dean':
                field.widget.attrs['class'] = 'form-select'
            if field_name == 'established_date':
                field.widget.attrs['placeholder'] = 'Select date'
            if field_name in ['name', 'code']:
                field.widget.attrs['placeholder'] = f'Enter {field.label.lower()}'

    class Meta:
        model = School
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter school name'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter school code'
            }),
            'dean': forms.Select(attrs={
                'class': 'form-select'
            }),
            'established_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Enter school description...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'School Name',
            'code': 'School Code',
            'dean': 'School Dean',
            'established_date': 'Established Date',
            'description': 'Description',
            'is_active': 'Is Active',
        }
        help_texts = {
            'code': 'Unique code for the school (e.g., SON for School of Nursing)',
            'established_date': 'Date when the school was established',
        }