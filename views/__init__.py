# views/__init__.py
"""
Package Views - Contient toute l'interface utilisateur
"""
from .main_view import MainView
from .ui_components import Button, ColorPicker, StatusBar, UIComponent

__all__ = ['MainView', 'Button', 'ColorPicker', 'StatusBar', 'UIComponent']