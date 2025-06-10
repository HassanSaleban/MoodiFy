# Projet Moodyfy - Refonte Flask + HTML/CSS/JS
# Backend Python (Flask)

from flask import Flask, request, jsonify, render_template
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

# Chargement du dataset
df = pd.read_csv(r"C:\Users\saleban ali hassan\Documents\Projet_Moodify\csv\SpotifyFeatures.csv")
features_audio = ['acousticness', 'danceability', 'energy', 'instrumentalness',
                  'liveness', 'loudness', 'speechiness', 'tempo', 'valence']

# Configuration Spotify API (token à remplacer par une variable d'environnement)
SPOTIFY_TOKEN = os.getenv("SPOTIFY_TOKEN")

# Fonctions de recommandation
def preprocess_audio_features(df, features):
    scaler = StandardScaler()
    df_scaled = df.copy()
    df_scaled[features] = scaler.fit_transform(df[features])
    return df_scaled, scaler

def recommend_similar_songs(song_name, df, features, top_n=5):
    if song_name not in df['track_name'].values:
        return []
    df_features, _ = preprocess_audio_features(df, features)
    target_song = df_features[df_features['track_name'] == song_name]
    other_songs = df_features[df_features['track_name'] != song_name]
    similarities = cosine_similarity(target_song[features], other_songs[features])
    other_songs['similarity'] = similarities[0]
    recommendations = other_songs.sort_values(by='similarity', ascending=False).head(top_n)
    return enrich_with_covers(recommendations[['track_name', 'artist_name']])

def generate_mood_playlist(mood, df):
    mood_rules = {
        'joyeux': df[df['valence'] > 0.7],
        'triste': df[df['valence'] < 0.3],
        'énergique': df[df['energy'] > 0.7],
        'calme': df[df['energy'] < 0.4],
    }
    tracks = mood_rules.get(mood.lower(), df.sample(10))
    return enrich_with_covers(tracks[['track_name', 'artist_name']])

def generate_activity_playlist(activity, df):
    activity_rules = {
        'sport': df[df['tempo'] > 130],
        'relaxation': df[df['acousticness'] > 0.6],
        'travail': df[df['instrumentalness'] > 0.5],
        'conduite': df[df['danceability'] > 0.5],
    }
    tracks = activity_rules.get(activity.lower(), df.sample(10))
    return enrich_with_covers(tracks[['track_name', 'artist_name']])

def enrich_with_covers(tracks):
    enriched = []
    for _, row in tracks.iterrows():
        track = row['track_name']
        artist = row['artist_name']
        cover_url = get_spotify_cover(track, artist)
        enriched.append({
            'track_name': track,
            'artist_name': artist,
            'cover_url': cover_url
        })
    return enriched

def get_spotify_cover(track, artist):
    if not SPOTIFY_TOKEN:
        return None
    headers = {"Authorization": f"Bearer {SPOTIFY_TOKEN}"}
    query = f"{track} {artist}"
    url = f"https://api.spotify.com/v1/search?q={query}&type=track&limit=1"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        items = response.json().get('tracks', {}).get('items', [])
        if items:
            return items[0]['album']['images'][0]['url']
    return None

def get_lyrics_from_genius(artist, title):
    base_url = "https://genius.com"
    search_url = f"https://genius.com/api/search/multi?per_page=1&q={artist} {title}"
    response = requests.get(search_url)
    if response.status_code != 200:
        return "Erreur lors de la recherche Genius."
    json_response = response.json()
    hits = json_response.get("response", {}).get("sections", [])[0].get("hits", [])
    if not hits:
        return "Paroles introuvables sur Genius."
    song_path = hits[0]['result']['path']
    song_url = base_url + song_path
    song_page = requests.get(song_url)
    soup = BeautifulSoup(song_page.text, 'html.parser')
    lyrics_div = soup.find("div", class_="Lyrics__Container-sc-1ynbvzw-6")
    return lyrics_div.get_text(separator="\n") if lyrics_div else "Paroles non disponibles."

# Routes Flask
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.json
    results = recommend_similar_songs(data['song'], df, features_audio)
    return jsonify(results)

@app.route('/mood', methods=['POST'])
def mood():
    data = request.json
    results = generate_mood_playlist(data['mood'], df)
    return jsonify(results)

@app.route('/activity', methods=['POST'])
def activity():
    data = request.json
    results = generate_activity_playlist(data['activity'], df)
    return jsonify(results)

@app.route('/lyrics', methods=['POST'])
def lyrics():
    data = request.json
    lyrics = get_lyrics_from_genius(data['artist'], data['title'])
    return jsonify({"lyrics": lyrics})

if __name__ == '__main__':
    app.run(debug=True)
