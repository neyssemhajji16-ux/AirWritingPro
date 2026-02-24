# views/main_view.py
"""
Vue principale de l'application
Assemble tous les composants UI
"""
import cv2
import numpy as np
from views.ui_components import Button, ColorPicker, StatusBar, Slider, Tooltip
from utils.config import Config
from utils.logger import Logger

class MainView:
    """Vue principale - Pattern Observer"""
    
    def __init__(self, controller):
        self.logger = Logger()
        self.controller = controller
        
        # Dimensions
        self.width = Config.CAMERA_WIDTH
        self.height = Config.CAMERA_HEIGHT
        
        # Composants UI
        self.components = []
        self.status_bar = None
        self.color_picker = None
        self.buttons = {}
        self.sliders = {}
        self.tooltips = {}
        
        # Notifications
        self.notification = None
        self.notification_time = 0
        self.notification_color = (0, 255, 0)
        
        # Animation
        self.time = 0
        
        self.init_components()
        self.logger.info("✅ MainView initialisée")
    
    def init_components(self):
        """Initialise tous les composants UI"""
        
        # Barre de statut en haut
        self.status_bar = StatusBar(0, 0, self.width, 60)
        self.components.append(self.status_bar)
        
        # Boutons à droite
        bx = self.width - 130
        buttons_config = [
            ('clear', 'EFFACER', bx, 70, 120, 40, (0, 0, 255)),
            ('save', 'SAUV', bx, 120, 120, 40, (0, 255, 0)),
            ('pause', 'PAUSE', bx, 170, 120, 40, (255, 255, 0)),
            ('eraser', 'GOMME', bx, 220, 120, 40, (128, 128, 128)),
            ('shapes', 'FORMES', bx, 270, 120, 40, (255, 165, 0)),
            ('layers', 'CALQUES', bx, 320, 120, 40, (255, 192, 203)),
            ('quit', 'QUITTER', bx, 370, 120, 40, (255, 255, 255))
        ]
        
        for btn_id, text, x, y, w, h, color in buttons_config:
            btn = Button(x, y, w, h, text, color)
            self.buttons[btn_id] = btn
            self.components.append(btn)
            
            # Ajouter tooltip
            tooltip = Tooltip(x, y - 25, f"Cliquez pour {text.lower()}")
            self.tooltips[btn_id] = tooltip
            self.components.append(tooltip)
        
        # Palette de couleurs en bas
        colors = [
            Config.get_color('red'),
            Config.get_color('green'),
            Config.get_color('blue'),
            Config.get_color('yellow'),
            Config.get_color('purple'),
            Config.get_color('cyan'),
            Config.get_color('orange'),
            Config.get_color('white')
        ]
        self.color_picker = ColorPicker(50, self.height - 70, 45, colors)
        self.components.append(self.color_picker)
        
        # Slider pour taille pinceau
        brush_slider = Slider(50, self.height - 120, 200, 30, 
                              Config.BRUSH['min_size'], 
                              Config.BRUSH['max_size'],
                              Config.BRUSH['default_size'],
                              "Taille pinceau")
        self.sliders['brush'] = brush_slider
        self.components.append(brush_slider)
    
    def update(self, frame, canvas, state, doigt_detecte, doigt_position, 
               dans_zone, current_color, brush_size, fps):
        """
        Met à jour la vue avec les nouvelles données
        """
        self.time += 1
        
        # Mettre à jour statuts
        self.status_bar.fps = fps
        self.status_bar.brush_size = brush_size
        
        # Déterminer mode
        if state == self.controller.STATE_DRAWING:
            self.status_bar.mode = "DESSIN"
        elif state == self.controller.STATE_PAUSED:
            self.status_bar.mode = "PAUSE"
        elif state == self.controller.STATE_ERASER:
            self.status_bar.mode = "GOMME"
        
        # Mettre à jour points (si disponible)
        if hasattr(self.controller, 'canvas'):
            self.status_bar.points = self.controller.canvas.total_points
        
        # Dessiner zone de dessin
        zone = Config.DRAWING_ZONE
        cv2.rectangle(frame, (zone['x1'], zone['y1']), 
                     (zone['x2'], zone['y2']), (255, 255, 255), 2)
        
        # Ajouter effet de respiration sur la zone
        if dans_zone and doigt_detecte:
            alpha = 0.3 + 0.2 * np.sin(self.time * 0.1)
            overlay = frame.copy()
            cv2.rectangle(overlay, (zone['x1'], zone['y1']), 
                         (zone['x2'], zone['y2']), (0, 255, 0), -1)
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        
        # Dessiner curseur doigt
        x, y = doigt_position
        if x != -1 and y != -1:
            if doigt_detecte:
                if dans_zone:
                    # Dans zone = vert avec effet
                    cv2.circle(frame, (x, y), 10, (0, 255, 0), -1)
                    cv2.circle(frame, (x, y), 15, (0, 255, 0), 1)
                else:
                    # Hors zone = jaune
                    cv2.circle(frame, (x, y), 10, (0, 255, 255), -1)
                    cv2.circle(frame, (x, y), 15, (0, 255, 255), 1)
            else:
                # Doigt baissé = gris
                cv2.circle(frame, (x, y), 8, (128, 128, 128), -1)
        
        # Dessiner tous les composants
        for comp in self.components:
            frame = comp.draw(frame)
        
        # Afficher la couleur courante
        cv2.circle(frame, (self.width - 50, 40), 15, current_color, -1)
        cv2.circle(frame, (self.width - 50, 40), 18, (255, 255, 255), 1)
        
        # Afficher notification
        if self.notification and self.notification_time > 0:
            self._draw_notification(frame)
            self.notification_time -= 1
        
        # Fusionner avec canvas
        return self._merge_with_canvas(frame, canvas)
    
    def _merge_with_canvas(self, frame, canvas):
        """Fusionne la frame et le canvas"""
        # Créer masque
        gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)
        
        # Appliquer masques
        fond = cv2.bitwise_and(frame, frame, mask=mask_inv)
        dessin = cv2.bitwise_and(canvas, canvas, mask=mask)
        
        return cv2.add(fond, dessin)
    
    def _draw_notification(self, frame):
        """Dessine une notification"""
        h, w = frame.shape[:2]
        
        # Fond semi-transparent
        overlay = frame.copy()
        cv2.rectangle(overlay, (w//2 - 150, h//2 - 30), 
                     (w//2 + 150, h//2 + 30), (0, 0, 0), -1)
        
        # Animation de fondu
        alpha = min(1.0, self.notification_time / 30)
        cv2.addWeighted(overlay, alpha * 0.7, frame, 1 - alpha * 0.7, 0, frame)
        
        # Texte
        cv2.putText(frame, self.notification, (w//2 - 100, h//2 + 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.notification_color, 2)
    
    def handle_mouse(self, event, x, y, flags, param):
        """Gère les événements souris"""
        if event == cv2.EVENT_LBUTTONDOWN:
            for comp in self.components:
                if comp.handle_click(x, y):
                    return
        
        elif event == cv2.EVENT_MOUSEMOVE:
            for comp in self.components:
                if hasattr(comp, 'handle_hover'):
                    comp.handle_hover(x, y)
                
                # Gérer tooltips
                if isinstance(comp, Button) and comp.contains(x, y):
                    for tooltip in self.tooltips.values():
                        tooltip.show()
                else:
                    for tooltip in self.tooltips.values():
                        tooltip.hide()
        
        elif event == cv2.EVENT_LBUTTONUP:
            for comp in self.components:
                if hasattr(comp, 'handle_release'):
                    comp.handle_release()
    
    def set_button_callback(self, button_id, callback):
        """Assigne un callback à un bouton"""
        if button_id in self.buttons:
            self.buttons[button_id].callback = callback
    
    def set_color_callback(self, callback):
        """Assigne un callback au sélecteur de couleur"""
        self.color_picker.callback = callback
    
    def show_notification(self, message, duration=30, color=(0, 255, 0)):
        """Affiche une notification temporaire"""
        self.notification = message
        self.notification_time = duration
        self.notification_color = color
        self.logger.info(f"NOTIF: {message}")
