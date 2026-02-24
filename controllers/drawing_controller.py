# controllers/drawing_controller.py
"""
Contrôleur principal - Version finale avec toutes les fonctionnalités
"""
from models.hand_tracker import HandTracker
from models.canvas_model import CanvasModel
from views.main_view import MainView
from controllers.keyboard_controller import KeyboardController
from features.voice_commands import VoiceController
from features.data_analyzer import DataAnalyzer
from features.collaboration import CollaborationServer, CollaborationClient
from features.special_effects import SpecialEffects
from features.ai_assistant import AIAssistant
from utils.logger import Logger
from utils.config import Config
import cv2
import numpy as np
import threading
import time

class DrawingController:
    """Contrôleur principal - Le cerveau de l'application"""
    
    # États de l'application
    STATE_DRAWING = 1
    STATE_PAUSED = 2
    STATE_ERASER = 3
    STATE_SHAPE = 4
    STATE_COLLAB = 5
    
    def __init__(self):
        self.logger = Logger()
        self.logger.start_session()
        self.logger.info("="*50)
        self.logger.info("🚀 Initialisation du DrawingController...")
        self.logger.info("="*50)
        
        # ===== INITIALISATION CAMÉRA =====
        try:
            self.cap = cv2.VideoCapture(Config.CAMERA_ID)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, Config.CAMERA_FPS)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            if not self.cap.isOpened():
                self.logger.error("❌ Impossible d'ouvrir la caméra")
                raise Exception("Camera error")
            
            self.logger.info(f"✅ Caméra initialisée: {Config.CAMERA_WIDTH}x{Config.CAMERA_HEIGHT}")
        except Exception as e:
            self.logger.error(f"❌ Erreur caméra: {e}")
            raise
        
        # ===== MODÈLES =====
        self.logger.info("📦 Initialisation des modèles...")
        self.hand_tracker = HandTracker()
        self.canvas = CanvasModel(Config.CAMERA_WIDTH, Config.CAMERA_HEIGHT)
        self.logger.info("✅ Modèles initialisés")
        
        # ===== VUE =====
        self.logger.info("🖥️ Initialisation de la vue...")
        self.view = MainView(self)
        self.logger.info("✅ Vue initialisée")
        
        # ===== CONTRÔLEURS =====
        self.logger.info("🎮 Initialisation des contrôleurs...")
        self.keyboard = KeyboardController(self)
        self.voice = VoiceController(self)
        self.logger.info("✅ Contrôleurs initialisés")
        
        # ===== FONCTIONNALITÉS AVANCÉES =====
        self.logger.info("✨ Initialisation des fonctionnalités avancées...")
        self.data_analyzer = DataAnalyzer()
        self.special_effects = SpecialEffects()
        self.ai_assistant = AIAssistant()
        
        # Collaboration (optionnel)
        self.collab_server = None
        self.collab_client = None
        self.collab_mode = False
        self.logger.info("✅ Fonctionnalités avancées initialisées")
        
        # ===== ÉTAT =====
        self.state = self.STATE_DRAWING
        self.running = True
        self.last_point = None
        self.points_buffer = []  # Pour les effets et l'IA
        self.max_buffer_size = 50
        
        # ===== STATISTIQUES =====
        self.fps = 0
        self.frame_count = 0
        self.fps_start_time = cv2.getTickCount()
        self.total_frames = 0
        
        # ===== TIMERS =====
        self.last_save_time = time.time()
        self.save_interval = 300  # 5 minutes
        
        # ===== CALLBACKS =====
        self.setup_callbacks()
        
        # ===== DÉMARRAGE SERVICES =====
        self.voice.start_listening()
        
        self.logger.info("="*50)
        self.logger.info("✅✅✅ DrawingController prêt! ✅✅✅")
        self.logger.info("="*50)
        
        # Afficher les commandes disponibles
        self._show_welcome_message()
    
    def _show_welcome_message(self):
        """Affiche un message de bienvenue"""
        welcome = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🎨 AIR WRITING - TOUTES FONCTIONNALITÉS ACTIVES         ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  📋 COMMANDES RAPIDES :                                      ║
