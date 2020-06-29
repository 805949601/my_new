from django.urls import path
from . import views

app_name = 'course'

urlpatterns = [
    path('', views.course_list, name='course'),
    path('detail<int:course_id>/', views.CourseDetail.as_view(), name='course_detail'),
]