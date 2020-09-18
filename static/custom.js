var since_id = "";
var t; // check items' type when scroll at the end

$(function () {
    // 监听每篇文章
    $('#page-content').on('click', 'li', function () {
        show_article_content($(this).attr('item_id'));
    });

    // 监听二维码按钮
    $('i.fa-qrcode').on('click', function () {
        $("#qrcode-wrapper").toggle();
    });

    // 监听翻页按钮的点击
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
        change_status(this);
    });

    // 监听页面滚动操作
    $('#page-wrapper').on('scroll', function () {

        var p = ($("#page-wrapper").height() + $("#page-wrapper").scrollTop()) / $("#page-wrapper")[0].scrollHeight
        p = Number(p * 100).toFixed(1);
        $("#process").text(p + "%")

        if ($("#page-content").attr("status") === "article") {
            return
        }
        if ($("#page-wrapper").height() + $("#page-wrapper").scrollTop() === $("#page-wrapper")[0].scrollHeight) {
            var title = $('title').text().slice(0, 3)
            var url = "/api/article-list?type=" + t + "&since_id=" + since_id;
            addItems(url, title)
        }
    });

    if (location.pathname === "/article") {
        $("i.article.star").click()
    }
});


function show_article_content(id) {
    var url = "/api/article?item_id=" + id;
    scroll_to_end($("#page-wrapper"), 'top');
    $("#page-content").attr("status", "article")

    $.getJSON(url, function (result) {
        if (result['state'] === 'success') {
            $("#page-content").html(result['data']['html']);
            $("#page-content").attr("item_id", result['data']['id']);
            $('title').html(result['data']['title']);

            // 设置二维码
            var link = result['data']['url']
            var src = "/api/get-qrcode?content=" + encodeURIComponent(link);
            $("#qrcode").attr("src", src);

            change_icon(result['data']);
            //点进来就算已读
            if ($("i.article.read").hasClass("fa-square-o")) {
                $("i.article.read").click();
            }

        }
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

function change_status(obj) {
    if ($("#page-content").attr("status") === "main-page") {
        if ($(obj).hasClass("star")) {

            since_id = ''
            $("#items").html('')
            var title

            if ($(obj).hasClass("fa-star-o")) { //没加星的，目标为星标
                t = 'saved'
                var url = "/api/article-list?type=saved&since_id=" + since_id;
                $("i.article.star").removeClass("fa-star-o").addClass('fa-star');
                title = "星标 ";
            } else { //本来已加星的，目标为未读
                t = 'unread'
                var url = "/api/article-list?type=unread&since_id=" + since_id;
                $("i.article.star").removeClass("fa-star").addClass('fa-star-o');
                title = "未读 ";
            }

            addItems(url, title);

        } else if ($(obj).hasClass("read")) {
            var items = $("#items li")
            var itemsNumber = items.length
            var r = confirm("确定将这个页面中的" + itemsNumber + "个条目都设置为已读嘛？");
            if (r) {
                items = items.map(function (i) { return $(items[i]).attr("item_id") })
                items = $.map(items, function (value, index) {
                    return [value];
                })

                for (var i in items) {
                    markItem(items[i], 'read')
                }
                setTimeout(function () {
                    alert("Done!")
                    location.reload()
                }, 2000)

            }
        };
    } else if ($("#page-content").attr("status") === "article") {
        var url = "/api/action?item_id=" + $("#page-content").attr("item_id") + "&type=";

        if ($(obj).hasClass("star")) {
            if ($(obj).hasClass("fa-star-o")) { //没加星的
                url = url + "saved";
            } else {
                url = url + "unsaved";
            }
        } else if ($(obj).hasClass("read")) {
            if ($(obj).hasClass("fa-square-o")) { //未读的
                url = url + "read";
            } else {
                url = url + "unread";
            }
        }

        $.getJSON(url, function (result) {
            if (result['state'] === 'success') {
                $.getJSON("/api/article?item_id=" + $("#page-content").attr("item_id"), function (res) {
                    if (res['state'] === 'success') {
                        change_icon(res['data']);
                    }
                })

            };
        })

    }

}

function change_icon(data_obj) {
    if (data_obj['is_saved']) {
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

function addItems(url, title) {
    if (since_id === null) {
        return
    }
    $.getJSON(url, function (result) {
        if (result['state'] === 'success') {
            $('title').html(title + "(" + result.total + ")");
            var html = '';
            for (var i in result["items"]) {
                var li = '<li item_id="' + result["items"][i]["id"] + '">\
        <div class="feed-wrapper"><a class="feed-title">' + result["items"][i]["feed_title"] + '</a><a class="feed-date">\
        '+ GetDateToNewData(result["items"][i]["created_on_time"]) + '</a></div>\
        <p class="article-title">' + result["items"][i]["title"] + '</p>\
        </li>';
                html += li;
            }
            html += ""
            $("#items").html($("#items").html() + html);
            since_id = result.next_id
        };
    });
}

function markItem(id, type) {
    var url = '/api/action?item_id=' + id + '&type=' + type
    $.getJSON(url, function (result) {
        if (result['state'] === 'success') {
            return
        };
    });
}

function GetDateToNewData(diffValue) {
    // from https://blog.csdn.net/wangkunjiao/article/details/103577995 ,BTW,there are some bugs in the page but I fixed.
    diffValue = diffValue * 1000
    var minute = 60000;
    var hour = minute * 60;
    var day = hour * 24;
    var month = day * 30;

    var nowTime = (new Date()).getTime(); //获取当前时间戳

    var ShiJianCha = nowTime - diffValue;

    var monthC = ShiJianCha / month;
    var weekC = ShiJianCha / (7 * day);
    var dayC = ShiJianCha / day;
    var hourC = ShiJianCha / hour;
    var minC = ShiJianCha / minute;
    var res = '';

    if (monthC >= 12) {
        var date = new Date(diffValue);
        res = date.getFullYear() + '-' + (date.getMonth() + 1) + '-' + date.getDate();
    } else if (monthC >= 1) {
        res = parseInt(monthC) + "个月前";
    }
    else if (weekC >= 1) {
        res = parseInt(weekC) + "周前"
    }
    else if (dayC >= 1) {
        res = parseInt(dayC) + "天前"
    }
    else if (hourC >= 1) {
        res = parseInt(hourC) + "个小时前"
    }
    else if (minC >= 1) {
        res = parseInt(minC) + "分钟前"
    } else {
        res = "刚刚"
    }
    return res;

}
