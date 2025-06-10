# Projet Moodyfy - Système de recommandation musicale avec Streamlit
# Codex ChatGPT - Version enrichie

import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import streamlit as st
import requests
from bs4 import BeautifulSoup

# Chargement du dataset Spotify (exemple Streamlit)
df = pd.read_csv(r"C:\Users\saleban ali hassan\Documents\Projet_Moodify\csv\SpotifyFeatures.csv")


# Définition des features audio pertinentes
features_audio = ['acousticness', 'danceability', 'energy', 'instrumentalness',
                  'liveness', 'loudness', 'speechiness', 'tempo', 'valence']

# Prétraitement des données (standardisation)
def preprocess_audio_features(df, features):
    scaler = StandardScaler()
    df_scaled = df.copy()
    df_scaled[features] = scaler.fit_transform(df[features])
    return df_scaled, scaler

# Fonction Song-to-Song
def recommend_similar_songs(song_name, df, features, top_n=5):
    if song_name not in df['track_name'].values:
        return pd.DataFrame({'Erreur': [f"La chanson '{song_name}' est introuvable"]})

    df_features, _ = preprocess_audio_features(df, features)
    target_song = df_features[df_features['track_name'] == song_name]
    other_songs = df_features[df_features['track_name'] != song_name]

    similarities = cosine_similarity(target_song[features], other_songs[features])
    other_songs['similarity'] = similarities[0]
    recommendations = other_songs.sort_values(by='similarity', ascending=False).head(top_n)

    return recommendations[['track_name', 'artist_name', 'similarity']]

# Mood-to-Playlist (simulé)
def generate_mood_playlist(mood, df):
    mood_rules = {
        'joyeux': df[df['valence'] > 0.7],
        'triste': df[df['valence'] < 0.3],
        'énergique': df[df['energy'] > 0.7],
        'calme': df[df['energy'] < 0.4],
    }
    return mood_rules.get(mood.lower(), df.sample(10))

# Activity-to-Playlist (simulé)
def generate_activity_playlist(activity, df):
    activity_rules = {
        'sport': df[df['tempo'] > 130],
        'relaxation': df[df['acousticness'] > 0.6],
        'travail': df[df['instrumentalness'] > 0.5],
        'conduite': df[df['danceability'] > 0.5],
    }
    return activity_rules.get(activity.lower(), df.sample(10))

# API Genius : récupération des paroles d'une chanson
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

    if lyrics_div:
        return lyrics_div.get_text(separator="\n")
    else:
        return "Paroles non disponibles."

# Interface utilisateur Streamlit
st.title("🎧 Moodyfy - Système de Recommandation Musicale")

menu = st.sidebar.selectbox("Choisissez une fonctionnalité", [
    "Recommandation par chanson",
    "Playlist par humeur",
    "Playlist par activité",
    "Paroles via Genius"
])

if menu == "Recommandation par chanson":
    song_name = st.text_input("Entrez le nom d'une chanson")
    if st.button("Recommander"):
        results = recommend_similar_songs(song_name, df, features_audio)
        st.write(results)

elif menu == "Playlist par humeur":
    mood = st.selectbox("Choisissez une humeur", ["joyeux", "triste", "énergique", "calme"])
    results = generate_mood_playlist(mood, df)
    st.write(results[['track_name', 'artist_name']])

elif menu == "Playlist par activité":
    activity = st.selectbox("Choisissez une activité", ["sport", "relaxation", "travail", "conduite"])
    results = generate_activity_playlist(activity, df)
    st.write(results[['track_name', 'artist_name']])

elif menu == "Paroles via Genius":
    artist = st.text_input("Nom de l'artiste")
    title = st.text_input("Titre de la chanson")
    if st.button("Obtenir les paroles"):
        lyrics = get_lyrics_from_genius(artist, title)
        st.text_area("Paroles", lyrics, height=300)
