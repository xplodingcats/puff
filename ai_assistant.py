from kivy.uix.image import Image
from kivy.clock import Clock
import requests
import json

class PuffAI:
    def __init__(self):
        self.api_key = None
        self.sprites = {
            'idle': 'assets/sprites/idle.png',
            'talking': 'assets/sprites/talking.png',
            'alert': 'assets/sprites/alert.png'
        }
        self.current_sprite = Image(source=self.sprites['idle'])
        self.is_listening = False

    def set_api_key(self, key):
        self.api_key = key
        self.current_sprite.source = self.sprites['idle']

    def query(self, message):
        if not self.api_key:
            return "Please set API key in settings"
            
        try:
            self.current_sprite.source = self.sprites['talking']
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                data=json.dumps({
                    'model': 'gpt-3.5-turbo',
                    'messages': [
                        {'role': 'system', 'content': 'You are Puff, a helpful air quality assistant'},
                        {'role': 'user', 'content': message}
                    ],
                    'temperature': 0.7
                })
            )
            Clock.schedule_once(lambda dt: setattr(self.current_sprite, 'source', self.sprites['idle']), 2)
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.current_sprite, 'source', self.sprites['alert']), 2)
            return f"Error: {str(e)}"
