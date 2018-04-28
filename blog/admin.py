from django.contrib import admin

from blog.models import MainCategory, Category, Post
# Register your models here.


class MainCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_on', 'is_published', 'image')


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'main_category', 'created_on', 'is_published', 'image')


class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_published', 'created_on', 'user')
    search_fields = ('title', 'category', 'category__main_category')


admin.site.register(MainCategory, MainCategoryAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Post, PostAdmin)
