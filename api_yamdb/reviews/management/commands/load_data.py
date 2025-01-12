import csv
from django.core.management.base import BaseCommand
from django.conf import settings
from reviews.models import User, Category, Genre, Title, Review, Comment


TABLES = {
    User: 'users.csv',
    Category: 'category.csv',
    Genre: 'genre.csv',
    Title: 'titles.csv',
    Review: 'review.csv',
    Comment: 'comments.csv',
}


class Command(BaseCommand):
    help = 'Загрузка данных из CSV файлов в базу данных'

    def handle(self, *args, **kwargs):
        for model, csv_file in TABLES.items():
            file_path = f'{settings.BASE_DIR}/static/data/{csv_file}'
            self.stdout.write(
                f'Загрузка данных из {file_path} в {model.__name__}...'
            )
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    model.objects.bulk_create(
                        model(**self.clean_data(model, row)) for row in reader
                    )
                self.stdout.write(self.style.SUCCESS(
                    f'Данные для {model.__name__} успешно загружены')
                )
            except Exception as error:
                self.stdout.write(self.style.ERROR(
                    f'Ошибка загрузки для {model.__name__}: {error}')
                )

    def clean_data(self, model, row):
        """Очистка данных перед созданием объектов"""
        if model == Title:
            row['category_id'] = Category.objects.get(id=row['category']).id
        if model in [Review, Comment]:
            row['author_id'] = User.objects.get(id=row['author']).id
        return row
