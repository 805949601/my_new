
from django.shortcuts import render,redirect
# Create your views here.
from django.urls import reverse
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie

from utils.res_code import to_json_data,Code,error_map
import json
from .froms import RegisterForm,LoginForm
from .models import Users
from django.contrib.auth import login,logout
from django.utils.decorators import method_decorator


class Register(View):
    def get(self,request):
        return render(request,'users/register.html')

    def post(self, request):
        """
        用户名
        密码
        确认密码
        mobile
        短信验证码
        :param request:
        :return:
        """
        json_str = request.body
        if not json_str:
            return to_json_data(errno=Code.PARAMERR, errmsg=[error_map[Code.PARAMERR]])
        data_dict = json.loads(json_str.decode('utf8'))  #json转字典类型
        form = RegisterForm(data=data_dict)

        if form.is_valid(): #拿个表单具体去校验。
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            mobile = form.cleaned_data.get('mobile')
            user = Users.objects.create_user(username=username, password=password, mobile=mobile)
            login(request, user)  #有保存session信息
            return to_json_data(errmsg='恭喜您注册成功')

        else:
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)  # 拼接错误信息为一个字符串
            return to_json_data(errno=Code.PARAMERR, errmsg=err_msg_str)



class Login(View):
    # @method_decorator(ensure_csrf_cookie)
    def get(self,request):
        return render(request,'users/login.html')

    def post(self,request):
        json_str = request.body
        if not json_str:
            return to_json_data(errno=Code.PARAMERR,errmsg=error_map[Code.PARAMERR])
        data_dict = json.loads(json_str)
        form = LoginForm(data=data_dict,request=request)

        if form.is_valid():
            return to_json_data(errmsg="恭喜您，登录成功！")
        else:
            # 定义一个错误信息列表
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)  # 拼接错误信息为一个字符串

            return to_json_data(errno=Code.PARAMERR, errmsg=err_msg_str)

class LogoutView(View):

    def get(self,request):
        logout(request)
        return redirect(reverse('user:login'))

