from django import forms
from .models import CustomUser


class RequestOtpForm(forms.Form):
    phone_number = forms.RegexField(
        '^09[0-9]{9}$',
        help_text='example 09125798348'
    )

    def get_or_create_user(self):
        if self.errors:
            raise ValueError('the phone number is not validated, make sure to call this method after is_valid')
        phone_number = self.cleaned_data['phone_number']
        try:
            user = CustomUser.objects.get(phone_number=phone_number)
            return False, user
        except CustomUser.DoesNotExist:
            user = CustomUser.objects.create_user(phone_number)
            return True, user


class ValidateOtpForm(forms.Form):
    otp_code = forms.RegexField(
        '^[1-9][0-9]{3}$',
        help_text='enter the code you got via sms.'
    )
