
$(function () {

  let $thumbnailUrl = $("#news-thumbnail-url");   // 获取缩略图输入框元素
  let $docFileUrl = $("#docs-file-url");    // 获取文档地址输入框元素

  // ================== 上传图片文件至服务器 ================
  let $upload_image_server = $("#upload-image-server");
  $upload_image_server.change(function () {
    // let _this = this;
    let file = this.files[0];   // 获取文件
    let oFormData = new FormData();  // 创建一个 FormData
    oFormData.append("image_file", file); // 把文件添加进去
    // 发送请求
    $.ajax({
      url: "/admin/news/images/",
      method: "POST",
      data: oFormData,
      processData: false,   // 定义文件的传输
      contentType: false,
    })
      .done(function (res) {
        if (res.errno === "0") {
          message.showSuccess("图片上传成功");
          let sImageUrl = res.data.image_url;
          $thumbnailUrl.val('');
          $thumbnailUrl.val(sImageUrl);

        } else {
          message.showError(res.errmsg)
        }
      })
      .fail(function () {
        message.showError('服务器超时，请重试！');
      });

  });
  // ================== 上传文件至服务器 ================
  let $upload_file_server = $("#upload-file-server");
  $upload_file_server.change(function () {
    // let _this = this;
    let file = this.files[0];   // 获取文件
    let oFormData = new FormData();  // 创建一个 FormData
    oFormData.append("text_file", file); // 把文件添加进去
    // 发送请求
    $.ajax({
      url: "/admin/docs/files/",
      method: "POST",
      data: oFormData,
      processData: false,   // 定义文件的传输
      contentType: false,
    })
      .done(function (res) {
        if (res.errno === "0") {
          message.showSuccess("文件上传成功");
          let sTextFileUrl = res.data.text_file;
          $docFileUrl.val('');
          $docFileUrl.val(sTextFileUrl);

        } else {
          message.showError(res.errmsg)
        }
      })
      .fail(function () {
        message.showError('服务器超时，请重试！');
      });

  });


  // ================== 发布文章 ================
  let $docsBtn = $("#btn-pub-news");
  $docsBtn.click(function () {
    // 判断文档标题是否为空
    let sTitle = $("#news-title").val();  // 获取文件标题
    if (!sTitle) {
        message.showError('请填写文档标题！');
        return
    }

    // 判断文档缩略图url是否为空
    let sThumbnailUrl = $thumbnailUrl.val();
    if (!sThumbnailUrl) {
      message.showError('请上传文档缩略图');
      return
    }

    // 判断文档描述是否为空
    let sDesc = $("#news-desc").val();  // 获取文档描述
    if (!sDesc) {
        message.showError('请填写文档描述！');
        return
    }

    // 判断文档url是否为空
    let sDocFileUrl = $docFileUrl.val();
    if (!sDocFileUrl) {
      message.showError('请上传文档或输入文档地址');
      return
    }

    // 获取docsId 存在表示更新 不存在表示发表
    let docsId = $(this).data("news-id");
    let url = docsId ? '/admin/docs/' + docsId + '/' : '/admin/docs/pub/';
    let data = {
      "title": sTitle,
      "desc": sDesc,
      "image_url": sThumbnailUrl,
      "file_url": sDocFileUrl,
    };

    $.ajax({
      // 请求地址
      url: url,
      // 请求方式
      type: docsId ? 'PUT' : 'POST',
      data: JSON.stringify(data),
      // 请求内容的数据类型（前端发给后端的格式）
      contentType: "application/json; charset=utf-8",
      // 响应数据的格式（后端返回给前端的格式）
      dataType: "json",
    })
      .done(function (res) {
        if (res.errno === "0") {
          if (docsId) {
            fAlert.alertNewsSuccessCallback("文档更新成功", '跳到文档管理页', function () {
              window.location.href = '/admin/docs/'
            });

          } else {
            fAlert.alertNewsSuccessCallback("文档发表成功", '跳到文档管理页', function () {
              window.location.href = '/admin/docs/'
            });
          }
        } else {
          fAlert.alertErrorToast(res.errmsg);
        }
      })
      .fail(function () {
        message.showError('服务器超时，请重试！');
      });

  });


  // get cookie using jQuery
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      let cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        let cookie = jQuery.trim(cookies[i]);
        // Does this cookie string begin with the name we want?
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
  }

  // Setting the token on the AJAX request
  $.ajaxSetup({
    beforeSend: function (xhr, settings) {
      if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
      }
    }
  });

});