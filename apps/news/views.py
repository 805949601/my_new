from django.core.paginator import Paginator,PageNotAnInteger,EmptyPage
from django.http import HttpResponse,HttpResponseNotFound
from django.views import View
import logging
import json

from utils.res_code import to_json_data, Code, error_map
from . import models
from haystack.views import SearchView as _SearchView

# Create your views here.
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
logger = logging.getLogger('django')


@method_decorator(cache_page(timeout=120,cache='page_cache'),name='dispatch')
class Index(View):
    def get(self,request):
        tags = models.Tag.objects.only('name','id').filter(is_delete=False)
        hot_news = models.HotNews.objects.select_related('news').only('news__title', 'news__image_url', 'news_id').filter(
            is_delete=False).order_by('priority', '-news__clicks')[0:3]
        return render(request,'news/index.html',locals())

def demo(request,id):
    res = "<h1 style='color:red'> four in the morning %s </h1>"
    return HttpResponse(res % id)

#新闻列表
class NewsListView(View):
    def get(self,request):
        try:
            tag_id = int(request.GET.get('tag_id',0))
        except Exception as e:
            logger.error('页面或标签定义错误\n{}'.format(e))
            tag_id = 0
        try:
            page = int(request.GET.get('page', 1))
        except Exception as e:
            logger.error('页面或标签定义错误\n{}'.format(e))
            page = 1

        news_list = models.News.objects.select_related('tag','author').only('id','title','digest','image_url','author__username','update_time','tag__name').filter(is_delete=False)
        # news_list = models.News.objects.values('id', 'title', 'digest', 'image_url', 'update_time').annotate(tag_name=F('tag__name'), author=F('author__username'))
        news = news_list.filter(is_delete=False,tag_id=tag_id) or news_list.filter(is_delete=False)

        # 分页
        paginator = Paginator(news,3)
        try:
            news_info = paginator.page(page)
        except Exception as e:
            logger.info('给定的页码错误\n{}'.format(e))
            news_info = paginator.page(paginator.num_pages)

        news_info_list = []#因为原来发回的是查询及对象，所以要提出来，存列表里。
        for n in news_info:
            news_info_list.append({
            'id':n.id,
            'title':n.title,
             'digest':n.digest,
            'author':n.author.username,
            'image_url':n.image_url,
            'tag_name':n.tag.name,
            'update_time':n.update_time.strftime('%Y年%m月%d日 %H:%M')
        })
        data = {
            "total_pages":paginator.num_pages,
            "news":news_info_list
        }
        return to_json_data(data=data)

#新闻详情
class News_detail(View):
    def get(self, request, news_id):
        news = models.News.objects.select_related('tag', 'author').only('title', 'content', 'update_time', 'tag__name','author__username').filter(is_delete=False, id=news_id).first()

        comments = models.Comments.objects.select_related('author', 'parent').only('author__username', 'update_time','parent__update_time').filter(is_delete=False, news_id=news_id)
        comments_list = []
        for comm in comments:
            comments_list.append(comm.to_dict_data())

        if news:
            return render(request, 'news/news_detail.html', locals())
        else:
            return HttpResponseNotFound('PAGE NOT FOUND')

#轮播图
class Banner_View(View):
    def get(self, request):
        banners = models.Banner.objects.select_related('news').only('image_url', 'news__title', 'news_id').filter(is_delete=False)[0:6]
        # banners = models.Banner.objects.values("image_url").annotate(news_id=F("news_id")).filter(is_delete=False)[0:6] #如果这样就不需要列表化了可以直接传
        banner_info = []
        for i in banners:
            banner_info.append({
                'image_url': i.image_url,
                'news_id': i.news.id,  # ID 传给前台做轮播图详情页渲染
                'news_title': i.news.title
            })
        data = {
            'banners': banner_info
        }

        return to_json_data(data=data)#传输json格式就需要用列表，不用直接在模板渲染就不需要。

#新闻评论
class CommentView(View):
    """
       /news/<int:news_id>/comments/
       1, 判断用户是否已登录
       2，获取参数
       3，校验参数
       4，保存到数据库
       """
    def post(self,request,news_id):
        if not request.user.is_authenticated:
            return to_json_data(errno=Code.SESSIONERR, errmsg=error_map[Code.SESSIONERR])

        if not models.News.objects.only('id').filter(is_delete=False,id=news_id).exists():
            return to_json_data(errno=Code.PARAMERR, errmsg='新闻不存在！')

            # 2 获取参数
        json_data = request.body  # 一个汉字几个字节
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg='参数错误')

        dict_data = json.loads(json_data.decode('utf8'))#json变字典

        #  一级评论内容
        content = dict_data.get('content')#dict_data["content"]
        if not dict_data.get('content'):
            return to_json_data(errno=Code.PARAMERR, errmsg='评论内容不能为空！')

        # 回复评论 ---  二级评论
        parent_id = dict_data.get('parent_id')
        try:
            if parent_id:
                if not models.Comments.objects.only('id').filter(is_delete=False, id=parent_id, news_id=news_id).exists():
                    return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])

        except Exception as e:
            logging.info('前台传的parent_id 异常：\n{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='未知异常')

        # 保存数据库
        news_content = models.Comments()
        news_content.content = content
        news_content.news_id = news_id
        news_content.author = request.user
        news_content.parent_id = parent_id if parent_id else None
        news_content.save()
        return to_json_data(data=news_content.to_dict_data())#进行序列化返回

class Search(_SearchView):
    template = 'news/search.html'
    def create_response(self):
        # 接受前台用户输入的查询的值
        kw = self.request.GET.get('q','')#默认为空，看一下前端模板对应表达的name，这里是q，后面是默认为空
        # 如果没有值，显示热门新闻数据
        if  not kw:
            show = True
            host_news = models.HotNews.objects.select_related('news').only('news__title','news__image_url','news__id').filter(is_delete=False).order_by('priority','-news__clicks')#关联表的用两个_，或者表名.字段名
            # 参数  分页
            paginator = Paginator(host_news,5)
            try:
                page = paginator.page(int(self.request.GET.get('page',1)))
            # 假如传的不是整数
            except PageNotAnInteger:
                #  默认返回第一页
                page = paginator.page(1)
            except EmptyPage:
                page = paginator.page(paginator.num_pages)
                #返回当前页
            return render(self.request, self.template, locals())
        else:
            show = False
            return super().create_response()#自己调用自己super