from django.urls import path
from django.urls import path
from . import views


# app的名字
app_name = 'admin'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),  # 将这条路由命名为index
    path('tags/', views.TagsManageView.as_view(), name='tags'),
    path('tags/<int:tag_id>/',views.TagsManageView.as_view()),
    path('hotnews/', views.HotNewsManageView.as_view(), name='hot_manage'),
    path('hotnews/<int:hotnews_id>/', views.HotNewsEditView.as_view(), name='hotnews_edit'),
    path('hotnews/add/', views.HotNewsAddView.as_view(), name='hotnews_add'),
    path('tags/<int:tag_id>/news/', views.NewsByTagIdView.as_view(), name='news_by_tagid'),
    path('news/', views.NewsManageView.as_view(), name='news_manage'),
    path('news/<int:news_id>/', views.NewsEditView.as_view(), name='news_edit'),
    path('news/images/', views.NewsUploadImage.as_view(), name='upload_image'),
    path('markdown/images/', views.MarkDownUploadImage.as_view(), name='markdown_image_upload'),
    path('news/pub/',views.NewsPub.as_view(),name='news_pub'),
    path('banners/', views.BannerManageView.as_view(), name='banners_manage'),
    path('banners/<int:banner_id>/', views.BannerEditView.as_view(), name='banners_edit'),
    path('banners/add/', views.BannerAddView.as_view(), name='banners_add'),
    path('courses/',views.CourseManageView.as_view(),name='course_manage'),
    path('courses/<int:course_id>/',views.CourseEditView.as_view(),name='course_edit'),
    path('courses/pub/', views.CoursePubView.as_view(), name='course_pub'),
    path('docs/', views.DocsManageView.as_view(), name='docs_manage'),
    path('docs/<int:doc_id>/', views.DocEditView.as_view(), name='docs_edit'),
    path('docs/pub/', views.DocsPubView.as_view(), name='docs_pub'),
    path('docs/files/', views.DocsUploadFile.as_view(), name='upload_text'),
    path('groups/', views.GroupsManageView.as_view(), name='groups_manage'),
    path('groups/<int:group_id>/', views.GroupsEditView.as_view(), name='groups_edit'),
    path('groups/add/',views.GroupsAddView.as_view(),name='groups_add'),
    path('users/', views.UsersManageView.as_view(), name='users_manage'),
    path('users/<int:user_id>/', views.UserEditView.as_view(), name='users_edit'),

]