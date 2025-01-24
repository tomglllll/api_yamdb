from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import Category, Comment, Genre, Review, Title

User = get_user_model()


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    list_filter = ('name',)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    list_filter = ('name',)


@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    list_display = ('name', 'year', 'category', 'description')
    list_filter = ('category',)
    search_fields = ('name',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('review', 'text', 'author', 'pub_date')
    list_filter = ('review',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('title', 'text', 'author', 'pub_date')
    list_filter = ('title', 'pub_date')
    search_fields = ('title',)


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'role',
        'first_name',
        'last_name',
        'email_confirmed',
        'bio'
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('role', 'email_confirmed')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'bio'
            )
        }),
        ('Permissions', {
            'fields': (
                'role',
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            ),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Email Confirmation', {'fields': ('email_confirmed',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password1', 'password2', 'role',
                'email_confirmed'
            ),
        }),
    )
