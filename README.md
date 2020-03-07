<p align="center"><img src="https://i.loli.net/2020/03/06/Q8dyDxz63OKbZml.png"></p>

## About Kinss

Kinss is a minimalist feed reader.

- Written in python (Python3)
- Works only with sqlite
- Doesn't use any complicated framework
- Use only necessary Javascript (Fully support kindle browser)

## Quickstart

1. `pip install -r requirements.txt`
2. revise `config.json`
2. run the script

## Read On Kindle3
![](assets/1.png)
![](assets/2.png)
![](assets/3.png)
![](assets/4.png)

## Advanced Usage

After script running,you can use it as an api server.

- get feed list  
  `/api/feedlist`  
  example:  
  `http://127.0.0.1:8080/api/feedlist`  
  return:  
    ```
  {
  "state": "success",
  "feed": [{
          "title": "test",
          "read": 0,
          "unread": 1
          }, {
          "title": "cnBeta",
          "read": 3,
          "unread": 196
          }]
  }
    ```

- get article list from category  
  `/api/category`  
  ```
  params:  
  category: `2`:all,`1`:read,or `0`:unread  
  sort: `asc` or `desc` (ascending or descending by time)  
  ```
  example:  
  `http://127.0.0.1:8080/api/category?category=2&sort=desc`  
  return:  
    ```
    {
    "state": "success",
    "list": [
            [101, "cnBeta", "Intel NUC11搭载11代酷睿Tiger Lake平台：10nm+、支持PCIe 4.0", 1583459104, 0],
            [102, "cnBeta", "统一操作系统UOS适配NTKO Office控件：浏览器在线编辑文档", 1583458855, 0]
	        ]
    }
    ```

- get article list from feed  
  `/api/feed`  
  ```
  params:  
  feed: feed title
  sort: `asc` or `desc` (ascending or descending by time)  
  ```
  example:  
  `http://127.0.0.1:8080/api/feed?feed=cnBeta`  
  return:  
    ```
    {
    "state": "success",
    "list": [
            [101, "cnBeta", "Intel NUC11搭载11代酷睿Tiger Lake平台：10nm+、支持PCIe 4.0", 1583459104, 0],
            [102, "cnBeta", "统一操作系统UOS适配NTKO Office控件：浏览器在线编辑文档", 1583458855, 0]
	        ]
    }
    ```

- get article content  
  `/api/article`  
  ```
  params:  
  id: article id
  ```
  example:  
  `http://127.0.0.1:8080/api/article?id=103`  
  return:  
    ```
    {
	"state": "success",
	"detail": [103, "cnBeta", "AMD确认索尼PS5、微软XSX主机都是RDNA2架构 支持硬件光追", 1583458818, "<p>最近围绕新一代主机索尼PS5、微软Xbox Series X（简称XSX）的光追问题产生了分歧，不过两家主机的粉丝不用担心了，<strong>AMD确认它们都支持基于RDNA2架构的光追</strong>。在今天的财务分析师会议上，AMD接连官宣2个重磅产品，一个是5nm Zen4，一个是全新的GPU，包括游戏用的RDNA及计算用的CDNA，其中今年的GPU是RDNA2代。<br/> </p>", "https://www.cnbeta.com/articles/tech/952271.htm", 0]
    }
    ```

- mark as read/unread  
  `/api/markread`  
  ```
  params:
  id: article id
  read_state: int
  ```
  example:  
  `http://127.0.0.1:8080/api/markread?id=101&read_state=1`  
  return:  
    ```
    {"state": "success"}
    ```

## License

Kinss is open-sourced software licensed under the [MIT license](https://opensource.org/licenses/MIT).
