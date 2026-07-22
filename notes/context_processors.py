from .models import Tag

def tags_processor(request):
    if request.user.is_authenticated:
        tags = Tag.objects.filter(notes__user=request.user).distinct()
    else:
        tags = []
    return {'sidebar_tags': tags}
