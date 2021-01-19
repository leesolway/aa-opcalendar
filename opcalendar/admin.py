from django.contrib import admin
from opcalendar.models import Event, EventCategory, EventSignal, WebHook, EventHost, EventImport, Owner, IngameEvents

from django.utils.translation import ugettext_lazy as _

class WebHookAdmin(admin.ModelAdmin):
    list_display=('name', 'enabled')

admin.site.register(WebHook, WebHookAdmin)

class EventSignalAdmin(admin.ModelAdmin):
	list_display=('get_webhook','ignore_past_fleets')

	def get_webhook(self, obj):
		return obj.webhook.name
	get_webhook.short_description = 'Webhook Name'
	get_webhook.admin_order_field = 'webhook__name'

admin.site.register(EventSignal, EventSignalAdmin)

class EventCategoryAdmin(admin.ModelAdmin):
    model = EventCategory

admin.site.register(EventCategory, EventCategoryAdmin)

class EventHostAdmin(admin.ModelAdmin):
    model = EventHost

admin.site.register(EventHost, EventHostAdmin)

class EventHostAdmin(admin.ModelAdmin):
    model = EventImport

admin.site.register(EventImport, EventHostAdmin)


admin.site.register(Owner)

admin.site.register(IngameEvents)

admin.site.register(Event)


