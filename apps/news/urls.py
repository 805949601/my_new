from django.urls import path
from . import views

app_name='news'
urlpatterns = [
    path('', views.Index.as_view(),name='index'),
    path('<int:id>/', views.demo),
    path('news/', views.NewsListView.as_view(), name='news_list'),
    path('news/<int:news_id>/',views.News_detail.as_view(),name='news_detail'),
    path('news/banners/',views.Banner_View.as_view(),name='news_banner'),
    path('news/<int:news_id>/comments/',views.CommentView.as_view(),name='comments'),#路由与js保持一致
    path('search/',views.Search(),name='search')
]