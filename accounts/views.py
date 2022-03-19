from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import FormView
from django.contrib import messages
from django.views import View
from .forms import RequestOtpForm, ValidateOtpForm
from .exceptions import ActiveOtpExists, OtpAccessDenied
from .models import CustomUser
from django.contrib.auth import login


class RequestLoginView(FormView):
    template_name = 'accounts/login_signup.html'
    form_class = RequestOtpForm

    def form_valid(self, form):
        request = self.request
        created, user = form.get_or_create_user()
        if not created:
            try:
                user.otpverification.get_code()
            except ActiveOtpExists as e:
                messages.add_message(request, messages.ERROR, str(e))
                return redirect('login_signup')
            except OtpAccessDenied as e:
                messages.add_message(request, messages.ERROR, str(e))
                return redirect('home')
        request.session['phone_number'] = form.cleaned_data['phone_number']
        return redirect('verify_otp')


class VerifyOtpView(View):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        if 'phone_number' not in self.request.session:
            return redirect('login_signup')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, 'accounts/verify_otp.html', {'form': ValidateOtpForm()})

    def post(self, request):
        phone_number = request.session['phone_number']
        user = get_object_or_404(CustomUser, phone_number=phone_number)
        form = ValidateOtpForm(request.POST)
        if form.is_valid():
            try:
                is_valid = user.otpverification.verify_code(int(form.cleaned_data['otp_code']))
                if is_valid:
                    login(request, user)
                    return redirect('home')
                else:
                    messages.add_message(request, messages.ERROR, 'the code is not valid or expired.')
                    return redirect('verify_otp')
            except OtpAccessDenied as e:
                messages.add_message(request, messages.ERROR, str(e))
                return redirect('home')
        return render(request, 'accounts/verify_otp.html', {'from': form})
