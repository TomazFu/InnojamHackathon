import requests
from datetime import datetime, timedelta
import os

def fetch_news_data(date, location="Singapore"):
    """Fetch news related to health/disease for given date and location"""
    
    # Example using NewsAPI (requires API key)
    api_key = os.getenv("NEWS_API_KEY", "")
    
    if not api_key:
        # Return simulated data if no API key
        return simulate_news_data(date)
    
    try:
        url = f"https://newsapi.org/v2/everything"
        params = {
            'q': f'{location} AND (health OR disease OR outbreak OR flu OR illness)',
            'from': (date - timedelta(days=3)).strftime('%Y-%m-%d'),
            'to': date.strftime('%Y-%m-%d'),
            'language': 'en',
            'sortBy': 'relevancy',
            'apiKey': api_key
        }
        
        response = requests.get(url, params=params)
        articles = response.json().get('articles', [])
        
        return [{'date': a['publishedAt'][:10], 'headline': a['title']} for a in articles[:5]]
    
    except Exception as e:
        return simulate_news_data(date)


def fetch_weather_data(date, lat=1.35, lon=103.82):
    """Fetch weather data for given date and location"""
    
    # Example using OpenWeatherMap (requires API key)
    api_key = os.getenv("WEATHER_API_KEY", "")
    
    if not api_key:
        return simulate_weather_data(date)
    
    try:
        # For historical weather
        timestamp = int(datetime.combine(date, datetime.min.time()).timestamp())
        url = f"https://api.openweathermap.org/data/2.5/onecall/timemachine"
        params = {
            'lat': lat,
            'lon': lon,
            'dt': timestamp,
            'appid': api_key,
            'units': 'metric'
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        return [{
            'date': date.strftime('%Y-%m-%d'),
            'condition': data['current']['weather'][0]['main'],
            'temp': data['current']['temp'],
            'humidity': data['current']['humidity']
        }]
    
    except Exception as e:
        return simulate_weather_data(date)


def fetch_public_events(date, location="Singapore"):
    """Fetch public events for given date"""
    
    # In production: Integrate with Eventbrite, Google Calendar, local event APIs
    # For now, return simulated data
    return simulate_events_data(date)


def simulate_news_data(date):
    """Simulated news data for demo"""
    return [
        {'date': (date - timedelta(days=2)).strftime('%Y-%m-%d'), 
         'headline': 'Health officials monitoring flu-like symptoms in Eastern districts'},
        {'date': (date - timedelta(days=1)).strftime('%Y-%m-%d'), 
         'headline': 'Increased hospital visits for respiratory conditions reported'},
        {'date': date.strftime('%Y-%m-%d'), 
         'headline': 'Schools implement health screening amid rising illness cases'}
    ]


def simulate_weather_data(date):
    """Simulated weather data"""
    import random
    conditions = ['Rainy', 'Cloudy', 'Sunny', 'Stormy']
    return [{
        'date': (date - timedelta(days=i)).strftime('%Y-%m-%d'),
        'condition': random.choice(conditions),
        'temp': random.randint(22, 32),
        'humidity': random.randint(60, 90)
    } for i in range(3)]


def simulate_events_data(date):
    """Simulated public events"""
    return [
        {'date': (date - timedelta(days=3)).strftime('%Y-%m-%d'), 
         'event': 'Outdoor Festival (50,000 attendees)'},
        {'date': (date - timedelta(days=1)).strftime('%Y-%m-%d'), 
         'event': 'National Day Parade (mass gathering)'}
    ]