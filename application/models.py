from .database import db
from flask_login import UserMixin


class Users(db.Model, UserMixin):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    role = db.Column(db.Integer, nullable=False)
    profile_pic = db.Column(db.String, nullable=True)
    playlists = db.relationship("Playlists", backref="user", lazy=True)
    queue = db.relationship("Queue", backref="user", lazy=True)
    blacklist = db.Column(db.Boolean, default=False, nullable=False)
    dark_mode = db.Column(db.Boolean, default=False, nullable=False)
    
    def get_id(self):
        return self.user_id


class Songs(db.Model):
    __tablename__ = 'songs'
    song_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    title = db.Column(db.String, nullable=False)
    singer = db.Column(db.String, nullable=False)
    genre = db.Column(db.String, nullable=False)
    release_date = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.String, nullable=False)
    file_path = db.Column(db.String, nullable=False)
    lyrics = db.Column(db.String, nullable=True)
    cover = db.Column(db.String, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    flagged = db.Column(db.Boolean, default=False, nullable=False)
    user = db.relationship("Users", backref="songs")
    playlists = db.relationship('Playlists', secondary='playlist_song', backref=db.backref('songs', lazy='dynamic'))

    def __repr__(self):
        return f"Songs('{self.title}', '{self.singer}', '{self.genre}', '{self.release_date}', '{self.duration}', '{self.file_path}', '{self.lyrics}', '{self.cover}', '{self.user_id}')"


class Playlists(db.Model):
    __tablename__ = 'playlists'
    playlist_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False)
    access = db.Column(db.String, nullable=False)


class PlaylistSong(db.Model):
    __tablename__ = 'playlist_song'

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.playlist_id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.song_id'), nullable=False)


class Queue(db.Model):
    __tablename__ = 'queue'
    queue_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.song_id'), nullable=False)


class Albums(db.Model):
    __tablename__ = 'albums'
    album_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String, nullable=False)
    genre = db.Column(db.String, nullable=False)
    cover = db.Column(db.String, nullable=True)
    description = db.Column(db.String, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    release_date = db.Column(db.Integer, nullable=False)
    user = db.relationship("Users", backref="albums")
    songs = db.relationship('Songs', secondary='album_song', backref=db.backref('albums', lazy='dynamic'))
    flagged = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"Albums('{self.title}', '{self.cover}', '{self.description}', '{self.user_id}')"


class AlbumSong(db.Model):
    __tablename__ = 'album_song'

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    album_id = db.Column(db.Integer, db.ForeignKey('albums.album_id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.song_id'), nullable=False)


class Ratings(db.Model):
    __tablename__ = 'ratings'

    rating_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.song_id'), nullable=False)
    user = db.relationship("Users", backref="ratings")
    song = db.relationship("Songs", backref="ratings")


# Maybe I need to use Logging for this, instead of creating entry in database.
# This data will be RESET after every month. To get monthly usages.
class Plays(db.Model):
    __tablename__ = 'plays'

    play_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    play_count = db.Column(db.Integer, nullable=False)
    date_created = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.user_id'), nullable=False)
    user = db.relationship("Users", backref="plays")
    song = db.relationship("Songs", backref="plays")
