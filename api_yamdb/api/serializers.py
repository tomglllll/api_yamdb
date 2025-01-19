from rest_framework import serializers
from reviews.models import Category, Genre, Title, User, Review, Comment
from django.db.models import Avg

from reviews.validators import validate_username, validate_email

import logging

logger = logging.getLogger(__name__)


class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio', 'role')


class NotAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio', 'role')
        read_only_fields = ('role',)


class GetTokenSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    confirmation_code = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('username', 'confirmation_code')


class SignUpSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        required=True,
        validators=(validate_username,)
    )
    email = serializers.EmailField(
        required=True,
        validators=(validate_email,)
    )

    class Meta:
        model = User
        fields = ('email', 'username')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('name', 'slug')


class TitleGetSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(many=True, read_only=True)
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Title
        fields = '__all__'

    def get_rating(self, obj):
        reviews = Review.objects.filter(title=obj)
        if reviews.exists():
            return reviews.aggregate(Avg('score'))['score__avg']
        return None


class TitleCreateUpdateSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug',
        required=False
    )
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(),
        slug_field='slug',
        many=True,
        required=False
    )

    class Meta:
        model = Title
        fields = '__all__'

    def validate(self, data):

        if 'category' in data and not data['category']:
            raise serializers.ValidationError(
                {'category': 'Категория не может быть пустой.'}
            )

        if 'genre' in data and not data['genre']:
            raise serializers.ValidationError(
                {'genre': 'Жанры не могут быть пустыми.'}
            )

        return data

    def update(self, instance, validated_data):

        if 'name' in validated_data:
            instance.name = validated_data['name']
        if 'year' in validated_data:
            instance.year = validated_data['year']
        if 'description' in validated_data:
            instance.description = validated_data['description']
        if 'category' in validated_data:
            instance.category = validated_data['category']
        if 'genre' in validated_data:
            instance.genre.set(validated_data['genre'])

        instance.save()
        return instance


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Review
        fields = ('id', 'title', 'text', 'author', 'score', 'pub_date')
        read_only_fields = ('id', 'author', 'pub_date', 'title')

    def validate_score(self, value):
        if not (1 <= value <= 10):
            raise serializers.ValidationError('Оценка должна быть от 1 до 10.')
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        title = self.context['view'].get_title()

        return Review.objects.create(
            author=user, title=title, **validated_data)


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')
        read_only_fields = ('author',)

    def validate_text(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                'Комментарий не может быть пустым.'
            )
        return value

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return Comment.objects.create(**validated_data)
