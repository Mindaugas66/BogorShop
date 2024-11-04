from django.urls import path, include
from . import views
from . import adminviews
from django.conf import settings
from django.conf.urls.static import static

app_name = 'shop'

urlpatterns = [
    path('', views.index, name='index'),
    path('puokste/', views.flower, name='flowers'),
    path('dekoracijos/', views.decoration, name='decorations'),
    path('dekoracija/<int:deco_type_id>/', views.product_detail, name='product_detail'),
    path('duk/', views.faq, name='faq'),
    path('Kontaktai/', views.contact_view, name='contact'),
    path('pristatymas/', views.delivery, name='shipping'),
    path('krepselis/', views.cart_view, name='cart'),
    path('krepselis/prideti/', views.add_to_cart, name='add_to_cart'),
    path('krepselis/atnaujinti/', views.update_cart, name='update_cart'),
    path('prekselis/pasalinti/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('krepselis/isvalyti/', views.clear_cart, name='clear_cart'),
    path('atsiskaitymas/', views.checkout_view, name='checkout'),
    path('uzsakymas/<int:order_id>/', views.checkout_complete_view, name='checkout_complete'),

    ### Admin ###
    path('adminas/', adminviews.admin_login, name='admin_login'),
    path('adminas/dashboard', adminviews.admin_dashboard, name='admin_dashboard'),
    path('adminas/products', adminviews.admin_products, name='admin_products'),
    path('adminas/products/flowers', adminviews.admin_products_flowers, name='admin_products_flowers'),
    path('adminas/products/decorations', adminviews.admin_products_decorations, name='admin_products_decorations'),
    path('adminas/products/decoration/<int:decoration_id>/', adminviews.get_decoration, name='get_decoration'),
    path('adminas/products/decorationtype/<int:type_id>/', adminviews.get_decoration_type, name='get_decoration_type'),
    path('adminas/products/decorationtype/delete/<int:type_id>/', adminviews.delete_decoration_type, name='delete_decoration_type'),
    path('adminas/products/decoration/delete/<int:decoration_id>/', adminviews.delete_decoration, name='delete_decoration'),
    path('adminas/products/wrappingpaper', adminviews.admin_products_wrapping_paper, name='admin_products_wrapping_paper'),
    path('adminas/products/wrappingpaper/<int:wrapping_paper_id>/', adminviews.get_wrapping_paper, name='get_wrapping_paper'),
    path('adminas/orders', adminviews.admin_orders, name='admin_orders'),
    path('adminas/order/<int:order_id>/', adminviews.admin_order_detail, name='admin_order_detail'),
    path('adminas/inventory', adminviews.admin_inventory, name='admin_inventory'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
