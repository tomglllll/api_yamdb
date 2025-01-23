from rest_framework import mixins, viewsets, filters
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination

from .permissions import IsAdminUserOrReadOnly


class CategoryGenreViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = (IsAdminUserOrReadOnly,)
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    pagination_class = PageNumberPagination
