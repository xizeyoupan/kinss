<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>

<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>Kinss</title>
    <link href="static/custom.css" rel="stylesheet" type="text/css">
    <link href="https://cdn.bootcss.com/font-awesome/4.7.0/css/font-awesome.min.css" rel="stylesheet">
    <script src="https://upcdn.b0.upaiyun.com/libs/jquery/jquery-2.0.2.min.js"></script>
</head>

<body>

    <div id="wrapper">
        
        <i id="navbtn" class="fa fa-bars fa-rotate-90"></i>&nbsp;
        <span class="page-title">全部文章</span>
    </div>


        <div id="navbar">
            <ul class="fa-ul">
                <li class="all-articles"><i class="fa-li fa fa-book"></i> 全部文章</li>
                <li class="read-articles"><i class="fa-li fa fa-book"></i> 已读</li>
                <li class="unread-articles"><i class="fa-li fa fa-book"></i> 未读</li>
            </ul>

            <hr>
            <ul id="folders" class="fa-ul">
                %if data:
                    %feed_titles=[ i[1] for i in data]
                    %feed_titles=set(feed_titles)
                    %for i in feed_titles:
                        <li class="rss-item"><i class="fa-li fa fa-rss"></i>{{ i }}</li>
                    %end
                %end
            </ul>
        </div>
        <div id="page-wrapper">
            %if data:
                %for i in data:
                    <div class="article" id="{{ i[0] }}">
                        <p class="feed-title">{{ i[1] }}</p>
                        <p class="article-title">{{ i[2] }}</p>
                    </div>
                %end
            %end

        </div>

        <div id="article-wrapper"></div>


    <script src="static/custom.js"></script>
</body>

</html>