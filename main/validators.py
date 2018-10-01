from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


def validate_password(password):
    rules = [
        # lambda s: any(x.isupper() for x in s),  # must have at least one uppercase
        # lambda s: any(x.islower() for x in s),  # must have at least one lowercase
        # lambda s: any(x.isdigit() for x in s),  # must have at least one digit
        lambda s: len(s) >= 8  # must be at least 5 characters
    ]
    # if not all(rule(password) for rule in rules):
    #     raise ValidationError(
    #         _('Password must contain at least 8 characters'),
    #     )


class ValidatePassword:
    """
    Validate whether the password is alphanumeric.
    """
    def __init__(self):
        self.rules = [
            # lambda s: any(x.isupper() for x in s),  # must have at least one uppercase
            # lambda s: any(x.islower() for x in s),  # must have at least one lowercase
            # lambda s: any(x.isdigit() for x in s),  # must have at least one digit
            lambda s: len(s) >= 5  # must be at least 5 characters
        ]

    def validate(self, password, user=None):
        if not all(rule(password) for rule in self.rules):
            raise ValidationError(
                _('Password must contain at least 8 characters'),
            )

    def get_help_text(self):
        return ''
        # return _('Password must contain at least 8 characters')
