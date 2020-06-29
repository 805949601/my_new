from datetime import datetime
from collections import OrderedDict
from urllib.parse import urlencode
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
# Create your view here.
import json,logging
from .forms import NewsPubForm,CoursePubForm,DocsPubForm
from my_news import settings
from utils.fastdfs.fdfs import FDFS_Client
from django.core.paginator import Paginator, EmptyPage
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views import View
from django.db.models import Count
from . import paginator_script
from news import models
from course import models as modelss
from utils.res_code import Code, error_map, to_json_data
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from doc import models as d_models
from django.contrib.auth.models import Group,Permission
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin

logger = logging.getLogger('django')
class IndexView(LoginRequiredMixin,View):
    """
    """
    login_url = 'user:login'
    redirect_field_name = 'next'
    def get(self, request):
        return render(request, 'admin/index/index.html')


class TagsManageView(PermissionRequiredMixin,View):
    permission_required = ('news.view_tag','news.add_tag','news.delete_tag','news.change_tag')#news. 的那个news是指写模型类的apps名字
    raise_exception = True #你有查看的权限但是没有增删改的权限

    #下面函数的意思就是没有权限的情况下不能进行操作，有增删改操作才用
    def handle_no_permission(self):
        if self.request.method != 'GET':
            return to_json_data(errno=Code.PARAMERR,errmsg='没有操作权限')
        else:
            return super(TagsManageView,self).handle_no_permission()

    """
    """

    def get(self, request):
        """
        """
        tags = models.Tag.objects.values('id', 'name').annotate(num_news=Count('news')). \
            filter(is_delete=False).order_by('-num_news')
        # 在我们的博客侧边栏有分类列表，显示博客已有的全部文章分类。现在想在分类名后显示该分类下有多少篇文章，该怎么做呢？最优雅的方式就是使用 Django 模型管理器的 annotate 方法。
        return render(request, 'admin/news/tag_manage.html', locals())

    def post(self, request):
        """
        """
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data.decode('utf8'))
        tag_name = dict_data.get('name')
        if tag_name and tag_name.strip():
            #返回一个元祖，没有值就返回False并进行保存，如果有值就不保存，返回True
            tag_tuple = models.Tag.objects.get_or_create(name=tag_name)
            return to_json_data(errmsg="标签创建成功") if tag_tuple[-1] else \
                to_json_data(errno=Code.DATAEXIST, errmsg="标签名已存在")
        else:
            return to_json_data(errno=Code.PARAMERR, errmsg="标签名为空")

    def put(self, request, tag_id):#也是请求体，修改的时候用Put方法
        json_str = request.body

        if not json_str:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_str.decode('utf8'))
        tag_name = dict_data.get('name')
        tag = models.Tag.objects.only('id').filter(id=tag_id).first()
        if tag:
            if tag_name and tag_name.strip():
                if not models.Tag.objects.only('id').filter(name=tag_name).exists():
                    tag.name = tag_name
                    tag.save(update_fields=['name'])
                    return to_json_data(errmsg='标签更新成功')
                else:
                    return to_json_data(errno=Code.DATAEXIST, errmsg='标签名已存在')
            else:
                return to_json_data(errno=Code.PARAMERR, errmsg='标签名为空')

        else:
            return to_json_data(errno=Code.PARAMERR, errmsg='需要更新的标签不存在')

    def delete(self, request, tag_id):
        tag = models.Tag.objects.only('id').filter(id=tag_id).first()
        if tag:
            tag.delete()
            return to_json_data(errmsg="标签更新成功")
        else:
            return to_json_data(errno=Code.NODATA, errmsg="需要删除的标签不存在")


class HotNewsManageView(PermissionRequiredMixin,View):
    """
    """
    permission_required = ('news.view_hotnews') #news. 的那个news是指写模型类的apps名字
    raise_exception = True #你有查看的权限但是没有增删改的权限

    def get(self, request):
        hot_news = models.HotNews.objects.select_related('news__tag'). \
                       only('news_id', 'news__title', 'news__tag__name', 'priority'). \
                       filter(is_delete=False).order_by('priority', '-news__clicks')[0:3]

        return render(request, 'admin/news/hot_news.html', locals())


