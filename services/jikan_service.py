import requests
from config import Config

def get_anime_data(query):
    try:
        # Search anime
        search_url = f"{Config.JIKAN_API_URL}/anime"
        params = {'q': query, 'limit': 1}
        search_res = requests.get(search_url, params=params).json()
        
        if not search_res['data']:
            return None
            
        anime_id = search_res['data'][0]['mal_id']
        
        # Get full details
        details_url = f"{Config.JIKAN_API_URL}/anime/{anime_id}/full"
        details = requests.get(details_url).json()['data']
        
        # Get characters & staff
        chars_url = f"{Config.JIKAN_API_URL}/anime/{anime_id}/characters"
        characters = requests.get(chars_url).json()['data']
        
        return {
            'title': details['title'],
            'synopsis': details['synopsis'],
            'rating': details['score'],
            'episodes': details['episodes'],
            'genres': [g['name'] for g in details['genres']],
            'characters': [{
                'name': c['character']['name'],
                'role': c['role'],
                'voice_actor': c['voice_actors'][0]['person']['name'] if c['voice_actors'] else None
            } for c in characters],
            'staff': [{
                'name': s['person']['name'],
                'role': s['positions'][0]
            } for s in details['staff']]
        }
    except Exception as e:
        print(f"Jikan API error: {e}")
        return None