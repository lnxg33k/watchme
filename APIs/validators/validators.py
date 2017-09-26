from django.core.exceptions import ValidationError
import os


def validate_share_path(value):
    if not os.path.exists(value):
        raise ValidationError(
            '%(value)s is not a valid path.',
            params={'value': value},
        )


def is_empty_share_path(value):
    if not os.listdir(value):
        return True
