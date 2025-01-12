from rest_framework import viewsets, filters

from reviews.models import Category, Genre, Title
from .serializers import (
    CategorySerializer,
    GenreSerializer,
    TitleGetSerializer,
    TitleCreateUpdateSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    # permission_classes = (IsAdminOrReadOnly, )
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    # permission_classes = (IsAdminOrReadOnly, )
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter,)
    search_fields = ['name']


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all()
    # permission_classes = (IsAdminOrReadOnly, )
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'year']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return TitleGetSerializer
        return TitleCreateUpdateSerializer
