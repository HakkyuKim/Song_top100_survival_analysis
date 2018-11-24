
import os
import json
import numpy as np
import pandas as pd
from SongData import SongData
import ast
from collections import Counter
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm


before_date = None
before_chart = dict()
current_chart = dict()
book = dict()
genre_fix_dict = dict()
composer_set = None

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


def process_track(track, date, year):
    global before_date

    song_name = track["song_name"]
    artist_name = track["artist_name"]
    album_name = track["album_name"]
    song_id = track["song_id"]
    artist_id = track["artist_id"]
    album_id = track["album_id"]

    if song_id not in before_chart.keys():
        sd = SongData(song_id, song_name, date, artist_name, album_name, album_id, artist_id)
        book[(song_id, date)] = sd
        current_chart[song_id] = date
    elif song_id in before_chart.keys():
        current_chart[song_id] = before_chart[song_id]


def update_in_out(path, df_argument, last_date=20181028):
    process_files(path)
    chart_in = list()
    chart_out = list()
    for k, v in book.items():
        chart_in.append(v.date)
        if v.end_date is None:
            chart_out.append(last_date)
        else:
            chart_out.append(v.end_date)
    df_argument["chart_in"] = pd.Series(chart_in)
    df_argument["chart_out"] = pd.Series(chart_out)
    df_argument["period"] = df_argument["period"]/7
    df_argument.loc[df_argument["censoring"] == 1, ["period", "chart_out"]] = None
    return df_argument


def update_composer(df_argument):
    composers = list(df_argument["composer"])
    newcomposer = list()
    for composer in composers:
        flag = False
        if composer is np.nan:
            newcomposer.append(0)
            continue
        for name in ast.literal_eval(composer):
            if name in composer_set:
                newcomposer.append(1)
                flag = True
                break
        if not flag:
            newcomposer.append(0)
    df_argument["composer"] = pd.Series(newcomposer)
    return df_argument


def composer_histogram(composers):
    global composer_set
    composer_cnt = Counter()
    composers = list(composers)
    sz = 0
    for composer in composers:
        if composer is np.nan:
            continue
        sz += 1
        for name in ast.literal_eval(composer):
            composer_cnt[name] += 1
    s = sum(composer_cnt.values())
    a_list = [(x[0], round(x[1] / s * 100, 2)) for x in composer_cnt.items() if x[1] > 20]
    a_list = sorted(a_list, key=lambda x: x[1], reverse=True)
    xdata = [x[0] for x in a_list]
    composer_set = set(xdata)
    ydata = [x[1] for x in a_list]
    sns.set_style("whitegrid")
    fm.get_fontconfig_fonts()
    font_location = r'C:/Windows/Fonts/NanumBarunGothic.ttf'
    font_name = fm.FontProperties(fname=font_location).get_name()
    mpl.rc('font', family=font_name)
    g = sns.barplot(x=xdata, y=ydata)
    g.set_title("20곡 이상을 작업한 작곡가(총{}곡)(%)".format(sz))
    g.set_xticklabels(xdata, rotation=70)
    for p in g.patches:
        height = p.get_height()
        g.text(p.get_x() + p.get_width() / 2.,
               height, '{:1.2f}'.format(height), ha="center")
    plt.show()


def genre_histogram(genres):
    genre_cnt = Counter()
    genres = list(genres)
    for genre in genres:
        genre_cnt[genre] += 1
    s = sum(genre_cnt.values())
    a_list = genre_cnt.items()
    a_list = [(x[0], round(x[1]/s*100, 2)) for x in a_list]
    a_list = sorted(a_list, key=lambda x: x[1], reverse=True)
    xdata = [x[0] for x in a_list]
    ydata = [x[1] for x in a_list]
    for idx, genre in enumerate(xdata):
        genre_list = genre.split(",")
        if len(genre_list) == 2:
            if genre_cnt[genre_list[0]] > genre_cnt[genre_list[1]]:
                genre_fix_dict[genre] = genre_list[0]
            else:
                genre_fix_dict[genre] = genre_list[1]
        elif ydata[idx] < 0.9:
            genre_fix_dict[genre] = "etc"
        else:
            genre_fix_dict[genre] = genre
    sns.set_style("whitegrid")
    fm.get_fontconfig_fonts()
    font_location = r'C:/Windows/Fonts/NanumBarunGothic.ttf'
    font_name = fm.FontProperties(fname=font_location).get_name()
    mpl.rc('font', family=font_name)
    g = sns.barplot(x=xdata, y=ydata)
    g.set_title("장르(총{}곡)(%)".format(s))
    g.set_xticklabels(xdata, rotation=70)
    for p in g.patches:
        height = p.get_height()
        g.text(p.get_x() + p.get_width()/2.,
               height, '{:1.2f}'.format(height), ha="center")
    plt.show()


def update_genre(df_argument):
    genres = list(df_argument["genre"])
    newgenres = list()
    for genre in genres:
        newgenres.append(genre_fix_dict[genre])
    df_argument["genre"] = pd.Series(newgenres)
    return df_argument


if __name__ == "__main__":
    df = pd.read_csv(r"C:\Users\inha\Desktop\Projects\Crawling-Scraping\output2.csv")
    df = update_in_out(r"C:\Users\inha\Desktop\Projects\Crawling-Scraping\melon_chart_data", df)
    composer_histogram(df["composer"])
    genre_histogram(df["genre"])
    df = update_composer(df)
    df = update_genre(df)
    df.to_csv("output_fix.csv", encoding='utf-8-sig', index=False)
