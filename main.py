from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from flask_restful import Api
from werkzeug.security import generate_password_hash, check_password_hash
from application.database import db
from application.models import Users, Songs, Albums, AlbumSong, Playlists, PlaylistSong, Queue, Ratings, Plays
from datetime import datetime
from matplotlib import pyplot as plt
from sqlalchemy import func
import math
import os
from application.config import Config
from mutagen.mp3 import MP3
import logging


# ------------------------------------------ SQL codes for remembering: ------------------------------------------------
# To fetch all the rows from a table:
#     playlists = db.session.query(Albums)
#
# To fetch a specific user from Users table:
#     user = db.get_or_404(Users, current_user.user_id)
#
# To fetch all rows with a filtered condition:
#     playlists = Playlists.query.filter_by(access="public").all()
# ----------------------------------------------------------------------------------------------------------------------

# ------------------------------ Initializing logging config
logging.basicConfig(filename='debug.log',
                    level=logging.DEBUG,
                    format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

# ------------------------------ Initializing the Flask app
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
app.app_context().push()
app.config.from_object(Config)

with app.app_context():
    db.create_all()

# Migrate
migrate = Migrate(app, db)

# Initializing the API
api = Api(app)

# Creating an Admin account into the Users table, if it is already not there
# Also, Admin has access to most of the pages
if Users.query.filter_by(email="admin@cassette.com").first():
    pass
else:
    name = "Admin"
    email = "admin@cassette.com"
    password = os.getenv("ADMIN_PASSWORD")
    hashed_password = generate_password_hash(password)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    role = 0
    # Saving the Admin into the Users table
    try:
        new_user = Users(name=name,
                         email=email,
                         password=hashed_password,
                         created_at=datetime.now(),
                         role=0)
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # flash('Error creating Admin account. Please try again.', category='error')
        print(str(e))
    finally:
        db.session.close()


# ------------------------------ Login Manager
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


# -------------------------------------Functions
# Function: Convert minutes into seconds
def to_minute_seconds(seconds):
    return f"{math.floor(seconds // 60)}:{math.floor(seconds % 60)}"


# Function: Generate Monthly Usage Graph
def monthly_usage_graph_generator():
    # Functionality to generate monthly_plays graph
    plays = Plays.query.all()
    monthly_plays = {}

    for play in plays:
        play_date = datetime.fromtimestamp(play.date_created)
        year_month = (play_date.year, play_date.month)
        # Check if the year_month key exists
        if year_month not in monthly_plays:
            monthly_plays[year_month] = 0

        monthly_plays[year_month] += play.play_count

    year_months = sorted(monthly_plays.keys())
    monthly_counts = [monthly_plays[ym] for ym in year_months]

    plt.figure(figsize=(10, 6))
    plt.plot(year_months, monthly_counts, marker='o')
    plt.title('Monthly Usage')
    plt.xlabel('Year-Month')
    plt.ylabel('Plays')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Now, saving this file into my static/img directory
    graph_filename = 'monthly_usage_graph.png'
    image_path = os.path.join(app.root_path, 'static', 'img', graph_filename)
    plt.savefig(image_path)


# Calling monthly_usage_graph_generator function here, to generate a graph
monthly_usage_graph_generator()


# Function to generate Song VS Plays graph
def generate_song_vs_plays_graph():
    songs = Songs.query.all()
    song_play_counts = {}
    for song in songs:
        play_count = Plays.query.filter_by(song_id=song.song_id).count()
        song_play_counts[song.title] = play_count
    sorted_song_titles = sorted(song_play_counts.keys(), key=lambda x: song_play_counts[x])
    sorted_play_counts = [song_play_counts[title] for title in sorted_song_titles]
    plt.figure(figsize=(12, 8))
    plt.barh(sorted_song_titles, sorted_play_counts, color='skyblue')
    plt.xlabel('Number of Plays')
    plt.title('Song vs. Plays')
    plt.tight_layout()

    # Again, saving this file into my static/img directory too
    graph_filename = 'song_vs_plays_graph.png'
    image_path = os.path.join(app.root_path, 'static', 'img', graph_filename)
    plt.savefig(image_path)


# Calling monthly_usage_graph_generator function here, to generate a graph
generate_song_vs_plays_graph()


# -------------------------------------Routes/Controllers
# Route for the Index page
@app.route('/')
def index():
    return render_template("index.html")


# -------------------------------------Route to load user into the current session
@login_manager.user_loader
def load_user(user_id):
    # return Users.Session.get(int(user_id))
    return db.session.get(Users, user_id)


# -------------------------------------Route for New User Registration page
@app.route('/user_registration', methods=['GET', 'POST'])
def user_registration():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        if "@" in email:
            pass
        else:
            error = "Enter a valid email!"
            flash("Enter a valid email!")
            return render_template("user_registration.html", error=error)

        existing_user = Users.query.filter_by(email=email).first()
        if existing_user:

            # Admin login
            if existing_user.role == 0:
                login_user(existing_user)
                # Redirect to admin dashboard or admin-specific page
                return redirect(url_for('admin_dashboard'))

            # User login
            elif existing_user.role == 1 or existing_user.role == 2:
                # Redirect to normal user dashboard or user-specific page
                login_user(existing_user)
                return redirect(url_for('user_dashboard'))
        else:
            hashed_password = generate_password_hash(password)
            try:
                new_user = Users(name=name,
                                 email=email,
                                 password=hashed_password,
                                 created_at=datetime.now(),
                                 role=1,
                                 dark_mode=False)
                db.session.add(new_user)
                db.session.commit()
                flash('Account created successfully', category='success')
                user = Users.query.filter_by(email=email).first()
                login_user(user)
                return redirect(url_for('user_dashboard'))
            except Exception as error:
                db.session.rollback()
                flash('Error creating account. Please try again.', category='error')
                print(str(error))
            finally:
                db.session.close()
    return render_template("user_registration.html")


# -------------------------------------Route for Login page
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    error = None
    endpoint_title = "admin_login"

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Users.query.filter_by(email=email).first()

        if "@" in email:
            pass
        else:
            error = "Enter a valid email!"
            return render_template("login.html", error=error)

        if user and check_password_hash(user.password, password):

            # Admin login
            if user.role == 0:
                login_user(user)
                # Redirect to admin dashboard or admin-specific page
                flash('You were successfully logged in as an Admin!')
                return redirect(url_for('admin_dashboard'))

            # User login
            elif user.role == 1 or user.role == 2:
                # Redirect to User Login Page
                flash('Log in as a Standard User!')
                return redirect(url_for('login'))
        else:
            error = 'Invalid credentials'
            print(error)
    return render_template('admin_login.html', endpoint_title=endpoint_title)


# -------------------------------------Route for Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    endpoint_title = "login"

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Users.query.filter_by(email=email).first()

        if "@" in email:
            pass
        else:
            error = "Enter a valid email!"
            return render_template("login.html", error=error)

        if user and check_password_hash(user.password, password):

            if not user.blacklist:
                # Admin login
                if user.role == 0:
                    # Redirect to admin dashboard or admin-specific page
                    flash('Log in as an Admin!')
                    return redirect(url_for('admin_login'))

                # User login
                elif user.role == 1 or user.role == 2:
                    # Redirect to normal user dashboard or user-specific page
                    login_user(user)
                    flash('You were successfully logged in as a Standard User!')
                    return redirect(url_for('user_dashboard'))
            else:
                flash('You have been blacklisted! Contact the Admin.')
                return redirect(url_for('login'))
        else:
            error = 'Invalid credentials'
            print(error)
    return render_template('login.html', endpoint_title=endpoint_title)


# -------------------------------------Route to handle Admin Dashboard functionality
@app.route('/admin_dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    user = db.get_or_404(Users, current_user.user_id)

    # Logic to display admin dashboard
    standard_users_count = db.session.query(Users).filter_by(role=1).count()
    creators_count = db.session.query(Users).filter_by(role=2).count()
    songs_count = db.session.query(Songs).count()
    albums_count = db.session.query(Albums).count()
    genres_count = db.session.query(Songs.genre, func.count(Songs.genre)).group_by(Songs.genre).count()

    # Fetching the monthly_usage_graph_filename
    monthly_usage_graph_filename = "/static/img/monthly_usage_graph.png"
    # Fetching the monthly_usage_graph_filename
    song_vs_play_graph_filename = "/static/img/song_vs_plays_graph.png"

    # Song listen counts
    song_counts = {}
    plays = Plays.query.with_entities(Plays.song_id, func.sum(Plays.play_count)).group_by(Plays.song_id).all()
    for song_id, count in plays:
        if song_id not in song_counts:
            song_counts[song_id] = 0
        song_counts[song_id] += count

    # User listens counts
    user_counts = {}
    plays = Plays.query.with_entities(Plays.user_id, func.sum(Plays.play_count)).group_by(Plays.user_id).all()
    for user_id, count in plays:
        if user_id not in user_counts:
            user_counts[user_id] = 0
        user_counts[user_id] += count

    return render_template('admin_dashboard.html',
                           current_user_level=0,
                           user=user,
                           standard_users_count=standard_users_count,
                           creators_count=creators_count,
                           songs_count=songs_count,
                           albums_count=albums_count,
                           genres_count=genres_count,
                           monthly_usage_graph_filename=monthly_usage_graph_filename,
                           song_vs_play_graph_filename=song_vs_play_graph_filename,
                           song_counts=song_counts,
                           user_counts=user_counts)


# -------------------------------------Route to list all the users
@app.route('/admin_dashboard/all_users', methods=['GET', 'POST'])
@login_required
def all_users():
    user = db.get_or_404(Users, current_user.user_id)
    users = db.session.query(Users)
    return render_template('all_users.html',
                           user=user,
                           users=users,
                           current_user_level=current_user.role)


# -------------------------------------Route to Flag a song
@app.route('/flag_song/<int:song_id>', methods=['GET', 'POST'])
@login_required
def flag_song(song_id):
    song_to_flag = Songs.query.filter_by(song_id=song_id).first()
    song_name = song_to_flag.title
    # If statement, to remove flag from a song
    if song_to_flag.flagged:
        try:
            song_to_flag.flagged = False
            db.session.commit()

        except Exception as error:
            db.session.rollback()
            flash(f"Error removing flag from song: {error}")
        finally:
            db.session.close()
            flash(f"Removed flag from Song '{song_name}' successfully!")
        return redirect(url_for('all_songs'))

    # Else block, to remove Flag from a song
    else:
        try:
            song_to_flag.flagged = True
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            flash(f"Error flagging song: {error}")
        finally:
            db.session.close()
            flash(f"Song '{song_name}' flagged successfully!")
        return redirect(url_for('all_songs'))


# -------------------------------------Route to Flag a song
@app.route('/flag_album/<int:album_id>', methods=['GET', 'POST'])
@login_required
def flag_album(album_id):
    album_to_flag = Albums.query.filter_by(album_id=album_id).first()
    album_name = album_to_flag.title
    # If statement, to remove flag from a song
    if album_to_flag.flagged:
        try:
            album_to_flag.flagged = False
            db.session.commit()

        except Exception as error:
            db.session.rollback()
            flash(f"Error removing flag from album: {error}")
        finally:
            db.session.close()
            flash(f"Removed flag from Song '{album_name}' successfully!")
        return redirect(url_for('all_albums'))

    # Else block, to remove Flag from an album
    else:
        try:
            album_to_flag.flagged = True
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            flash(f"Error flagging album: {error}")
        finally:
            db.session.close()
            flash(f"Album '{album_name}' flagged successfully!")
        return redirect(url_for('all_albums'))


# -------------------------------------Route for deleting a user (Through Admins access)
@app.route('/admin_dashboard/all_users/delete_user/<int:user_id>', methods=['GET', 'POST'])
def delete_user(user_id):

    # To stop the Admin from self-destruction
    if user_id != current_user.user_id:

        try:
            user_to_delete = Users.query.filter_by(user_id=user_id).first()

            # Delete related entries from other tables
            Playlists.query.filter_by(user_id=user_id).delete()
            Queue.query.filter_by(user_id=user_id).delete()
            Ratings.query.filter_by(user_id=user_id).delete()

            # Fetch associated albums and delete related songs
            albums_to_delete = Albums.query.filter_by(user_id=user_id).all()
            for album in albums_to_delete:
                Songs.query.filter(Songs.song_id.in_([song.song_id for song in album.songs])).delete(synchronize_session=False)
                db.session.delete(album)

            # Delete the user
            db.session.delete(user_to_delete)
            db.session.commit()
            print("User, related data, songs, and albums deleted successfully")
        except Exception as error:
            db.session.rollback()
            print(f"Error deleting user: {error}")
        finally:
            db.session.close()
        return redirect(url_for('all_users'))

    else:
        flash("You cannot delete our own credentials!")


# -------------------------------------Route to blacklist a user
@app.route('/admin_dashboard/all_users/blacklist_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def blacklist_user(user_id):
    user_to_blacklist = Users.query.filter_by(user_id=user_id).first()
    user_name = user_to_blacklist.name
    # If statement, to whitelist a user
    if user_to_blacklist.blacklist:
        try:
            user_to_blacklist.blacklist = False
            db.session.commit()

        except Exception as error:
            db.session.rollback()
            flash(f"Error whitelisting user: {error}")
        finally:
            db.session.close()
            flash(f"User '{user_name}' whitelisted successfully!")
        return redirect(url_for('all_users'))

    # Else block, to blacklist a user
    else:
        try:
            user_to_blacklist.blacklist = True
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            flash(f"Error blacklisting user: {error}")
        finally:
            db.session.close()
            flash(f"User '{user_name}' blacklisted successfully!")
        return redirect(url_for('all_users'))


# -------------------------------------Route to handle the User Dashboard functionality
@app.route('/user_dashboard', methods=['GET', 'POST'])
@login_required
def user_dashboard():
    user = db.get_or_404(Users, current_user.user_id)
    songs = db.session.query(Songs)
    playlists = Playlists.query.filter_by(user_id=current_user.user_id)

    # Sorted Songs by average Rating
    # The "Recommended Songs" section inside the else-block in Search Results
    # isn't taking this as an input
    sorted_songs = (
        db.session.query(Songs, func.avg(Ratings.rating).label('avg_rating'))
        .join(Ratings)
        .group_by(Songs.song_id)
        .order_by(func.avg(Ratings.rating).desc())
        .all()
    )

    # Search Functionality
    if request.method == 'GET':

        # fetching the search_query
        search_query = request.args.get('search_query', '').lower()

        # Checking if the search query is empty
        if len(search_query) == 0:
            return render_template('user_dashboard.html',
                                   current_user_level=1,
                                   user=user,
                                   songs=songs,
                                   sorted_songs=sorted_songs,
                                   playlists=playlists)
        else:
            pass

        # Filtering songs from the Songs table from the database
        filtered_songs = Songs.query.filter(
            Songs.title.ilike(f'%{search_query}%') |
            Songs.singer.ilike(f'%{search_query}%') |
            Songs.genre.ilike(f'%{search_query}%')
        ).all()

        # Filtering albums from the Albums table from the database
        filtered_albums = Albums.query.filter(Albums.title.ilike(f'%{search_query}%')).all()

        # Filtering by Artists(Creators)
        filtered_creators = Users.query.filter(Users.name.ilike(f'%{search_query}%')).all()

        # A boolean output, just to use in the logic in "for" loop for Search component in Jinja2
        if len(filtered_songs) > 0:
            filtered_songs_bool = True
        else:
            filtered_songs_bool = False

        # A boolean output for no input in Search component in Jinja2
        if search_query != "":
            search_query_bool = True
        else:
            search_query_bool = False

        return render_template('user_dashboard.html',
                               current_user_level=1,
                               search_query=search_query,
                               search_query_bool=search_query_bool,
                               filtered_songs=filtered_songs,
                               filtered_songs_bool=filtered_songs_bool,
                               user=user,
                               songs=songs,
                               playlists=playlists,
                               sorted_songs=sorted_songs)

    # Music Streaming functionality
    if request.method == 'POST':
        if 'stream' in request.form:
            song_id = request.form.get('song_id')
            song_to_stream = Songs.query.filter_by(song_id=song_id).first()
            return render_template('user_dashboard.html',
                                   current_user_level=1,
                                   user=user,
                                   songs=songs,
                                   playlists=playlists,
                                   song_to_stream=song_to_stream,
                                   song_to_stream_duration=to_minute_seconds(float(song_to_stream.duration)),
                                   sorted_songs=sorted_songs)
    else:
        return render_template('user_dashboard.html',
                               current_user_level=1,
                               user=user,
                               songs=songs,
                               playlists=playlists,
                               sorted_songs=sorted_songs)


# -------------------------------------Route for Creator registration
@app.route('/creator_registration', methods=['GET', 'POST'])
@login_required
def creator_registration():
    user = db.get_or_404(Users, current_user.user_id)

    return render_template('creator_registration.html',
                           current_user_level=1,
                           user=user)


# -------------------------------------Route for Creator dashboard
@app.route('/creator_dashboard', methods=['GET', 'POST'])
@login_required
def creator_dashboard():
    endpoint_title = "Creator Dashboard"
    # If Normal User account detected, redirect to the creator registration page
    if current_user.role == 1:
        return redirect(url_for('creator_registration'))
    else:
        user = db.get_or_404(Users, current_user.user_id)
        songs = db.session.query(Songs).filter_by(user_id=current_user.user_id).all()
        playlists = db.session.query(Playlists).filter_by(user_id=current_user.user_id).all()
        albums = db.session.query(Albums).filter_by(user_id=current_user.user_id).all()
        ratings = db.session.query(Ratings).filter_by(user_id=current_user.user_id).all()

        # Various counts
        my_songs_count = len(songs)
        my_albums_count = len(albums)
        my_playlists_count = len(playlists)

        my_songs_average_rating = db.session.query(func.avg(Ratings.rating)) \
            .join(Songs, Ratings.song_id == Songs.song_id) \
            .filter(Songs.user_id == current_user.user_id) \
            .scalar()
        if my_songs_average_rating is not None:
            my_songs_average_rating = round(my_songs_average_rating, 1)
        else:
            my_songs_average_rating = 0

        # Function to show the performance of the songs uploaded by the current user
        user_id = current_user.user_id
        song_play_counts = {}
        plays = Plays.query.with_entities(Plays.song_id, func.sum(Plays.play_count)).filter_by(
            user_id=user_id).group_by(Plays.song_id).all()
        for song_id, count in plays:
            if song_id not in song_play_counts:
                song_play_counts[song_id] = 0
            song_play_counts[song_id] += count

        # song_vs_plays_graph_filename = "song_vs_plays_graph.png"
        song_vs_plays_graph_filename = "/static/img/song_vs_plays_graph.png"

        return render_template('creator_dashboard.html',
                               current_user_level=2,
                               endpoint_title=endpoint_title,
                               user=user,
                               songs=songs,
                               playlists=playlists,
                               albums=albums,
                               my_songs_count=my_songs_count,
                               my_albums_count=my_albums_count,
                               my_playlists_count=my_playlists_count,
                               my_songs_average_rating=my_songs_average_rating,
                               song_play_counts=song_play_counts,
                               song_vs_plays_graph_filename=song_vs_plays_graph_filename)


# -------------------------------------Route for User role change to Creator role
@app.route('/update_role', methods=['GET', 'POST'])
@login_required
def update_current_user_role():
    if current_user:
        # Assuming the role 1 should be updated to 2
        if current_user.role == 1:
            try:
                current_user.role = 2  # Change the user's role from 1 to 2
                db.session.commit()
            except Exception as error:
                db.session.rollback()
                flash('Error updating role of the selected account. Please try again.', category='error')
                print(str(error))
            finally:
                db.session.close()
            return redirect(url_for('upload_song'))
        else:
            return redirect(url_for('creator_dashboard'))
    return "User not found"


# -------------------------------------Route for Welcoming page for new Creator accounts to upload their first song
@app.route('/upload_song', methods=['GET', 'POST'])
@login_required
def upload_song():
    user = db.get_or_404(Users, current_user.user_id)

    return render_template('upload_song.html',
                           current_user_level=2,
                           user=user)


# -------------------------------------Route for uploading a song
@app.route('/upload_song_form', methods=['GET', 'POST'])
@login_required
def upload_song_form():
    user = db.get_or_404(Users, current_user.user_id)

    if request.method == 'POST' and user.role == 2:
        try:
            title = request.form['title']
            singer = request.form['singer']
            genre = request.form['genre']
            release_date = request.form['release_date']
            lyrics = request.form['lyrics']
            user_id = user.user_id

            # Save the song file into the uploads folder
            music_file = request.files['music_file']
            music_file_path = f'static/audio/{title}.mp3'  # Unique path for music file
            music_file.save(music_file_path)

            # Save the album cover picture into the uploads folder
            cover_file = request.files['cover_file']
            cover_file_path = f'static/covers/{title}.jpg'  # Unique path for cover file
            cover_file.save(cover_file_path)

            # Get the duration details of mp3 file
            duration = MP3(music_file_path).info.length

            # Save the new song object into the database
            new_song = Songs(
                title=title,
                singer=singer,
                genre=genre,
                release_date=release_date,
                duration=duration,
                file_path=music_file_path,
                lyrics=lyrics,
                cover=cover_file_path,
                user_id=user_id
            )
            db.session.add(new_song)
            db.session.commit()
            flash("'" + title + "' has been successfully uploaded!")
        except Exception as error:
            db.session.rollback()
            flash('Error uploading the new song. Please try again.', category='error')
            print(str(error))
        finally:
            db.session.close()

        # Redirect to the Creator Dashboard
        return redirect(url_for('creator_dashboard'))

    return render_template('upload_song_form.html',
                           current_user_level=2,
                           user=user)


# -------------------------------------Route for listing  a User's Songs
@app.route('/creator_dashboard/my_songs', methods=['GET', 'POST'])
@login_required
def my_songs():
    user = db.get_or_404(Users, current_user.user_id)
    songs = Songs.query.filter_by(user_id=current_user.user_id)

    # Need to add functionality for that "Play" button beside playlist name

    return render_template('my_songs.html',
                           current_user_level=2,
                           user=user,
                           songs=songs)


# -------------------------------------Route for viewing a song
@app.route('/view_song/<int:song_id>', methods=['GET', 'POST'])
@login_required
def view_song(song_id):
    user = db.get_or_404(Users, current_user.user_id)
    song = db.session.query(Songs).filter_by(song_id=song_id).first()
    average_rating = db.session.query(func.avg(Ratings.rating)) \
        .join(Songs, Ratings.song_id == Songs.song_id) \
        .scalar()
    if average_rating is not None:
        rating = math.floor(average_rating)
    else:
        rating = 0

    # Music Streaming functionality
    if request.method == 'POST':
        if 'stream' in request.form:
            song_id = request.form.get('song_id')
            song_to_stream = Songs.query.filter_by(song_id=song_id).first()
            return render_template('view_song.html',
                                   current_user_level=1,
                                   user=user,
                                   playlist=playlist,
                                   song=song,
                                   rating=rating,
                                   song_to_stream=song_to_stream,
                                   song_to_stream_duration=to_minute_seconds(float(song_to_stream.duration)))

    else:
        return render_template('view_song.html',
                               current_user_level=1,
                               user=user,
                               song=song,
                               rating=rating,
                               song_duration=to_minute_seconds(float(song.duration)))


# NEED TO IMPLEMENT THE RATING FUNCTION FOR ANY SONG IN THE "view_song" ROUTE


# -------------------------------------Route for editing songs
@app.route('/edit_song/<int:song_id>', methods=['GET', 'POST'])
@login_required
def edit_song(song_id):
    user = db.get_or_404(Users, current_user.user_id)
    song = db.session.query(Songs).filter_by(song_id=song_id).first()
    
    # Checking if the song exists
    if song:
        # Double-checking if that current user was also the uploader of that song
        if current_user.role == 2 and user and song.user_id == current_user.user_id:
            if request.method == 'POST':
                try:
                    # Update song details based on the form data
                    song.title = request.form['title']
                    song.singer = request.form['singer']
                    song.genre = request.form['genre']
                    song.release_date = request.form['release_date']
                    song.lyrics = request.form['lyrics']

                    # Update the music file if provided
                    # music_file = request.files['music_file']
                    # if music_file:
                    #     music_file_path = f'uploads/{song.title}_{music_file.filename}'
                    #     music_file.save(music_file_path)
                    #     song.file_path = music_file_path
                    #     # Update the duration of the song
                    #     song.duration = MP3(music_file_path).info.length
                    
                    # Update the music file if provided
                    if request.files['music_file']:
                        music_file = request.files['music_file']
                        music_file_path = f'uploads/{song.title}_{music_file.filename}'
                        music_file.save(music_file_path)
                        song.file_path = music_file_path
                        # Update the duration of the song
                        song.duration = MP3(music_file_path).info.length

                    # Update the cover file if provided
                    if request.files['cover_file']:
                        cover_file = request.files['cover_file']
                        cover_file_path = f'uploads/{song.title}_{cover_file.filename}'
                        cover_file.save(cover_file_path)
                        song.cover = cover_file_path

                    # Commit the changes to the database
                    db.session.commit()
                except Exception as error:
                    db.session.rollback()
                    flash('Error Editing the song. Please try again.', category='error')
                    print(str(error))
                finally:
                    db.session.close()
                    # Redirect to the Creator Dashboard
                    return redirect(url_for('my_songs'))
                    # return redirect(url_for('view_song', song_id=song.song_id))

            return render_template('edit_song.html',
                                current_user_level=2,
                                user=user,
                                song=song)
        else:
            return redirect(url_for('view_song', song_id=song.song_id))
    else:
        # Handle the case where the song ID doesn't exist
        # (e.g., show an error message)
        pass


# -------------------------------------Route for deleting a song
@app.route('/delete_song/<int:song_id>', methods=['GET', 'POST'])
@login_required
def delete_song(song_id):
    song_to_delete = Songs.query.filter_by(song_id=song_id).first()
    song_name = song_to_delete.title

    # deleting from Admin account
    if current_user.role == 0:
        if song_to_delete:
            # Delete the song from the database
            try:
                # Delete related entries first, from other models
                PlaylistSong.query.filter_by(song_id=song_id).delete()
                Ratings.query.filter_by(song_id=song_id).delete()
                Plays.query.filter_by(song_id=song_id).delete()

                # And then, delete the song
                db.session.delete(song_to_delete)
                db.session.commit()
            except Exception as error:
                db.session.rollback()
                flash('Error deleting the song. Please try again.', category='error')
                print(str(error))
            finally:
                db.session.close()
                flash(("Song " + song_name + "is deleted from the database"))
                return redirect(url_for('admin_dashboard'))
        else:
            print("couldn't find any song with that song_id")
        return redirect(url_for('admin_dashboard'))

    # deleting from Creator account
    elif current_user.role == 2 and current_user.user_id == song_to_delete.user_id:
        if song_to_delete:
            # Delete the song from the database
            try:
                # Delete related entries first, from other models
                PlaylistSong.query.filter_by(song_id=song_id).delete()
                Ratings.query.filter_by(song_id=song_id).delete()
                Plays.query.filter_by(song_id=song_id).delete()

                # And then, delete the song
                db.session.delete(song_to_delete)
                db.session.commit()
                print("Song is deleted from the database")
            except Exception as error:
                db.session.rollback()
                flash('Error deleting the song. Please try again.', category='error')
                print(str(error))
            finally:
                db.session.close()
                flash(("Song '" + song_name + "' is deleted from the database"))
                return redirect(url_for('creator_dashboard'))
        else:
            print("couldn't find any song with that song_id")
        return redirect(url_for('creator_dashboard'))

    else:
        return redirect(url_for('view_song'), song_id)


# -------------------------------------Route for deleting an album
@app.route('/delete_album/<int:album_id>', methods=['GET', 'POST'])
@login_required
def delete_album(album_id):
    album_to_delete = Albums.query.filter_by(album_id=album_id).first()
    album_name = album_to_delete.title
    # Deleting from Admin account
    if current_user.role == 0:
        if album_to_delete:
            try:
                # Delete related entries first, from other models
                AlbumSong.query.filter_by(album_id=album_id).delete()
                # Add additional deletions as needed for related tables

                # Then delete the album
                db.session.delete(album_to_delete)
                db.session.commit()
            except Exception as error:
                db.session.rollback()
                flash('Error deleting the album. Please try again.', category='error')
                print(str(error))
            finally:
                db.session.close()
                flash(f"Album '{album_name}' is deleted from the database")
                return redirect(url_for('admin_dashboard'))
        else:
            flash("Couldn't find any album with that album_id")
        return redirect(url_for('admin_dashboard'))

    # Deleting from Creator account
    elif current_user.role == 2 and current_user.user_id == album_to_delete.user_id:
        if album_to_delete:
            try:
                # Delete related entries first, from other models
                AlbumSong.query.filter_by(album_id=album_id).delete()
                # Add additional deletions as needed for related tables

                # Then delete the album
                db.session.delete(album_to_delete)
                db.session.commit()
                print("Album is deleted from the database")
            except Exception as error:
                db.session.rollback()
                flash('Error deleting the album. Please try again.', category='error')
                print(str(error))
            finally:
                db.session.close()
                flash(f"Album '{album_name}' is deleted from the database")
                return redirect(url_for('creator_dashboard'))
        else:
            print("Couldn't find any album with that album_id")
        return redirect(url_for('creator_dashboard'))

    else:
        return redirect(url_for('my_albums'), album_id)


# -------------------------------------Route for deleting a playlist
@app.route('/delete_playlist/<int:playlist_id>', methods=['GET', 'POST'])
@login_required
def delete_playlist(playlist_id):
    playlist_to_delete = Playlists.query.filter_by(playlist_id=playlist_id).first()

    # deleting from Admin account
    if current_user.role == 0:
        if playlist_to_delete:
            # Delete the playlist from the database
            try:
                # Delete related entries first, from other models
                PlaylistSong.query.filter_by(playlist_id=playlist_id).delete()
                # Add other related deletions as necessary

                # And then, delete the playlist
                db.session.delete(playlist_to_delete)
                db.session.commit()
            except Exception as error:
                db.session.rollback()
                flash('Error deleting the playlist. Please try again.', category='error')
                print(str(error))
            finally:
                db.session.close()
                flash("Playlist is deleted from the database")
                return redirect(url_for('admin_dashboard'))
        else:
            flash("couldn't find any playlist with that playlist_id")
        return redirect(url_for('admin_dashboard'))
    
    # deleting from Standard User account
    if current_user.role == 1:
        if playlist_to_delete:
            if playlist_to_delete.user_id == current_user.user_id:
                # Delete the playlist from the database
                try:
                    # Delete related entries first, from other models
                    PlaylistSong.query.filter_by(playlist_id=playlist_id).delete()
                    # Add other related deletions as necessary

                    # And then, delete the playlist
                    db.session.delete(playlist_to_delete)
                    db.session.commit()
                except Exception as error:
                    db.session.rollback()
                    flash('Error deleting the playlist. Please try again.', category='error')
                    print(str(error))
                finally:
                    db.session.close()
                    flash("Playlist is deleted from the database.")
                    return redirect(url_for('user_dashboard'))
            else:
                flash("You can only delete your own playlists!")
            return redirect(url_for('user_dashboard'))
        else:
            flash("couldn't find any playlist with that playlist_id.")
        return redirect(url_for('user_dashboard'))

    # deleting from Creator account
    elif current_user.role == 2:
        if playlist_to_delete:
            if current_user.user_id == playlist_to_delete.user_id:
                # Delete the playlist from the database
                try:
                    # Delete related entries first, from other models
                    PlaylistSong.query.filter_by(playlist_id=playlist_id).delete()
                    # Add other related deletions as necessary

                    # And then, delete the playlist
                    db.session.delete(playlist_to_delete)
                    db.session.commit()
                    print("Playlist is deleted from the database")
                except Exception as error:
                    db.session.rollback()
                    flash('Error deleting the playlist. Please try again.', category='error')
                    print(str(error))
                finally:
                    db.session.close()
                    flash("Playlist is deleted from the database")
                    return redirect(url_for('creator_dashboard'))
            else:
                flash("You can only delete your own playlists!")
            return redirect(url_for('creator_dashboard'))
        else:
            flash("couldn't find any playlist with that playlist_id")
        return redirect(url_for('creator_dashboard'))

    else:
        return redirect(url_for('my_playlist'), playlist_id)


# -------------------------------------Route for viewing lyrics
@app.route('/view_lyrics/<int:song_id>', methods=['GET', 'POST'])
@login_required
def view_lyrics(song_id):
    user = db.get_or_404(Users, current_user.user_id)
    song = db.session.query(Songs).filter_by(song_id=song_id).first()
    # Do whatever you want with the 'song' object, like fetching its lyrics
    lyrics = song.lyrics if song else None
    return render_template('view_lyrics.html',
                           current_user_level=1,
                           user=user,
                           song=song,
                           lyrics=lyrics)


# -------------------------------------Route for creating a playlist
@app.route('/create_playlist', methods=['GET', 'POST'])
@login_required
def create_playlist():
    user = db.get_or_404(Users, current_user.user_id)
    if request.method == 'POST':
        title = request.form['title']
        access = request.form['access']
        description = request.form['description']
        existing_playlist = Playlists.query.filter_by(title=title).first()
        if not existing_playlist:
            try:
                user_id = user.user_id
                new_playlist = Playlists(user_id=user_id,
                                         title=title,
                                         description=description,
                                         created_at=datetime.now(),
                                         access=access)
                db.session.add(new_playlist)
                db.session.commit()
            except Exception as error:
                db.session.rollback()
                flash('Error creating a new playlist. Please try again.', category='error')
                print(str(error))
            finally:
                db.session.close()
            return redirect(url_for('user_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    else:
        return render_template('create_playlist.html',
                               current_user_level=1,
                               user=user)


# -------------------------------------Route for creating a playlist
@app.route('/playlist/<int:playlist_id>', methods=['GET', 'POST'])
@login_required
def playlist(playlist_id):
    user = db.get_or_404(Users, current_user.user_id)
    playlist = Playlists.query.get_or_404(playlist_id)
    playlist_songs = playlist.songs

    # Need to add functionality for that "Play all" button
    # It should add all the songs in a playlist into the current queue

    # Music Streaming functionality
    if request.method == 'POST':
        if 'stream' in request.form:
            song_id = request.form.get('song_id')
            song_to_stream = Songs.query.filter_by(song_id=song_id).first()
            return render_template('playlist.html',
                                   current_user_level=1,
                                   user=user,
                                   playlist=playlist,
                                   song_to_stream=song_to_stream,
                                   playlist_songs=playlist_songs,
                                   song_to_stream_duration=to_minute_seconds(float(song_to_stream.duration)))

    return render_template('playlist.html',
                           current_user_level=1,
                           user=user,
                           playlist=playlist,
                           playlist_songs=playlist_songs)


# -------------------------------------Route for listing  a User's playlist
@app.route('/creator_dashboard/my_playlists', methods=['GET', 'POST'])
@login_required
def my_playlists():
    user = db.get_or_404(Users, current_user.user_id)
    playlists = Playlists.query.filter_by(user_id=current_user.user_id)

    # Need to add functionality for that "Play" button beside playlist name

    return render_template('my_playlists.html',
                           current_user_level=current_user.role,
                           user=user,
                           playlists=playlists)


# -------------------------------------Route for creating a playlist
@app.route('/add_to_playlist/<int:song_id>', methods=['GET', 'POST'])
@login_required
def add_to_playlist(song_id):
    user = db.get_or_404(Users, current_user.user_id)
    playlists = db.session.query(Playlists).filter_by(user_id=current_user.user_id).all()
    return render_template('add_to_playlist.html',
                           current_user_level=1,
                           user=user,
                           song_id=song_id,
                           playlists=playlists)


# -------------------------------------Route for creating a playlist
@app.route('/add_to_playlist_song/<int:playlist_id>/<int:song_id>', methods=['GET', 'POST'])
@login_required
def add_to_playlist_song(playlist_id, song_id):
    try:
        new_playlist_song = PlaylistSong(playlist_id=playlist_id,
                                         song_id=song_id)
        db.session.add(new_playlist_song)
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        flash('Error creating a new PlaylistSong item. Please try again.', category='error')
        print(str(error))
    finally:
        db.session.close()
        # Redirecting to playlist endpoint, to display the current playlist
        return redirect(url_for('playlist', playlist_id=playlist_id))


# -------------------------------------Route for uploading a song
@app.route('/create_album', methods=['GET', 'POST'])
@login_required
def create_album():
    user = db.get_or_404(Users, current_user.user_id)
    title = ""

    if request.method == 'POST' and user.role == 2:
        try:
            title = request.form['title']
            genre = request.form['genre']
            release_date = request.form['release_date']
            description = request.form['description']
            user_id = user.user_id

            # Save the album cover picture into the uploads folder
            cover_file = request.files['cover_file']
            cover_file_path = f'static/covers/{title}.jpg'  # Unique path for cover file
            cover_file.save(cover_file_path)

            print("1")
            # Save the new song object into the database
            new_album = Albums(
                title=title,
                genre=genre,
                release_date=release_date,
                description=description,
                cover=cover_file_path,
                user_id=user_id
            )
            print("2")
            db.session.add(new_album)
            print("3")
            db.session.commit()
            print("4")
        except Exception as error:
            print("5")
            db.session.rollback()
            flash('Error uploading the new song. Please try again.', category='error')
            print(str(error))
        finally:
            db.session.close()

            # Fetching the album_id of the newly created album
            new_album = Albums.query.filter_by(title=title).first()

            # Redirect to the Creator Dashboard
            return redirect(url_for('album', album_id=new_album.album_id))

    return render_template('create_album.html',
                           current_user_level=2,
                           user=user)


# Route for Creator's own albums
@app.route('/creator_albums/<int:album_id>', methods=['GET', 'POST'])
@login_required
def creator_albums(album_id):
    user = db.get_or_404(Users, current_user.user_id)
    album = Albums.query.get_or_404(album_id)
    album_songs = album.songs

    # Need to add functionality for that "Play all" button
    # It should add all the songs in a playlist into the current queue

    # Music Streaming functionality
    if request.method == 'POST':
        if 'stream' in request.form:
            song_id = request.form.get('song_id')
            song_to_stream = Songs.query.filter_by(song_id=song_id).first()
            return render_template('album.html',
                                   current_user_level=1,
                                   user=user,
                                   playlist=playlist,
                                   song_to_stream=song_to_stream,
                                   album_songs=album_songs,
                                   song_to_stream_duration=to_minute_seconds(float(song_to_stream.duration)))

    return render_template('my_albums.html',
                           current_user_level=1,
                           user=user,
                           album=album,
                           album_songs=album_songs)


# -------------------------------------Route for creating a playlist
@app.route('/album/<int:album_id>', methods=['GET', 'POST'])
@login_required
def album(album_id):
    user = db.get_or_404(Users, current_user.user_id)
    album = Albums.query.get_or_404(album_id)
    album_songs = album.songs

    # Music Streaming functionality
    if request.method == 'POST':
        if 'stream' in request.form:
            song_id = request.form.get('song_id')
            song_to_stream = Songs.query.filter_by(song_id=song_id).first()
            return render_template('album.html',
                                   current_user_level=current_user.role,
                                   user=user,
                                   album=album,
                                   album_songs=album_songs,
                                   song_to_stream=song_to_stream,
                                   song_to_stream_duration=to_minute_seconds(float(song_to_stream.duration)))

    # current_album = Albums.query.filter_by(album_id=album_id).first()
    # songs = ""
    # if current_album:
    #     songs = current_album.songs

    # Need to add functionality for that "Play all" button
    # It should add all the songs in Album into the current queue

    if Albums.query.filter_by(user_id=current_user.user_id).first():

        return render_template('album.html',
                               current_user_level=2,
                               user=user,
                               album=album,
                               album_songs=album_songs)
    else:
        return render_template('album.html',
                               current_user_level=1,
                               user=user,
                               album=album,
                               album_songs=album_songs)


# -------------------------------------Route for page, showing adding song into an album
@app.route('/add_to_album/<int:album_id>', methods=['GET', 'POST'])
@login_required
def add_to_album(album_id):
    user = db.get_or_404(Users, current_user.user_id)
    album = db.get_or_404(Albums, album_id)

    # Code to filter out songs that are already in the current album
    songs = (db.session.query(Songs)
             .filter(Songs.user_id == current_user.user_id)
             .all())

    if Albums.query.filter_by(user_id=current_user.user_id).first():
        return render_template('add_to_album.html',
                               current_user_level=2,
                               user=user,
                               songs=songs,
                               album=album,
                               album_id=album_id)

    else:
        return redirect(url_for('album', album_id=album_id))


# -------------------------------------Route for adding song into an album
@app.route('/add_to_album_song/<int:album_id>/<int:song_id>', methods=['GET', 'POST'])
@login_required
def add_to_album_song(album_id, song_id):

    if (Albums.query.filter_by(user_id=current_user.user_id).first()
            and Songs.query.filter_by(user_id=current_user.user_id).first()):
        try:
            new_album_song = AlbumSong(album_id=album_id,
                                       song_id=song_id)
            db.session.add(new_album_song)
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            flash('Error creating a new AlbumSong item. Please try again.', category='error')
            print(str(error))
        finally:
            db.session.close()
            # Redirecting to album endpoint, to display the current playlist
            return redirect(url_for('album', album_id=album_id))

    else:
        return redirect(url_for('album', album_id=album_id))


# -------------------------------------Route for listing  a User's playlist
@app.route('/creator_dashboard/my_albums', methods=['GET', 'POST'])
@login_required
def my_albums():
    user = db.get_or_404(Users, current_user.user_id)
    albums = db.session.query(Albums).filter_by(user_id=current_user.user_id).all()

    if len(albums) == 0:
        album_count_bool = False
    else:
        album_count_bool = True

    # Need to add functionality for that "Play" button beside playlist name

    return render_template('my_albums.html',
                           current_user_level=2,
                           user=user,
                           albums=albums,
                           album_count_bool=album_count_bool)


# -------------------------------------Route to handle adding songs to the queue
@app.route('/add_to_queue/<int:song_id>', methods=['POST'])
def add_to_queue(song_id):

    song = Songs.query.get(song_id)
    if song:
        try:
            current_user.queue.append(song)  # Add the song to the user's queue
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            flash('Error adding song into the selected queue. Please try again.', category='error')
            print(str(error))
        finally:
            db.session.close()
            flash('Song added to your queue successfully', category='success')
    else:
        flash('Song not found', category='error')

    # Redirect to the user dashboard after adding the song
    return redirect(url_for('user_dashboard'))


# -------------------------------------Route to handle the User Dashboard functionality
@app.route('/all_songs', methods=['GET', 'POST'])
@login_required
def all_songs():
    user = db.get_or_404(Users, current_user.user_id)
    songs = db.session.query(Songs)

    if current_user.role == 0:

        # Search Functionality
        if request.method == 'GET':

            # fetching the search_query
            search_query = request.args.get('search_query', '').lower()

            # Checking if the search query is empty
            if len(search_query) == 0:
                return render_template('all_songs.html',
                                       current_user_level=1,
                                       user=user,
                                       songs=songs)
            else:
                pass

            # Filtering songs from the Songs table from the database
            filtered_songs = Songs.query.filter(
                Songs.title.ilike(f'%{search_query}%') |
                Songs.singer.ilike(f'%{search_query}%') |
                Songs.genre.ilike(f'%{search_query}%')
            ).all()

            # A boolean output, just to use in the logic in "for" loop for Search component in Jinja2
            if len(filtered_songs) > 0:
                filtered_songs_bool = True
            else:
                filtered_songs_bool = False

            # A boolean output for no input in Search component in Jinja2
            if search_query != "":
                search_query_bool = True
            else:
                search_query_bool = False

            return render_template('all_songs.html',
                                   current_user_level=0,
                                   search_query=search_query,
                                   search_query_bool=search_query_bool,
                                   filtered_songs=filtered_songs,
                                   filtered_songs_bool=filtered_songs_bool,
                                   user=user,
                                   songs=songs)
        else:
            return render_template('all_songs.html',
                                   current_user_level=0,
                                   user=user,
                                   songs=songs)
    else:
        # Search Functionality
        if request.method == 'GET':

            # fetching the search_query
            search_query = request.args.get('search_query', '').lower()

            # Checking if the search query is empty
            if len(search_query) == 0:
                return render_template('all_songs.html',
                                       current_user_level=1,
                                       user=user,
                                       songs=songs)
            else:
                pass

            # Filtering songs from the Songs table from the database
            filtered_songs = Songs.query.filter(
                Songs.title.ilike(f'%{search_query}%') |
                Songs.singer.ilike(f'%{search_query}%') |
                Songs.genre.ilike(f'%{search_query}%')
            ).all()

            # A boolean output, just to use in the logic in "for" loop for Search component in Jinja2
            if len(filtered_songs) > 0:
                filtered_songs_bool = True
            else:
                filtered_songs_bool = False

            # A boolean output for no input in Search component in Jinja2
            if search_query != "":
                search_query_bool = True
            else:
                search_query_bool = False

            return render_template('all_songs.html',
                                   current_user_level=1,
                                   search_query=search_query,
                                   search_query_bool=search_query_bool,
                                   filtered_songs=filtered_songs,
                                   filtered_songs_bool=filtered_songs_bool,
                                   user=user,
                                   songs=songs)

        else:
            return render_template('all_songs.html',
                                   current_user_level=1,
                                   user=user,
                                   songs=songs)


# -------------------------------------Route to handle the User Dashboard functionality
@app.route('/all_albums', methods=['GET', 'POST'])
@login_required
def all_albums():
    user = db.get_or_404(Users, current_user.user_id)
    albums = db.session.query(Albums)
    return render_template('all_albums.html',
                           current_user_level=1,
                           user=user,
                           albums=albums)


# -------------------------------------Route to handle the User Dashboard functionality
@app.route('/all_playlists', methods=['GET', 'POST'])
@login_required
def all_playlists():
    user = db.get_or_404(Users, current_user.user_id)
    playlists = db.session.query(Playlists)

    return render_template('all_playlists.html',
                           current_user_level=1,
                           user=user,
                           playlists=playlists)


# -------------------------------------Route to handle Ratings of songs
@app.route('/rate/<int:song_id>/<int:rating>', methods=['GET', 'POST'])
@login_required
def rate(song_id, rating):
    user = db.get_or_404(Users, current_user.user_id)

    # if rating in [0, 1, 3, 4, 5]:
    if 0 <= rating <= 5:
        try:
            new_rating = Ratings(rating=rating,
                                 user_id=user.user_id,
                                 song_id=song_id)
            db.session.add(new_rating)
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            flash('Error giving ratings to a song. Please try again.', category='error')
            print(str(error))
        finally:
            db.session.close()
        return redirect(url_for('view_song', song_id=song_id))
    else:
        return redirect(url_for('404'))


# -------------------------------------Route for User account settings page
@app.route('/user_settings', methods=['GET'])
@login_required
def user_settings():
    if current_user.role == 1:
        user = db.get_or_404(Users, current_user.user_id)
        return render_template('user_settings.html',
                               current_user_level=1,
                               user=user)
    elif current_user.role == 2:
        redirect(url_for('creator_settings.html'))
    else:
        redirect(url_for('error_404'))


# -------------------------------------Route for Creator account settings page
@app.route('/creator_settings', methods=['GET', 'POST'])
@login_required
def creator_settings():
    if current_user.role == 2:
        user = db.get_or_404(Users, current_user.user_id)
        return render_template('creator_settings.html',
                               current_user_level=2,
                               user=user)
    elif current_user.role == 1:
        redirect(url_for('user_settings.html'))
    else:
        redirect(url_for('error_404'))


# Route for user profile
@app.route('/profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
def profile(user_id):
    selected_user = db.get_or_404(Users, user_id)
    user = db.get_or_404(Users, current_user.user_id)
    return render_template('profile.html',
                           selected_user=selected_user,
                           user=user)


# Route for uploading profile picture
@app.route('/profile_picture', methods=['GET', 'POST'])
@login_required
def profile_picture():
    user = db.get_or_404(Users, current_user.user_id)

    if request.method == 'POST':
        try:
            # Save the new profile picture into the profie_image folder
            profile_image = request.files['profile_image']
            profile_image_file_path = f'static/profile_pic/{user.name}.jpg'  # Unique path for cover file
            profile_image.save(profile_image_file_path)

            # Update the new profile picture into the user object
            logout_user()
            user.profile_pic = profile_image_file_path
            db.session.commit()
            flash("Login again. Profile picture updated!")
        except Exception as error:
            db.session.rollback()
            flash('Error uploading the profile picture. Please try again.', category='error')
            print(str(error))
        finally:
            db.session.close()

        # Redirect to the user profile
        return redirect(url_for('login'))

    return render_template('profile_picture.html',
                           user=user)


# -------------------------------------Route for Logout functionality
@app.route('/logout')
@login_required
def logout():

    # Clear the queue list associated with the user
    if current_user.is_authenticated:
        try:
            current_user.queue.clear()
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            flash('Error clearing the queue for the current user. Please try again.', category='error')
            print(str(error))
        finally:
            db.session.close()

    logout_user()
    flash('Logged out successfully', category='success')
    return redirect(url_for('login'))


# -------------------------------------Toggle Dark/Light Mode
# @app.route('/toggle_dark_mode/<str:current_route>', methods=['GET', 'POST'])
@app.route('/toggle_dark_mode', methods=['GET', 'POST'])
def toggle_dark_mode():
    if current_user.dark_mode == False:
        current_user.dark_mode = True
        # Write the logic for SQLAlchemy to change the detail for dark_mode
    else:
        current_user.dark_mode = False
    return redirect(url_for(user_dashboard))


# -------------------------------------Route to test if the trigger mechanism is working
@app.route('/trigger_flash')
def trigger_flash():
    flash('This is a test flash message!', 'info')  # Flash a test message
    return redirect(url_for('index'))


# -------------------------------------Route for error code: 404
@app.route('/404')
def error_404():
    user = db.get_or_404(Users, current_user.user_id)
    return render_template('404.html',
                           user=user)


# -------------------------------------Route for error code: 403
@app.errorhandler(403)
def not_authorized():
    user = db.get_or_404(Users, current_user.user_id)
    return render_template('403.html',
                           user=user)


# -------------------------------------Route for custom page_not_found error
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == "__main__":

    # app.run(debug=True)

    # To allow access for other users in local network
    # app.run(host='0.0.0.0', port=5000, debug=True)
    # app.run(debug=False)
    app.run(port=8000, debug=False)
