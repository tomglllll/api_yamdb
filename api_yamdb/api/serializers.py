from rest_framework import serializers
from reviews.models import Category, Comment, Genre, Review, Title, User
from reviews.validators import validate_username

from reviews.constants import EMAIL_MAX_LENGTH, USERNAME_MAX_LENGTH


class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role',
        )


class NotAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role',
        )
        read_only_fields = ('role',)


class GetTokenSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    confirmation_code = serializers.CharField(required=True)


class SignUpSerializer(serializers.Serializer):
    username = serializers.CharField(
        required=True,
        validators=[validate_username],
        max_length=USERNAME_MAX_LENGTH
    )
    email = serializers.EmailField(
        required=True,
        max_length=EMAIL_MAX_LENGTH
    )

    def validate(self, attrs):
        email = attrs.get('email')
        username = attrs.get('username')

        existing_email_user = User.objects.filter(
            email=email
        ).exclude(
            username=username
        ).first()
        if existing_email_user:
            raise serializers.ValidationError(
                'Email already used with another username.'
            )

        existing_username_user = User.objects.filter(
            username=username
        ).exclude(
            email=email
        ).first()
        if existing_username_user:
            raise serializers.ValidationError(
                'Username already used with another email.'
            )

        return attrs

    def create(self, validated_data):
        user, created = User.objects.get_or_create(
            username=validated_data['username'],
            email=validated_data['email']
        )

        if created:
            user.send_confirmation_email()

        return user


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
    rating = serializers.IntegerField(default=None)

    class Meta:
        model = Title
        fields = '__all__'


class TitleCreateUpdateSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug',
    )
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(),
        slug_field='slug',
        many=True,
    )

    class Meta:
        model = Title
        fields = '__all__'

    def to_representation(self, instance):
        return TitleGetSerializer(instance, context=self.context).data


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
    )

    class Meta:
        model = Review
        fields = ('id', 'title', 'text', 'author', 'score', 'pub_date')
        read_only_fields = ('id', 'author', 'pub_date', 'title')

    def validate(self, data):
        request = self.context['request']
        title_id = self.context['view'].kwargs.get('title_id')
        if request.method == 'POST' and Review.objects.filter(
                title_id=title_id, author=request.user
        ).exists():
            raise serializers.ValidationError(
                'You have already reviewed this title.'
            )
        return data


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')
        read_only_fields = ('author',)

    def validate_text(self, value):
        if not value.strip():
            raise serializers.ValidationError('Comment cannot be empty.')
        return value
