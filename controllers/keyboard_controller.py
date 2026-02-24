# controllers/keyboard_controller.py
"""
Contrôleur de clavier avancé avec macros et raccourcis
"""
import cv2
from utils.logger import Logger

class KeyboardController:
    """Gestionnaire de clavier professionnel"""
    
    def __init__(self, drawing_controller):
        self.logger = Logger()
        self.drawing_controller = drawing_controller
        
        # Mapping des touches
        self.key_actions = {
            # Touches standards
            27: self._quit,           # Echap
            ord('c'): self._clear,     # c
            ord('s'): self._save,       # s
            ord('p'): self._pause,      # p
            ord('e'): self._eraser,     # e
            ord('u'): self._undo,       # u
            ord('r'): self._redo,       # r
            ord('h'): self._help,       # h
            ord('l'): self._toggle_layers,  # l
            ord('f'): self._toggle_fps,     # f
            ord('m'): self._toggle_mute,    # m
            
            # Chiffres pour couleurs
            ord('1'): lambda: self._change_color(1),
            ord('2'): lambda: self._change_color(2),
            ord('3'): lambda: self._change_color(3),
            ord('4'): lambda: self._change_color(4),
            ord('5'): lambda: self._change_color(5),
            ord('6'): lambda: self._change_color(6),
            ord('7'): lambda: self._change_color(7),
            ord('8'): lambda: self._change_color(8),
            
            # Taille pinceau
            ord('+'): self._brush_up,
            ord('='): self._brush_up,
            ord('-'): self._brush_down,
            ord('_'): self._brush_down,
            
            # Formes
            ord('t'): lambda: self._start_shape('triangle'),
            ord('o'): lambda: self._start_shape('circle'),
            ord('x'): lambda: self._start_shape('rectangle'),
        }
        
        self.key_history = []
        self.modifiers = {'ctrl': False, 'shift': False, 'alt': False}
        self.macro_mode = False
        self.macro_keys = []
        
        self.logger.info("⌨️ KeyboardController avancé prêt")
    
    def handle_key(self, key):
        """Gère une touche pressée"""
        if key == -1:
            return True
        
        key = key & 0xFF
        
        # Gestion des modificateurs
        if key in [ord('à'), ord('â')]:  # Ctrl (simulé)
            self.modifiers['ctrl'] = True
            return True
        
        # Ajouter à l'historique
        self.key_history.append(key)
        if len(self.key_history) > 20:
            self.key_history.pop(0)
        
        # Mode macro
        if self.macro_mode:
            self.macro_keys.append(key)
            if len(self.macro_keys) > 10:
                self.macro_mode = False
                self._save_macro()
            return True
        
        # Exécuter action
        if key in self.key_actions:
            action_name = self._get_action_name(key)
            self.logger.info(f"⌨️ Touche: {action_name}")
            return self.key_actions[key]()
        
        return True
    
    def _get_action_name(self, key):
        """Retourne le nom de l'action pour une touche"""
        actions = {
            27: "QUITTER",
            ord('c'): "EFFACER",
            ord('s'): "SAUVEGARDER",
            ord('p'): "PAUSE",
            ord('e'): "GOMME",
            ord('u'): "UNDO",
            ord('r'): "REDO",
            ord('h'): "AIDE",
            ord('l'): "CALQUES",
            ord('f'): "FPS",
            ord('m'): "SON",
        }
        
        if ord('1') <= key <= ord('8'):
            return f"COULEUR {key - ord('0')}"
        
        if key in [ord('+'), ord('=')]:
            return "TAILLE +"
        if key in [ord('-'), ord('_')]:
            return "TAILLE -"
        
        return chr(key) if 32 <= key <= 126 else f"0x{key:02X}"
    
    # ===== ACTIONS =====
    
    def _quit(self):
        self.drawing_controller.quit()
        return False
    
    def _clear(self):
        self.drawing_controller.clear_canvas()
        return True
    
    def _save(self):
        self.drawing_controller.save_canvas()
        return True
    
    def _pause(self):
        self.drawing_controller.toggle_pause()
        return True
    
    def _eraser(self):
        self.drawing_controller.toggle_eraser()
        return True
    
    def _undo(self):
        if hasattr(self.drawing_controller.canvas, 'undo'):
            self.drawing_controller.canvas.undo()
        return True
    
    def _redo(self):
        if hasattr(self.drawing_controller.canvas, 'redo'):
            self.drawing_controller.canvas.redo()
        return True
    
    def _help(self):
        self._show_help()
        return True
    
    def _toggle_layers(self):
        self.drawing_controller.view.show_notification("📑 GESTION CALQUES")
        return True
    
    def _toggle_fps(self):
        # Implémenter toggle FPS
        return True
    
    def _toggle_mute(self):
        # Implémenter mute
        return True
    
    def _change_color(self, num):
        self.drawing_controller.change_color(num)
        return True
    
    def _brush_up(self):
        if hasattr(self.drawing_controller.canvas, 'brush_size'):
            current = self.drawing_controller.canvas.brush_size
            self.drawing_controller.canvas.set_brush_size(current + 1)
        return True
    
    def _brush_down(self):
        if hasattr(self.drawing_controller.canvas, 'brush_size'):
            current = self.drawing_controller.canvas.brush_size
            self.drawing_controller.canvas.set_brush_size(current - 1)
        return True
    
    def _start_shape(self, shape):
        self.drawing_controller.view.show_notification(f"📐 FORME: {shape}")
        return True
    
    def _show_help(self):
        """Affiche l'aide"""
        help_text = """
╔══════════════════════════════════════════════╗
║         AIR WRITING - AIDE RAPIDE            ║
╠══════════════════════════════════════════════╣
║ 1-8 : Changer couleur    c : Effacer        ║
║ s : Sauvegarder          p : Pause          ║
║ e : Gomme                u : Annuler        ║
║ r : Rétablir             h : Cette aide     ║
║ + : Taille +             - : Taille -       ║
║ t : Triangle             o : Cercle         ║
║ x : Rectangle            l : Calques        ║
║ Echap : Quitter                              ║
╚══════════════════════════════════════════════╝
        """
        print(help_text)
        self.drawing_controller.view.show_notification("📖 AIDE AFFICHÉE")
    
    def get_stats(self):
        """Retourne les statistiques clavier"""
        return {
            'history_size': len(self.key_history),
            'last_keys': [self._get_action_name(k) for k in self.key_history[-5:]]
        }
