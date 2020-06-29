from django.urls import path,re_path
from . import views
app_name = 'verifications'
urlpatterns = [
    path('image_codes/<uuid:image_id>/', views.Image_code.as_view(),name='Image_code'),
    re_path('username/(?P<username>\w{5,20})/', views.UsernameView.as_view(), name='username'),
    re_path('mobiles/(?P<mobile>1[3-9]\d{9})/', views.MobileView.as_view(), name='mobile'),
    path('sms_code/',views.Sms_code.as_view(),name='sms_code'),
]