from django.urls import path
from . import views, models


urlpatterns = [
    # Index
    path('', views.TemplateView.as_view(template_name="index.html"), name="index"),

    # Thesis detail
    path('thesis/<str:pk>/', views.ThesisDetail.as_view(), name="thesis-detail"),

    # Author assigning
    path('thesis/<str:pk>/assign/<str:role>', views.assign, name="thesis-assign"),
    path('thesis/<str:pk>/unassign/<str:role>', views.unassign, name="thesis-unassign"),

    # Editing
    path('thesis/<str:pk>/assignment', views.ThesisAssignmentUpdate.as_view(), name="thesis-assignment"),
    path('thesis/<str:pk>/title', views.thesis_title_update, name="thesis-title"),
    path('thesis/<str:pk>/state', views.LogEntryCreate.as_view(), name="thesis-state"),
    path('thesis/<str:pk>/abstract', views.thesis_abstract_update, name="thesis-abstract"),
    path('thesis/<str:pk>/approve', views.approve, name="thesis-approve"),

    # Attachments
    path('thesis/<str:pk>/attachment/link', 
        views.attachment_link_create, 
        name="attachment-link"),
    path('thesis/<str:pk>/attachment/upload', 
        views.attachment_file_create, 
        name="attachment-upload"),
    path('thesis/<str:thesis_pk>/attachment/<str:pk>/delete', views.attachment_delete, name="attachment-delete"),

    # Submit
    path('thesis/<str:pk>/submit', views.submit, name="thesis-submit"),
    path('thesis/<str:pk>/submit-cancel', views.submit_cancel, name="thesis-submit-cancel"),
]


from django.conf.urls.static import static
from django.conf import settings
from django.views.static import serve
from django.views.decorators.clickjacking import xframe_options_sameorigin

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, view=xframe_options_sameorigin(serve), document_root=settings.MEDIA_ROOT) # pragma: no cover
