from django.contrib import admin

from .models import Flowers, Decorations, Order, Client, DecorationType, DeliveryOption, OrderDecoration, OrderFlower, Cart, CartItem, ContactUs, WrappingPaper, Visitor


class FlowersAdmin(admin.ModelAdmin):
    list_display = ('color', 'remaining', 'price', 'flower_img', 'bouquets_img')


class DecorationAdmin(admin.ModelAdmin):
    list_display = ('type', 'color', 'remaining', 'cost_to_buy' ,'price', 'image')


class DecorationTypeAdmin(admin.ModelAdmin):
    list_display = ('decoration_type',)

class WrappingPaperAdmin(admin.ModelAdmin):
    list_display = ('color', 'remaining', 'image')

class ClientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'client_phone_number', 'client_address')

    def get_total(self, obj):
        return obj.total()

    get_total.short_description = 'Total'


class DeliveryOptionAdmin(admin.ModelAdmin):
    list_display = ('delivery_option', 'delivery_price')

class ContactUsAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'message')

class OrderAdmin(admin.ModelAdmin):
    list_display = ('client', 'created_at', 'delivery_option', 'status', 'total_price')

class VisotorAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'date')


admin.site.register(Flowers, FlowersAdmin)
admin.site.register(Visitor, VisotorAdmin)
admin.site.register(Decorations, DecorationAdmin)
admin.site.register(WrappingPaper, WrappingPaperAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderFlower)
admin.site.register(OrderDecoration)
admin.site.register(Client, ClientAdmin)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(DecorationType, DecorationTypeAdmin)
admin.site.register(DeliveryOption, DeliveryOptionAdmin)
admin.site.register(ContactUs, ContactUsAdmin)
