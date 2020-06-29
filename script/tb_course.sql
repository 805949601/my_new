insert into tb_teachers (name, positional_title, profile, avatar_url, create_time, update_time, is_delete) values
('蓝羽', 'python高级讲师', '课堂第一帅', '/media/c.jpg', now(), now(), 0);

insert into tb_course_category (name, create_time, update_time, is_delete) values
('数据分析', now(), now(), 0),
('深度学习', now(), now(), 0),
('机器学习', now(), now(), 0);

insert into tb_course (title, cover_url, video_url, duration, profile, outline, teacher_id, category_id, create_time, update_time, is_delete) values
('linux链接问题', 'https://python-django-my-news.cdn.bcebos.com/videoworks/mda-kd2mm0ycugbw1wd1/python_django_my_news/缩略图/linux连接问题.jpg', 'https://python-django-my-news.cdn.bcebos.com/videoworks/mda-kd2mm0ycugbw1wd1/python_django_my_news/源文件发布/linux连接问题.mp4', 3.16, '关于linux连接pycharm的最常见问题的简答 ', 'linux常见问题', 1, 2, now(), now(), 0),

('检查安装', 'https://python-django-my-news.cdn.bcebos.com/videoworks/mda-kd2mq8n9mqdfrnn4/python_django_my_news/缩略图/检查安装.jpg', 'https://python-django-my-news.cdn.bcebos.com/videoworks/mda-kd2mq8n9mqdfrnn4/python_django_my_news/源文件发布/检查安装.mp4', 1.56, '检查python安装有没有成功', '1. 检查视频安装有无成功 2. 发布任务', 1, 1, now(), now(), 0);
