import requests
from bs4 import BeautifulSoup
import json
import time
import datetime

host_url_prefix = 'https://www.melon.com/chart/week/index.htm#params%5Bidx%5D=1&params%5BstartDay%5D='
host_url_middle = '&params%5BendDay%5D='
host_url_suffix = '&params%5BisFirstDate%5D=false&params%5BisLastDate%5D=true'

song_detail_url = 'https://www.melon.com/song/detail.htm?songId='

header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko'}

r1_fail_list = list()
r2_fail_list = list()


def get_chart(date_s, date_f):
    URL = host_url_prefix + str(date_s) + host_url_middle + str(date_f) + host_url_suffix
    r = requests.get(URL, headers=header)
    if r.status_code != 200:
        r1_fail_list.append(r)
        raise Exception
    print(URL)
    print('date: {} status: {}'.format(date_s, r.status_code))
    html = r.text
    soup = BeautifulSoup(html, 'html.parser')
    list_dict = dict()
    list_dict['date'] = date_s
    a_list = list()
    for idx, tag in enumerate(soup.find_all('tr', class_='lst50')):
        a_dict = dict()
        song_name = tag.find('div', class_='ellipsis rank01').text.strip()
        artist_name = tag.find('span', class_='checkEllipsis').text.strip()
        album_name = tag.find('div', class_='ellipsis rank03').text.strip()
        rank = tag.find('span', class_='rank_wrap').text.strip()
        songid = tag['data-song-no']
        num = '0'
        if '순위 진입' in rank:
            stat = 'new'
        elif '순위 동일' in rank:
            stat = 'static'
        elif '단계 상승' in rank:
            stat = 'up'
            num = rank.strip('단계 상승')
        elif('단계 하락') in rank:
            stat = 'down'
            num = rank.strip('단계 하락')
        else:
            stat = rank
        r2 = requests.get(song_detail_url + songid, headers=header)
        if r2.status_code != 200:
            r2_fail_list.append(r)
            raise Exception
        html2 = r2.text
        soup2 = BeautifulSoup(html2, 'html.parser')
        meta_key = soup2.find('div', class_='meta').find_all('dt')
        meta_val = soup2.find('div', class_='meta').find_all('dd')
        tmp_dict = dict()
        for i, _ in enumerate(meta_key):
            tmp_dict[meta_key[i].text.strip()] = meta_val[i].text.strip()
        release = tmp_dict['발매일']
        genre = tmp_dict['장르'].split(',')
        soup3 = soup2.find('ul', class_='list_person clfix')
        tmp_dict.clear()
        meta_key = soup3.find_all('div', class_='ellipsis artist')
        meta_val = soup3.find_all('div', class_='meta')
        for i, _ in enumerate(meta_key):
            tmp_dict[meta_key[i].text.strip()] = meta_val[i].text.strip()
        a_dict['song_name'] = song_name
        a_dict['artist_name'] = artist_name
        a_dict['album_name'] = album_name
        a_dict['rank'] = idx + 1
        a_dict['rank_status'] = stat
        a_dict['rank_change'] = int(num)
        a_dict['release'] = release
        a_dict['genre'] = genre
        a_dict['songid'] = songid
        for k, v in tmp_dict.items():
            if v not in a_dict.keys():
                a_dict[v] = list()
            a_dict[v].append(k)
        a_list.append(a_dict)
        print(a_dict)
        time.sleep(2)
    list_dict['chart'] = a_list
    return list_dict


if __name__ == "__main__":
    date = datetime.date(2018, 8, 27)
    seven_days = datetime.timedelta(days=7)
    six_days = datetime.timedelta(days=6)
    until = datetime.date(2013, 10, 22)
    while date > until:
        d = date.year*10000 + date.month*100 + date.day
        d2 = date + six_days
        d2 = d2.year*10000 + d2.month*100 + d2.day
        try:
            w_dict = get_chart(d, d2)
            time.sleep(2)
            with open('melon_chart' + str(d) + '.json', 'w', encoding='utf-8-sig') as f:
                f.write(json.dumps(w_dict, indent=2, ensure_ascii=False))
            print('{} complete'.format(date))
        except:
            print('{} error'.format(date))
        date = date - seven_days

    print(r1_fail_list)
    print(r2_fail_list)


