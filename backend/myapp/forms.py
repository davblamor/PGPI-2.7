from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()

class RegistrationForm(forms.ModelForm):
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={'placeholder': 'Ingrese su correo electrónico'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Ingrese una contraseña'}), 
        label="Contraseña"
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirme la contraseña'}), 
        label="Confirmar contraseña"
    )

    class Meta:
        model = User
        fields = ('email',)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        try:
            # Valida la contraseña con los validadores predeterminados de Django
            validate_password(password)
        except ValidationError as e:
            raise forms.ValidationError(("La contraseña debe tener al menos 8 caracteres y cumplir con los requisitos de seguridad."))
        return password

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        if password != password_confirm:
            raise forms.ValidationError("Las contraseñas no coinciden")
        return password_confirm

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user
    
class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={'placeholder': 'Ingrese su correo electrónico'})
        )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Ingrese su contraseña'}), 
        label="Contraseña"
    )
    class Meta:
        model = User
        fields = ('username', 'password')
