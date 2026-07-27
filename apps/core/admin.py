from django.contrib import admin
from .models import BlogPost, ContactMessage

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'is_published')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        ('Content', {'fields': ('title', 'slug', 'excerpt', 'content', 'featured_image')}),
        ('Author', {'fields': ('author',)}),
        ('Publishing', {'fields': ('is_published',)}),
        ('SEO', {'fields': ('seo_title', 'seo_description', 'seo_keywords')}),
    )

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'subject')
    readonly_fields = ('created_at',)