class HotNewsEditView(PermissionRequiredMixin,View):
    permission_required = ('news.delete_hotnews','news.change_hotnews')#news. 的那个news是指写模型类的apps名字
    raise_exception = True #你有查看的权限但是没有增删改的权限

    #下面函数的意思就是没有权限的情况下不能进行操作，有增删改操作才用
    def handle_no_permission(self):
        if self.request.method != 'GET':
            return to_json_data(errno=Code.PARAMERR,errmsg='没有操作权限')
        else:
            return super().handle_no_permission()


    def delete(self, request, hotnews_id):
        hotnews = models.HotNews.objects.only('id').filter(id=hotnews_id).first()
        if hotnews:
            hotnews.is_delete = True
            hotnews.save(update_fields=['is_delete'])
            return to_json_data(errmsg="热门文章删除成功")
        else:
            return to_json_data(errno=Code.PARAMERR, errmsg="需要删除的热门文章不存在")

    def put(self, request, hotnews_id):
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        # 将json转化为dict
        dict_data = json.loads(json_data.decode('utf8'))

        try:
            priority = int(dict_data.get('priority'))
            priority_list = [i for i, _ in models.HotNews.PRI_CHOICES] #字典推导式，i 代表1，_代表value的值不需要。
            if priority not in priority_list:
                return to_json_data(errno=Code.PARAMERR, errmsg='热门文章的优先级设置错误')
        except Exception as e:
            logger.info('热门文章优先级异常：\n{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='热门文章的优先级设置错误')

        hotnews = models.HotNews.objects.only('id').filter(id=hotnews_id).first()
        if not hotnews:
            return to_json_data(errno=Code.PARAMERR, errmsg="需要更新的热门文章不存在")

        if hotnews.priority == priority:
            return to_json_data(errno=Code.PARAMERR, errmsg="热门文章的优先级未改变")

        hotnews.priority = priority
        hotnews.save(update_fields=['priority'])
        return to_json_data(errmsg="热门文章更新成功")


class HotNewsAddView(PermissionRequiredMixin,View):
    """
    route: /admin/hotnews/add/
    """
    permission_required = ('news.add_hotnews')  # news. 的那个news是指写模型类的apps名字
    raise_exception = True  # 你有查看的权限但是没有增删改的权限

    # 下面函数的意思就是没有权限的情况下不能进行操作，有增删改操作才用
    def handle_no_permission(self):
        if self.request.method != 'GET':
            return to_json_data(errno=Code.PARAMERR, errmsg='没有操作权限')
        else:
            return super().handle_no_permission()

    def get(self, request):
        tags = models.Tag.objects.values('id', 'name').annotate(num_news=Count('news')). \
            filter(is_delete=False).order_by('-num_news', 'update_time') #Count（）里面填与你请求的外键的模型类的名称
        # 优先级列表
        # priority_list = {K: v for k, v in models.HotNews.PRI_CHOICES}
        priority_dict = OrderedDict(models.HotNews.PRI_CHOICES)#将列表转化为字典形式

        return render(request, 'admin/news/hot_news_add.html', locals())

    def post(self, request):
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        # 将json转化为dict
        dict_data = json.loads(json_data.decode('utf8'))

        try:
            news_id = int(dict_data.get('news_id'))
        except Exception as e:
            logger.info('前端传过来的文章id参数异常：\n{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='参数错误')

        if not models.News.objects.filter(id=news_id).exists():
            return to_json_data(errno=Code.PARAMERR, errmsg='文章不存在')

        try:
            priority = int(dict_data.get('priority'))
            priority_list = [i for i, _ in
                                     models.HotNews.PRI_CHOICES]  # 推导式，i 代表1，_代表value的值不需要。_list = [i for i, _ in models.HotNews.PRI_CHOICES]
            if priority not in priority_list:
                return to_json_data(errno=Code.PARAMERR, errmsg='热门文章的优先级设置错误')
        except Exception as e:
            logger.info('热门文章优先级异常：\n{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='热门文章的优先级设置错误')

        # 创建热门新闻
        hotnews_tuple = models.HotNews.objects.get_or_create(news_id=news_id)
        hotnews, is_created = hotnews_tuple
        hotnews.priority = priority  # 修改优先级
        hotnews.save(update_fields=['priority'])
        return to_json_data(errmsg="热门文章创建成功")

#获取标签
class NewsByTagIdView(View):
    """
    route: /admin/tags/<int:tag_id>/news/
    """

    def get(self, request, tag_id):
        newses = models.News.objects.values('id', 'title').filter(is_delete=False, tag_id=tag_id)
        news_list = [i for i in newses]#把对象提取出来成为推导式

        return to_json_data(data={
            'news': news_list
        })

#文章管理

from news import models


class NewsManageView(PermissionRequiredMixin,View):
    """
    """
    permission_required = ('news.view_news')  # news. 的那个news是指写模型类的apps名字
    raise_exception = True  # 你有查看的权限但是没有增删改的权限

    def get(self, request):
        tags = models.Tag.objects.only('id', 'name').filter(is_delete=False)
        newses = models.News.objects.only('id', 'title', 'author__username', 'tag__name', 'update_time').\
            select_related('author', 'tag').filter(is_delete=False)

        # 通过时间进行过滤
        try:
            start_time = request.GET.get('start_time', '')
            start_time = datetime.strptime(start_time, '%Y/%m/%d') if start_time else ''
                        #strptime就是把字符串格式转化为日期格式

            end_time = request.GET.get('end_time', '')
            end_time = datetime.strptime(end_time, '%Y/%m/%d') if end_time else ''
        except Exception as e:
            logger.info("用户输入的时间有误：\n{}".format(e))
            start_time = end_time = ''

        if start_time and not end_time:
            newses = newses.filter(update_time__gte=start_time)
            #gte 大于等于 lte小于等于
        if end_time and not start_time:
            newses = newses.filter(update_time__lte=end_time)

        if start_time and end_time:
            newses = newses.filter(update_time__range=(start_time, end_time))

        # 通过title进行过滤
        title = request.GET.get('title', '')
        if title:
            newses = newses.filter(title__icontains=title)
            #忽略查询 的大小写

        # 通过作者名进行过滤
        author_name = request.GET.get('author_name', '')
        if author_name:
            newses = newses.filter(author__username__icontains=author_name)

        # 通过标签id进行过滤
        try:
            tag_id = int(request.GET.get('tag_id', 0))
        except Exception as e:
            logger.info("标签错误：\n{}".format(e))
            tag_id = 0
        newses = newses.filter(is_delete=False, tag_id=tag_id) or \
               newses.filter(is_delete=False)
             #怕程序出故障

        # 获取第几页内容
        try:
            page = int(request.GET.get('page', 1))
        except Exception as e:
            logger.info("当前页数错误：\n{}".format(e))
            page = 1
        paginator = Paginator(newses, 8)
        try:
            news_info = paginator.page(page)
        except EmptyPage:
            # 若用户访问的页数大于实际页数，则返回最后一页数据
            logging.info("用户访问的页数大于总页数。")
            news_info = paginator.page(paginator.num_pages)

        paginator_data = paginator_script.get_paginator_data(paginator, news_info)

        start_time = start_time.strftime('%Y/%m/%d') if start_time else ''
        end_time = end_time.strftime('%Y/%m/%d') if end_time else ''
        context = {
            'news_info': news_info,
            'tags': tags,
            'paginator': paginator,
            'start_time': start_time,
            "end_time": end_time,
            "title": title,
            "author_name": author_name,
            "tag_id": tag_id,
            "other_param": urlencode({
                "start_time": start_time,
                "end_time": end_time,
                "title": title,
                "author_name": author_name,
                "tag_id": tag_id,
            })
        }
        context.update(paginator_data)
        return render(request, 'admin/news/new_manage.html', context=context)


class NewsEditView(PermissionRequiredMixin,View):
    permission_required = ('news.delete_news', 'news.change_news')  # news. 的那个news是指写模型类的apps名字
    raise_exception = True  # 你有查看的权限但是没有增删改的权限

    # 下面函数的意思就是没有权限的情况下不能进行操作，有增删改操作才用
    def handle_no_permission(self):
        if self.request.method != 'GET':
            return to_json_data(errno=Code.PARAMERR, errmsg='没有操作权限')
        else:
            return super().handle_no_permission()

    def get(self, request, news_id):
        news = models.News.objects.filter(is_delete=False, id=news_id).first()
        if news:
            tags = models.Tag.objects.only('id', 'name').filter(is_delete=False)
            context = {
                "news": news,
                "tags": tags
            }
            return render(request, 'admin/news/news_pub.html', context=context)
        else:
            raise Http404('需要更新的文章不存在')

    def delete(self, request, news_id):
        news = models.News.objects.only('id').filter(id=news_id,is_delete=False).first()
        if news:
            news.is_delete = True
            news.save(update_fields=['is_delete'])
            return to_json_data(errmsg='文章删除成功')
        else:
            return to_json_data(errno=Code.PARAMERR, errmsg='需要删除的文章不存在')

    def put(self, request, news_id):
        news = models.News.objects.only('id').filter(id=news_id).first()
        if not news:
            return to_json_data(errno=Code.NODATA, errmsg='需要更新的文章不存在')

        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data.decode('utf8'))
        form = NewsPubForm(data=dict_data)
        if form.is_valid():
            news.title = form.cleaned_data.get('title')
            news.digest = form.cleaned_data.get('digest')
            news.content = form.cleaned_data.get('content')
            news.image_url = form.cleaned_data.get('image_url')
            news.tag = form.cleaned_data.get('tag')
            news.save()
            return to_json_data(errmsg='文章更新成功')
        else:
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)
            return to_json_data(errno=Code.PARAMERR, errmsg=err_msg_str)

@method_decorator(csrf_exempt,name='dispatch') #免除csrf验证
class NewsUploadImage(View):
    def post(self, request):
        image_file = request.FILES.get('image_file')  # 2018.png

        if not image_file:
            logger.info('获取图片失败')
            return to_json_data(errno=Code.NODATA, errmsg='获取图片失败')
        if image_file.content_type not in ('image/jpeg', 'image/png', 'image/gif'):
            return to_json_data(errno=Code.DATAERR, errmsg='不能上传非图片文件')

        try:
            image_ext_name = image_file.name.split('.')[-1]
        except Exception as e:
            logger.info('图片后缀名异常：{}'.format(e))
            image_ext_name = 'jpg'
        try:
            upload_res = FDFS_Client.upload_by_buffer(image_file.read(), file_ext_name=image_ext_name)
        except Exception as e:
            logger.error('图片上传异常{}'.format(e))
            return to_json_data(errno=Code.UNKOWNERR, errmsg='图片上传异常')
        else:
            if upload_res.get('Status') != 'Upload successed.':
                logger.info('图片上传到fdfs失败')
                return to_json_data(errno=Code.UNKOWNERR, errmsg='图片上传失败')
            else:
                image_name = upload_res.get('Remote file_id')
                image_url = settings.FDFS_URL + image_name
                return to_json_data(data={'image_url': image_url} ,errmsg='图片上传成功')


@method_decorator(csrf_exempt,name='dispatch') #免除csrf验证
class MarkDownUploadImage(View):
    def post(self, request):
        image_file = request.FILES.get('editormd-image-file')  # 记得这个不要写错啦,这个是文件名字，在php的某文件里看，不是js文件
        if not image_file:
            logger.info('从前端获取图片失败')
            return JsonResponse({'success': 0, 'message': '从前端获取图片失败'})

        if image_file.content_type not in ('image/jpeg', 'image/png', 'image/gif'):
            return JsonResponse({'success': 0, 'message': '不能上传非图片文件'})

        try:  # jpg
            image_ext_name = image_file.name.split('.')[-1]  # 切割后返回列表取最后一个元素尾缀
        except Exception as e:
            logger.info('图片拓展名异常：{}'.format(e))
            image_ext_name = 'jpg'

        try:
            upload_res = FDFS_Client.upload_by_buffer(image_file.read(), file_ext_name=image_ext_name)
        except Exception as e:
            logger.error('图片上传出现异常：{}'.format(e))
            return JsonResponse({'success': 0, 'message': '图片上传异常'})
        else:
            if upload_res.get('Status') != 'Upload successed.':
                logger.info('图片上传到FastDFS服务器失败')
                return JsonResponse({'success': 0, 'message': '图片上传到服务器失败'})
            else:
                image_name = upload_res.get('Remote file_id')
                image_url = settings.FDFS_URL + image_name
                return JsonResponse({'success': 1, 'message': '图片上传成功', 'url': image_url})


#文章发布
class NewsPub(PermissionRequiredMixin,View):
    permission_required = ('news.add_news')  # news. 的那个news是指写模型类的apps名字
    raise_exception = True  # 你有查看的权限但是没有增删改的权限

    # 下面函数的意思就是没有权限的情况下不能进行操作，有增删改操作才用
    def handle_no_permission(self):
        if self.request.method != 'GET':
            return to_json_data(errno=Code.PARAMERR, errmsg='没有操作权限')
        else:
            return super().handle_no_permission()
    def get(self,request):

        tags = models.Tag.objects.only('id','name').filter(is_delete=False)
        return render(request,'admin/news/news_pub.html',locals())

    def post(self,request):
        """
        获取表单数据
        数据清洗/判断是否合法
        保存到数据库
        :param request:
        :return:
        """
        json_str= request.body
        if not json_str:
            to_json_data(errno=Code.PARAMERR,errmsg='参数错误')
        dict_data = json.loads(json_str)

        # 数据清洗
        form = NewsPubForm(data=dict_data)
        if form.is_valid():
            # 对于作者更新对于的新闻， 知道新闻是哪个作者发布的
            # 创建实例  不保存到数据库
            newss = form.save(commit=False)
            newss.author_id = request.user.id
            newss.save()
            return to_json_data(errmsg='文章发布成功')
        else:
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)
            return to_json_data(errno=Code.PARAMERR, errmsg=err_msg_str)


