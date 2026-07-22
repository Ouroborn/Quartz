from django.contrib import admin
from .models import Tag, Note, NoteRelation

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'updated_at', 'views_count')
    search_fields = ('title', 'content')
    list_filter = ('user', 'tags')
    filter_horizontal = ('tags',)

@admin.register(NoteRelation)
class NoteRelationAdmin(admin.ModelAdmin):
    list_display = ('source', 'target', 'weight')
    list_filter = ('weight',)
