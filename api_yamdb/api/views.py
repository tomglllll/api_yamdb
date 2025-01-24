from django.db.models import Avg
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode

from .filters import TitleFilter
from .mixins import CategoryGenreViewSet
from .permissions import AdminOnly, IsAdminUserOrReadOnly, IsAuthorOrReadOnly
from .serializers import (CategorySerializer, CommentSerializer,
                          GenreSerializer, GetTokenSerializer,
                          NotAdminSerializer, ReviewSerializer,
                          SignUpSerializer, TitleCreateUpdateSerializer,
                          TitleGetSerializer, UsersSerializer)
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
        if request.method == 'PATCH':
            serializer = NotAdminSerializer(
                request.user,
                data=request.data,
                partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(UsersSerializer(request.user).data)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class APIGetToken(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GetTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = get_object_or_404(User, username=data['username'])

        token = data.get('token')
        if not default_token_generator.check_token(user, token):
            return Response(
                {'detail': 'Неверный токен.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        token = AccessToken.for_user(user)
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

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(str(user.pk).encode())

        email_body = (
            f'Привет, {user.username}.\n'
            'Для подтверждения email перейдите по ссылке: '
            f'http://example.com/confirm/{uid}/{token}'
        )
        send_mail(
            subject='Подтверждение email для доступа к API!',
            message=email_body,
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response(
            {'username': user.username, 'email': user.email},
            status=status.HTTP_200_OK
        )


class CategoryViewSet(CategoryGenreViewSet):
    queryset = Category.objects.all().order_by('id')
    serializer_class = CategorySerializer


class GenreViewSet(CategoryGenreViewSet):
    queryset = Genre.objects.all().order_by('id')
    serializer_class = GenreSerializer


class TitleViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    queryset = Title.objects.annotate(
        rating=Avg('reviews__score')
    ).order_by('id')
    permission_classes = (IsAdminUserOrReadOnly,)
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return TitleCreateUpdateSerializer
        return TitleGetSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_title(self):
        return get_object_or_404(Title, id=self.kwargs.get('title_id'))

    def get_queryset(self):
        return self.get_title().reviews.all().order_by('id')

    def perform_create(self, serializer):
        title = get_object_or_404(Title, id=self.kwargs.get('title_id'))
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    serializer_class = CommentSerializer
    permission_classes = (IsAuthorOrReadOnly,
                          permissions.IsAuthenticatedOrReadOnly)

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
