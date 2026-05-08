from django.contrib import admin

from .models import Category, JournalCategory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass

@admin.register(JournalCategory)
class JournalCategoryAdmin(admin.ModelAdmin):
    pass
