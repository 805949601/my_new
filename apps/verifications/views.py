import random

from django.shortcuts import render
from django_redis import get_redis_connection
from utils.captcha.captcha import captcha
from . import forms
# Create your views here.
from django.views import View
from django.http import HttpResponse,JsonResponse
from user.models import Users
import logging
import json
from utils.yuntongxun.sms import CCP
from celery_tasks.sms import task as sms_task

logger = logging.getLogger('django')
from utils.res_code import to_json_data, error_map, Code


class Image_code(View):
    """
    1. 图形验证保存到数据库
        链接数据库
        保存
        hash string set zset list
    """

    def get(self, request, image_id):
        text, image = captcha.generate_captcha()
        con_redis = get_redis_connection('verify_codes')
        redis_key = 'img_{}'.format(image_id)
        con_redis.setex(redis_key, 300, text)
        logger.info('图片验证码：{}'.format(text))
        return HttpResponse(content=image, content_type='image/jpg')


class UsernameView(View):

    def get(self, request, username):
        """

        route:username/(?<username>\w[5,20])/
            \w 匹配字母 数字 下划线
            {"errno":"0","errmsg":"","data":{
            "username":"表单输入的名字",
            "count":0   2
            }}
        ：return json object

        :param request:
        :param username:
        :return:
        """
        count = Users.objects.filter(username=username).count()

        data = {
            'username': username,
            'count': count
        }
        # return JsonResponse({'data':data})#可以转换成json格式
        return to_json_data(data=data)


class MobileView(View):
    """
    mobile
    route:mobiles/(?P<mobile>1[3-9]\d{9})/
    """

    def get(self, request, mobile):
        # mobile = request.GET.get('mobile')
        data = {
            'count': Users.objects.filter(mobile=mobile).count(),
            'mobile': mobile
        }
        return to_json_data(data=data)


class Sms_code(View):
    """
    1. 校验图片是否正确
    2. 判断60秒是否有发送记录
    3. 构造6位短信验证码
    4. 保存到数据库
    5. 发送短信
    """

    def post(self, request):
        """mobile text image_code_id"""
        json_str = request.body
        if not json_str:
            return to_json_data(errno=Code.PARAMERR, errmsg='参数为空')
        dict_data = json.loads(json_str)
        form = forms.FromRegister(data=dict_data)

        if form.is_valid():
            mobile = form.cleaned_data.get('mobile')
            # 生产六位短信验证码
            sms_num = '%06d' % random.randint(0,999999)

            # 构建外键
            con_redis = get_redis_connection('verify_codes')
            # 短信键 5分钟 sms_num
            sms_text_flag = 'sms_{}'.format(mobile).encode('utf8')
            # 过期时间
            sms_flag_fmt = 'sms_flag{}'.format(mobile).encode('utf8')
            # 存
            con_redis.setex(sms_text_flag, 300, sms_num)
            con_redis.setex(sms_flag_fmt, 60, 1)  # 过期时间 1—判断标致

            # 发送短信
            logger.info('短信验证码:{}'.format(sms_num))
            # logging.info('发送短信验证码正常[moblie:%s,sms_num:%s]' % (mobile, sms_num))
            # return to_json_data(errmsg='短信验证码发送成功')
            # try:
            #     result = CCP().send_template_sms(mobile,[sms_num,5],1)
            # except Exception as e:
            #     logger.error('发送短信异常[mobile:%s message:%s]'%(mobile,e))
            #     return to_json_data(errno=Code.SMSERROR, errmsg=error_map[Code.SMSERROR])
            # else:
            #     if result == 0:
            #         logger.info('发送短信验证码成功[mobile:%s sms_code:%s]'%(mobile, sms_num))
            #         return to_json_data(errmsg='短信验证码发送成功')
            #     else:
            #         logger.warning('发送短信失败 [mobile:%s]' % mobile)
            #         return to_json_data(errno=Code.SMSFAIL,errmsg=error_map[
            #             Code.SMSFAIL])


            #使用celery异步发送短信
            expires = 300
            sms_task.send_sms_code.delay(mobile,sms_num,expires,1)
            return to_json_data(errmsg="短信验证成功")

        else:
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)
            return to_json_data(errno=Code.PARAMERR, errmsg=err_msg_str)
