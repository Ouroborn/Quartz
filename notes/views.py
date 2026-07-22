from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from .models import Note, Tag, NoteRelation, UserSettings
from .forms import NoteForm, UserSettingsForm
from .ai_services import list_provider_models, run_ai_analysis

@login_required
def settings_view(request):
    settings, created = UserSettings.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = UserSettingsForm(instance=settings)
    return render(request, 'notes/settings.html', {'form': form})


@login_required
def get_provider_models(request):
    """AJAX: вернуть актуальный список моделей для выбранного провайдера.

    api_key не обязателен в query — если не передан, подставляем ключ,
    уже сохранённый в UserSettings пользователя (чтобы не заставлять
    вводить его повторно, если он уже был сохранён ранее).
    """
    provider = request.GET.get('provider', '')
    api_key = request.GET.get('api_key', '')

    if not api_key:
        try:
            api_key = request.user.settings.api_key
        except UserSettings.DoesNotExist:
            api_key = ''

    if not provider:
        return JsonResponse({'models': []})

    models = list_provider_models(provider, api_key)
    return JsonResponse({'models': models})

@login_required
def add_tag(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    tag_name = request.POST.get('tag_name', '').strip()
    if tag_name:
        tag, created = Tag.objects.get_or_create(name=tag_name)
        note.tags.add(tag)
        return JsonResponse({'status': 'ok', 'tag': tag.name})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def remove_tag(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    tag_name = request.POST.get('tag_name', '').strip()
    if tag_name:
        tag = Tag.objects.filter(name=tag_name).first()
        if tag:
            note.tags.remove(tag)
            return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)
import markdown2
from django.db.models import Q
import time

@login_required
def track_view(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    
    # Логика сессий
    viewed_notes = request.session.get('viewed_notes', {})
    current_time = time.time()
    
    last_view_time = viewed_notes.get(str(pk))
    
    if not last_view_time or (current_time - last_view_time > 1800): # 1800 сек = 30 мин
        note.views_count += 1
        note.save()
        viewed_notes[str(pk)] = current_time
        request.session['viewed_notes'] = viewed_notes
        return JsonResponse({'status': 'view_tracked', 'count': note.views_count})
    
    return JsonResponse({'status': 'already_viewed'}, status=200)

@login_required
def index(request):
    query = request.GET.get('q')
    tag_filter = request.GET.get('tag')
    
    notes = Note.objects.filter(user=request.user).order_by('-created_at')
    
    if query:
        notes = notes.filter(Q(title__icontains=query) | Q(content__icontains=query))
    
    if tag_filter:
        notes = notes.filter(tags__name=tag_filter)
        
    tags = Tag.objects.filter(notes__user=request.user).distinct()
    
    return render(request, 'notes/index.html', {
        'notes': notes,
        'tags': tags,
        'query': query,
        'tag_filter': tag_filter
    })

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def note_detail(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    
    content_html = markdown2.markdown(note.content)
    
    return render(request, 'notes/note_detail.html', {
        'note': note,
        'content_html': content_html
    })

@login_required
def note_create(request):
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.user = request.user
            note.save()
            form.save_m2m()
            run_ai_analysis(note)
            return redirect('note_detail', pk=note.pk)
    else:
        form = NoteForm()
    return render(request, 'notes/note_form.html', {'form': form, 'title': 'Создать заметку'})

@login_required
def note_edit(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            note = form.save()
            run_ai_analysis(note)
            return redirect('note_detail', pk=note.pk)
    else:
        form = NoteForm(instance=note)
    return render(request, 'notes/note_form.html', {'form': form, 'title': 'Редактировать заметку'})

@login_required
def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    if request.method == 'POST':
        note.delete()
        return redirect('index')
    return render(request, 'notes/note_confirm_delete.html', {'note': note})

@login_required
def quartz(request):
    return render(request, 'notes/graph.html', {'is_graph_page': True})

@login_required
def graph_data(request):
    notes = Note.objects.filter(user=request.user)
    relations = NoteRelation.objects.filter(source__user=request.user)
    
    nodes = []
    for note in notes:
        nodes.append({
            'id': note.id,
            'label': note.title,
            'title': note.title,
        })
        
    edges = []
    seen_edges = set()
    for rel in relations:
        # Убираем дубликаты для визуализации (т.к. мы создавали обратные связи в ai_services)
        edge = tuple(sorted((rel.source_id, rel.target_id)))
        if edge not in seen_edges:
            edges.append({
                'from': rel.source_id,
                'to': rel.target_id,
                'title': rel.reason,
                'value': rel.weight
            })
            seen_edges.add(edge)
        
    return JsonResponse({'nodes': nodes, 'edges': edges})

@login_required
def export_note_md(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    response = HttpResponse(note.content, content_type='text/markdown')
    # Очищаем название файла от недопустимых символов
    safe_title = "".join([c for c in note.title if c.isalnum() or c in (' ', '.', '_')]).strip()
    response['Content-Disposition'] = f'attachment; filename="{safe_title}.md"'
    return response