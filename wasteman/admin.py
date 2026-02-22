from django.contrib import admin

from .models import Wasteman, Painting, Poster, ArtworkImage, PosterVariation

admin.site.register(Wasteman)

class ArtworkImageStackedInline(admin.StackedInline):
    model = ArtworkImage
    extra = 1


@admin.register(Painting)
class PaintingAdmin(admin.ModelAdmin):
    inlines = [ArtworkImageStackedInline]


class PosterVariationInline(admin.StackedInline):
    model = PosterVariation
    extra = 0


@admin.register(Poster)
class PosterAdmin(admin.ModelAdmin):
    inlines = [ArtworkImageStackedInline, PosterVariationInline]


admin.site.register(PosterVariation)