from django.urls import path

from notes import views

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('notes/create/', views.note_create, name='note_create'),
    path('notes/<int:pk>/', views.note_detail, name='note_detail'),
    path('notes/<int:pk>/edit/', views.note_edit, name='note_edit'),
    path('notes/<int:pk>/delete/', views.note_delete, name='note_delete'),
    path('notes/<int:pk>/export/', views.export_note_md, name='note_download'),
    path('notes/<int:pk>/add-tag/', views.add_tag, name='add_tag'),
    path('notes/<int:pk>/remove-tag/', views.remove_tag, name='remove_tag'),
    path('notes/<int:pk>/track-view/', views.track_view, name='track_view'),
    path('settings/', views.settings_view, name='settings'),
    path('settings/models/', views.get_provider_models, name='get_provider_models'),
    path('graph/', views.quartz, name='quartz'),
    path('graph/data/', views.graph_data, name='graph_data'),
    path('notes/<int:pk>/regenerate-tags/', views.regenerate_tags, name='regenerate_tags'),
]