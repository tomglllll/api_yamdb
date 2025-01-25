from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .constants import (
    EMAIL_MAX_LENGTH, NAME_MAX_LENGTH, SLUG_MAX_LENGTH,
    USERNAME_MAX_LENGTH, TITLE_GENRE_CATEGORY_MAX_LENGTH
)
from .validators import validate_score, validate_username, validate_year

ROLE_USER = 'user'
ROLE_ADMIN = 'admin'
ROLE_MODERATOR = 'moderator'


class RoleChoices(models.TextChoices):
    USER = ROLE_USER, 'User'
    ADMIN = ROLE_ADMIN, 'Admin'
    MODERATOR = ROLE_MODERATOR, 'Moderator'


class User(AbstractUser):
    username = models.CharField(
        validators=[validate_username],
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
    )
    email = models.EmailField(
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
    )
    role = models.CharField(
        'Роль',
        max_length=max(len(role) for role, _ in RoleChoices.choices),
        choices=RoleChoices.choices,
        default=RoleChoices.USER,
        blank=True
    )
    email_confirmed = models.BooleanField(default=False, blank=True)
    bio = models.TextField('Биография', blank=True)
    first_name = models.CharField(
        'Имя',
        max_length=NAME_MAX_LENGTH,
        blank=True,
        null=True
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=NAME_MAX_LENGTH,
        blank=True,
        null=True
    )

    @property
    def is_admin(self):
        return (
            self.role == RoleChoices.ADMIN
            or self.is_staff
            or self.is_superuser
        )

    @property
    def is_moderator(self):
        return self.role == RoleChoices.MODERATOR

    class Meta:
        ordering = ['username']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username

    def generate_confirmation_token(self):

        return default_token_generator.make_token(self)

    def send_confirmation_email(self):

        token = self.generate_confirmation_token()
        uid = urlsafe_base64_encode(str(self.pk).encode()).decode()
        confirmation_url = f'http://example.com/confirm/{uid}/{token}'

        subject = 'Подтверждение email'
        message = render_to_string('email/confirmation_email.html', {
            'user': self,
            'confirmation_url': confirmation_url,
        })

        send_mail(subject, message, 'from@example.com', [self.email])


class CategoryGenreBaseModel(models.Model):
    name = models.CharField(
        max_length=TITLE_GENRE_CATEGORY_MAX_LENGTH,
        verbose_name='Название'
    )
    slug = models.SlugField(
        max_length=SLUG_MAX_LENGTH,
        unique=True,
        verbose_name='Слаг',
    )

    class Meta:
        abstract = True
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(CategoryGenreBaseModel):
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Genre(CategoryGenreBaseModel):
    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'


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

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'
        ordering = ['name']

    def __str__(self):
        return self.name


class Review(models.Model):
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Произведение'
    )
    text = models.TextField('Текст отзыва')
    author = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Автор отзыва'
    )
    score = models.PositiveSmallIntegerField(
        'Оценка',
        validators=[validate_score]
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_review_per_author_per_title'
            )
        ]
        ordering = ['pub_date']

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
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор комментария'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['pub_date']

    def __str__(self):
        return f'Комментарий {self.author} на {self.review}'
