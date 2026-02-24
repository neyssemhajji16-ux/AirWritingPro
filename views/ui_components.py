# views/ui_components.py
"""
Composants d'interface utilisateur réutilisables
Pattern Composite pour l'UI
"""
import cv2
import numpy as np
import math

class UIComponent:
    """Classe de base pour tous les composants UI"""
    
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.visible = True
        self.enabled = True
        self.parent = None
        self.children = []
        self.id = id(self)
    
    def draw(self, frame):
        """À surcharger dans les classes filles"""
        pass
    
    def update(self, *args, **kwargs):
        """Met à jour l'état du composant"""
        pass
    
    def handle_click(self, x, y):
        """Gère un clic sur le composant"""
        return self.contains(x, y)
    
    def contains(self, px, py):
        """Vérifie si un point est dans le composant"""
        return (self.x <= px <= self.x + self.width and 
                self.y <= py <= self.y + self.height)
    
    def add_child(self, child):
        """Ajoute un composant enfant"""
        child.parent = self
        self.children.append(child)
    
    def remove_child(self, child):
        """Retire un composant enfant"""
        if child in self.children:
            self.children.remove(child)

class Button(UIComponent):
    """Bouton interactif"""
    
    # États du bouton
    STATE_NORMAL = 0
    STATE_HOVER = 1
    STATE_PRESSED = 2
    STATE_DISABLED = 3
    
    def __init__(self, x, y, width, height, text, color, 
                 icon=None, callback=None):
        super().__init__(x, y, width, height)
        self.text = text
        self.normal_color = color
        self.hover_color = self._lighten_color(color, 1.3)
        self.pressed_color = self._darken_color(color, 0.7)
        self.disabled_color = (128, 128, 128)
        
        self.state = self.STATE_NORMAL
        self.callback = callback
        self.icon = icon
        
        # Animation
        self.animation_progress = 0
        self.pulse_direction = 1
        
        # Police
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.5
        self.font_thickness = 1
    
    def _lighten_color(self, color, factor):
        """Éclaircit une couleur"""
        return tuple(min(255, int(c * factor)) for c in color)
    
    def _darken_color(self, color, factor):
        """Assombrit une couleur"""
        return tuple(max(0, int(c * factor)) for c in color)
    
    def draw(self, frame):
        if not self.visible:
            return frame
        
        # Choisir couleur selon état
        if self.state == self.STATE_DISABLED:
            color = self.disabled_color
        elif self.state == self.STATE_PRESSED:
            color = self.pressed_color
        elif self.state == self.STATE_HOVER:
            color = self.hover_color
        else:
            color = self.normal_color
        
        # Animation de pulse si hover
        if self.state == self.STATE_HOVER:
            self.animation_progress += 0.1 * self.pulse_direction
            if self.animation_progress >= 1:
                self.pulse_direction = -1
            elif self.animation_progress <= 0:
                self.pulse_direction = 1
            
            # Effet de glow
            glow_size = int(5 * self.animation_progress)
            cv2.rectangle(frame, 
                         (self.x - glow_size, self.y - glow_size),
                         (self.x + self.width + glow_size, 
                          self.y + self.height + glow_size),
                         color, 1)
        
        # Dessiner le bouton
        cv2.rectangle(frame, (self.x, self.y), 
                     (self.x + self.width, self.y + self.height), 
                     color, -1)
        
        # Bordure
        border_color = (255, 255, 255)
        if self.state == self.STATE_PRESSED:
            border_color = (0, 0, 0)
        
        cv2.rectangle(frame, (self.x, self.y), 
                     (self.x + self.width, self.y + self.height), 
                     border_color, 2)
        
        # Texte
        text_size = cv2.getTextSize(self.text, self.font, 
                                    self.font_scale, self.font_thickness)[0]
        text_x = self.x + (self.width - text_size[0]) // 2
        text_y = self.y + (self.height + text_size[1]) // 2
        
        cv2.putText(frame, self.text, (text_x, text_y), 
                   self.font, self.font_scale, (255, 255, 255), 
                   self.font_thickness)
        
        return frame
    
    def handle_click(self, x, y):
        if not self.enabled or not self.visible:
            return False
        
        if self.contains(x, y):
            self.state = self.STATE_PRESSED
            if self.callback:
                self.callback()
            return True
        return False
    
    def handle_hover(self, x, y):
        if not self.enabled or not self.visible:
            return
        
        if self.contains(x, y):
            if self.state != self.STATE_PRESSED:
                self.state = self.STATE_HOVER
        else:
            if self.state != self.STATE_PRESSED:
                self.state = self.STATE_NORMAL

