from django import forms
from news.models import News, Tag
from course.models import Course
from doc.models import Doc


class NewsPubForm(forms.ModelForm):
    """
    """
    image_url = forms.URLField(label='文章图片url',
                               error_messages={"required": "文章图片url不能为空"})
    tag = forms.ModelChoiceField(queryset=Tag.objects.only('id').filter(is_delete=False),
                                 error_messages={"required": "文章标签id不能为空", "invalid_choice": "文章标签id不存在", }
                                 )

    class Meta:
        model = News  # 与数据库模型关联
        # 需要关联的字段
        # exclude 排除
        fields = ['title', 'digest', 'content', 'image_url', 'tag']
        error_messages = {
            'title': {
                'max_length': "文章标题长度不能超过150",
                'min_length': "文章标题长度大于1",
                'required': '文章标题不能为空',
            },
            'digest': {
                'max_length': "文章摘要长度不能超过200",
                'min_length': "文章标题长度大于1",
                'required': '文章摘要不能为空',
            },
            'content': {
                'required': '文章内容不能为空',
            },
        }


class CoursePubForm(forms.ModelForm):
    """
    写表单认证
    """
    cover_url = forms.URLField(label='封面图',error_messages={"required":"图片不能为空"})
    video_url = forms.URLField(label='视频URL',error_messages={"required":'视频url不能为空'})

    #排除法,即不验证他们

    class Meta:
        model = Course
        exclude = ['is_delete','update_time','create_time']

        error_messages = {
            'title':{
                'max_length':'视频标题长度不能超过150',
                'min_length':'视频标题长度大于1',
                'required':''
            }

        }


class DocsPubForm(forms.ModelForm):
    """
    """
    image_url = forms.URLField(label='文档缩略图url',
                               error_messages={"required": "文档缩略图url不能为空"})

    file_url = forms.URLField(label='文档url',
                               error_messages={"required": "文档url不能为空"})

    class Meta:
        model = Doc  # 与数据库模型关联
        # 需要关联的字段
        # exclude 排除
        fields = ['title', 'desc', 'file_url', 'image_url']
        error_messages = {
            'title': {
                'max_length': "文档标题长度不能超过150",
                'min_length': "文档标题长度大于1",
                'required': '文档标题不能为空',
            },
            'desc': {
                'max_length': "文档描述长度不能超过200",
                'min_length': "文档描述长度大于1",
                'required': '文档描述不能为空',
            },
        }