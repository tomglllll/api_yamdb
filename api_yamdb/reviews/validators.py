import re

from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_username(value):
    if value == 'me':
        raise ValidationError(
            ('Имя пользователя не может быть <me>.'),
            params={'value': value},
        )
    if re.search(r'^[a-zA-Z][a-zA-Z0-9-_\.]{1,20}$', value) is None:
        raise ValidationError(
            (f'Недопустимые символы <{value}> в никнейме.'),
            params={'value': value},
        )


def validate_year(value):
    current_year = timezone.now().year
    if value > current_year:
        raise ValidationError(
            f'Год выпуска не может превышать текущий год: {current_year}.'
        )


def validate_score(value):
    if value < 1 or value > 10:
        raise ValidationError(
            'Оценка должна быть в диапазоне от 1 до 10.'
        )
