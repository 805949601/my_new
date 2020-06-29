from django.db import models

# Create your models here.
from django.db import models

from utils.models import ModelBase


class Tag(ModelBase):
    """
    """

    name = models.CharField(max_length=64, verbose_name="标签名", help_text="标签名")

    class Meta:
        ordering = ['-update_time', '-id']
        db_table = "tb_tag"  # 指明数据库表名
        verbose_name = "新闻标签"  # 在admin站点中显示的名称
        verbose_name_plural = verbose_name  # 显示的复数名称

    def __str__(self):
        return self.name


class News(ModelBase):
    """
    """
    title = models.CharField(max_length=150, verbose_name="标题", help_text="标题")
    digest = models.CharField(max_length=200, verbose_name="摘要", help_text="摘要")
    content = models.TextField(verbose_name="内容", help_text="内容")
    clicks = models.IntegerField(default=0, verbose_name="点击量", help_text="点击量")
    image_url = models.URLField(default="", verbose_name="图片url", help_text="图片url")
    tag = models.ForeignKey('Tag', on_delete=models.SET_NULL, null=True)#一对多的外键写在少的一方
    author = models.ForeignKey('user.Users', on_delete=models.SET_NULL, null=True) #models.SET_NULL即删除时候置空

    class Meta:
        ordering = ['-update_time', '-id']
        db_table = "tb_news"  # 指明数据库表名
        verbose_name = "新闻"  # 在admin站点中显示的名称
        verbose_name_plural = verbose_name  # 显示的复数名称

    def __str__(self):
        return self.title


class Comments(ModelBase):
    """
    """
    content = models.TextField(verbose_name="内容", help_text="内容")
    author = models.ForeignKey('user.Users', on_delete=models.SET_NULL, null=True)
    news = models.ForeignKey('News', on_delete=models.CASCADE)
    parent = models.ForeignKey('self',on_delete=models.CASCADE,null=True,blank=True)#无限添加子评论，自己是自己的外键


    class Meta:
        ordering = ['-update_time', '-id']
        db_table = "tb_comment"  # 指明数据库表名
        verbose_name = "评论"  # 在admin站点中显示的名称
        verbose_name_plural = verbose_name  # 显示的复数名称

    def to_dict_data(self):
        comment_dict = {
            'news_id': self.news.id,
            'content_id': self.id,
            'content': self.content,
            'author': self.author.username,
            'update_time': self.update_time.strftime('%Y年%m月%d日 %H:%M'),

            'parent': self.parent.to_dict_data() if self.parent else None,
        }
        return comment_dict

    def __str__(self):
        return '<评论{}>'.format(self.id)


class HotNews(ModelBase):

    PRI_CHOICES=[
        (1,'第一级'),
        (2,'第二级'),
        (3,'第三级')

    ]
    news = models.OneToOneField('News', on_delete=models.CASCADE)
    priority = models.IntegerField(choices=PRI_CHOICES,verbose_name="优先级", help_text="优先级")

    class Meta:
        ordering = ['-update_time', '-id']
        db_table = "tb_hot"  # 指明数据库表名
        verbose_name = "热门新闻"  # 在admin站点中显示的名称
        verbose_name_plural = verbose_name  # 显示的复数名称

    def __str__(self):
        return '<热门新闻{}>'.format(self.id)


class Banner(ModelBase):
    """
    """

    PRI_CHOICES=[
        (1,'第一级'),
        (2,'第二级'),
        (3,'第三级'),
        (4,'第四级'),
        (5,'第五级'),
        (6,'第六级'),

    ]
    image_url = models.URLField(verbose_name="轮播图url", help_text="轮播图url")
    priority = models.IntegerField(choices=PRI_CHOICES,default=6,verbose_name="优先级", help_text="优先级")
    news = models.OneToOneField('News', on_delete=models.CASCADE)

    class Meta:
        ordering = ['priority', '-update_time', '-id']
        db_table = "tb_banner"  # 指明数据库表名
        verbose_name = "轮播图"  # 在admin站点中显示的名称
        verbose_name_plural = verbose_name  # 显示的复数名称

    def __str__(self):
        return '<轮播图{}>'.format(self.id)

#
# class Course(object):
#     pass