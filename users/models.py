# users/models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
import uuid

class CustomUserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    def _create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    # Burahin ang username field
    username = None

    # Idagdag ang mga custom fields mo
    email = models.EmailField(_('email address'), unique=True)
    middle_name = models.CharField(max_length=150, blank=True)
    suffix = models.CharField(max_length=10, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    birthday = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    BARANGAY_POSITION_CHOICES = [
        ('Punong Barangay', 'Punong Barangay'),
        ('Barangay Kagawad', 'Barangay Kagawad'),
        ('SK Chairperson', 'SK Chairperson'),
        ('Barangay Secretary', 'Barangay Secretary'),
        ('Barangay Treasurer', 'Barangay Treasurer'),
        ('Chief Tanod', 'Chief Tanod'),
        ('Barangay Tanod', 'Barangay Tanod'),
        ('Lupong Tagapamayapa', 'Lupong Tagapamayapa'),
        ('Staff', 'Staff'), 
    ]
    barangay_position = models.CharField(
        max_length=50, 
        choices=BARANGAY_POSITION_CHOICES, 
        blank=True, 
        null=True,
        verbose_name="Barangay Position"
    )

    id_image = models.ImageField(upload_to='user_ids/', null=True, blank=True)
    
    is_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        unique=True,
        null=True, 
        blank=True
    )

    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name'] 

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    def is_otp_valid(self):
        if not self.otp_created_at:
            return False
        # 5 minutes validity
        return timezone.now() < self.otp_created_at + timedelta(minutes=5)