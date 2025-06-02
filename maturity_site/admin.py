from django.contrib import admin
from .models import Company,Survey,Axis,Question,PossibleAnswer,Results,Recommendation,Diagnostic,Answer, Dimension
# Register your models here.
admin.site.register(Company)
admin.site.register(Survey)
admin.site.register(Axis)
admin.site.register(Question)
admin.site.register(PossibleAnswer)
admin.site.register(Results)
admin.site.register(Diagnostic)
admin.site.register(Answer)
admin.site.register(Dimension)


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('type', "axe", "dimension",'question', "threshold", "min_difference")
    list_filter = ('type',)
    search_fields = ('template_text',)
    fieldsets = (
        (None,{
            'fields': ('type', 'template_text')
        }),
        ('Ciblage', {
            'fields': ('axe', 'dimension','question')
        }),
        ('Trigger Point', {
            'fields': ('threshold', 'min_difference')
        }),
    )
