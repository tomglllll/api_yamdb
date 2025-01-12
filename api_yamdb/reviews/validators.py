import datetime
from django.core.exceptions import ValidationError


def validate_year(value):
    """Проверка: год выпуска не превышает текущий год."""
    current_year = datetime.datetime.now().year
    if value > current_year:
        raise ValidationError(
            f'Год выпуска не может превышать текущий год: {current_year}.'
        )