║  • 1-8 : Changer couleur                                     ║
║  • c   : Effacer                                             ║
║  • s   : Sauvegarder                                         ║
║  • p   : Pause                                                ║
║  • e   : Gomme                                                ║
║  • u   : Undo                                                 ║
║  • r   : Redo                                                 ║
║  • h   : Aide                                                 ║
║  • v   : Activer/Désactiver voix                              ║
║  • ESC : Quitter                                              ║
║                                                              ║
║  🎤 COMMANDES VOCALES :                                       ║
║  • "rouge", "vert", "bleu", ...                              ║
║  • "effacer", "sauvegarder", "pause", "gomme"                ║
║  • "aide", "quitter"                                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(welcome)
    
    def setup_callbacks(self):
        """Configure tous les callbacks"""
        # Boutons standards
        self.view.set_button_callback('clear', self.clear_canvas)
        self.view.set_button_callback('save', self.save_canvas)
        self.view.set_button_callback('pause', self.toggle_pause)
        self.view.set_button_callback('eraser', self.toggle_eraser)
        self.view.set_button_callback('quit', self.quit)
        
        # Nouveaux boutons
        self.view.set_button_callback('stats', self.show_stats)
        self.view.set_button_callback('voice', self.toggle_voice)
        self.view.set_button_callback('effects', self.toggle_effects)
        self.view.set_button_callback('ai', self.toggle_ai)
        
        # Color picker
        self.view.set_color_callback(self.change_color)
    
    def run(self):
        """Boucle principale de l'application"""
        self.logger.info("▶️ Démarrage de la boucle principale")
        
        while self.running:
            loop_start = cv2.getTickCount()
            
            # ===== LECTURE FRAME =====
            ret, frame = self.cap.read()
            if not ret:
                self.logger.error("❌ Erreur lecture caméra")
                break
            
            frame = cv2.flip(frame, 1)
            self.total_frames += 1
            
            # ===== DÉTECTION MAIN =====
            doigt_leve, x, y, dans_zone, gesture, landmarks = self.hand_tracker.process_frame(frame)
            
            # ===== GESTION DU DESSIN SELON ÉTAT =====
            if self.state == self.STATE_DRAWING and doigt_leve and dans_zone:
                # Ajouter au buffer
                self.points_buffer.append((x, y))
                if len(self.points_buffer) > self.max_buffer_size:
                    self.points_buffer.pop(0)
                
                # Dessiner
                if self.last_point:
                    # Appliquer les effets si actifs
                    if hasattr(self, 'current_effect') and self.current_effect:
                        # Utiliser le buffer pour l'effet
                        if len(self.points_buffer) > 2:
                            frame = self.special_effects.apply_effect(
                                self.current_effect,
                                frame,
                                self.points_buffer,
                                self.canvas.current_color,
                                self.canvas.brush_size
                            )
                    
                    # Dessin normal
                    self.canvas.draw_line(
                        self.last_point[0], self.last_point[1],
                        x, y
                    )
                    
                    # Analyse de données
                    self.data_analyzer.add_point(
                        x, y,
                        self.canvas.current_color,
                        self.canvas.brush_size
                    )
                    
                    # Suggestion IA
                    if hasattr(self, 'ai_enabled') and self.ai_enabled:
                        if len(self.points_buffer) >= 10 and len(self.points_buffer) % 10 == 0:
                            suggestion = self.ai_assistant.suggest_shape(self.points_buffer)
                            if suggestion:
                                self.view.show_notification(f"🤖 {suggestion['name']}?")
                
                self.last_point = (x, y)
                
            elif self.state == self.STATE_ERASER and doigt_leve and dans_zone:
                if self.last_point:
                    self.canvas.draw_line(
                        self.last_point[0], self.last_point[1],
                        x, y
                    )
                self.last_point = (x, y)
            else:
                self.last_point = None
                self.points_buffer = []  # Vider buffer quand on arrête de dessiner
            
            # ===== SAUVEGARDE AUTOMATIQUE =====
            if time.time() - self.last_save_time > self.save_interval:
                self.auto_save()
            
            # ===== MISE À JOUR VUE =====
            frame = self.view.update(
                frame=frame,
                canvas=self.canvas.canvas,
                state=self.state,
                doigt_detecte=doigt_leve,
                doigt_position=(x, y),
                dans_zone=dans_zone,
                current_color=self.canvas.current_color,
                brush_size=self.canvas.brush_size,
                fps=self.fps
            )
            
            # ===== AFFICHAGE =====
            cv2.imshow("AIR WRITING - VERSION FINALE", frame)
            
            # ===== GESTION CLAVIER =====
            key = cv2.waitKey(1) & 0xFF
            self.keyboard.handle_key(key)
            
            # ===== CALCUL FPS =====
            self.frame_count += 1
            if self.frame_count >= 30:
                elapsed = (cv2.getTickCount() - self.fps_start_time) / cv2.getTickFrequency()
                self.fps = self.frame_count / elapsed
                self.frame_count = 0
                self.fps_start_time = cv2.getTickCount()
        
        self.cleanup()
    
    # ===== FONCTIONS PRINCIPALES =====
    
    def clear_canvas(self):
        """Efface la toile"""
        self.canvas.clear()
        self.view.show_notification("🧹 Toile effacée")
        self.logger.info("🧹 Toile effacée")
    
    def save_canvas(self):
        """Sauvegarde le dessin"""
        path = self.canvas.save()
        self.view.show_notification(f"💾 Sauvegardé")
        self.logger.info(f"💾 Sauvegardé: {path}")
    
    def auto_save(self):
        """Sauvegarde automatique"""
        path = self.canvas.save(filename=f"auto_save_{time.strftime('%Y%m%d_%H%M%S')}.png")
        self.last_save_time = time.time()
        self.logger.info(f"🤖 Sauvegarde auto: {path}")
    
    def toggle_pause(self):
        """Pause/Reprise"""
        if self.state == self.STATE_DRAWING:
            self.state = self.STATE_PAUSED
            self.view.show_notification("⏸️ PAUSE")
            self.logger.info("⏸️ Mode PAUSE")
        else:
            self.state = self.STATE_DRAWING
            self.view.show_notification("▶️ REPRISE")
            self.logger.info("▶️ Mode DESSIN")
    
    def toggle_eraser(self):
        """Active/Désactive la gomme"""
        self.canvas.toggle_eraser()
        if self.canvas.eraser_mode:
            self.state = self.STATE_ERASER
            self.view.show_notification("🧽 GOMME")
            self.logger.info("🧽 Mode GOMME")
        else:
            self.state = self.STATE_DRAWING
            self.view.show_notification("🎨 PINCEAU")
            self.logger.info("🎨 Mode PINCEAU")
    
    def change_color(self, color_number):
        """Change la couleur (1-8)"""
        colors = ['red', 'green', 'blue', 'yellow', 'purple', 'cyan', 'orange', 'white']
        if 1 <= color_number <= len(colors):
            self.canvas.set_color(colors[color_number - 1])
            self.view.show_notification(f"🎨 {colors[color_number - 1].upper()}")
            self.logger.info(f"🎨 Couleur: {colors[color_number - 1]}")
    
    # ===== NOUVELLES FONCTIONS =====
    
    def show_stats(self):
        """Affiche les statistiques"""
        stats = self.data_analyzer.get_statistics()
        if stats:
            self.view.show_notification(f"📊 Points: {stats['total_points']}")
            self.logger.info(f"📊 Stats: {stats}")
    
    def toggle_voice(self):
        """Active/Désactive la reconnaissance vocale"""
        if self.voice.is_available():
            if hasattr(self, 'voice_active') and self.voice_active:
                self.voice.stop_listening()
                self.voice_active = False
                self.view.show_notification("🎤 Voix OFF")
            else:
                self.voice.start_listening()
                self.voice_active = True
                self.view.show_notification("🎤 Voix ON")
    
    def toggle_effects(self):
        """Active/Désactive les effets spéciaux"""
        if not hasattr(self, 'current_effect') or not self.current_effect:
            # Activer un effet aléatoire
            effects = self.special_effects.get_effect_names()
            import random
            self.current_effect = random.choice(effects)
            self.view.show_notification(f"✨ Effet: {self.current_effect}")
        else:
            self.current_effect = None
            self.view.show_notification("✨ Effets OFF")
    
    def toggle_ai(self):
        """Active/Désactive l'assistant IA"""
        if hasattr(self, 'ai_enabled') and self.ai_enabled:
            self.ai_enabled = False
            self.view.show_notification("🤖 IA OFF")
        else:
            self.ai_enabled = True
            self.view.show_notification("🤖 IA ON - Dessinez une forme!")
    
    def start_collab_server(self, port=5000):
        """Démarre un serveur de collaboration"""
        self.collab_server = CollaborationServer(host='0.0.0.0', port=port)
        if self.collab_server.start():
            self.collab_mode = True
            self.state = self.STATE_COLLAB
            self.view.show_notification(f"🌐 Serveur démarré port {port}")
    
    def connect_to_collab(self, host, port=5000):
        """Se connecte à un serveur de collaboration"""
        self.collab_client = CollaborationClient(host=host, port=port, 
                                                callback=self._handle_collab_data)
        if self.collab_client.connect():
            self.collab_mode = True
            self.state = self.STATE_COLLAB
            self.view.show_notification(f"🌐 Connecté à {host}")
    
    def _handle_collab_data(self, data_type, data):
        """Gère les données de collaboration"""
        if data_type == 'draw':
            # Dessiner les données reçues
            pass
        elif data_type == 'canvas':
            # Mettre à jour le canvas
            pass
    
    # ===== UNDO/REDO =====
    
    def undo(self):
        """Annule la dernière action"""
        if hasattr(self.canvas, 'undo') and self.canvas.undo():
            self.view.show_notification("↩️ Undo")
    
    def redo(self):
        """Rétablit la dernière action"""
        if hasattr(self.canvas, 'redo') and self.canvas.redo():
            self.view.show_notification("↪️ Redo")
    
    # ===== EXPORT =====
    
    def export_pdf(self):
        """Exporte en PDF"""
        try:
            path = self.canvas.export_to_pdf()
            self.view.show_notification(f"📄 PDF exporté")
        except Exception as e:
            self.logger.error(f"Erreur export PDF: {e}")
            self.view.show_notification("❌ Erreur PDF", color=(0,0,255))
    
    def export_data(self):
        """Exporte les données d'analyse"""
        path = self.data_analyzer.export_json()
        self.view.show_notification(f"📊 Données exportées")
    
    # ===== NETTOYAGE =====
    
    def quit(self):
        """Quitte l'application"""
        self.logger.info("👋 Arrêt demandé...")
        self.running = False
    
    def cleanup(self):
        """Nettoyage avant fermeture"""
        self.logger.info("="*50)
        self.logger.info("🧹 Nettoyage des ressources...")
        
        # Arrêter les services
        if hasattr(self, 'voice'):
            self.voice.stop_listening()
        
        if hasattr(self, 'collab_server') and self.collab_server:
            self.collab_server.stop()
        
        if hasattr(self, 'collab_client') and self.collab_client:
            self.collab_client.disconnect()
        
        # Sauvegarde finale
        if hasattr(self, 'canvas') and self.canvas.total_points > 0:
            self.canvas.save(filename="final_drawing.png")
            self.data_analyzer.export_json()
        
        # Libérer caméra
        if self.cap:
            self.cap.release()
        
        cv2.destroyAllWindows()
        
        # Afficher statistiques finales
        stats = self.data_analyzer.get_statistics()
        if stats:
            self.logger.info("="*50)
            self.logger.info("📊 STATISTIQUES FINALES")
            self.logger.info(f"   Points dessinés: {stats['total_points']}")
            self.logger.info(f"   Durée session: {stats['session_duration']}")
            self.logger.info(f"   Vitesse moyenne: {stats['avg_speed']:.1f} px/s")
            self.logger.info(f"   Traits: {stats['stroke_count']}")
            self.logger.info("="*50)
        
        self.logger.info("👋 Session terminée")
        self.logger.end_session()
        
        # Message final
        print("\n" + "="*60)
        print("🎨 AIR WRITING - TERMINÉ")
        print(f"📊 Points dessinés: {stats['total_points'] if stats else 0}")
        print("📁 Dessins dans: sauvegardes/")
        print("📁 Logs dans: logs/")
        print("="*60)