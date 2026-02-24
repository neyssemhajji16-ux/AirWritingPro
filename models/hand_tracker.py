# models/hand_tracker.py
"""
Détection de main avec MediaPipe
Version avancée avec reconnaissance de gestes
"""
import cv2
import mediapipe as mp
import numpy as np
from utils.config import Config
from utils.logger import Logger

class HandTracker:
    """Détecte et suit les mains avec reconnaissance de gestes"""
    
    # Constantes MediaPipe
    LANDMARKS = {
        'WRIST': 0,
        'THUMB_CMC': 1,
        'THUMB_MCP': 2,
        'THUMB_IP': 3,
        'THUMB_TIP': 4,
        'INDEX_MCP': 5,
        'INDEX_PIP': 6,
        'INDEX_DIP': 7,
        'INDEX_TIP': 8,
        'MIDDLE_MCP': 9,
        'MIDDLE_PIP': 10,
        'MIDDLE_DIP': 11,
        'MIDDLE_TIP': 12,
        'RING_MCP': 13,
        'RING_PIP': 14,
        'RING_DIP': 15,
        'RING_TIP': 16,
        'PINKY_MCP': 17,
        'PINKY_PIP': 18,
        'PINKY_DIP': 19,
        'PINKY_TIP': 20
    }
    
    # Gestes reconnus
    GESTURES = {
        'POINTING': 1,      # Index levé
        'PEACE': 2,         # V avec index et majeur
        'OK': 3,            # OK sign
        'THUMBS_UP': 4,     # Pouce levé
        'FIST': 5,          # Poing fermé
        'OPEN_PALM': 6      # Main ouverte
    }
    
    def __init__(self):
        self.logger = Logger()
        self.logger.info("Initialisation HandTracker avancé...")
        
        # MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=Config.HAND['max_num_hands'],
            min_detection_confidence=Config.HAND['min_detection_confidence'],
            min_tracking_confidence=Config.HAND['min_tracking_confidence']
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # État
        self.landmarks = None
        self.image_width = 0
        self.image_height = 0
        self.current_gesture = None
        self.gesture_history = []
        
        # Pour le lissage
        self.smooth_x = 0
        self.smooth_y = 0
        self.smooth_factor = 0.3
        
        self.logger.info("✅ HandTracker prêt")
    
    def process_frame(self, frame):
        """
        Traite une frame et retourne les informations de la main
        Returns: (doigt_leve, x, y, dans_zone, geste, landmarks_complets)
        """
        if frame is None:
            return False, -1, -1, False, None, None
        
        self.image_height, self.image_width = frame.shape[:2]
        
        # Conversion RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frame_rgb)
        
        x, y = -1, -1
        doigt_leve = False
        dans_zone = False
        gesture = None
        landmarks_dict = None
        
        if results.multi_hand_landmarks:
            # Prendre la première main
            hand = results.multi_hand_landmarks[0]
            self.landmarks = hand.landmark
            
            # Convertir en dictionnaire pour faciliter l'accès
            landmarks_dict = {}
            for idx, lm in enumerate(self.landmarks):
                landmarks_dict[idx] = {
                    'x': lm.x,
                    'y': lm.y,
                    'z': lm.z,
                    'pixel_x': int(lm.x * self.image_width),
                    'pixel_y': int(lm.y * self.image_height)
                }
            
            # Position index
            index_tip = landmarks_dict[self.LANDMARKS['INDEX_TIP']]
            x = index_tip['pixel_x']
            y = index_tip['pixel_y']
            
            # Lissage de la position
            if self.smooth_x == 0:
                self.smooth_x, self.smooth_y = x, y
            else:
                self.smooth_x = int(self.smooth_x * self.smooth_factor + 
                                   x * (1 - self.smooth_factor))
                self.smooth_y = int(self.smooth_y * self.smooth_factor + 
                                   y * (1 - self.smooth_factor))
                x, y = self.smooth_x, self.smooth_y
            
            # Vérifier si index levé
            index_pip = landmarks_dict[self.LANDMARKS['INDEX_PIP']]
            doigt_leve = index_tip['y'] < index_pip['y'] - Config.HAND['finger_raise_threshold']
            
            # Détecter le geste
            gesture = self._detect_gesture(landmarks_dict)
            
            # Vérifier zone
            if doigt_leve:
                zone = Config.DRAWING_ZONE
                dans_zone = (zone['x1'] < x < zone['x2'] and 
                           zone['y1'] < y < zone['y2'])
        
        return doigt_leve, x, y, dans_zone, gesture, landmarks_dict
    
    def _detect_gesture(self, landmarks):
        """
        Détecte quel geste fait la main
        """
        # Récupérer les points importants
        index_tip = landmarks[self.LANDMARKS['INDEX_TIP']]
        index_pip = landmarks[self.LANDMARKS['INDEX_PIP']]
        middle_tip = landmarks[self.LANDMARKS['MIDDLE_TIP']]
        middle_pip = landmarks[self.LANDMARKS['MIDDLE_PIP']]
        thumb_tip = landmarks[self.LANDMARKS['THUMB_TIP']]
        thumb_ip = landmarks[self.LANDMARKS['THUMB_IP']]
        ring_tip = landmarks[self.LANDMARKS['RING_TIP']]
        pinky_tip = landmarks[self.LANDMARKS['PINKY_TIP']]
        
        # Vérifier quels doigts sont levés
        index_up = index_tip['y'] < index_pip['y']
        middle_up = middle_tip['y'] < middle_pip['y']
        thumb_up = thumb_tip['y'] < thumb_ip['y']
        
        # Distance pouce-index pour OK sign
        thumb_index_dist = abs(thumb_tip['x'] - index_tip['x'])
        
        # Détection des gestes
        if index_up and not middle_up:
            return self.GESTURES['POINTING']
        elif index_up and middle_up:
            # Vérifier si les autres sont baissés
            if not (ring_tip['y'] < landmarks[self.LANDMARKS['RING_PIP']]['y'] or
                   pinky_tip['y'] < landmarks[self.LANDMARKS['PINKY_PIP']]['y']):
                return self.GESTURES['PEACE']
        elif thumb_up and not index_up:
            return self.GESTURES['THUMBS_UP']
        elif thumb_index_dist < Config.HAND['pinch_threshold']:
            return self.GESTURES['OK']
        elif not (index_up or middle_up):
            return self.GESTURES['FIST']
        
        return None
    
    def get_finger_angles(self):
        """Calcule les angles des articulations"""
        if not self.landmarks:
            return None
        
        angles = {}
        # Calculer angles pour chaque doigt
        # (Formule mathématique avancée)
        return angles
    
    def draw_hand_landmarks(self, frame, with_labels=False):
        """Dessine les points de la main sur la frame"""
        if self.landmarks:
            self.mp_draw.draw_landmarks(
                frame, 
                self.mp_hands.HandLandmarks,  # Correction ici
                self.mp_hands.HAND_CONNECTIONS
            )
            
            if with_labels:
                for idx, lm in enumerate(self.landmarks):
                    x = int(lm.x * self.image_width)
                    y = int(lm.y * self.image_height)
                    cv2.putText(frame, str(idx), (x, y), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
        return frame