#轮播图管理
class BannerManageView(PermissionRequiredMixin,View):
    permission_required = ('news.view_banner')  # news. 的那个news是指写模型类的apps名字
    raise_exception = True  # 你有查看的权限但是没有增删改的权限

    def get(self, request):
        priority_dict = OrderedDict(models.Banner.PRI_CHOICES)
        banners = models.Banner.objects.only('id','image_url', 'priority').filter(is_delete=False)
        return render(request, 'admin/news/news_banner.html', locals())

#轮播图编辑
@method_decorator(csrf_exempt,name='dispatch')
class BannerEditView(PermissionRequiredMixin,View):
    permission_required = ('news.delete_banner', 'news.change_banner')  # news. 的那个news是指写模型类的apps名字
    raise_exception = True  # 你有查看的权限但是没有增删改的权限

    # 下面函数的意思就是没有权限的情况下不能进行操作，有增删改操作才用
    def handle_no_permission(self):
        if self.request.method != 'GET':
            return to_json_data(errno=Code.PARAMERR, errmsg='没有操作权限')
        else:
            return super().handle_no_permission()
    def delete(self,request,banner_id):
        banner = models.Banner.objects.only('id').filter(id=banner_id).first()
        if  banner:
            banner.is_delete = True
            banner.save(update_fields=['is_delete'])
            return to_json_data(errmsg='轮播图删除成功！')
        else:
            return to_json_data(errno=Code.NODATA,errmsg='轮播图不存在')

    def put(self,request,banner_id):
        """
        1. 获取参数
        2. 校验参数
        3. 保存并返回
        :param request:
        :param banner_id:
        :return:
        """
        banner = models.Banner.objects.only('id').filter(id=banner_id).first()
        if not banner:
            return to_json_data(errno=Code.PARAMERR,errmsg='The rotation chart that needs to be updated does not exist')
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR,errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data.decode('utf8'))

        try:
            priority = int(dict_data['priority'])
            priority_list = [i for i,_ in models.Banner.PRI_CHOICES]
            if priority not in priority_list:
                return to_json_data(errno=Code.PARAMERR,errmsg='轮播图优先级设置错误')
        except Exception as e:
            logger.info('轮播图优先级异常\n{}'.format(e))
            return to_json_data(errno=Code.PARAMERR,errmsg='轮播图优先级设置错误')

        image_url = dict_data['image_url']
        if not image_url:
            return to_json_data(errno=Code.PARAMERR,errmsg='图片为空')
        if banner.priority == priority and banner.image_url == image_url:
            return to_json_data(errno=Code.PARAMERR,errmsg='轮播图优先级未更改')

        banner.priority = priority
        banner.image_url = image_url
        banner.save(update_fields=['priority','image_url'])
        return to_json_data(errmsg='轮播图更新成功')


