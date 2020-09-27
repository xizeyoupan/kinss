<p align="center"><img src="https://i.loli.net/2020/03/06/Q8dyDxz63OKbZml.png"></p>

## About Kinss
Kinss is a minimalist feed reader for kindle.

## Quickstart
1. `pip install -r requirements.txt`
2. 运行`app.py`，默认 ip 是 `0.0.0.0` & 端口 `5000`。

## Docker 部署
### 安装
运行下面的命令下载 kinss 镜像

`$ docker pull intemd/kinss`

然后运行 kinss 即可

`$ docker run -d --name kinss -p 5000:5000 intemd/kinss`

在浏览器中打开 http://0.0.0.0:5000/ ，enjoy it! ✅

您可以使用下面的命令来关闭 kinss

`$ docker stop kinss`
### 更新
删除旧容器

`$ docker stop kinss`

`$ docker rm kinss`

然后重复安装步骤

## Aggregator
此程序依赖**feverapi**，任何集成了此api的服务理论上都能运行。以下是几个大佬提供的公开服务，我稍微进行了测试。体验地址：[kinss](https://kinss.herokuapp.com)，当然，由于网络线路，反应**会比较慢**。建议自建。

|Aggregator|Fever UesrName|Fever Password|Fever API endpoint|thanks to|
|  ----  | ----  |--------|  ----  | ----  |
|FreshRSS|kinss|kinsses|https://rss.othing.xyz/p/api/fever.php|@yzqzss|
|Tiny Tiny RSS|kinss|kinsses|https://rss.ioiox.com/plugins/fever/|@stilleshan|

## Features
- [x] 已读/未读
- [x] 星标
- [x] 二维码
- [x] 多账户

## Read On KPW3
![](assets/1.png)
![](assets/2.png)
![](assets/5.png)

## License
Kinss is open-sourced software licensed under the [MIT license](https://opensource.org/licenses/MIT).
