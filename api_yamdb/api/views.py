from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .filters import TitleFilter
from .mixins import CreateListDestroyMixin
from .permissions import AdminOnly, IsAdminUserOrReadOnly, IsAuthorOrReadOnly
from .serializers import (CategorySerializer, CommentSerializer,
                          GenreSerializer, GetTokenSerializer,
                          NotAdminSerializer, ReviewSerializer,
                          SignUpSerializer, TitleCreateUpdateSerializer,
                          TitleGetSerializer, UsersSerializer)
from api.permissions import IsAuthorOrReadOnly
from reviews.models import Category, Genre, Review, Title, User


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UsersSerializer
    permission_classes = (AdminOnly,)
    lookup_field = 'username'
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email']
    http_method_names = ['get', 'post', 'patch', 'delete']

    @action(
        methods=['GET', 'PATCH'],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='me')
    def get_current_user_info(self, request):
        serializer = UsersSerializer(request.user)
        if request.method == 'PATCH':
            if request.user.is_admin:
                serializer = UsersSerializer(
                    request.user,
                    data=request.data,
                    partial=True)
            else:
                serializer = NotAdminSerializer(
                    request.user,
                    data=request.data,
                    partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class APIGetToken(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        confirmation_code = request.data.get('confirmation_code')

        if not username or not confirmation_code:
            return Response(
                {
                    'detail': (
                        'Отсутствуют необходимые данные: username или '
                        'confirmation_code.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = GetTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = get_object_or_404(User, username=data['username'])

        if data.get('confirmation_code') != user.confirmation_code:
            return Response(
                {'detail': 'Неверные учетные данные.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        token = RefreshToken.for_user(user).access_token
        return Response({'token': str(token)}, status=status.HTTP_200_OK)


class APISignup(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        username = serializer.validated_data['username']

        user, created = User.objects.get_or_create(
            email=email,
            username=username
        )

        if not created:
            user.confirmation_code = User.objects.make_random_password(
                length=6
            )
            user.save()
        else:
            user.confirmation_code = User.objects.make_random_password(
                length=6
            )
            user.save()

        email_body = (
            f'Привет, {user.username}.\n'
            'Ваш код подтверждения для доступа к API: '
            f'{user.confirmation_code}'
        )
        send_mail(
            subject='Код подтверждения для доступа к API!',
            message=email_body,
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response(
            {'username': user.username, 'email': user.email},
            status=status.HTTP_200_OK
        )


class CategoryViewSet(CreateListDestroyMixin):
    queryset = Category.objects.all().order_by('id')
    serializer_class = CategorySerializer
    permission_classes = (IsAdminUserOrReadOnly,)
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    pagination_class = PageNumberPagination


class GenreViewSet(CreateListDestroyMixin):
    queryset = Genre.objects.all().order_by('id')
    serializer_class = GenreSerializer
    permission_classes = (IsAdminUserOrReadOnly,)
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter,)
    search_fields = ['name']


class TitleViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    queryset = Title.objects.all().order_by('id')
    permission_classes = (IsAdminUserOrReadOnly,)
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return TitleCreateUpdateSerializer
        return TitleGetSerializer

    def partial_update(self, request, *args, **kwargs):
        title = self.get_object()
        serializer = self.get_serializer(
            title, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)

    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_title(self):
        return get_object_or_404(Title, id=self.kwargs.get('title_id'))

    def get_queryset(self):
        return Review.objects.filter(title=self.get_title()).order_by('id')

    def create(self, request, *args, **kwargs):
        title = self.get_title()
        user = request.user

        if not user:
            raise ValidationError('Пользователь не авторизован')

        if Review.objects.filter(title=title, author=user).exists():
            raise ValidationError(
                'Вы уже оставляли отзыв для этого произведения.')

        return super().create(request, *args, **kwargs)

    def check_permission(self, review):
        user = self.request.user
        if user.role == 'admin' or user.role == 'moderator':
            return True
        return review.author == user

    def update(self, request, *args, **kwargs):
        review = self.get_object()
        if not self.check_permission(review):
            return Response(
                {'detail': 'Вы не можете редактировать чужой отзыв.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        review = self.get_object()
        if not self.check_permission(review):
            return Response(
                {'detail': 'Вы не можете удалить чужой отзыв.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


class CommentViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    serializer_class = CommentSerializer
    permission_classes = (
        permissions.IsAuthenticatedOrReadOnly,
    )

    def get_queryset(self):
        review = get_object_or_404(
            Review,
            id=self.kwargs.get('review_id')
        )
        return review.comments.all().order_by('id')

    def perform_create(self, serializer):
        review = get_object_or_404(
            Review,
            id=self.kwargs.get('review_id')
        )
        serializer.save(author=self.request.user, review=review)

    def check_permission(self, comment):
        user = self.request.user
        if user.role == 'admin' or user.role == 'moderator':
            return True
        return comment.author == user

    def update(self, request, *args, **kwargs):
        comment = self.get_object()
        if not self.check_permission(comment):
            return Response(
                {'detail': 'Вы не можете редактировать чужой комментарий.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        if not self.check_permission(comment):
            return Response(
                {'detail': 'Вы не можете удалить чужой комментарий.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
