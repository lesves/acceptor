from django.contrib import admin
from . import models


class ConsultationPeriodInline(admin.TabularInline):
    model = models.ConsultationPeriod
    extra = 1


class SubjectAdmin(admin.ModelAdmin):
    model = models.Subject

    inlines = [ConsultationPeriodInline]


class LogEntryInline(admin.TabularInline):
    model = models.LogEntry
    readonly_fields = ("timestamp",)
    ordering = ("timestamp",)
    extra = 0


class ConsultationInline(admin.TabularInline):
    model = models.Consultation
    extra = 1


class ThesisAdmin(admin.ModelAdmin):
    model = models.Thesis

    readonly_fields = ("state",)
    filter_horizontal = ("keywords",)

    inlines = [ConsultationInline, LogEntryInline]


admin.site.register(models.State)
admin.site.register(models.Thesis, ThesisAdmin)
admin.site.register(models.Subject, SubjectAdmin)
admin.site.register(models.Keyword)
