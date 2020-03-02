$(function () {
    $("#navbtn").click(function () {
        $(this).toggleClass("fa-rotate-90");
        $("#navbar").toggle();
        if ($(this).attr("class").split(" ").indexOf("fa-rotate-90") === -1) {
            $("#page-wrapper").css("width", "98%");
            $("#article-wrapper").css("width", "98%");
        } else {
            $("#page-wrapper").css("width", "73%");
            $("#article-wrapper").css("width", "73%");

        };
    });

    $("a.all-articles").click(function () {
        $("#article-wrapper").css("display", "none");
    });

    $("div.article").click(function () {
        $("#article-wrapper").css("display", "block");
        $("#page-wrapper").css("display", "none");
        $("span.page-title").text($(this).children("p.article-title").text())

        $.ajax({
            url: "/article/" + $(this).attr("id"), success: function (result) {
                $("#article-wrapper").html(result);
            }
        });
    });

    $("li.all-articles").click(function () {
        $("#article-wrapper").css("display", "none");
        $("#page-wrapper").css("display", "block");
        $("span.page-title").text($(this).text())

    });

})
