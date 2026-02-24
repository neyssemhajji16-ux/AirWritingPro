# utils/config.py
"""
Configuration centrale du projet
Tous les paramètres sont ici
"""

class Config:
    # ===== CAMÉRA =====
    CAMERA_ID = 0
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    CAMERA_FPS = 30
    CAMERA_BRIGHTNESS = 150
    CAMERA_CONTRAST = 50
    
    # ===== ZONE DE DESSIN =====
    DRAWING_ZONE = {
        'x1': 150, 'y1': 80,    # Coin haut-gauche
        'x2': 490, 'y2': 360,    # Coin bas-droit
        'color': (255, 255, 255),
        'border_thickness': 2
    }
    
    # ===== COULEURS DISPONIBLES (BGR) =====
    COLORS = {
        'red': (0, 0, 255),
        'green': (0, 255, 0),
        'blue': (255, 0, 0),
        'yellow': (0, 255, 255),
        'purple': (255, 0, 255),
        'cyan': (255, 255, 0),
        'orange': (0, 165, 255),
        'pink': (203, 192, 255),
        'brown': (42, 42, 165),
        'white': (255, 255, 255),
        'black': (0, 0, 0),
        'gray': (128, 128, 128)
    }
    
    # ===== PINCEAU =====
    BRUSH = {
        'min_size': 2,
        'max_size': 30,
        'default_size': 5,
        'eraser_multiplier': 2,  # Gomme plus grosse
        'pressure_sensitivity': True  # Taille varie avec vitesse
    }
    
    # ===== DÉTECTION MAIN =====
    HAND = {
        'min_detection_confidence': 0.5,
        'min_tracking_confidence': 0.3,
        'max_num_hands': 1,
        'finger_raise_threshold': 0.02,  # Seuil pour doigt levé
        'pinch_threshold': 0.05  # Seuil pour pincement
    }
    
    # ===== FONCTIONNALITÉS =====
    FEATURES = {
        'sound_effects': True,      # Sons au clic
        'auto_save': True,          # Sauvegarde auto toutes les 5min
        'auto_save_interval': 300,  # 5 minutes en secondes
        'show_fps': True,
        'show_instructions': True,
        'smooth_drawing': True,      # Lissage du trait
        'smooth_factor': 0.5
    }
    
    # ===== CHEMINS =====
    PATHS = {
        'saves': 'sauvegardes',
        'logs': 'logs',
        'exports': 'exports',
        'fonts': 'assets/fonts',
        'icons': 'assets/icons',
        'sounds': 'assets/sounds'
    }
    
    # ===== FORMATS D'EXPORT =====
    EXPORT_FORMATS = ['png', 'jpg', 'pdf', 'svg']
    
    @classmethod
    def get_color(cls, name):
        """Retourne une couleur par son nom"""
        return cls.COLORS.get(name, cls.COLORS['white'])
    
    @classmethod
    def get_path(cls, name):
        """Retourne un chemin"""
        return cls.PATHS.get(name, '')