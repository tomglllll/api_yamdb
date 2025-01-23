import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import (EMAIL_MAX_LENGTH, NAME_MAX_LENGTH, SLUG_MAX_LENGTH,
                        USERNAME_MAX_LENGTH, TITLE_GENRE_CATEGORY_MAX_LENGTH,
                        CONF_CODE_MAX_LENGTH)
from .validators import validate_score, validate_username, validate_year

ROLE_USER = 'user'
ROLE_ADMIN = 'admin'
ROLE_MODERATOR = 'moderator'


# Можно лучше: В Джанго есть подходящие енамы для организации вариантов выбора.
# https://docs.djangoproject.com/en/3.2/ref/models/fields/#enumeration-types
ROLE_CHOICES = [
    (ROLE_USER, ROLE_USER),
    (ROLE_ADMIN, ROLE_ADMIN),
    (ROLE_MODERATOR, ROLE_MODERATOR),
]


class User(AbstractUser):
    username = models.CharField(
        validators=(validate_username,),
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
    )
    email = models.EmailField(
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
    )
    role = models.CharField(
        'роль',
        max_length=20,
        # TODO Максимальную длину стоит задать с запасом, чтобы в случае
        # добавления новой роли мы не уперлись в лимит символов (мы не знаем
        # какую роль понадобится добавить).

        # Можно лучше: можно прописать вычисление максимальной длины из
        # существующих ролей, т.е. взять длины всех ролей, и выбрать из них
        # максимальную. Это можно сделать прямо в этой строке. Понадобится
        # функция max, в которую надо передать список с длинами ролей (его
        # можно сформировать через list comprehension или через map и list.

        choices=ROLE_CHOICES,
        default=ROLE_USER,
        blank=True
    )

    bio = models.TextField(
        'биография',
        blank=True,
    )
    first_name = models.CharField(
        'имя',
        max_length=NAME_MAX_LENGTH,
        blank=True,
        null=True
    )
    last_name = models.CharField(
        'фамилия',
        max_length=NAME_MAX_LENGTH,
        blank=True,
        null=True
    )
    confirmation_code = models.CharField(
        # Можно лучше: Можно не хранить код подтверждения в БД, если
        # использовать default_token_generator из django.contrib.auth.tokens.
        # У этого объекта есть два метода: для генерации токена - make_token и
        # для проверки полученного токена  - check_token (оба метода принимают
        # на вход объект пользователя).

        'код подтверждения',
        max_length=CONF_CODE_MAX_LENGTH,
        unique=True,
        null=True,
        default=uuid.uuid4
    )

    @property
    def is_admin(self):
        return self.role == ROLE_ADMIN or self.is_staff or self.is_superuser

    @property
    def is_moderator(self):
        return self.role == ROLE_MODERATOR

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Category(models.Model):
    name = models.CharField(
        max_length=TITLE_GENRE_CATEGORY_MAX_LENGTH,
        verbose_name='Название категории'
    )
    slug = models.SlugField(
        max_length=SLUG_MAX_LENGTH,
        unique=True,
        verbose_name='Слаг категории'
    )

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(
        max_length=TITLE_GENRE_CATEGORY_MAX_LENGTH,
        unique=True,
        verbose_name='Название жанра'
    )
    slug = models.SlugField(
        max_length=SLUG_MAX_LENGTH,
        unique=True,
        verbose_name='Слаг жанра'
    )

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Title(models.Model):
    name = models.CharField(
        max_length=TITLE_GENRE_CATEGORY_MAX_LENGTH,
        verbose_name='Название произведения'
    )
    year = models.PositiveIntegerField(
        verbose_name='Год выпуска',
        validators=[validate_year]
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='titles',
        verbose_name='Категория',
        null=True,
        blank=True
    )
    genre = models.ManyToManyField(
        Genre,
        related_name='titles',
        verbose_name='Жанры'
    )

    rating = models.IntegerField(
        # Рейтинг - вычисляемое поле. Его не надо хранить в БД Надо
        # добавьте атрибут rating для всех элементов QuerySet путем его 
        # aннотирования во вью. Документация для annotate и для Avg
        # https://docs.djangoproject.com/en/4.1/ref/models/querysets/#django.db.models.query.QuerySet.annotate
        # https://docs.djangoproject.com/en/5.1/ref/models/querysets/#avg
        default=0.0,
        # В соответствии со спецификацией поле с рейтингом - целое число.
        verbose_name='Рейтинг'
    )

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Review(models.Model):
    User = get_user_model()
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Произведение'
    )
    text = models.TextField('Текст отзыва')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Автор отзыва'
    )
    score = models.PositiveSmallIntegerField(
        'Оценка',
        validators=(validate_score,)
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        unique_together = ('title', 'author')
        ordering = ('pub_date',)

    def __str__(self):
        return f'Отзыв {self.author} на {self.title}'


class Comment(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Отзыв'
    )
    text = models.TextField('Текст комментария')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор комментария'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('pub_date',)

    def __str__(self):
        return f'Комментарий {self.author} на {self.review}'
