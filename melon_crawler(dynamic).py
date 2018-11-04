# Past charts are rendered in the browser using javascript(Single Page Application:SPA)
# Instead of using popular modules such as 'Selenium' or 'PhantomJS', I found the URL of the AJAX request.
# Check this blog for detailed explanation
# https://blog.hartleybrody.com/web-scraping-cheat-sheet/#more-advanced-topics
# section: Javascript Heavy Websites
# -------------------- challenges encountered --------------------
# 1. Without 'Cookie' in header, the server returned 406 error which I believe was due to an authorization issue
# 2. Request GET using params parameter somehow did not work
#       request.get(host_url, headers=header, params=payload)
#    So I constructed a payload substring and appended to the host_url
# 3. Python by default is pointer reference, use .copy() to make another copy of the data
# ----------------------------------------------------------------


import requests
from bs4 import BeautifulSoup
import re
import json
import time
import datetime
from dateutil.relativedelta import *

host_url = 'https://www.melon.com/chart/search/list.htm'
likes_url = 'https://www.melon.com/commonlike/getSongLike.json'

header = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
    'Referer': 'https://www.melon.com/chart/search/index.htm',
    'Cookie': 'SCOUTER=x2tbftd69m7f5g; PCID=15394284289426392500889; PC_PCID=15394284289426392500889; POC=WP10; WMONID=jGE0lrNKToO; charttutorial=true; personalexpand=true; data-salePrtCodeBfBuyPhase=2S5; data-recmdDispIds=',
    'X-Requested-With': 'XMLHttpRequest'
}


def get_chart(payload):
    sub_string = ''
    for idx, t in enumerate(payload.items()):
        if idx == 0:
            sub_string += '?'
        else:
            sub_string += '&'
        sub_string += t[0] + '=' + t[1]
    r = requests.get(host_url + sub_string, headers=header)
    html = r.text
    soup = BeautifulSoup(html, 'html.parser')
    ret_dict = dict()
    ret_dict['year'] = payload['year']
    ret_dict['month'] = payload['mon']
    ret_dict['startDay'] = payload['startDay']
    ret_dict['endDay'] = payload['endDay']
    ret_dict['chart'] = list()
    chart_list = soup.find_all('tr', class_='lst50') + soup.find_all('tr', class_='lst100')
    for idx, tag in enumerate(chart_list):
        a_dict = dict()
        song_name = tag.find('div', class_='ellipsis rank01').text.strip()
        song_id = tag.find('div', class_='wrap pd_none left').find('input')['value']
        artist_name = tag.find('span', class_='checkEllipsis').text.strip()
        pattern = tag.find('span', class_='checkEllipsis').find('a')['href'].strip()
        artist_id = re.search(r'(?<=\')\d*(?=\')', pattern)[0]
        album_name = tag.find('div', class_='ellipsis rank03').text.strip()
        pattern = tag.find('div', class_='ellipsis rank03').find('a')['href'].strip()
        album_id = re.search(r'(?<=\')\d*(?=\')', pattern)[0]
        rank = tag.find('div', class_='wrap right_none').find_all('span')[0].text.strip()
        pattern = tag.find('span', class_='wrap_rank')['title']
        status = ''
        delta = '0'
        if '단계 상승' in pattern:
            status = 'up'
            delta = pattern.strip('단계 상승')
        elif '단계 하락' in pattern:
            status = 'down'
            delta = pattern.strip('단계 하락')
        elif '순위 집입' in pattern:
            status = 'new'
        elif '순위 동일' in pattern:
            status = 'static'
        else:
            status = pattern
        a_dict['rank'] = int(rank)
        a_dict['song_name'] = song_name
        a_dict['artist_name'] = artist_name
        a_dict['album_name'] = album_name
        a_dict['song_id'] = int(song_id)
        a_dict['artist_id'] = int(artist_id)
        a_dict['album_id'] = int(album_id)
        a_dict['status'] = status
        a_dict['delta'] = int(delta)
        ret_dict['chart'].append(a_dict)
    return ret_dict


def get_search_range(data, payload):
    url = 'https://www.melon.com/chart/search/cond.json'
    r = requests.post(url, headers=header, data=data)
    payload['year'] = data['year']
    payload['mon'] = data['mon']
    ret_list = list()
    print(r.json()['itemData'])
    for item in r.json()['itemData']:
        payload['startDay'] = item['STARTDAY']
        payload['endDay'] = item['ENDDAY']
        payload['day'] = item['ITEMVAL'].replace('^', '%5E')
        ret_list.append(payload.copy())
    return ret_list


if __name__ == "__main__":
    date = datetime.date(2016, 2, 22)
    until = datetime.date(2013, 10, 22)

    payload = {
        'chartType': 'WE',
        'age': '2010',
        'year': '2013',
        'mon': '06',
        'day': '20130603%5E20130609',
        'classCd': 'GN0000',
        'startDay': '20130603',
        'endDay': '20130609',
        'moved': 'Y'
    }

    data = {
        'chartType': 'WE',
        'searchDepth': '3',
        'age': '2010',
        'year': '2018',
        'mon': '10'
    }

    while date > until:
        try:
            data['year'] = str(date.year)
            date_str = str(date.year*10000 + date.month*100 + date.day)
            data['mon'] = date_str[4:6]
            iter_list = get_search_range(data, payload)
            for pl in iter_list:
                w_dict = get_chart(pl)
                if len(w_dict['chart']) == 0:
                    pl2 = pl.copy()
                    pl2['classCd'] = 'DP0000'
                    w_dict = get_chart(pl2)
                with open('./melon_chart_data/melon_chart' + pl['startDay'] + '-' + pl['endDay'] + '.json', 'w', encoding='utf-8-sig') as f:
                    f.write(json.dumps(w_dict, indent=2, ensure_ascii=False))
                print('{} complete'.format(pl['startDay']))
                time.sleep(2)
        except:
            print('{} error'.format(date))
        time.sleep(3)
        date = date - relativedelta(months=+1)