class ColorPicker(UIComponent):
    """Sélecteur de couleur circulaire"""
    
    def __init__(self, x, y, size, colors, callback=None):
        super().__init__(x, y, size * len(colors), size)
        self.size = size
        self.colors = colors
        self.callback = callback
        self.selected_index = 0
        self.hover_index = -1
    
    def draw(self, frame):
        if not self.visible:
            return frame
        
        for i, color in enumerate(self.colors):
            cx = self.x + i * self.size + self.size // 2
            cy = self.y + self.size // 2
            radius = self.size // 2 - 4
            
            # Cercle principal
            cv2.circle(frame, (cx, cy), radius, color, -1)
            
            # Bordure de sélection
            if i == self.selected_index:
                cv2.circle(frame, (cx, cy), radius + 3, (255, 255, 255), 2)
            
            # Effet hover
            if i == self.hover_index:
                cv2.circle(frame, (cx, cy), radius + 2, (255, 255, 255), 1)
            
            # Numéro
            cv2.putText(frame, str(i+1), (cx - 5, cy + 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        return frame
    
    def handle_click(self, x, y):
        if not self.enabled or not self.visible:
            return False
        
        for i in range(len(self.colors)):
            cx = self.x + i * self.size + self.size // 2
            cy = self.y + self.size // 2
            
            # Vérifier si clic dans le cercle
            distance = math.sqrt((x - cx)**2 + (y - cy)**2)
            if distance <= self.size // 2:
                self.selected_index = i
                if self.callback:
                    self.callback(i + 1)
                return True
        
        return False
    
    def handle_hover(self, x, y):
        if not self.enabled or not self.visible:
            return
        
        self.hover_index = -1
        for i in range(len(self.colors)):
            cx = self.x + i * self.size + self.size // 2
            cy = self.y + self.size // 2
            distance = math.sqrt((x - cx)**2 + (y - cy)**2)
            if distance <= self.size // 2:
                self.hover_index = i
                break

class Slider(UIComponent):
    """Slider pour régler des valeurs"""
    
    def __init__(self, x, y, width, height, min_val, max_val, 
                 default_val, label, callback=None):
        super().__init__(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = default_val
        self.label = label
        self.callback = callback
        
        self.dragging = False
        self.knob_radius = height // 2
    
    def draw(self, frame):
        if not self.visible:
            return frame
        
        # Ligne du slider
        line_y = self.y + self.height // 2
        cv2.line(frame, (self.x, line_y), 
                (self.x + self.width, line_y), 
                (200, 200, 200), 2)
        
        # Position du curseur
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        knob_x = int(self.x + ratio * self.width)
        knob_y = line_y
        
        # Curseur
        cv2.circle(frame, (knob_x, knob_y), self.knob_radius, 
                  (100, 100, 255), -1)
        cv2.circle(frame, (knob_x, knob_y), self.knob_radius, 
                  (255, 255, 255), 2)
        
        # Label et valeur
        cv2.putText(frame, f"{self.label}: {self.value}", 
                   (self.x, self.y - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def handle_click(self, x, y):
        if not self.enabled or not self.visible:
            return False
        
        # Vérifier si clic sur le curseur
        line_y = self.y + self.height // 2
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        knob_x = int(self.x + ratio * self.width)
        
        distance = math.sqrt((x - knob_x)**2 + (y - line_y)**2)
        if distance <= self.knob_radius:
            self.dragging = True
            return True
        
        return False
    
    def handle_drag(self, x, y):
        if self.dragging:
            # Calculer nouvelle valeur
            ratio = max(0, min(1, (x - self.x) / self.width))
            self.value = self.min_val + ratio * (self.max_val - self.min_val)
            self.value = int(self.value)
            
            if self.callback:
                self.callback(self.value)
            
            return True
        return False
    
    def handle_release(self):
        self.dragging = False

class StatusBar(UIComponent):
    """Barre de statut en haut"""
    
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.mode = "DESSIN"
        self.fps = 0
        self.brush_size = 3
        self.points = 0
        self.recording = False
    
    def draw(self, frame):
        if not self.visible:
            return frame
        
        # Fond
        cv2.rectangle(frame, (self.x, self.y), 
                     (self.x + self.width, self.y + self.height), 
                     (30, 30, 30), -1)
        
        # Mode
        mode_colors = {
            "DESSIN": (0, 255, 0),
            "PAUSE": (0, 0, 255),
            "GOMME": (128, 128, 128),
            "FORME": (255, 165, 0)
        }
        color = mode_colors.get(self.mode, (255, 255, 255))
        
        cv2.putText(frame, f"MODE: {self.mode}", (self.x + 20, self.y + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Informations
        cv2.putText(frame, f"TAILLE: {self.brush_size}", 
                   (self.x + 200, self.y + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        cv2.putText(frame, f"POINTS: {self.points}", 
                   (self.x + 350, self.y + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # FPS
        fps_color = (0, 255, 0) if self.fps >= 25 else (0, 255, 255) if self.fps >= 15 else (0, 0, 255)
        cv2.putText(frame, f"FPS: {int(self.fps)}", 
                   (self.x + self.width - 100, self.y + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, fps_color, 2)
        
        # Indicateur d'enregistrement
        if self.recording:
            cv2.circle(frame, (self.x + self.width - 30, self.y + 20), 
                      8, (0, 0, 255), -1)
        
        return frame

class Tooltip(UIComponent):
    """Infobulle qui apparaît au survol"""
    
    def __init__(self, x, y, text):
        super().__init__(x, y, 150, 40)
        self.text = text
        self.visible = False
        self.fade = 0
    
    def draw(self, frame):
        if not self.visible or self.fade <= 0:
            return frame
        
        # Fond semi-transparent
        overlay = frame.copy()
        cv2.rectangle(overlay, (self.x, self.y), 
                     (self.x + self.width, self.y + self.height), 
                     (50, 50, 50), -1)
        
        # Appliquer la transparence selon le fade
        alpha = self.fade
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        
        # Texte
        cv2.putText(frame, self.text, (self.x + 10, self.y + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def show(self):
        self.visible = True
        self.fade = min(1.0, self.fade + 0.1)
    
    def hide(self):
        self.fade = max(0, self.fade - 0.1)
        if self.fade <= 0:
            self.visible = False