#新增轮播图
@method_decorator(csrf_exempt,name='dispatch')
class BannerAddView(PermissionRequiredMixin,View):
    permission_required = ('news.add_banner')  # news. 的那个news是指写模型类的apps名字
    raise_exception = True  # 你有查看的权限但是没有增删改的权限

    # 下面函数的意思就是没有权限的情况下不能进行操作，有增删改操作才用
    def handle_no_permission(self):
        if self.request.method != 'GET':
            return to_json_data(errno=Code.PARAMERR, errmsg='没有操作权限')
        else:
            return super().handle_no_permission()
    def get(self, request):
        tags = models.Tag.objects.values('id', 'name').annotate(num_news=Count('news')). \
            filter(is_delete=False).order_by('-num_news', 'update_time')
        # 优先级列表
        # priority_list = {K: v for k, v in models.Banner.PRI_CHOICES}
        priority_dict = OrderedDict(models.Banner.PRI_CHOICES)#列表元祖的组合变成字典类型。

        return render(request, 'admin/news/news_banner_add.html', locals())

    def post(self, request):
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        # 将json转化为dict
        dict_data = json.loads(json_data.decode('utf8'))
        #校验参数
        try:
            news_id = int(dict_data.get('news_id'))
        except Exception as e:
            logger.info('前端传过来的文章id参数异常：\n{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='参数错误')

        if not models.News.objects.filter(id=news_id).exists():
            return to_json_data(errno=Code.PARAMERR, errmsg='文章不存在')

        try:
            priority = int(dict_data.get('priority'))
            priority_list = [i for i, _ in models.Banner.PRI_CHOICES]
            if priority not in priority_list:
                return to_json_data(errno=Code.PARAMERR, errmsg='轮播图的优先级设置错误')
        except Exception as e:
            logger.info('轮播图优先级异常：\n{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='轮播图的优先级设置错误')

        # 获取轮播图url
        image_url = dict_data.get('image_url')
        if not image_url:
            return to_json_data(errno=Code.PARAMERR, errmsg='轮播图url为空')

        # 创建轮播图 obj true
        banners_tuple = models.Banner.objects.get_or_create(news_id=news_id)
        banner, is_created = banners_tuple

        banner.priority = priority
        banner.image_url = image_url
        banner.save(update_fields=['priority', 'image_url'])
        return to_json_data(errmsg="轮播图创建成功")

#课程管理
class CourseManageView(PermissionRequiredMixin,View):
    permission_required = ('course.view_course','course.view_coursecategory')  # news. 的那个news是指写模型类的apps名字
    raise_exception = True  # 你有查看的权限但是没有增删改的权限

    def get(self,request):
        courses = modelss.Course.objects.select_related('category', 'teacher'). \
            only('title', 'category__name', 'teacher__name').filter(is_delete=False)
        return render(request,'admin/course/course_manage.html',locals())

#课程编辑
class CourseEditView(PermissionRequiredMixin,View):
    permission_required = ('course.change_course','course.delete_course','course.change_coursecategory','course.delete_coursecategory')  # news. 的那个news是指写模型类的apps名字
    raise_exception = True  # 你有查看的权限但是没有增删改的权限

    # 下面函数的意思就是没有权限的情况下不能进行操作，有增删改操作才用
    def handle_no_permission(self):
        if self.request.method != 'GET':
            return to_json_data(errno=Code.PARAMERR, errmsg='没有操作权限')
        else:
            return super().handle_no_permission()
    def get(self, request, course_id):
        course = modelss.Course.objects.filter(is_delete=False, id=course_id).first()
        if course:
            teachers = modelss.Teacher.objects.only('name').filter(is_delete=False)
            categories = modelss.CourseCategory.objects.only('name').filter(is_delete=False)
            return render(request, 'admin/course/course_pub.html', locals())
        else:
            Http404('需要更新的课程不存在')

    def delete(self, request, course_id):
        course = modelss.Course.objects.only('id').filter(is_delete=False, id=course_id).first()
        if course:
            course.is_delete = True
            course.save(update_fields=['is_delete'])
            return to_json_data(errmsg='课程删除成功')
        else:
            return to_json_data(errno=Code.PARAMERR, errmsg='更新的课程不存在')

    def put(self, request, course_id):
        course = modelss.Course.objects.filter(is_delete=False, id=course_id).first()
        if not course:
            return to_json_data(errno=Code.NODATA, errmsg='需要更新的课程不存在')
        json_str = request.body
        if not json_str:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_str.decode('utf8'))
        form = CoursePubForm(data=dict_data)
        if form.is_valid():
            for attr, value in form.cleaned_data.items():
                setattr(course, attr, value)
            course.save()
            return to_json_data(errmsg='课程更新成功')
        else:
            # 定义一个错误信息列表
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)  # 拼接错误信息为一个字符串
            return to_json_data(errno=Code.PARAMERR, errmsg=err_msg_str)


