import os
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
            file_path = os.path.join(
                settings.BASE_DIR,
                'static',
                'data',
                csv_file
            )
            self.stdout.write(
                f'Загрузка данных из {file_path} в {model.__name__}...'
            )
            if not os.path.exists(file_path):
                self.stdout.write(
                    self.style.ERROR(f'Файл {file_path} не найден')
                )
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    objects = [
                        model(**self.clean_data(model, row))
                        for row in reader
                    ]
                    model.objects.bulk_create(objects)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Данные для {model.__name__} успешно загружены'
                    )
                )
            except Exception as error:
                self.stdout.write(
                    self.style.ERROR(
                        f'Ошибка загрузки для {model.__name__}: {error}'
                    )
                )

    def clean_data(self, model, row):
        """Очистка данных перед созданием объектов"""
        if model == Title:
            row['category'] = Category.objects.get(pk=row['category'])
        elif model in [Review, Comment]:
            row['author'] = User.objects.get(pk=row['author'])
            if model == Review:
                row['title'] = Title.objects.get(pk=row['title_id'])
            elif model == Comment:
                row['review'] = Review.objects.get(pk=row['review_id'])
        return row
