import re

from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_username(value):
    if value == 'me':
        raise ValidationError('Имя пользователя не может быть me.')

    if not re.match(r'^[\w.@+-]+$', value):
        raise ValidationError(
            (f'Недопустимые символы <{value}> в никнейме.'),
            params={'value': value},
        )

    if len(value) > 150:
        raise ValidationError('Username не должен быть длинее 150 симвлов')


def validate_email(value):
    if len(value) > 254:
        raise ValidationError('Email не должен быть длиннее 254 символов')


def validate_name(value):
    if len(value) > 150:
        raise ValidationError(
            'Имя или фамилия не могут быть длиннее 150 символов'
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
