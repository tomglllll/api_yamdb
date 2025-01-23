import re

from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_username(value):
    if value == 'me':
        raise ValidationError('Имя пользователя не может быть me.')

    disallowed_chars = re.sub(r'[\w.@+-]+', '', value)
    if disallowed_chars:
        raise ValidationError('Недопустимые символы: '
                              f'{", ".join(set(disallowed_chars))}')


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
