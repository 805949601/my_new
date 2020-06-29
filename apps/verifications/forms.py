from django import forms
from django.core.validators import RegexValidator
from django_redis import get_redis_connection

mobile_validator = RegexValidator(r"^1[3-9]\d{9}$","手机号格式不正确")
class FromRegister(forms.Form):
    mobile = forms.CharField(max_length=11,min_length=11,validators=[mobile_validator],
                             error_messages={"max_length":"手机长度有误",
                                             "min_length":"手机长度有误",
                                             "required":"手机号不能为空"
                                             })
    image_code_id = forms.UUIDField(error_messages={'required':"图片UUID不能为空"})
    text = forms.CharField(max_length=4, min_length=4,
                             error_messages={"max_length": "验证码长度有误",
                                             "min_length": "验证码长度有误",
                                             "required": "验证码不能为空"
                                             })

    def clean(self):
        cleaned_data = super().clean() # super().clean() 可以跨越
        mobile = cleaned_data.get('mobile')
        img_uuid = cleaned_data.get("image_code_id")
        img_text = cleaned_data.get("text")

        #获取图片验证码
        con_redis = get_redis_connection(alias='verify_codes')

        #构建redis\
        img_key = 'img_{}'.format(img_uuid).encode('utf-8')
        image_code = con_redis.get(img_key)

        con_redis.delete(img_key)

        # if not image_code:
        #     real_image_code = None
        # else:
        #     real_image_code = image_code.decode('utf8')

        real_image_code = image_code.decode('utf8') if image_code else None

        #判断用户输入的验证码和数据库的验证码是否一致
        if img_text.upper() != real_image_code:
            raise forms.ValidationError('图形验证码校验失败')

        #校验60秒内是否有发送记录
        if con_redis.get('sms_flag_{}'.format(mobile)):
            raise forms.ValidationError("短信验证码获取频繁")
        return cleaned_data

