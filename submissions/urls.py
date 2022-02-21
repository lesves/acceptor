from django.urls import path
from . import forms, views, models


urlpatterns = [
    # Index
    path(
        '', 
        views.IndexView.as_view(), 
        name="index"
    ),

    # Theses list
    path('theses/', views.CurrentThesisList.as_view(), name="thesis-list"),
    path('theses/my-list/', views.MyThesisList.as_view(), name="thesis-me"),
    path('theses/subject/<int:subject>/', views.CurrentThesisList.as_view(), name="thesis-list"),
    #path('theses/subject/<int:subject>/create/', views.ThesisCreate.as_view(), name="thesis-create"),

    # Thesis create
    path('thesis/create/', views.ThesisCreate.as_view(), name="thesis-create"),

    # Thesis detail
    path(
        'thesis/<str:pk>/', 
        views.ThesisDetail.as_view(), 
        name="thesis-detail"
    ),

    # Author assigning
    path(
        'thesis/<str:pk>/assign/<str:role>', 
        views.assign, 
        name="thesis-assign"
    ),
    path(
        'thesis/<str:pk>/unassign/<str:role>', 
        views.unassign, 
        name="thesis-unassign"
    ),

    # Editing
    path(
        'thesis/<str:pk>/assignment', 
        views.ThesisAssignmentUpdate.as_view(), 
        name="thesis-assignment"
    ),
    path(
        'thesis/<str:pk>/title', 
        views.ThesisUpdate.as_view(fields=["title"]), 
        name="thesis-title"
    ),
    path(
        'thesis/<str:pk>/abstract', 
        views.ThesisUpdate.as_view(fields=["abstract"]), 
        name="thesis-abstract"
    ),
    path(
        'thesis/<str:pk>/keywords',
        views.ThesisUpdate.as_view(form_class=forms.ThesisKeywordUpdateForm),
        name="thesis-keywords",
    ),
    path(
        'thesis/<str:pk>/state', 
        views.LogEntryCreate.as_view(), 
        name="thesis-state"
    ),
    path('thesis/<str:pk>/approve', views.approve, name="thesis-approve"),

    # Attachments
    path(
        'thesis/<str:pk>/attachment/link', 
        views.AttachmentCreate.as_view(model=models.Link, fields=["url"]), 
        name="attachment-link"
    ),
    path(
        'thesis/<str:pk>/attachment/upload', 
        views.AttachmentCreate.as_view(model=models.File, fields=["upload"]), 
        name="attachment-upload"
    ),
    path(
        'thesis/<str:thesis_pk>/attachment/<str:pk>/delete', 
        views.attachment_delete, 
        name="attachment-delete"
    ),

    # Submit
    path(
        'thesis/<str:pk>/submit', 
        views.submit, 
        name="thesis-submit"
    ),
    path(
        'thesis/<str:pk>/submit-cancel', 
        views.submit_cancel, 
        name="thesis-submit-cancel"
    ),

    # Opinions
    path(
        'thesis/<str:pk>/opinion/opponent/update', 
        views.ThesisOpinionUpdate.as_view(
            role="opponent", 
            fields=["opponent_opinion"]
        ), 
        name="thesis-opponent-opinion-update"
    ),
    path(
        'thesis/<str:pk>/opinion/supervisor/update',
        views.ThesisOpinionUpdate.as_view(
            role="supervisor", 
            fields=["supervisor_opinion"]
        ), 
        name="thesis-supervisor-opinion-update"
    ),
    path(
        'thesis/<str:pk>/opinion/opponent/', 
        views.OpinionDetail.as_view(role="opponent"), 
        name="thesis-opponent-opinion"
    ),
    path(
        'thesis/<str:pk>/opinion/supervisor/',
        views.OpinionDetail.as_view(role="supervisor"), 
        name="thesis-supervisor-opinion"
    ),
]


from django.conf import settings

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.views.static import serve
    from django.views.decorators.clickjacking import xframe_options_sameorigin

    urlpatterns += static(settings.MEDIA_URL, view=xframe_options_sameorigin(serve), document_root=settings.MEDIA_ROOT) # pragma: no cover
