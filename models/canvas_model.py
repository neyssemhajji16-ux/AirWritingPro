# models/canvas_model.py
"""
Modèle de toile avec fonctionnalités avancées
"""
import numpy as np
import cv2
from datetime import datetime
import os
from utils.config import Config
from utils.logger import Logger
from features.shapes import ShapeDetector

class CanvasModel:
    """Toile de dessin avec fonctionnalités pro"""
    
    def __init__(self, width, height):
        self.logger = Logger()
        self.logger.info(f"Création canvas {width}x{height}")
        
        self.width = width
        self.height = height
        self.canvas = np.zeros((height, width, 3), dtype=np.uint8)
        self.background = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Calques (layers)
        self.layers = [np.zeros((height, width, 3), dtype=np.uint8)]
        self.active_layer = 0
        
        # Paramètres dessin
        self.current_color = Config.get_color('red')
        self.brush_size = Config.BRUSH['default_size']
        self.eraser_mode = False
        
        # Historique pour undo/redo
        self.history = []
        self.history_index = -1
        self.max_history = 50
        
        # Détection de formes
        self.shape_detector = ShapeDetector()
        
        # Statistiques
        self.total_points = 0
        self.last_positions = []  # Pour lissage
        self.max_positions = 5
        
        self.logger.info("✅ Canvas prêt")
    
    def draw_line(self, x1, y1, x2, y2):
        """Dessine une ligne avec lissage"""
        if not (0 <= x2 < self.width and 0 <= y2 < self.height):
            return
        
        # Sauvegarder l'état pour undo
        self._save_state()
        
        # Lissage du trait (moving average)
        self.last_positions.append((x2, y2))
        if len(self.last_positions) > self.max_positions:
            self.last_positions.pop(0)
        
        if len(self.last_positions) > 1 and Config.FEATURES['smooth_drawing']:
            # Moyenne des positions récentes
            avg_x = int(np.mean([p[0] for p in self.last_positions]))
            avg_y = int(np.mean([p[1] for p in self.last_positions]))
            x2, y2 = avg_x, avg_y
        
        # Choisir couleur/taille
        if self.eraser_mode:
            color = (0, 0, 0)
            size = self.brush_size * Config.BRUSH['eraser_multiplier']
        else:
            color = self.current_color
            size = self.brush_size
            
            # Sensibilité à la pression (vitesse)
            if Config.BRUSH['pressure_sensitivity'] and len(self.last_positions) > 1:
                # Calculer la vitesse
                dx = x2 - self.last_positions[-2][0]
                dy = y2 - self.last_positions[-2][1]
                speed = np.sqrt(dx*dx + dy*dy)
                
                # Adapter la taille (plus rapide = plus fin)
                if speed > 5:
                    size = max(Config.BRUSH['min_size'], 
                              int(size * 0.8))
        
        # Dessiner
        cv2.line(self.layers[self.active_layer], (x1, y1), (x2, y2), color, size)
        
        # Fusionner les calques
        self._merge_layers()
        
        self.total_points += 1
    
    def draw_shape(self, shape_type, points):
        """Dessine une forme géométrique"""
        self._save_state()
        self.shape_detector.draw_shape(
            self.layers[self.active_layer], 
            shape_type, 
            points,
            self.current_color,
            self.brush_size
        )
        self._merge_layers()
    
    def _save_state(self):
        """Sauvegarde l'état pour undo"""
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        
        state = self.layers[self.active_layer].copy()
        self.history.append(state)
        self.history_index += 1
        
        # Limiter la taille de l'historique
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.history_index -= 1
    
    def undo(self):
        """Annule la dernière action"""
        if self.history_index > 0:
            self.history_index -= 1
            self.layers[self.active_layer] = self.history[self.history_index].copy()
            self._merge_layers()
            return True
        return False
    
    def redo(self):
        """Rétablit la dernière action annulée"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.layers[self.active_layer] = self.history[self.history_index].copy()
            self._merge_layers()
            return True
        return False
    
    def add_layer(self):
        """Ajoute un nouveau calque"""
        self.layers.append(np.zeros((self.height, self.width, 3), dtype=np.uint8))
        self.logger.info(f"➕ Nouveau calque ajouté. Total: {len(self.layers)}")
    
    def remove_layer(self, index):
        """Supprime un calque"""
        if len(self.layers) > 1 and 0 <= index < len(self.layers):
            del self.layers[index]
            if self.active_layer >= len(self.layers):
                self.active_layer = len(self.layers) - 1
            self._merge_layers()
            self.logger.info(f"➖ Calque {index} supprimé")
    
    def _merge_layers(self):
        """Fusionne tous les calques"""
        self.canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        for layer in self.layers:
            mask = cv2.cvtColor(layer, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(mask, 1, 255, cv2.THRESH_BINARY)
            mask_inv = cv2.bitwise_not(mask)
            bg = cv2.bitwise_and(self.canvas, self.canvas, mask=mask_inv)
            fg = cv2.bitwise_and(layer, layer, mask=mask)
            self.canvas = cv2.add(bg, fg)
    
    def clear(self):
        """Efface la toile"""
        self._save_state()
        self.layers[self.active_layer] = np.zeros((self.height, self.width, 3), 
                                                  dtype=np.uint8)
        self._merge_layers()
        self.logger.info("🧹 Toile effacée")
    
    def clear_layer(self, index=None):
        """Efface un calque spécifique"""
        if index is None:
            index = self.active_layer
        self._save_state()
        self.layers[index] = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self._merge_layers()
    
    def save(self, filename=None, format='png'):
        """Sauvegarde la toile"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dessin_{timestamp}.{format}"
        
        save_dir = Config.PATHS['saves']
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        path = os.path.join(save_dir, filename)
        
        if format == 'jpg':
            cv2.imwrite(path, self.canvas, [cv2.IMWRITE_JPEG_QUALITY, 90])
        else:
            cv2.imwrite(path, self.canvas)
        
        self.logger.info(f"💾 Canvas sauvegardé: {path}")
        return path
    
    def export_to_pdf(self, filename=None):
        """Exporte le dessin en PDF"""
        try:
            from reportlab.pdfgen import canvas as pdf_canvas
            from reportlab.lib.utils import ImageReader
            from io import BytesIO
            
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"dessin_{timestamp}.pdf"
            
            export_dir = Config.PATHS['exports']
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
            
            path = os.path.join(export_dir, filename)
            
            # Convertir OpenCV image en PIL Image
            rgb = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2RGB)
            from PIL import Image
            pil_img = Image.fromarray(rgb)
            
            # Sauvegarder temporairement
            temp_path = os.path.join(export_dir, "temp.png")
            pil_img.save(temp_path)
            
            # Créer PDF
            c = pdf_canvas.Canvas(path, pagesize=(self.width, self.height))
            c.drawImage(temp_path, 0, 0, width=self.width, height=self.height)
            c.save()
            
            # Nettoyer
            os.remove(temp_path)
            
            self.logger.info(f"📄 PDF exporté: {path}")
            return path
            
        except Exception as e:
            self.logger.error(f"Erreur export PDF: {e}")
            return None
    
    def set_color(self, color_name):
        """Change la couleur courante"""
        self.current_color = Config.get_color(color_name)
        self.eraser_mode = False
        self.logger.info(f"🎨 Couleur: {color_name}")
    
    def set_brush_size(self, size):
        """Change la taille du pinceau"""
        self.brush_size = max(Config.BRUSH['min_size'], 
                             min(Config.BRUSH['max_size'], size))
    
    def toggle_eraser(self):
        """Active/désactive la gomme"""
        self.eraser_mode = not self.eraser_mode
        mode = "🧽 GOMME" if self.eraser_mode else "🎨 PINCEAU"
        self.logger.info(mode)
    
    def get_stats(self):
        """Retourne des statistiques détaillées"""
        return {
            'total_points': self.total_points,
            'brush_size': self.brush_size,
            'eraser_mode': self.eraser_mode,
            'layers': len(self.layers),
            'active_layer': self.active_layer,
            'history_size': len(self.history),
            'canvas_size': f"{self.width}x{self.height}"
        }