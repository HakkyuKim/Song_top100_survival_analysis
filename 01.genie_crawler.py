import requests
from bs4 import BeautifulSoup
import json
import time
import datetime

host_url = 'http://www.genie.co.kr/chart/top200?ditc=W&rtm=N&ymd='

def get_chart(date):
    html = requests.get(host_url + str(date)).text
    soup = BeautifulSoup(html, 'html.parser')
    list_dict = dict()
    list_dict['date'] = date
    a_list = list()
    for idx, tag in enumerate(soup.find_all('tr', class_='list')):
        a_dict = dict()
        song_name = tag.find('a', class_='title ellipsis').text.strip()
        artist_name = tag.find('a', class_='artist ellipsis').text.strip()
        rank = tag.find('span', class_='rank').text.strip()
        stat = ''
        num = '0'
        if 'new' in rank:
            stat = 'new'
        elif '유지' in rank:
            stat = 'same'
        elif '상승' in rank:
            stat = 'up'
            num = rank.strip('상승')
        elif '하강' in rank:
            stat = 'down'
            num = rank.strip('하강')
        a_dict['song_name'] = song_name
        a_dict['artist_name'] = artist_name
        a_dict['rank'] = idx + 1
        a_dict['rank_type'] = stat
        a_dict['rank_change_num'] = int(num)
        a_list.append(a_dict)
    list_dict['chart'] = a_list
    return list_dict


if __name__ == "__main__":
    date = datetime.date(2018, 10, 29)
    seven_days = datetime.timedelta(days=7)
    until = datetime.date(2013, 10, 29)
    list_dict = dict()
    a_list = list()
    while date > until:
        d = date.year*10000 + date.month*100 + date.day
        try:
            a_dict = get_chart(d)
            a_list.append(a_dict)
            time.sleep(2)
            print('{} complete'.format(date))
        except:
            print('{} error'.format(date))
        date = date - seven_days

    list_dict['charts'] = a_list
    with open('genie_chart.json', 'w', encoding='utf-8-sig') as f:
        f.write(json.dumps(list_dict, indent=2, ensure_ascii=False))

