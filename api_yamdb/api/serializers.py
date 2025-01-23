from django.db.models import Avg
from rest_framework import serializers

from reviews.constants import EMAIL_MAX_LENGTH, USERNAME_MAX_LENGTH
from reviews.models import Category, Comment, Genre, Review, Title, User
from reviews.validators import validate_username


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


class GetTokenSerializer(serializers.Serializer):

    # TODO В сериализаторе пропишем валидацию полученного кода подтверждения.

    username = serializers.CharField(required=True)
    confirmation_code = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('username', 'confirmation_code')


class SignUpSerializer(serializers.Serializer):
    username = serializers.CharField(
        required=True,
        validators=(validate_username,),
        max_length=USERNAME_MAX_LENGTH
    )
    email = serializers.EmailField(
        required=True,
        max_length=EMAIL_MAX_LENGTH,
    )

    class Meta:
        model = User
        fields = ('email', 'username')

    def validate(self, attrs):
        email = attrs.get('email')
        username = attrs.get('username')

        # TODO Немного модифицируем проверку: В начале получим два объекта
        # пользователя - в одном запросе используем username, во втором email.
        # Для получения объектов используем метод first (None нас тоже устроит
        # в качестве результата). После этого сравним между собой результаты
        # этих запросов. Если не совпадут - запрос невалиден. Останется только
        # проверить в каких полях получены невалидные данные. Если результат
        # соответствующего запроса вернул не None - значит в этом поле
        # невалидное значение.

        existing_user = User.objects.filter(email=email).exclude(
            username=username
        ).first()
        if existing_user:
            raise serializers.ValidationError(
                'Пользователь с таким email уже существует, '
                'но username отличается.'
            )

        existing_user = User.objects.filter(
            username=username
        ).exclude(
            email=email
        ).first()
        if existing_user:
            raise serializers.ValidationError(
                'Пользователь с таким username уже существует, '
                'но email отличается.'
            )

        return attrs
    
    # TODO В данный сериализатор добавим метод create. В нем создадим/получим
    # пользователя через метод get_or_create, отправим код подтверждения и
    # вернем объект пользователя. Во вью останется только передать данные из
    # запроса в сериализатор, проверить валидность данных и вызвать метод save,
    # после чего можно возвращать ответ пользователю.


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
    # Нам надо добавить поле rating для всех объектов в кверисете, не порождая
    # множество дополнительных запросов. Для этого используем аннотацию во вью
    # (подробнее в комментарии в модели произведений). Тут используем
    # IntegerField и зададим значение по умолчанию для этого поля - None.

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
        required=True,
        allow_null=False,
        allow_empty=False
    )
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(),
        slug_field='slug',
        many=True,
        required=True,
        allow_null=False,
        allow_empty=False
    )

    class Meta:
        model = Title
        fields = '__all__'

    def to_representation(self, instance):
        return TitleGetSerializer(instance, context=self.context).data


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Review
        fields = ('id', 'title', 'text', 'author', 'score', 'pub_date')
        read_only_fields = ('id', 'author', 'pub_date', 'title')

    def validate(self, data):
        request = self.context['request']
        title = self.context['view'].kwargs.get('title_id')
        user = request.user

        if request.method == 'POST' and Review.objects.filter(
           title_id=title, author=user).exists():
            raise serializers.ValidationError(
                'Вы уже оставляли отзыв для этого произведения.'
            )
        return data


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
