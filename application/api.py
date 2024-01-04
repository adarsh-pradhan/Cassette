from flask_restful import Resource, reqparse
from main import *
from application.database import *
from application.models import *
import math
import jsonify


# APIs for Index
class IndexAPI(Resource):
    def get(self):
        return {'hello': 'world'}


# API for login a user, so that the user can access protected api calls
class APILogin(Resource):
    def post(self):
        pass


# CRUD APIs for Songs
class SongsAPI(Resource):
    def get(self, song_id):
        pass

    def put(self, song_id):
        pass

    def delete(self, song_id):
        pass

    def post(self):
        pass


# CRUD APIs for Playlists
class PlaylistsAPI(Resource):
    def get(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass

    def post(self):
        pass


# API for fetching Graphs for Admin Dashboard
class AdminGraphsAPI(Resource):
    def get(self):
        pass
