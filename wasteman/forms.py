from django import forms
from django.contrib.auth.password_validation import validate_password
from django.utils.safestring import mark_safe


class ProfileForm(forms.Form):
    # TODO: Add custom clean method to validate username and email is available.
    username = forms.CharField(label="Username", max_length=100, required=False)
    email = forms.EmailField(label="Email", max_length=100, required=False)



class RegisterForm(forms.Form):
    username = forms.CharField(label="Username", max_length=100)
    email = forms.EmailField(label="Email", max_length=100)
    password = forms.CharField(
        label="Password", 
        max_length=100, 
        widget=forms.PasswordInput,
        validators=[validate_password]
    )
    terms = forms.BooleanField(label=mark_safe("Agree to <a href='/terms-of-service/'>terms of service</a>?"))


class LoginForm(forms.Form):
    username = forms.CharField(label="Username", max_length=100)
    password = forms.CharField(
        label="Password",
        max_length=100,
        widget=forms.PasswordInput,
    )


class AddToCartForm(forms.Form):
    # Choices are added dynamically from the view.
    variation = forms.ChoiceField(choices=[])
    quantity = forms.IntegerField(min_value=1, max_value=10)
    adding = forms.BooleanField(initial=True, widget=forms.HiddenInput())

    def __init__(self, *args, variation_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["variation"].choices = variation_choices


class UpdateCartForm(forms.Form):
    variation = forms.CharField(widget=forms.HiddenInput())
    quantity = forms.IntegerField()
    remove = forms.BooleanField(required=False)