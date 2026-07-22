from .models import Tag, Note

def tags_processor(request):
    if request.user.is_authenticated:
        tags = Tag.objects.filter(notes__user=request.user).distinct()
        recent_notes = Note.objects.filter(user=request.user).order_by('-updated_at')[:15]
    else:
        tags = []
        recent_notes = []
    return {
        'sidebar_tags': tags,
        'sidebar_notes': recent_notes
    }
