from random import randint
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import make_password
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from .exceptions import OtpAccessDenied, ActiveOtpExists
from .sms_service import send_sms


def generate_code():
    return randint(1000, 9999)


class CustomUserManager(BaseUserManager):
    def _create_user(self, phone_number, password, **extra_fields):
        if not phone_number:
            raise ValueError("The given phone number must be set")
        user = self.model(phone_number=phone_number, **extra_fields)
        user.password = make_password(password)
        user.save()
        return user

    def create_user(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(phone_number, password, **extra_fields)

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(phone_number, password, **extra_fields)


class CustomUser(AbstractUser):
    username = None
    phone_number = models.CharField(
        max_length=11,
        unique=True,
        db_index=True,
        help_text='example 09125798348',
        validators=[
            RegexValidator('^09[0-9]{9}$', 'please enter a valid phone number.')
        ]
    )
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()


class OtpVerification(models.Model):
    IS_VALID_DURATION = 120
    FAILURE_TOLERANCE = 3

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, db_index=True)
    code = models.PositiveIntegerField(
        default=generate_code,
        validators=[
            MinValueValidator(1000),
            MaxValueValidator(9999)
        ]
    )
    failures = models.PositiveSmallIntegerField(default=0)
    datetime_code_modified = models.DateTimeField(auto_now_add=True)
    is_blocked = models.BooleanField(default=False)

    def _renew_code(self):
        self.code = randint(1000, 9999)
        self.datetime_code_modified = timezone.now()
        self.save()

    def _is_expired(self):
        return self.datetime_code_modified + timedelta(seconds=self.IS_VALID_DURATION) < timezone.now()

    def _remaining_time(self):
        if not self._is_expired():
            return ((self.datetime_code_modified + timedelta(seconds=self.IS_VALID_DURATION)) - timezone.now()).seconds
        return 0

    def _increase_failure_count(self):
        if not self.is_blocked:
            if self.failures == self.FAILURE_TOLERANCE - 1:
                self.is_blocked = True
            self.failures += 1
            self.save()

    def _clear_failures(self):
        if self.failures > 0:
            self.failures = 0
            self.save()

    def get_code(self):
        if not self.is_blocked:
            if self._is_expired():
                self._renew_code()
                send_sms(self.user.phone_number, self.code)
                return
            raise ActiveOtpExists(f'You have to wait for more {self._remaining_time()} seconds to request code again.')
        raise OtpAccessDenied(
            'Your access to request code has been blocked due to exceeding amount of verification '
            'failures, please contact an administrator.'
        )

    def verify_code(self, code):
        if not self.is_blocked:
            if self.code == code:
                if not self._is_expired():
                    self._clear_failures()
                    return True
                return False
            self._increase_failure_count()
            return False
        raise OtpAccessDenied(
            'Your access to request code has been blocked due to exceeding amount of verification '
            'failures, please contact an administrator.'
        )
