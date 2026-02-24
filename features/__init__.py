# Crée le fichier __init__.py dans features

from .voice_commands import VoiceController
from .data_analyzer import DataAnalyzer
from .collaboration import CollaborationServer, CollaborationClient
from .special_effects import SpecialEffects, ParticleSystem
from .ai_assistant import AIAssistant

__all__ = [
    'VoiceController',
    'DataAnalyzer', 
    'CollaborationServer',
    'CollaborationClient',
    'SpecialEffects',
    'ParticleSystem',
    'AIAssistant'
]
