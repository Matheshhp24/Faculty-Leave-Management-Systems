from django import forms
from django.contrib.auth.models import User
from .models import StaffDetails,StaffDepartment,CancelLeave
from django.contrib.auth.forms import AuthenticationForm

class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'Your Staff ID'
        self.fields['password'].widget.attrs['placeholder'] = 'Your Password'


class FreezeDatesForm(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="Select the date to freeze."
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text="Enter the reason for freezing this date."
    )


class CancelLeaveForm(forms.ModelForm):
    class Meta:
        model = CancelLeave
        fields = ['leave_type', 'unique_id', 'reason', 'document']

class CreateUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password('srec@123')  # Default password
        if commit:
            user.save()
        return user

class StaffDetailsForm(forms.ModelForm):
    department = forms.ChoiceField(choices=[])

    class Meta:
        model = StaffDetails
        fields = ['department', 'doj']
        widgets = {
            'doj': forms.SelectDateWidget(years=range(1980, 2030))
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Fetch departments from StaffDepartment instance
        try:
            staff_department_instance = StaffDepartment.objects.first()
            departments = staff_department_instance.departments if staff_department_instance else []
            self.fields['department'].choices = [(dept, dept) for dept in departments]
        except StaffDepartment.DoesNotExist:
            self.fields['department'].choices = []

class LeaveDownloadForm(forms.Form):
    leave_type = forms.ChoiceField(choices=[
        ('All', 'All'),
        ('Casual Leave', 'Casual Leave'),
        ('LOP Leave', 'LOP Leave'),
        ('CH Leave', 'Compensated Holiday'),
        ('Earn Leave', 'Earn Leave'),
        ('Medical Leave', 'Medical Leave'),
        ('Onduty', 'Onduty'),
        ('Special Onduty', 'Special Onduty'),
        ('Vacation Leave', 'Vacation Leave'),
    ])

