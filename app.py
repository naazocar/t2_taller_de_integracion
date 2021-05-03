from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from base64 import b64encode
import os


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
base_link = 'https://t2-integracion-2021-1.herokuapp.com'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)


class Artist(db.Model):
    id = db.Column(db.String(22), primary_key=True)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    albums = db.Column(db.String(100))
    tracks = db.Column(db.String(100))
    self = db.Column(db.String(100))

    def __init__(self, name, age):
        self.id = b64encode(name.encode()).decode('utf-8')[0:22]
        self.name = name
        self.age = age
        self.albums = base_link + "/artists/" + str(self.id) + "/albums"
        self.tracks = base_link + "/artists/" + str(self.id) + "/tracks"
        self.self = base_link + "/artists/" + str(self.id)
        self.data = {'id': self.id, 'name': self.name, 'age': self.age, 'albums': self.albums, 'tracks': self.tracks,
                     'self': self.self}


class ArtistSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'age', 'albums', 'tracks', 'self')

artist_schema = ArtistSchema()
artists_schema = ArtistSchema(many=True)


class Album(db.Model):
    id = db.Column(db.String(22), primary_key=True)
    name = db.Column(db.String(100))
    genre = db.Column(db.String(100))
    artist = db.Column(db.String(100))
    tracks = db.Column(db.String(100))
    artist_id = db.Column(db.String(22))
    self = db.Column(db.String(100))

    def __init__(self, name, genre, artist_id):
        ide = name + ':' + artist_id
        self.id = b64encode(ide.encode()).decode('utf-8')[0:22]
        self.name = name
        self.genre = genre
        self.artist_id = artist_id
        self.artist = base_link + "/artists/" + artist_id
        self.tracks = base_link + "/albums/" + str(self.id) + "/tracks"
        self.self = base_link + "/albums/" + str(self.id)
        self.data = {'id': self.id, 'artist_id': artist_id, 'name': self.name, 'genre': self.genre,
                     'artist': self.artist, 'tracks': self.tracks, 'self': self.self}


class AlbumSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'genre', 'artist', 'tracks', 'self', 'artist_id')

album_schema = AlbumSchema()
albums_schema = AlbumSchema(many=True)


class Track(db.Model):
    id = db.Column(db.String(22), primary_key=True)
    name = db.Column(db.String(100))
    duration = db.Column(db.Float)
    times_played = db.Column(db.Integer)
    album_id = db.Column(db.String(100))
    artist = db.Column(db.String(100))
    album = db.Column(db.String(100))
    self = db.Column(db.String(100))

    def __init__(self, name, artist_id, album_id, duration):
        self.ide = name + ':' + album_id
        self.id = b64encode(self.ide.encode()).decode('utf-8')[0:22]
        self.name = name
        self.duration = float(duration)
        self.times_played = 0
        self.album_id = album_id
        self.artist = base_link + "/artists/" + str(artist_id)
        self.album = base_link + "/albums/" + str(album_id)
        self.self = base_link + "/tracks/" + str(self.id)
        self.data = {'id': self.id, 'name': self.name, 'duration': self.duration, 'artist': self.artist,
                     'album': self.album, 'self': self.self, 'times_played': self.times_played,
                     'album_id': self.album_id}


class TrackSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'duration', 'times_played', 'album_id', 'artist', 'album', 'self')

track_schema = TrackSchema()
tracks_schema = TrackSchema(many=True)


@app.route('/artists', methods=['GET', 'POST'])
def artists():
    if request.method == 'GET':
        all_artists = Artist.query.all()
        result = artists_schema.dump(all_artists)
        return jsonify(result), 200

    elif request.method == 'POST':
        try:
            name = request.json['name']
            age = request.json['age']
            new_id = b64encode(name.encode()).decode('utf-8')[0:22]
            any_artist = Artist.query.get(new_id)
            if any_artist:
                return artist_schema.jsonify(any_artist), 409
            else:
                new_artist = Artist(name, age)
                db.session.add(new_artist)
                db.session.commit()
                return artist_schema.jsonify(new_artist), 201
        except TypeError:
            return '400: Invalid input', 400
        except KeyError:
            return '400: Invalid input', 400


@app.route('/artists/<ide>', methods=['GET', 'DELETE'])
def artist(ide):
    if request.method == 'GET':
        any_artist = Artist.query.get(ide)
        if any_artist:
            return artist_schema.jsonify(any_artist)
        else:
            return '404: Artist not found', 404

    elif request.method == 'DELETE':
        any_artist = Artist.query.get(ide)
        if any_artist:
            any_link = any_artist.self
            db.session.delete(any_artist)
            any_albums = db.session.query(Album).filter_by(artist=any_link)
            for i in any_albums:
                db.session.delete(i)
            any_tracks = db.session.query(Track).filter_by(artist=any_link)
            for i in any_tracks:
                db.session.delete(i)
            db.session.commit()
            return '204', 204
        else:
            return '404', 404


