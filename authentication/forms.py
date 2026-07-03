from django import forms
from django.contrib.auth.forms import AuthenticationForm
from users.models import User


class SecureLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control premium-input',
            'placeholder': 'Enter your username'
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control premium-input',
            'placeholder': 'Enter your password'
        })
    )


class SecureRegisterForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control premium-input',
            'placeholder': 'Create Password'
        })
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control premium-input',
            'placeholder': 'Confirm Password'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'role']

        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control premium-input'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control premium-input'
            }),
            'role': forms.Select(attrs={
                'class': 'form-control premium-input'
            }),
        }

    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")

        if password != confirm:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data

    def save(self, commit=True):

        user = super().save(commit=False)

        # IMPORTANT: hash the password
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

        return user