import os
import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re
import datetime
from SongData import SongData

header = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
    'Referer': 'https://www.melon.com/chart/search/index.htm',
    'X-Requested-With': 'XMLHttpRequest'
}


song_check = set()
album_check = set()
before_chart = dict()
current_chart = dict()
song_dict = dict()
album_dict = dict()
book = dict()
song_info = dict()
artist_info = dict()
agency_point = dict()
before_date = None


def process_files(path):
    global before_date, before_chart
    filenames = os.listdir(path)
    cnt = 1
    total_file_num = len(filenames)
    for filename in sorted(filenames):
        fullpath = os.sep.join((path, filename))
        f = open(fullpath, encoding='utf-8-sig')
        js = f.read()
        f.close()
        data = json.loads(js)
        date = int(data["startDay"])
        year = int(data["year"])
        total_track_num = len(data["chart"])
        for idx, track in enumerate(data["chart"]):
            print("file {}/{}, track {}/{}".format(cnt, total_file_num, idx + 1, total_track_num))
            process_track(track, date, year)
        for song_id in before_chart.keys():
            if song_id not in current_chart.keys():
                book[(song_id, before_chart[song_id])].update_end_date(date)
        before_chart = current_chart.copy()
        current_chart.clear()
        print("{}/{}".format(cnt, len(filenames)))
        cnt += 1


def get_song_detail(song_id):
    host_url = "https://www.melon.com/song/detail.htm?songId="
    r = requests.get(host_url + str(song_id), headers=header)
    html = r.text
    soup = BeautifulSoup(html, "html.parser")
    meta_key = soup.find('div', class_='meta').find_all('dt')
    meta_val = soup.find('div', class_='meta').find_all('dd')
    temp_dict = dict()
    for idx, _ in enumerate(meta_key):
        temp_dict[meta_key[idx].text.strip()] = meta_val[idx].text.strip()
    release_list = temp_dict['발매일'].strip().split(".")
    release_string = ""
    for ele in release_list:
        release_string += str(ele)
    genre = temp_dict['장르']
    soup = soup.find('ul', class_='list_person clfix')
    if soup is None:
        return release_string, genre, None
    meta_val = soup.find_all('div', class_='ellipsis artist')
    meta_key = soup.find_all('div', class_='meta')
    temp_dict.clear()
    for idx, _ in enumerate(meta_key):
        if meta_key[idx].text.strip() not in temp_dict.keys():
            temp_dict[meta_key[idx].text.strip()] = list()
        temp_dict[meta_key[idx].text.strip()].append(meta_val[idx].text.strip())
    if "작곡" not in temp_dict.keys():
        composer = None
    else:
        composer = temp_dict["작곡"]
    return release_string, genre, composer


def get_artist_info(artist_id, last_year):
    host_url = "https://www.melon.com/artist/timeline.htm?artistId="
    r = requests.get(host_url + str(artist_id), headers=header)
    html = r.text
    soup = BeautifulSoup(html, "html.parser")
    soup = soup.find('dl', class_='atist_info clfix')
    meta_key = soup.find_all('dt')
    meta_val = soup.find_all('dd')
    temp_dict = dict()
    for idx, _ in enumerate(meta_key):
        temp_dict[meta_key[idx].text.strip()] = meta_val[idx].text.strip()
    activity_type = None
    agency = None
    flag = True
    if "활동유형" in temp_dict.keys():
        activity_type = temp_dict["활동유형"]
    if "소속사" in temp_dict.keys():
        agency = temp_dict["소속사"]
    if "생일" in temp_dict.keys():
        birthday_year = int(temp_dict["생일"].split(".")[0])
        year_gap = last_year - birthday_year
    elif activity_type == "솔로" and "생일" not in temp_dict.keys():
        flag = False
        year_gap = -1
    else:
        soup = BeautifulSoup(html, "html.parser")
        soup = soup.find('div', class_='wrap_atistname')
        temp_list = soup.find_all("a")
        if len(temp_list) == 0:
            flag = False
            year_gap = -1
        else:
            sum_year = 0
            for ppl in temp_list:
                txt = ppl["href"]
                at_id = re.search(r"\d+", txt).group(0)
                _, _, year_gap = get_artist_info(at_id, last_year)
                if year_gap == -1:
                    flag = False
                    break
                time.sleep(1)
                sum_year += year_gap
            year_gap = sum_year // len(temp_list)
    if not flag:
        year_gap = -1
    return activity_type, agency, year_gap


def get_artist_sex(artist_name):
    host_url = "http://www.genie.co.kr/search/searchMain?query="
    r = requests.get(host_url + str(artist_name))
    html = r.text
    soup = BeautifulSoup(html, "html.parser")
    if soup is None or soup.find("ul", class_="info-data") is None:
        return None
    artist_sex = soup.find("ul", class_="info-data").find_all("li")[0].find("span", class_="value").text.split("/")[0]
    return artist_sex


def get_artist_likes(artist_id):
    host_url = "https://www.melon.com/artist/getArtistFanNTemper.json?artistId="
    r = requests.get(host_url + str(artist_id), headers=header)
    js = json.loads(r.text)
    artist_likes = js["fanInfo"]["SUMMCNT"]
    return artist_likes