#课程发布
class CoursePubView(PermissionRequiredMixin,View):
    permission_required = ('course.add_course', 'course.add_coursecategory')  # news. 的那个news是指写模型类的apps名字
    raise_exception = True  # 你有查看的权限但是没有增删改的权限

    # 下面函数的意思就是没有权限的情况下不能进行操作，有增删改操作才用
    def handle_no_permission(self):
        if self.request.method != 'GET':
            return to_json_data(errno=Code.PARAMERR, errmsg='没有操作权限')
        else:
            return super().handle_no_permission()
    def get(self,request):
        teachers = modelss.Teacher.objects.only('name').filter(is_delete=False)
        categories = modelss.CourseCategory.objects.only('name').filter(is_delete=False)
        return render(request,'admin/course/course_pub.html',locals())

    def post(self,request):
        json_str = request.body
        if not json_str:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        data_dict = json.loads(json_str.decode('utf8'))
        form = CoursePubForm(data=data_dict)
        if form.is_valid():
            course_instance = form.save(commit=False)
            course_instance.save()
            return to_json_data(errmsg='课程发布成功')
        else:
            # 定义一个错误信息列表
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)  # 拼接错误信息为一个字符串
            return to_json_data(errno=Code.PARAMERR, errmsg=err_msg_str)

