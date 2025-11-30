import re
from django import forms

from .models import Domain

FQDN_REGEX = re.compile(
    r'^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$'
)


class AddSiteForm(forms.Form):
    domain = forms.CharField(
        label="Domain",
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": "example.com"})
    )

    def clean_domain(self):
        value = self.cleaned_data['domain'].strip().lower()

        if value.startswith('http://'):
            value = value[7:]
        elif value.startswith('https://'):
            value = value[8:]

   
        if '/' in value:
            value = value.split('/')[0]

        # Verification for FQDN
        if not FQDN_REGEX.match(value):
            raise forms.ValidationError(
                "Please enter a valid domain, for example: example.com"
            )

        return value