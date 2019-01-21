import os
import platform

from APIs.core.libs.helpers import is_valid_mountpoint
from django.core.exceptions import ValidationError


def validate_share_path(value):
    if not os.path.exists(value):
        raise ValidationError(
            '%(value)s is not a valid path.',
            params={'value': value},
        )
    if platform.system() == 'Linux' and not is_valid_mountpoint(value):
        raise ValidationError(
            '%(value)s is not a valid mountpoint.',
            params={'value': value},
        )


def is_empty_share_path(value):
    if not os.listdir(value):
        return True
