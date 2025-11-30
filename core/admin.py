from django.contrib import admin
from .models import Domain, Collector, Contact


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    search_fields = ('name',)


@admin.register(Collector)
class CollectorAdmin(admin.ModelAdmin):
    list_display = ('id', 'domain', 'type', 'status', 'enabled', 'started_at', 'finished_at')
    list_filter = ('type', 'status', 'enabled')
    search_fields = ('domain__name',)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'domain', 'email', 'phone', 'source_collector', 'created_at')
    search_fields = ('email', 'phone', 'domain__name')
    list_filter = ('source_collector',)


