# features/shapes.py
"""
Module de détection et dessin de formes géométriques
Permet de reconnaître et dessiner des formes parfaites
"""
import numpy as np
import cv2
import math
from utils.logger import Logger

class ShapeDetector:
    """Détecte et dessine des formes géométriques"""
    
    SHAPES = {
        'line': 1,
        'rectangle': 2,
        'circle': 3,
        'triangle': 4,
        'square': 5,
        'ellipse': 6,
        'arrow': 7,
        'star': 8
    }
    
    def __init__(self):
        self.logger = Logger()
        self.logger.info("📐 ShapeDetector initialisé")
        self.points = []  # Pour dessin de formes
        self.current_shape = None
        
    def detect_shape(self, contour):
        """
        Détecte la forme d'un contour
        Retourne: (nom_forme, confiance, paramètres)
        """
        # Péri mètre du contour
        peri = cv2.arcLength(contour, True)
        
        # Approximation du contour
        approx = cv2.approxPolyDP(contour, 0.04 * peri, True)
        
        # Nombre de sommets
        vertices = len(approx)
        
        # Calculer l'aire
        area = cv2.contourArea(contour)
        if area < 100:  # Trop petit
            return None, 0, None
        
        # Déterminer la forme
        if vertices == 3:
            return 'triangle', 0.8, approx
        elif vertices == 4:
            # Vérifier si c'est un carré ou rectangle
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = w / float(h)
            
            if 0.95 <= aspect_ratio <= 1.05:
                return 'square', 0.9, (x, y, w, h)
            else:
                return 'rectangle', 0.8, (x, y, w, h)
        elif vertices > 4:
            # Vérifier si c'est un cercle
            (x, y), radius = cv2.minEnclosingCircle(contour)
            circularity = 4 * math.pi * area / (peri * peri)
            
            if circularity > 0.8:
                return 'circle', circularity, (int(x), int(y), int(radius))
            else:
                return 'ellipse', 0.6, cv2.fitEllipse(contour)
        
        return None, 0, None
    
    def draw_shape(self, canvas, shape_type, points, color, thickness=2):
        """
        Dessine une forme sur le canvas
        """
        if shape_type == 'line' and len(points) >= 2:
            cv2.line(canvas, points[0], points[1], color, thickness)
            
        elif shape_type == 'rectangle' and len(points) >= 2:
            cv2.rectangle(canvas, points[0], points[1], color, thickness)
            
        elif shape_type == 'circle' and len(points) >= 2:
            center = points[0]
            radius = int(np.sqrt((points[1][0] - points[0][0])**2 + 
                                (points[1][1] - points[0][1])**2))
            cv2.circle(canvas, center, radius, color, thickness)
            
        elif shape_type == 'triangle' and len(points) >= 3:
            pts = np.array(points[:3], np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(canvas, [pts], True, color, thickness)
            
        elif shape_type == 'arrow' and len(points) >= 2:
            self._draw_arrow(canvas, points[0], points[1], color, thickness)
            
        self.logger.info(f"📐 Forme dessinée: {shape_type}")
    
    def _draw_arrow(self, canvas, start, end, color, thickness):
        """Dessine une flèche"""
        # Ligne principale
        cv2.line(canvas, start, end, color, thickness)
        
        # Tête de flèche
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        arrow_length = 20
        arrow_angle = math.pi / 6  # 30 degrés
        
        # Point gauche de la flèche
        left_x = end[0] - arrow_length * math.cos(angle - arrow_angle)
        left_y = end[1] - arrow_length * math.sin(angle - arrow_angle)
        
        # Point droit de la flèche
        right_x = end[0] - arrow_length * math.cos(angle + arrow_angle)
        right_y = end[1] - arrow_length * math.sin(angle + arrow_angle)
        
        # Dessiner la tête
        cv2.line(canvas, end, (int(left_x), int(left_y)), color, thickness)
        cv2.line(canvas, end, (int(right_x), int(right_y)), color, thickness)
    
    def start_shape(self, shape_type, point):
        """Commence à dessiner une forme"""
        self.current_shape = shape_type
        self.points = [point]
        self.logger.info(f"🎨 Début forme: {shape_type}")
    
    def add_point(self, point):
        """Ajoute un point à la forme en cours"""
        if self.current_shape:
            self.points.append(point)
    
    def end_shape(self, canvas, color, thickness):
        """Termine et dessine la forme"""
        if self.current_shape and len(self.points) >= 2:
            self.draw_shape(canvas, self.current_shape, self.points, 
                          color, thickness)
        
        self.current_shape = None
        self.points = []
    
    def recognize_hand_drawn_shape(self, points):
        """
        Reconnaît une forme dessinée à main levée
        """
        if len(points) < 5:
            return None
        
        # Convertir en contour
        contour = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
        
        # Détecter la forme
        shape, confidence, params = self.detect_shape(contour)
        
        if shape and confidence > 0.6:
            return shape, confidence, params
        
        return None, 0, None
