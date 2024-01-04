# Cassette - Music Streaming Application


## Local setup

### Creating virtual environment  
- `python -m venv venv`

### Activate the virtual environment 
- `.\venv\Scripts\activate`

### Install all the required packages
- `pip install -r requirements.txt`

### Start the application
- `python main.py`

Or, just open the root foder in any IDE, 
it will automatically create a virtual environment 
and install all the requirements from the requirements.txt file.

### To add new packages into the requirements.txt file
- `python -m pip freeze > requirements.txt`

## Folder Structure

```


├── .env
├──	debug.log
├── favicon.ico
├── main.py
├── readme.md
├── requirements.txt
├── application 
│ 	├── __init__.py
│ 	├── api.py
│ 	├── config.py
│ 	├── controllers.py
│ 	├── database.py
│ 	├── functions.py
│   └── models.py
├── instance 
│   └── cassette.sqlite3
├── static
│	├── audio
│	│	└── ( To be filled during code exucution)
│	├── covers
│	│	└── ( To be filled during code exucution)
│	├── img 
│	│	├──	403.png
│	│	├──404.png
│	│	├── admin_icon.png
│	│	├──	album_art.png
│	│	├──	bg_resized.jpeg
│	│	├──	cassette.png
│	│	├──	cassette_basic.png
│	│	├──	cassette_with_controls - original.png
│	│	├──	cassette_with_controls.png
│	│	├──	cassette_with_controls_resized.png
│	│	├──	creator_icon.png
│	│	├──	favicon.ico
│	│	├──	monthly_usage_graph.png
│	│	├──	song_vs_plays_graph.png
│	│	├──	standard_user_icon.png
│	│	├──	start_button.png
│	│	├──	tag_admin.png
│	│	├──	tag_creator.png
│	│	├──	tag_standard_user.png
│	│	└── user_icon_default.png
│   ├── js
│	│	└── control_audio.js
│   └── style.css
└── templates
    ├── 403.html
    ├── 404.html
    ├── add_to_album.html
    ├── add_to_playlist.html
	├── admin_dashboard.html
    ├── admin_login.html
    ├── album.html
    ├── all_albums.html
	├── all_playlists.html			
    ├── all_songs.html
    ├── all_users.html
    ├── audio_controls.html
	├── create_album.html			
    ├── create_playlist.html
    ├── creator_dashboard.html
    ├── creator_dashboard_dropdown_bar.html
	├── creator_registration.html
    ├── creator_settings.html
    ├── edit_song.html
	├── footer.html    
    ├── header.html
    ├── index.html
	├── login.html
    ├── my_albums.html
	├── my_playlists.html
    ├── my_songs.html
    ├── now_playing.html
	├── playlist.html  
    ├── playlists_row.html
    ├── profile.html
	├── profile_picture.html   
    ├── queue_component.html
    ├── search_functionality_input.html
	├── search_functionality_results.html   
    ├── temp.html
	├── upload_song.html    
	├── upload_song_form.html
	├── user_dashboard.html
	├── user_registration.html
	├── user_settings.html
    ├── view_lyrics.html
    └── view_song.html

```
