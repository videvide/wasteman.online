from django import forms
from django.contrib.auth.password_validation import validate_password
from django.utils.safestring import mark_safe

from .models import Address

"""This is for later..."""
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
    """Form used on poster page to add poster to cart. Variation choices should be added from the view."""
    variation = forms.ChoiceField(choices=[])
    quantity = forms.IntegerField(min_value=1, max_value=10)
    # ?
    adding = forms.BooleanField(initial=True, widget=forms.HiddenInput())

    def __init__(self, *args, variation_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["variation"].choices = variation_choices


class UpdateCartForm(forms.Form):
    """Form used inside cart page to update/remove each cart item."""
    variation = forms.CharField(widget=forms.HiddenInput(), help_text="Should be provided from view.")
    quantity = forms.IntegerField()
    remove = forms.BooleanField(required=False)


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            "first_name",
            "last_name",
            "line_1",
            "line_2",
            "city",
            "state",
            "zip",
            "country",
            "email"
        ]