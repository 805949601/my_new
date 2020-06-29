from django.http import Http404
from django.shortcuts import render
import logging

# Create your views here.
from django.shortcuts import render
from django.views import View

from . import models
logger = logging.getLogger("django")

def course_list(request):
    courses = models.Course.objects.only('title', 'cover_url', 'teacher__positional_title').filter(is_delete=False)
    return render(request, 'course/course.html', locals())

class CourseDetail(View):
    def get(self,request,course_id):
        try:
            course = models.Course.objects.only('title','cover_url','video_url','profile','outline',
                                   'teacher__name','teacher__positional_title','teacher__avatar_url','teacher__profile').select_related('teacher').filter(is_delete=False,id=course_id).first()
        except models.Course.DoesNotExist as e:
            logger.info('当前课程出现异常{}'.format(e))
            raise Http404('课程不存在')
        return render(request,'course/course_detail.html',locals())