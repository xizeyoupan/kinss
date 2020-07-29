// $(function () {
//     $.ajax({
//         url: "/api/feedlist", success: function (result) {
//             if (result['state'] === 'success') {
//                 var html = '';
//                 for (var i in result["feed"]) {
//                     var li = '<li class="feed-list">' + '<i class="fa-li fa fa-rss fa-fw"></i>' + result["feed"][i]['title'] + '</li>';
//                     html += li;
//                 }
//                 $("#folders").html(html);
//             }
//         }
//     });

//     $("#navbtn").click(function () {
//         $(this).toggleClass("fa-rotate-90");
//         $("#navbar").toggle();
//         if ($(this).attr("class").split(" ").indexOf("fa-rotate-90") === -1) {
//             $("#page-wrapper").css("width", "100%");
//             $("div.page-bottom").css("width", "100%");

//         } else {
//             $("div.page-bottom").css("width", "73%");
//             $("#page-wrapper").css("width", "73%");
//         }
//     });

//     $("li.all-articles.btn").click(function () {
//         $("a.page-title").text($(this).text());
//         $.ajax({
//             url: "/api/category", success: function (result) {
//                 if (result['state'] === 'success') {
//                     var html = '';
//                     for (var i in result["list"]) {
//                         var div = '<div class="article-list"' + 'idx="' + result["list"][i][0] + '">';
//                         var feed_title = '<p class="feed-title">' + result["list"][i][1] + '</p>';
//                         var article_title = '<p class="article-title">' + result["list"][i][2] + '</p>';
//                         div += feed_title + article_title + '</div>';
//                         html += div;
//                     }
//                     $("#page-content").html(html);
//                 }
//             }
//         });
//     });

//     $("li.read-articles.btn").click(function () {
//         $("a.page-title").text($(this).text());
//         $.ajax({
//             url: "/api/category", success: function (result) {
//                 if (result['state'] === 'success') {
//                     var html = '';
//                     for (var i in result["list"]) {
//                         if (result["list"][i][4] === 0) {
//                             continue;
//                         }
//                         var div = '<div class="article-list"' + 'idx="' + result["list"][i][0] + '">';
//                         var feed_title = '<p class="feed-title">' + result["list"][i][1] + '</p>';
//                         var article_title = '<p class="article-title">' + result["list"][i][2] + '</p>';
//                         div += feed_title + article_title + '</div>';
//                         html += div;
//                     }
//                     $("#page-content").html(html);
//                 }
//             }
//         });
//     });

//     $("li.unread-articles.btn").click(function () {
//         $("a.page-title").text($(this).text());
//         $.ajax({
//             url: "/api/category", success: function (result) {
//                 if (result['state'] === 'success') {
//                     var html = '';
//                     for (var i in result["list"]) {
//                         if (result["list"][i][4] === 1) {
//                             continue;
//                         }
//                         var div = '<div class="article-list"' + 'idx="' + result["list"][i][0] + '">';
//                         var feed_title = '<p class="feed-title">' + result["list"][i][1] + '</p>';
//                         var article_title = '<p class="article-title">' + result["list"][i][2] + '</p>';
//                         div += feed_title + article_title + '</div>';
//                         html += div;
//                     }
//                     $("#page-content").html(html);
//                 }
//             }
//         });
//     });


//     $(document).on('click', 'li.feed-list', function () {
//         $("a.page-title").text($(this).text());
//         $.ajax({
//             url: "/api/feed?feed=" + $(this).text(), success: function (result) {
//                 if (result['state'] === 'success') {
//                     var html = '';
//                     for (var i in result["list"]) {
//                         var div = '<div class="article-list"' + 'idx="' + result["list"][i][0] + '">';
//                         var feed_title = '<p class="feed-title">' + result["list"][i][1] + '</p>';
//                         var article_title = '<p class="article-title">' + result["list"][i][2] + '</p>';
//                         div += feed_title + article_title + '</div>';
//                         html += div;
//                     }
//                     $("#page-content").html(html);
//                 }
//             }
//         });
//     });

//     $(document).on('click', 'div.article-list', function () {
//         $("a.page-title").text($(this).children("p.article-title").text().substring(0, 20));
//         $.ajax({
//             url: "/api/article?id=" + $(this).attr('idx'), success: function (result) {
//                 if (result['state'] === 'success') {
//                     $("#page-content").html(result['detail'][4]);
//                     $("#page-content").attr("idx", result['detail'][0]);
//                     $("i.mark-as-read.btn").show()
//                 }
//             }
//         });
//     });

//     $("#navbar").on("click", function () {
//         $("i.mark-as-read.btn").hide()
//     });

//     $("i.mark-as-read.btn").on("click", function () {
//         $.ajax({
//             url: "/api/markread?id=" + $("#page-content").attr('idx'), success: function (result) {
//                 if (result['state'] === 'success') {
//                     $("i.mark-as-read.btn").hide();
//                 }
//             }
//         });
//     });

//     $("i.fa-arrow-up.page-bottom").click(function () {
//         var pos = $("#page-wrapper").scrollTop();
//         $("#page-wrapper").scrollTop(pos - 500);
//     });

//     $("i.fa-arrow-down.page-bottom").click(function () {
//         var pos = $("#page-wrapper").scrollTop();
//         $("#page-wrapper").scrollTop(pos + 500);
//     });

//     $("i.fa-angle-double-up.page-bottom").click(function () {
//         $("#page-wrapper").scrollTop(0);
//     });

//     $("i.fa-angle-double-down.page-bottom").click(function () {
//         $("#page-wrapper").scrollTop($("#page-content").height());
//     });

//     $("li.all-articles.btn").click();
// })

// $(function({
// $("i.fa-refresh").click(function() {
//     $.ajax({
//         url: "/api?action=refresh",
//         success: function(result) {
//             if (result['state'] === 'success') {
//                 $("i.mark-as-read.btn").hide();
//             }
//         }
//     })
// }))

$(function () {
    // 立刻刷新rss
    $("i.fa-refresh").click(function () {
        // result = get_data("/api?action=refresh");
        // if (result['state'] === 'success') {
        //     alert("正在抓取，请在几秒后刷新。");
        // };
        $.getJSON("/api?action=refresh", function (result) {
            if (result['state'] === 'success') {
                alert("正在抓取，请在几秒后刷新。");
            };
        });
    });

    if (location.pathname === "/article") {
        // alert()
    } else {

    };

    $('#navbar').on('click', 'li', function () { //监听每个rss源的点击
        show_article_list(this)
    });


});


function show_article_list(obj) {
    if ($(obj).attr('class').indexOf("btn") != -1) { //上面四个大类
        var url = $(obj).attr('eachurl')
    } else if ($(obj).attr('class').indexOf("each-feed") != -1) { //每个Feed源
        var url = "/api?action=getlist&type=each&url=" + encodeURIComponent($(obj).attr('eachurl'))
    } else {
    };

    $.getJSON(url, function (result) {
        if (result['state'] === 'success') {
            var html = '<ul>';
            for (var i in result["data"]) {
                var li = '<li>\
                <p class="feed-title">'+ result["data"][i].feed_title + '</p>\
                <p class="article-title">'+ result["data"][i].article_title + '</p>\
                </li>';
                html += li;
            }
            html += "</ul>"
            $("#page-content").html(html);
        };
    });


}