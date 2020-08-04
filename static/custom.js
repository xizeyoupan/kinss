$(function () {
    // 立刻刷新rss
    $("i.fa-refresh").click(function () {
        $.getJSON("/api/refresh", function (result) {
            if (result['state'] === 'success') {
                alert("正在抓取，请在几秒后刷新。");
            };
        });
    });

    //监听每个rss源的点击
    $('#navbar').on('click', 'li', function () {
        $('title').html($(this).text());
        show_article_list(this);
        scroll_to_end($("#page-wrapper"), 'top');
        // 删除文章操作按钮
        $("i.article").css("display", "none");
    });

    //监听每篇文章
    $('#page-content').on('click', 'li', function () {
        show_article_content($(this).attr('url'));
    });

    // 监听二维码按钮
    $('i.fa-qrcode').on('click', function () {
        $("#qrcode-wrapper").toggle();
    });

    //监听翻页按钮的点击
    $('i.nav-btn-up').on('click', function () {
        scroll_content($("#navbar"), 'up');
    });
    $('i.nav-btn-down').on('click', function () {
        scroll_content($("#navbar"), 'down');
    });
    $('i.page-btn-down').on('click', function () {
        scroll_content($("#page-wrapper"), 'down');
    });
    $('i.page-btn-up').on('click', function () {
        scroll_content($("#page-wrapper"), 'up');
    });
    $('i.top-btn').on('click', function () {
        scroll_to_end($("#page-wrapper"), 'top');
    });
    $('i.end-btn').on('click', function () {
        scroll_to_end($("#page-wrapper"), 'end');
    });
    $('i.next-btn').on('click', function () {
        show_article_content("next");
    });

    // 监听动作操作
    $("i.article.read,i.article.star").on('click', function () {
        change_state(this);
    });

    $("#navbtn").click(function () {
        $(this).toggleClass("fa-rotate-90");
        $("#navbar").toggle();

        if ($("#page-wrapper").css("max-width") === "100%") {
            $("#page-wrapper").css("max-width", "75%");
        } else if ($("#page-wrapper").css("max-width") === "75%") {
            $("#page-wrapper").css("max-width", "100%");
        };

    });

    if (location.pathname === "/article") {
        $("li.unread.btn").click();
    } else { };

});


function show_article_list(obj) {
    if ($(obj).attr('class').indexOf("btn") != -1) { //上面四个大类
        var url = $(obj).attr('eachurl')
    } else if ($(obj).attr('class').indexOf("each-feed") != -1) { //每个Feed源
        var url = "/api/article-list?type=each&url=" + encodeURIComponent($(obj).attr('eachurl'));
    } else { };

    $.getJSON(url, function (result) {
        if (result['state'] === 'success') {
            var html = '<ul>';
            for (var i in result["data"]) {
                var li = '<li url="' + result["data"][i].link + '">\
                <p class="feed-title">' + result["data"][i].feed_title + '</p>\
                <p class="article-title">' + result["data"][i].article_title + '</p>\
                </li>';
                html += li;
            }
            html += "</ul>"
            $("#page-content").html(html);
        };
    });
}


function show_article_content(url) {
    var url = "/api/article?url=" + encodeURIComponent(url);
    $.getJSON(url, function (result) {
        if (result['state'] === 'success') {
            $("#page-content").html(result['data'][0]['summary']);
            $("#page-content").attr("url", result['data'][0]['link']);
            $('title').html(result['data'][0]['article_title']);

            // 设置二维码
            var link = result['data'][0]['link']
            var src = "/api/get-qrcode?content=" + encodeURIComponent(link);
            $("#qrcode").attr("src", src);

            change_icon(result['data'][0]);
            //点进来就算已读
            if ($("i.article.read").hasClass("fa-square-o")) {
                $("i.article.read").click();
            }
            if (url === "/api/article?url=next") {
                return;
            }
            $("#navbtn").click();
            $("#page-wrapper").css("max-width", "100%");
            $("i.article").css("display", "");

        };
    });
}

function scroll_content(obj, direction) {
    var t = 500;
    var pos = $(obj).scrollTop();
    if (direction === 'up') {
        $(obj).scrollTop(pos - t);
    } else if (direction === 'down') {
        $(obj).scrollTop(pos + t);
    };
}

function scroll_to_end(obj, direction) {
    if (direction === 'top') {
        $(obj).scrollTop(0);
    } else if (direction === 'end') {
        $(obj).scrollTop($(obj)[0].scrollHeight);
    };
}

function change_state(obj) {
    var url = "/api/action?url=" + $("#page-content").attr("url");

    if ($(obj).hasClass("star")) {
        if ($(obj).hasClass("fa-star-o")) { //没加星的
            url = url + "&action=is_star&type=1";
        } else {
            url = url + "&action=is_star&type=0";
        }
    } else if ($(obj).hasClass("read")) {
        if ($(obj).hasClass("fa-square-o")) { //未读的
            url = url + "&action=is_read&type=1";
        } else {
            url = url + "&action=is_read&type=0";
        }
    };

    $.getJSON(url, function (result) {
        if (result['state'] === 'success') {
            change_icon(result['data'][0]);
        };
    });

}

function change_icon(data_obj) {
    if (data_obj['is_star']) {
        $("i.article.star").removeClass("fa-star-o").addClass('fa-star');
    } else {
        $("i.article.star").removeClass("fa-star").addClass('fa-star-o');
    };

    if (data_obj['is_read']) {
        $("i.article.read").removeClass("fa-square-o").addClass('fa-check-square-o');
    } else {
        $("i.article.read").removeClass("fa-check-square-o").addClass('fa-square-o');
    };
}