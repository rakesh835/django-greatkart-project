from django.contrib import admin
import admin_thumbnails

from .models import Product, Variations, ReviewRating, ProductGallary

# Register your models here.

@admin_thumbnails.thumbnail('image')
class ProductGallaryInline(admin.TabularInline):
	model = ProductGallary
	extra = 1


class ProductAdmin(admin.ModelAdmin):
	prepopulated_fields = {'slug': ('product_name',)}
	list_display = ('product_name', 'price', 'stock', 'category', 'modified_date', 'is_available')
	inlines = [ProductGallaryInline]

	
admin.site.register(Product, ProductAdmin)


class VariationsAdmin(admin.ModelAdmin):
	list_display = ('product', 'variation_category', 'variation_value', 'is_active')
	list_editable = ('is_active',)
	list_filter = ('product', 'variation_category', 'variation_value', 'is_active')


admin.site.register(Variations, VariationsAdmin)


admin.site.register(ReviewRating)
admin.site.register(ProductGallary)