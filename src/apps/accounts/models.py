from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_MEMBER = "member"
    ROLE_STAFF = "staff"
    ROLE_BOARD = "board"
    ROLE_CHOICES = [
        (ROLE_MEMBER, "Mitglied"),
        (ROLE_STAFF, "Mitarbeiter"),
        (ROLE_BOARD, "Vorstand"),
    ]

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    social_club = models.ForeignKey("core.SocialClub", null=True, blank=True, on_delete=models.SET_NULL, related_name="users")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    class Meta:
        ordering = ["email"]

    def __str__(self):
        return self.email

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
