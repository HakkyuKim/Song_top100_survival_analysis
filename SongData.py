

class SongData:

    def __init__(self, song_id, song_name, date, artist_name, album_name, album_id, artist_id):
        self.song_id = song_id
        self.song_name = song_name
        self.date = date
        self.artist_name = artist_name
        self.artist_id = artist_id
        self.album_name = album_name
        self.album_id = album_id
        self.rank = None
        self.end_date = None
        self.censoring = 1

    def update_rank(self, rank):
        if self.rank is None:
            self.rank = rank
        else:
            self.rank = min(self.rank, rank)

    def update_end_date(self, end_date):
        self.end_date = end_date