@app.route('/artists/<artist_id>/albums', methods=['GET', 'POST'])
def artist_album(artist_id):
    if request.method == 'GET':
        any_artist = Artist.query.get(artist_id)
        if any_artist:
            all_albums = Album.query.all()
            result = albums_schema.dump(all_albums)
            return jsonify(result), 200
        else:
            return '404: Artist not found', 404

    elif request.method == 'POST':
        try:
            any_artist = Artist.query.get(artist_id)
            if any_artist:
                name = request.json['name']
                genre = request.json['genre']
                new_str = name + ':' + artist_id
                new_id = b64encode(new_str.encode()).decode('utf-8')[0:22]
                any_album = Album.query.get(new_id)
                if any_album:
                    return album_schema.jsonify(any_album), 409
                else:
                    new_album = Album(name, genre, artist_id)
                    db.session.add(new_album)
                    db.session.commit()
                    return album_schema.jsonify(new_album), 201
            else:
                return '422: Artist not found', 422
        except TypeError:
            return '400: Invalid input', 400
        except KeyError:
            return '400: Invalid input', 400


@app.route('/artists/<artist_id>/tracks', methods=['GET'])
def artist_track(artist_id):
    if request.method == 'GET':
        try:
            any_artist = Artist.query.get(artist_id)
            if any_artist:
                any_link = any_artist.self
                any_tracks = db.session.query(Track).filter_by(artist=any_link)
                return tracks_schema.jsonify(any_tracks)
            return'404', 404
        except KeyError:
            return '404: Artist not found', 404


@app.route('/artists/<artist_id>/albums/play', methods=['PUT'])
def play_artist(artist_id):
    try:
        any_artist = Artist.query.get(artist_id)
        if any_artist:
            any_link = any_artist.self
            any_albums = db.session.query(Album).filter_by(artist=any_link)
            for i in any_albums:
                any_link2 = i.self
                any_tracks = db.session.query(Track).filter_by(album=any_link2)
                for j in any_tracks:
                    j.times_played += 1
            db.session.commit()
            return '200: Artist played', 200
        else:
            return '404: Artist not found', 404
    except KeyError:
        return '404: Artist not found', 404


@app.route('/albums', methods=['GET'])
def albums():
    all_albums = Album.query.all()
    result = albums_schema.dump(all_albums)
    return jsonify(result), 200


@app.route('/albums/<ide>', methods=['GET', 'DELETE'])
def album(ide):
    if request.method == 'GET':
        any_album = Album.query.get(ide)
        if any_album:
            return album_schema.jsonify(any_album)
        else:
            return '404: Album not found', 404

    elif request.method == 'DELETE':
        any_album = Album.query.get(ide)
        if any_album:
            any_link = any_album.self
            db.session.delete(any_album)
            any_tracks = db.session.query(Track).filter_by(album=any_link)
            for i in any_tracks:
                db.session.delete(i)
            db.session.commit()
            return '204', 204
        else:
            return '404', 404


@app.route('/albums/<album_id>/play', methods=['PUT'])
def play_album(album_id):
    try:
        any_album = Album.query.get(album_id)
        if any_album:
            any_link = any_album.self
            any_tracks = db.session.query(Track).filter_by(album=any_link)
            for i in any_tracks:
                i.times_played += 1
            db.session.commit()
            return '200: Album played', 200
        else:
            return '404: Album not found', 404
    except KeyError:
        return '404: Album not found', 404


@app.route('/albums/<album_id>/tracks', methods=['GET', 'POST'])
def album_track(album_id):
    if request.method == 'GET':
        any_album = Album.query.get(album_id)
        if any_album:
            any_link = any_album.self
            all_tracks = db.session.query(Track).filter_by(album=any_link)
            result = tracks_schema.dump(all_tracks)
            return jsonify(result), 200
        else:
            return '404: Album not found', 404

    elif request.method == 'POST':
        try:
            any_album = Album.query.get(album_id)
            if any_album:
                name = request.json['name']
                duration = request.json['duration']
                new_str = name + ':' + album_id
                new_id = b64encode(new_str.encode()).decode('utf-8')[0:22]
                artist_id = any_album.artist_id
                any_track = Track.query.get(new_id)
                if any_track:
                    return track_schema.jsonify(any_track), 409
                else:
                    new_track = Track(name, artist_id, album_id, duration)
                    db.session.add(new_track)
                    db.session.commit()
                    return track_schema.jsonify(new_track), 201
            else:
                return '422: Album not found', 422
        except TypeError:
            return '400: Invalid input', 400
        except KeyError:
            return '400: Invalid input', 400


@app.route('/tracks', methods=['GET'])
def tracks():
    all_tracks = Track.query.all()
    result = tracks_schema.dump(all_tracks)
    return jsonify(result), 200


@app.route('/tracks/<ide>', methods=['GET', 'DELETE'])
def track(ide):
    if request.method == 'GET':
        any_track = Track.query.get(ide)
        if any_track:
            return track_schema.jsonify(any_track)
        else:
            return '404: Track not found', 404

    elif request.method == 'DELETE':
        any_track = Track.query.get(ide)
        if any_track:
            db.session.delete(any_track)
            db.session.commit()
            return '204', 204
        else:
            return '404', 404


@app.route('/tracks/<track_id>/play', methods=['PUT'])
def play_track(track_id):
    any_track = Track.query.get(track_id)
    if any_track:
        any_track.times_played += 1
        db.session.commit()
        return '200: Track played', 200
    else:
        return '404: Track not found', 404


if __name__ == '__main__':
    app.run(debug=True)