def process_track(track, date, year):
    global before_date

    song_name = track["song_name"]
    artist_name = track["artist_name"]
    album_name = track["album_name"]
    song_id = track["song_id"]
    artist_id = track["artist_id"]
    album_id = track["album_id"]
    rank = track["rank"]
    print("song_name: {}, artist_name: {}".format(song_name, artist_name))

    if song_id not in song_info.keys():
        song_release_date, genre, composer = get_song_detail(song_id)
        song_info[song_id] = {"song_release_date": song_release_date, "genre": genre, "composer": composer}
        print(song_info[song_id])
        time.sleep(1)
    if artist_id not in artist_info.keys():
        artist_activity_type, agency, year_gap = get_artist_info(artist_id, year)
        time.sleep(1)
        artist_sex = get_artist_sex(artist_name)
        time.sleep(1)
        artist_likes = get_artist_likes(artist_id)
        time.sleep(1)
        if agency not in agency_point.keys():
            agency_point[agency] = 0
        agency_point[agency] += artist_likes
        artist_info[artist_id] = {"artist_activity_type": artist_activity_type, "agency": agency,
                                  "artist_sex": artist_sex, "artist_likes": artist_likes, "year_gap": year_gap}
        print(artist_info[artist_id])

    if song_id not in before_chart.keys():
        sd = SongData(song_id, song_name, date, artist_name, album_name, album_id, artist_id)
        sd.update_rank(rank)
        book[(song_id, date)] = sd
        current_chart[song_id] = date
    elif song_id in before_chart.keys():
        book[(song_id, before_chart[song_id])].update_rank(rank)
        current_chart[song_id] = before_chart[song_id]


def cal_date_gap(date1, date2):
    tmp = date1
    year = tmp // 10000
    month = (tmp - year * 10000) // 100
    day = (tmp - year * 10000 - month * 100)
    d1 = datetime.date(year, month, day)
    tmp = date2
    year = tmp // 10000
    month = (tmp - year * 10000) // 100
    day = (tmp - year * 10000 - month * 100)
    d2 = datetime.date(year, month, day)
    return (d1 - d2).days


def make_csv(last_date=20181028):
    song_name = list()
    artist_name = list()
    album_name = list()
    period = list()
    best_rank = list()
    song_release_list = list()
    group_boolean = list()
    censoring = list()
    artist_sex = list()
    genre = list()
    idol = list()
    artist_reputation = list()
    agency_reputation = list()
    composer = list()
    agency = list()

    for k, v in book.items():
        song_name.append(v.song_name)
        artist_name.append(v.artist_name)
        album_name.append(v.album_name)
        if v.end_date is None:
            censoring.append(1)
            period.append(cal_date_gap(last_date, v.date))
        else:
            censoring.append(0)
            period.append(cal_date_gap(v.end_date, v.date))
        best_rank.append(v.rank)
        song_release_list.append(song_info[v.song_id]["song_release_date"])
        artist_sex.append(artist_info[v.artist_id]["artist_sex"])
        if artist_info[v.artist_id]["artist_activity_type"] == "그룹":
            group_boolean.append(1)
        else:
            group_boolean.append(0)
        genre.append(song_info[v.song_id]["genre"])
        artist_reputation.append(artist_info[v.artist_id]["artist_likes"])
        if artist_info[v.artist_id]["agency"] is None:
            agency_reputation.append(None)
        else:
            agency_reputation.append(agency_point[artist_info[v.artist_id]["agency"]])
        composer.append(song_info[v.song_id]["composer"])
        if artist_info[v.artist_id]["year_gap"] == -1:
            idol.append(None)
        elif artist_info[v.artist_id]["year_gap"] < 30:
            idol.append(1)
        else:
            idol.append(0)
        agency.append(artist_info[v.artist_id]["agency"])

    song_name = pd.Series(song_name)
    artist_name = pd.Series(artist_name)
    album_name = pd.Series(album_name)
    period = pd.Series(period)
    censoring = pd.Series(censoring)
    group_boolean = pd.Series(group_boolean)
    best_rank = pd.Series(best_rank)
    song_release_series = pd.Series(song_release_list)
    artist_sex = pd.Series(artist_sex)
    genre = pd.Series(genre)
    idol = pd.Series(idol)
    artist_reputation = pd.Series(artist_reputation)
    agency = pd.Series(agency)
    agency_reputation = pd.Series(agency_reputation)
    composer = pd.Series(composer)
    df = pd.DataFrame({"song_name": song_name, "artist_name": artist_name, "album_name": album_name, "genre": genre,
                       "artist_reputation": artist_reputation, "agency": agency, "agency_reputation": agency_reputation,
                       "composer": composer, "idol": idol, "gender": artist_sex, "group": group_boolean,
                       "birth": song_release_series, "period": period, "best_rank": best_rank, "censoring": censoring})
    df.to_csv("output.csv", encoding='utf-8-sig', index=False)


if __name__ == "__main__":
    process_files(r"C:\Users\inha\Desktop\Projects\Crawling-Scraping\melon_chart_data")
    make_csv(20181028)