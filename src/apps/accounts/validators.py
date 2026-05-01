from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from django.contrib.auth.password_validation import (
    CommonPasswordValidator,
    MinimumLengthValidator,
    NumericPasswordValidator,
    UserAttributeSimilarityValidator,
)


class GermanUserAttributeSimilarityValidator(UserAttributeSimilarityValidator):
    def validate(self, password, user=None):
        try:
            super().validate(password, user=user)
        except ValidationError as exc:
            verbose_name = (exc.params or {}).get("verbose_name") or _("persoenlichen Angaben")
            raise ValidationError(
                _("Das Passwort ist den %(verbose_name)s zu aehnlich."),
                code="password_too_similar",
                params={"verbose_name": verbose_name},
            ) from exc

    def get_help_text(self):
        return _("Das Passwort darf deinen persoenlichen Angaben nicht zu aehnlich sein.")


class GermanMinimumLengthValidator(MinimumLengthValidator):
    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _("Das Passwort muss mindestens %(min_length)d Zeichen enthalten."),
                code="password_too_short",
                params={"min_length": self.min_length},
            )

    def get_help_text(self):
        return _("Das Passwort muss mindestens %(min_length)d Zeichen enthalten.") % {
            "min_length": self.min_length
        }


class GermanCommonPasswordValidator(CommonPasswordValidator):
    def validate(self, password, user=None):
        if password.lower().strip() in self.passwords:
            raise ValidationError(
                _("Dieses Passwort ist zu haeufig und dadurch unsicher."),
                code="password_too_common",
            )

    def get_help_text(self):
        return _("Das Passwort darf nicht zu haeufig vorkommen.")


class GermanNumericPasswordValidator(NumericPasswordValidator):
    def validate(self, password, user=None):
        if password.isdigit():
            raise ValidationError(
                _("Das Passwort darf nicht nur aus Zahlen bestehen."),
                code="password_entirely_numeric",
            )

    def get_help_text(self):
        return _("Das Passwort darf nicht nur aus Zahlen bestehen.")