#文档管理
class DocsManageView(PermissionRequiredMixin,View):
    permission_required = ('doc.view_doc')  # news. 的那个news是指写模型类的apps名字
    raise_exception = True  # 你有查看的权限但是没有增删改的权限

    def get(self, request):
        docs = d_models.Doc.objects.only('title', 'create_time').filter(is_delete=False)
        return render(request, 'admin/doc/docs_manage.html', locals())


#文档编辑
class DocEditView(PermissionRequiredMixin,View):
    permission_required = ('doc.change_doc', 'course.delete_doc')  # news. 的那个news是指写模型类的apps名字
    raise_exception = True  # 你有查看的权限但是没有增删改的权限

    # 下面函数的意思就是没有权限的情况下不能进行操作，有增删改操作才用
    def handle_no_permission(self):
        if self.request.method != 'GET':
            return to_json_data(errno=Code.PARAMERR, errmsg='没有操作权限')
        else:
            return super().handle_no_permission()

    def get(self,request,doc_id):
        doc = d_models.Doc.objects.only('id').filter(id=doc_id).first()
        if doc:
            return render(request,'admin/doc/doc_pub.html',locals())
        else:
            raise Http404('需要更新得文档不存在')

    def delete(self,request,doc_id):
        doc = d_models.Doc.objects.only('id').filter(id=doc_id).first()
        if doc:
            doc.is_delete=True
            doc.save(update_fields=['is_delete'])
            return to_json_data(errmsg='文档删除成功')
        else:
            to_json_data(errno=Code.PARAMERR,errmsg='需要删除的文档不存在')

    def put(self,request,doc_id):
        """
        1. 找到编辑的书籍
        2. 获取表单提交的书籍
        3. 清洗书籍
        4. 保存到数据库
        5. 返回
        :param request:
        :param doc_id:
        :return:
        """
        doc = d_models.Doc.objects.only('id').filter(id=doc_id).first()
        if not doc:
            return to_json_data(errno=Code.NODATA, errmsg='需要更新的文档不存在')
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        # 将json转化为dict
        dict_data = json.loads(json_data.decode('utf8'))

        form = DocsPubForm(data=dict_data)
        if form.is_valid():
            doc.title = form.cleaned_data.get('title')
            doc.desc = form.cleaned_data.get('desc')
            doc.file_url = form.cleaned_data.get('file_url')
            doc.image_url = form.cleaned_data.get('image_url')
            doc.save()
            return to_json_data(errmsg='文档更新成功')
        else:
            # 定义一个错误信息列表
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)  # 拼接错误信息为一个字符串

            return to_json_data(errno=Code.PARAMERR, errmsg=err_msg_str)


#上传文档借口
class DocsUploadFile(View):
    """route: /admin/doc/files/
    """

    def post(self, request):
        text_file = request.FILES.get('text_file')
        if not text_file:
            logger.info('从前端获取文件失败')
            return to_json_data(errno=Code.NODATA, errmsg='从前端获取文件失败')

        if text_file.content_type not in ('application/octet-stream', 'application/pdf',
                                          'application/zip', 'text/plain', 'application/x-rar'):
            return to_json_data(errno=Code.DATAERR, errmsg='不能上传非文本文件')

        try:
            text_ext_name = text_file.name.split('.')[-1]
        except Exception as e:
            logger.info('文件拓展名异常：{}'.format(e))
            text_ext_name = 'pdf'

        try:
            upload_res = FDFS_Client.upload_by_buffer(text_file.read(), file_ext_name=text_ext_name)
        except Exception as e:
            logger.error('文件上传出现异常：{}'.format(e))
            return to_json_data(errno=Code.UNKOWNERR, errmsg='文件上传异常')
        else:
            if upload_res.get('Status') != 'Upload successed.':
                logger.info('文件上传到FastDFS服务器失败')
                return to_json_data(Code.UNKOWNERR, errmsg='文件上传到服务器失败')
            else:
                text_name = upload_res.get('Remote file_id')
                text_url = settings.FDFS_URL + text_name
                return to_json_data(data={'text_file': text_url}, errmsg='文件上传成功')

