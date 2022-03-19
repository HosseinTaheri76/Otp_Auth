from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, OtpVerification
from .sms_service import send_sms


@receiver(post_save, sender=CustomUser)
def bind_otp_verification_to_user(sender, instance, created, **kwargs):
    if created:
        otp = OtpVerification.objects.create(user_id=instance.id)
        if not instance.is_superuser:
            send_sms(instance.phone_number, otp.code)


