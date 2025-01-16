import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.tokens import default_token_generator
from django.db import models
from django.db.models import Avg
from django.db.models.signals import post_save
from django.dispatch import receiver

from .validators import (validate_email, validate_name, validate_score,
                         validate_username, validate_year)


ROLE_USER = 'user'
ROLE_ADMIN = 'admin'
ROLE_MODERATOR = 'moderator'

ROLE_CHOICES = [
    (ROLE_USER, ROLE_USER),
    (ROLE_ADMIN, ROLE_ADMIN),
    (ROLE_MODERATOR, ROLE_MODERATOR),
]


class User(AbstractUser):
    username = models.CharField(
        validators=(validate_username,),
        max_length=150,
        unique=True,
        blank=False,
        null=False
    )
    email = models.EmailField(
        validators=(validate_email,),
        max_length=254,
        unique=True,
        blank=False,
        null=False
    )
    role = models.CharField(
        'роль',
        max_length=20,
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
        validators=(validate_name,),
        max_length=150,
        blank=True,
        null=True
    )
    last_name = models.CharField(
        'фамилия',
        validators=(validate_name,),
        max_length=150,
        blank=True,
        null=True
    )
    confirmation_code = models.CharField(
        'код подтверждения',
        max_length=255,
        unique=True,
        null=True,
        blank=False,
        default=uuid.uuid4
    )

    @property
    def is_user(self):
        return self.role == ROLE_USER

    @property
    def is_admin(self):
        return self.role == ROLE_ADMIN

    @property
    def is_moderator(self):
        return self.role == ROLE_MODERATOR

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


@receiver(post_save, sender=User)
def post_save(sender, instance, created, **kwargs):
    if created:
        confirmation_code = default_token_generator.make_token(instance)
        instance.confirmation_code = confirmation_code
        instance.save()


class Category(models.Model):
    name = models.CharField(
        max_length=256,
        verbose_name='Название категории'
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name='Слаг категории'
    )

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(
        max_length=256,
        unique=True,
        verbose_name='Название жанра'
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name='Слаг жанра'
    )

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return self.name


class Title(models.Model):
    name = models.CharField(
        max_length=256,
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
    rating = models.FloatField(
        default=0.0,
        verbose_name='Рейтинг'
    )

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'

    def __str__(self):
        return self.name

    def update_rating(self):
        reviews = self.reviews.aggregate(Avg('score'))
        self.rating = reviews['score__avg'] if reviews['score__avg'] else 0.0
        self.save(update_fields=['rating'])


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
    score = models.IntegerField(
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

    def __str__(self):
        return f'Комментарий {self.author} на {self.review}'