#文档发布
class DocsPubView(PermissionRequiredMixin,View):
    """
    route: /admin/news/pub/
    """
    permission_required = ('doc.add_doc')  # news. 的那个news是指写模型类的apps名字
    raise_exception = True  # 你有查看的权限但是没有增删改的权限

    # 下面函数的意思就是没有权限的情况下不能进行操作，有增删改操作才用
    def handle_no_permission(self):
        if self.request.method != 'GET':
            return to_json_data(errno=Code.PARAMERR, errmsg='没有操作权限')
        else:
            return super().handle_no_permission()

    def get(self, request):

        return render(request, 'admin/doc/doc_pub.html', locals())

    def post(self, request):
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        # 将json转化为dict
        dict_data = json.loads(json_data.decode('utf8'))

        form = DocsPubForm(data=dict_data)
        if form.is_valid():
            docs_instance = form.save(commit=False)
            docs_instance.author_id = request.user.id
            docs_instance.save()
            return to_json_data(errmsg='文档创建成功')
        else:
            # 定义一个错误信息列表
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)  # 拼接错误信息为一个字符串

            return to_json_data(errno=Code.PARAMERR, errmsg=err_msg_str)

class GroupsManageView(PermissionRequiredMixin,View):
    """
    财务部 1 2 3 4
    人事 2 1 3 4
    行政
    开发
    route: /admin/groups/
    """
    permission_required = ('auth.view_group')  # news. 的那个news是指写模型类的apps名字
    raise_exception = True  # 你有查看的权限但是没有增删改的权限

    def get(self, request):

        groups = Group.objects.values('id', 'name').annotate(num_users=Count('user')).\
            order_by('-num_users', 'id')
        return render(request, 'admin/user/groups_manage.html', locals())


