import re
import os
import csv
import time
import random
import requests
from lxml import etree


class BilibiliCrawler:
    def __init__(self, user):
        self.user = user
        self.video_data_list = []
        self.video_dic = {}
        self.video_data_dic = {}
        self.aid_dic = {}
        self.comment_data_list = []
        self.sum_comment = 0
        self.comment_error = 0
        self.url_error = 0
        self.data_error = 0
        self.aid_error = 0
        self.search_url = 'https://search.bilibili.com/all'
        self.headers = {
            # 可模拟登陆状态，获取更多数据
            'Cookie': "i-wanna-go-back=-1; b_ut=7; enable_web_push=DISABLE; header_theme_version=CLOSE; "
                      "buvid_fp_plain=undefined; LIVE_BUVID=AUTO8317006657783591; hit-dyn-v2=1; "
                      "buvid3=C7AA4DF4-EBF7-395C-2996-7AB1BCD6241944429infoc; b_nut=1703669044; "
                      "_uuid=1E66DA7A-C687-1027B-10B41-BCD885AA856943600infoc; rpdid=|(ummJYY|Rm~0J'u~|JYYm|RY; "
                      "is-2022-channel=1; DedeUserID=399881629; DedeUserID__ckMd5=8ddbdd60dd865b1f; "
                      "buvid4=13A500D1-9AA1-DB4A-3AA3-F967FF78DEAA86372-023112012-; _ga=GA1.1.2006564153.1706962237; "
                      "_ga_HE7QWR90TV=GS1.1.1706962236.1.1.1706962361.0.0.0; CURRENT_FNVAL=4048; CURRENT_QUALITY=80; "
                      "blackside_state=0; CURRENT_BLACKGAP=0; home_feed_column=5; browser_resolution=1528-790; "
                      "fingerprint=217b51bbc0ec97e52b8dd325620a0301; FEED_LIVE_VERSION=V_WATCHLATER_PIP_WINDOW3; "
                      "buvid_fp=217b51bbc0ec97e52b8dd325620a0301; PVID=1; "
                      "bp_video_offset_399881629=913221797917229110; b_lsid=8CA6BEC8_18E941ADCE5; "
                      "SESSDATA=690c5856%2C1727433776%2C9542d%2A31CjAuB1DQ"
                      "-J0W8w5Ftzxw7c1jbefmp6J7FdfDFKPhZMha2dsLGghFbEG0IXcCMWFNBjESVnNzWjV2bU14Nk5tVWxsbnpqZ3F3"
                      "ZFdlYnJmcWNMX0NIN1ptU3c2T3NzUEdrRVJvNUVSMjVDUzMtWEo2bElPQVZFUVEzTlRseDhUdUx4cjNXNjlJWUZ3IIEC; "
                      "bili_jct=687222dc78f575819b223ff25be92bf9; sid=gsaq2644; arrange=matrix",

            # 防止盗链 指示来源网站
            'Referer': 'https://search.bilibili.com/all',

            'User-Agent': 'Mozilla/5.0 (MSIE 10.0; Windows NT 6.1; Trident/5.0)'
        }

    def crawler(self):
        self.create_folder()
        self.get_video_url()
        self.get_video_data()
        self.get_aid()
        self.get_comments()
        self.add_video_data()
        self.save_results()

    # 创建所需文件夹
    def create_folder(self):
        paths = ['./视频数据', './评论用户数据', './评论内容', './爬取结果']
        for path in paths:
            if not os.path.exists(path):
                os.makedirs(path)

    # 获取视频URL
    def get_video_url(self):
        for i in range(1, 51):
            print(f'第{i}页')

            if i == 1:
                params = {
                    'keyword': self.user,
                    'from_source': 'webtop_search',
                    'spm_id_from': '333.1007',
                    'search_source': '5'
                }
            else:
                params = {
                    'keyword': self.user,
                    'from_source': 'webtop_search',
                    'spm_id_from': '333.1007',
                    'search_source': '5',
                    'page': str(i),
                    'o': str(30 * (i - 1))
                }

            response = requests.get(url=self.search_url, headers=self.headers, params=params)
            # 200表示请求成功
            if response.status_code == 200:
                html = response.text
                tree = etree.HTML(html)
                try:
                    li_list = tree.xpath('//ul[@class="video-list clearfix"]')[0].xpath('./li')
                    for li in li_list:
                        video_url = 'https:' + li.xpath('./a/@href')[0]
                        video_name = li.xpath('./a/@title')[0]
                        self.video_dic[video_name] = video_url
                        print(video_name, video_url)
                except Exception as e:
                    print(f"{e}\n第{i}页获取失败,跳过")
                    self.url_error += 1

                time.sleep(random.uniform(1, 2))
                # TODO:测试
                break
            else:
                print('请求被拒绝')
                break
        print(f"共获取{len(self.video_dic)}个视频, 有{self.url_error * 20}个视频获取失败")

    # 获取视频数据
    def get_video_data(self):
        for video_name, video_url in self.video_dic.items():
            try:
                response = requests.get(url=video_url, headers=self.headers)
                if response.status_code == 200:
                    html = response.text
                    tree = etree.HTML(html)

                    video_data_list = [video_url]
                    video_span_list = (tree.xpath('//div[@class="video-info-detail-list video-info-detail-content"]')[0]
                                       .xpath('./div'))
                    # 总播放数
                    plays_number = {"总播放数": video_span_list[0].xpath('./div[@class="view-text"]/text()')[0]}
                    video_data_list.append(plays_number)
                    # 历史累计弹幕数
                    cumulative_number = {"历史累计弹幕数": video_span_list[1].xpath('./div[@class="dm-text"]/text()')[0]}
                    video_data_list.append(cumulative_number)
                    # 上传时间
                    upload_time = {"上传时间": video_span_list[2].xpath('./div[@class="pubdate-ip-text"]/text()')[0]}
                    video_data_list.append(upload_time)

                    video_toolbar_left = tree.xpath('//div[@class="video-toolbar-left-main"]')[0].xpath('./div')
                    # 点赞，投币，转发
                    for video_toolbar in video_toolbar_left[0:3]:
                        toolbar = {
                            video_toolbar.xpath('./div')[0].get('title')[0:2] + "数": video_toolbar.xpath('./div/span/text()')[0]}
                        video_data_list.append(toolbar)
                    video_transpond = {'转发数': video_toolbar_left[3].xpath('.//text()')[0]}
                    video_data_list.append(video_transpond)

                    tag_list = tree.xpath('//div[@class="tag-panel"]')[0].xpath('./div')
                    tag = []
                    # 标签
                    for li in tag_list:
                        if len(li.xpath('.//text()')) > 0:
                            tag_name = li.xpath('.//text()')[0]
                            tag_name = tag_name.replace("\n", "").replace(" ", "")
                            tag.append(tag_name)
                    video_data_list.append(tag)

                    self.video_data_dic[video_name] = video_data_list
                    print(video_name, video_data_list)

                else:
                    print("请求被拒绝")
                    return
            except Exception as e:
                self.data_error += 1
                print(f"{e}\n{video_name} 数据获取失败,跳过")
        print(f"共读取到{len(self.video_data_dic)}个视频数据, 有{self.data_error}个读取失败")

    # 获取视频标识符，用于构造评论链接URL
    def get_aid(self):
        for video_name, video_url in self.video_dic.items():
            try:
                # 传递查询参数
                params = {
                    # 标识请求来源
                    'spm_id_from': '333.337.search-card.all.click',
                    'vd_source': '338bd991afa6b925f51c9e8742e1891f'
                }
                response = requests.get(url=video_url, headers=self.headers, params=params)
                if response.status_code == 200:
                    html = response.text

                    # 正则, 返回match对象
                    match = re.search(r'"aid"\s*:\s*(\d+)', html)
                    # 获取匹配到的第一个数据
                    aid = match.group(1)

                    self.aid_dic[video_name] = aid
                    print(video_name, aid)

                else:
                    print("请求被拒绝")
            except Exception as e:
                self.aid_error += 1
                print(f"{e}\n{video_name} aid获取失败,跳过")
        print(f"共读取到{len(self.aid_dic)}个aid, 有{self.aid_error}个读取失败")

    def get_comments(self):
        with open(f'./评论内容/{self.user}_评论内容.txt', 'w', encoding='utf-8') as fp:
            for video_name, aid in self.aid_dic.items():
                self.comment_error += self.get_comments_for_video(video_name, aid, fp)
                # TODO:测试
                break
        print(f"共获取{self.sum_comment}条评论, 共丢失{self.comment_error}个评论数据包")

    # 获取视频评论
    def get_comments_for_video(self, video_name, aid, fp):
        comment_error = 0
        print(video_name, aid)
        params = {
            'csrf': 'b4556cda615f29d225bbd111d28439cf',
            'mode': '3',
            # aid区分不同视频
            'oid': aid,
            'pagination_str': '{"offset":""}',
            'plat': '1',
            'seek_rpid': '',
            'type': '1'
        }

        n = 1
        while True:

            # 评论api_url，n是数据包的编号，根据规律改变 aid 和 n 构造url
            api_url = f'https://api.bilibili.com/x/v2/reply/main?csrf=b4556cda615f29d225bbd111d28439cf&mode=3&oid={aid}' \
                      f'&pagination_str=%7B%22offset%22:%22%7B%5C%22type%5C%22:1,%5C%22direction%5C%22:1,' \
                      f'%5C%22data%5C%22:%7B%5C%22pn%5C%22:{n}%7D%7D%22%7D&plat=1&type=1'
            response2 = requests.get(url=api_url, headers=self.headers, params=params)
            # 200表示请求成功，抓取到json数据
            if response2.status_code == 200:
                try:
                    # 分析json文件结构编写代码
                    data = response2.json()
                    if data['message'] == 'UP主已关闭评论区':
                        print('UP主已关闭评论区')
                        break
                    else:
                        replies1_list = data['data']['replies']
                        if len(replies1_list) == 0:
                            print("评论爬取完毕")
                            break
                        else:
                            for i in range(len(replies1_list)):
                                # 用户主页url
                                home1_url = 'https://space.bilibili.com/' + replies1_list[i]['member']['mid']
                                # 用户名称
                                name1 = replies1_list[i]['member']['uname']
                                # 用户性别
                                sex1 = replies1_list[i]['member']['sex']
                                # 用户评论
                                message1 = replies1_list[i]['content']['message']
                                # 有的视频可能找不到ip地址
                                if replies1_list[i]['reply_control'].get('location') is not None:
                                    # ip地址
                                    location1 = replies1_list[i]['reply_control']['location']
                                else:
                                    location1 = "IP属地：未知"
                                print(home1_url, name1, sex1, message1, location1)
                                user_list = {
                                    '用户主页url': home1_url,
                                    '用户名称': name1,
                                    '用户性别': sex1,
                                    'ip地址': location1,
                                    '用户评论': message1
                                }
                                self.comment_data_list.append(user_list)
                                fp.write(f'{message1}\n')
                                self.sum_comment += 1

                                # 遍历评论中的回复
                                replies2_list = replies1_list[i]['replies']

                                if replies2_list is not None:
                                    for j in range(len(replies2_list)):
                                        home2_url = 'https://space.bilibili.com/' + replies2_list[j]['member']['mid']
                                        name2 = replies2_list[j]['member']['uname']
                                        sex2 = replies2_list[j]['member']['sex']
                                        message2 = replies2_list[j]['content']['message']
                                        if replies2_list[j]['reply_control'].get('location') is not None:
                                            location2 = replies2_list[j]['reply_control']['location']
                                        else:
                                            location2 = "IP属地：未知"
                                        print(home2_url, name2, sex2, message2, location2)
                                        user_list = {
                                            '用户主页url': home2_url,
                                            '用户名称': name2,
                                            '用户性别': sex2,
                                            'ip地址': location2,
                                            '用户评论': message2
                                        }
                                        self.comment_data_list.append(user_list)
                                        fp.write(f'{message2}\n')
                                        self.sum_comment += 1
                except Exception as e:
                    print(f"{e}\n{video_name} 第{n}个评论数据包获取失败,跳过")
                    comment_error += 1
            else:
                print('请求被拒绝')
                break

            n += 1
            time.sleep(random.uniform(1, 2))

        print(f"{video_name} 丢失{comment_error}个评论数据包")
        return comment_error

    # 构造创建csv文件所需的数据结构
    def add_video_data(self):
        video_data_ll = [[key, value] for key, value in self.video_data_dic.items()]
        for video_data in video_data_ll:
            for data in self.video_data_list:
                if data['视频链接'] == video_data[1][0]:
                    return
            video_dict = {
                '视频链接': video_data[1][0],
                '视频名称': video_data[0],
                '总播放数': list(video_data[1][1].values())[0],
                '历史累计弹幕数': list(video_data[1][2].values())[0],
                '上传时间': list(video_data[1][3].values())[0],
                '点赞数': list(video_data[1][4].values())[0],
                '投币数': list(video_data[1][5].values())[0],
                '收藏数': list(video_data[1][6].values())[0],
                '转发数': list(video_data[1][7].values())[0],
                '标签': ','.join(video_data[1][8])
            }
            self.video_data_list.append(video_dict)

    # 保存数据
    def save_results(self):
        fp = open(f'./爬取结果/{self.user}_爬取结果.txt', 'w', encoding='utf-8')
        fp.write(f"共获取{len(self.video_dic)}个视频, 有{self.url_error * 20}个视频获取失败\n")
        fp.write(f"共读取到{len(self.video_data_dic)}个视频的数据, 有{self.data_error}个读取失败\n")
        fp.write(f"共读取到{len(self.aid_dic)}个aid, 有{self.aid_error}个读取失败\n")
        fp.write(f"共获取{self.sum_comment}条评论, 共丢失{self.comment_error}个评论数据包\n")
        fp.close()

        csvfile = open(f'./视频数据/{self.user}_视频数据.csv', 'w', newline='', encoding='utf-8')
        fieldnames = self.video_data_list[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for video_data in self.video_data_list:
            writer.writerow(video_data)
        csvfile.close()

        csvfile = open(f'./评论用户数据/{self.user}_评论用户数据.csv', 'w', newline='', encoding='utf-8')
        fieldnames = self.comment_data_list[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for comment_data in self.comment_data_list:
            writer.writerow(comment_data)
        csvfile.close()


def main():
    # 搜索关键词
    user_list = ['永雏塔菲']
    for user in user_list:
        crawler = BilibiliCrawler(user)
        crawler.crawler()


if __name__ == "__main__":
    main()