#用户组编辑
class GroupsEditView(PermissionRequiredMixin,View):
    permission_required = ('auth.change_group', 'auth.delete_group')  # news. 的那个news是指写模型类的apps名字
    raise_exception = True  # 你有查看的权限但是没有增删改的权限

    # 下面函数的意思就是没有权限的情况下不能进行操作，有增删改操作才用
    def handle_no_permission(self):
        if self.request.method != 'GET':
            return to_json_data(errno=Code.PARAMERR, errmsg='没有操作权限')
        else:
            return super().handle_no_permission()
    def get(self,request, group_id):

        group = Group.objects.filter(id=group_id).first()
        if group:
            permissions = Permission.objects.only('id').all()
            return render(request,'admin/user/groups_add.html',locals())
        else:
            raise Http404('需要更新的组不存在')


    def delete(self, request, group_id):
        group = Group.objects.filter(id=group_id).first()
        if group:
            group.permissions.clear()  # 清空权限
            group.delete()
            return to_json_data(errmsg="用户组删除成功")
        else:
            return to_json_data(errno=Code.PARAMERR, errmsg="需要删除的用户组不存在")

    def put(self, request, group_id):
        group = Group.objects.filter(id=group_id).first()
        if not group:
            return to_json_data(errno=Code.NODATA, errmsg='需要更新的用户组不存在')

        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        # 将json转化为dict
        dict_data = json.loads(json_data.decode('utf8'))

        # 取出组名，进行判断 ''就是默认为空（没有东西就是空），strip是去掉两边的空白
        group_name = dict_data.get('name', '').strip()
        if not group_name:
            return to_json_data(errno=Code.PARAMERR, errmsg='组名为空')

        if group_name != group.name and Group.objects.filter(name=group_name).exists():
            return to_json_data(errno=Code.DATAEXIST, errmsg='组名已存在')

        # 取出权限
        group_permissions = dict_data.get('group_permissions')#取到的是列表 如：[1,2,3,4,5,6]
        if not group_permissions:
            return to_json_data(errno=Code.PARAMERR, errmsg='权限参数为空')

        try:
            permissions_set = set(int(i) for i in group_permissions)#去重，要迭代一下，原来是个对象。
        except Exception as e:
            logger.info('传的权限参数异常：\n{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='权限参数异常')

        #数据库里的权限组
        all_permissions_set = set(i.id for i in Permission.objects.only('id'))
        if not permissions_set.issubset(all_permissions_set): #包不包含在内
            return to_json_data(errno=Code.PARAMERR, errmsg='有不存在的权限参数')

        existed_permissions_set = set(i.id for i in group.permissions.all())
        if group_name == group.name and permissions_set == existed_permissions_set:
            return to_json_data(errno=Code.DATAEXIST, errmsg='用户组信息未修改')
        # 设置权限
        for perm_id in permissions_set:
            p = Permission.objects.get(id=perm_id)
            group.permissions.add(p)
        group.name = group_name
        group.save()
        return to_json_data(errmsg='组更新成功！')

#用户组添加
class GroupsAddView(PermissionRequiredMixin,View):
    """
    route: /admin/groups/add/
    """
    permission_required = ('auth.add_group')  # news. 的那个news是指写模型类的apps名字
    raise_exception = True  # 你有查看的权限但是没有增删改的权限

    # 下面函数的意思就是没有权限的情况下不能进行操作，有增删改操作才用
    def handle_no_permission(self):
        if self.request.method != 'GET':
            return to_json_data(errno=Code.PARAMERR, errmsg='没有操作权限')
        else:
            return super().handle_no_permission()

    def get(self, request):
        permissions = Permission.objects.only('id').all()#在作为后端的当前页面只需要用id，传给后台的还是all

        return render(request, 'admin/user/groups_add.html', locals())

    def post(self, request):
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data.decode('utf8'))

        # 取出组名，进行判断
        group_name = dict_data.get('name', '').strip()
        if not group_name:
            return to_json_data(errno=Code.PARAMERR, errmsg='组名为空')

        one_group, is_created = Group.objects.get_or_create(name=group_name)
        if not is_created:
            return to_json_data(errno=Code.DATAEXIST, errmsg='组名已存在')

        # 取出权限
        group_permissions = dict_data.get('group_permissions')
        if not group_permissions:
            return to_json_data(errno=Code.PARAMERR, errmsg='权限参数为空')

        try:
            permissions_set = set(int(i) for i in group_permissions)
        except Exception as e:
            logger.info('传的权限参数异常：\n{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='权限参数异常')

        all_permissions_set = set(i.id for i in Permission.objects.only('id'))
        if not permissions_set.issubset(all_permissions_set):
            return to_json_data(errno=Code.PARAMERR, errmsg='有不存在的权限参数')

        # 设置权限
        for perm_id in permissions_set:
            p = Permission.objects.get(id=perm_id)
            one_group.permissions.add(p)

        one_group.save()
        return to_json_data(errmsg='组创建成功！')


from user.models import Users
#用户权限管理
class UsersManageView(PermissionRequiredMixin,View):
    """
    route: /admin/users/
    """
    permission_required = ('user.view_users')  # news. 的那个news是指写模型类的apps名字
    raise_exception = True  # 你有查看的权限但是没有增删改的权限

    def get(self, request):
        users = Users.objects.only('username', 'is_staff', 'is_superuser').filter(is_active=True)
        return render(request, 'admin/user/users_manage.html', locals())


class UserEditView(View):
    def get(self,request,user_id):
        user_instance = Users.objects.filter(id=user_id).first()
        if user_instance:
            groups = Group.objects.only('name').all()
            return render(request,'admin/user/user_edit.html',locals())
        else:
            raise Http404('更新得用户组不存在')


    def put(self,request,user_id):
        user_instance = Users.objects.filter(id=user_id).first()
        if not user_instance:
            return to_json_data(errno=Code.NODATA,errmsg='无数据')

        json_str = request.body
        if not json_str:
            return to_json_data(errno=Code.PARAMERR,errmsg=error_map[Code.NODATA])

        dict_data = json.loads(json_str)
        try:
            groups = dict_data.get('groups')
            is_superuser = int(dict_data['is_superuser'])  # 0
            is_staff = int(dict_data.get('is_staff'))   # 1
            is_active = int(dict_data['is_active'])  # 1
            params = (is_active,is_staff,is_superuser) #转元祖
            if not all([q in (0,1) for q in params]):#判断是否这两个变量值都在0和1里面
                return to_json_data(errno=Code.PARAMERR,errmsg='参数错误')
        except Exception as e:
            logger.info('从前端获取得用户参数错误{}'.format(e))
            return to_json_data(errno=Code.PARAMERR,errmsg='参数错误')

        try:
            if groups:
                groups_set = set(int(i) for i in groups)
            else:
                groups_set = set()
        except Exception as e:
            logger.info('用户组参数异常{}'.format(e))
            return to_json_data(errno=Code.PARAMERR,errmsg='用户组参数异常')

        # 组
        all_groups_set = set(i.id for i in Group.objects.only('id'))
        # 判断前台传得组是否在所有用户组里面
        if not groups_set.issubset(all_groups_set):
            return to_json_data(errno=Code.PARAMERR,errmsg='有不存在的用户组参数')

        gsa = Group.objects.filter(id__in=groups_set)  # [1,3,4]

        # 保存
        user_instance.groups.clear()
        user_instance.groups.set(gsa)
        user_instance.is_staff = bool(is_staff)
        user_instance.is_superuser = bool(is_superuser)
        user_instance.is_active = bool(is_active)
        user_instance.save()
        return to_json_data(errmsg='用户组更新成功')


    def delete(self,request,user_id):
        user_instance = Users.objects.filter(id=user_id).first()
        if user_instance:
            user_instance.groups.clear() # 去除用户组
            user_instance.user_permissions.clear()  # 清楚用户权限
            user_instance.is_active = False
            user_instance.save()
            return to_json_data(errmsg='用户删除成功')
        else:
            return to_json_data(errno=Code.PARAMERR,errmsg='需要删除的用户不存在')

