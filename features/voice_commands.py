# features/voice_commands.py
"""
Contrôle vocal simplifié et robuste
"""
import threading
import queue
import time
from utils.logger import Logger

# Essayer d'importer speech_recognition, mais ne pas planter si absent
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    print("⚠️ speech_recognition non installé. Commande vocale désactivée.")
    print("   Pour l'activer: pip install SpeechRecognition pyaudio")

class VoiceController:
    """Contrôleur vocal avec fallback si bibliothèque manquante"""
    
    def __init__(self, drawing_controller):
        self.logger = Logger()
        self.drawing_controller = drawing_controller
        self.listening = False
        self.thread = None
        self.command_queue = queue.Queue()
        
        # Vérifier disponibilité
        self.available = SPEECH_RECOGNITION_AVAILABLE
        
        if self.available:
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
                # Adapter pour le bruit ambiant
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                self.logger.info("🎤 Microphone initialisé avec succès")
            except Exception as e:
                self.logger.error(f"Erreur initialisation microphone: {e}")
                self.available = False
        
        # Commandes vocales disponibles
        self.commands = {
            'effacer': self._cmd_clear,
            'efface': self._cmd_clear,
            'clear': self._cmd_clear,
            
            'sauvegarder': self._cmd_save,
            'sauvegarde': self._cmd_save,
            'save': self._cmd_save,
            
            'pause': self._cmd_pause,
            'arrête': self._cmd_pause,
            'stop': self._cmd_pause,
            
            'gomme': self._cmd_eraser,
            'effaceur': self._cmd_eraser,
            
            'rouge': lambda: self._cmd_color(1),
            'vert': lambda: self._cmd_color(2),
            'bleu': lambda: self._cmd_color(3),
            'jaune': lambda: self._cmd_color(4),
            'violet': lambda: self._cmd_color(5),
            'blanc': lambda: self._cmd_color(6),
            
            'aide': self._cmd_help,
            'help': self._cmd_help,
            
            'quitter': self._cmd_quit,
            'sortir': self._cmd_quit
        }
        
        if self.available:
            self.logger.info("🎤 VoiceController initialisé (actif)")
        else:
            self.logger.warning("🎤 VoiceController initialisé (inactif - bibliothèque manquante)")
    
    def start_listening(self):
        """Démarre l'écoute vocale"""
        if not self.available:
            self.logger.warning("Impossible de démarrer: speech_recognition non installé")
            return False
        
        if self.listening:
            return True
        
        self.listening = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        self.logger.info("🎤 Écoute vocale démarrée (parlez dans le micro)")
        
        # Notification visuelle
        if hasattr(self.drawing_controller, 'view'):
            self.drawing_controller.view.show_notification("🎤 Micro actif")
        
        return True
    
    def _listen_loop(self):
        """Boucle d'écoute dans un thread séparé"""
        while self.listening:
            try:
                with self.microphone as source:
                    # Écouter avec timeout pour pouvoir vérifier self.listening
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                
                # Reconnaissance Google (nécessite internet)
                try:
                    text = self.recognizer.recognize_google(audio, language='fr-FR')
                    text = text.lower().strip()
                    
                    if text:
                        self.logger.info(f"🎤 Commande reçue: '{text}'")
                        self._process_command(text)
                        
                except sr.UnknownValueError:
                    # Pas de parole comprise - silencieux
                    pass
                except sr.RequestError as e:
                    self.logger.error(f"Erreur service Google: {e}")
                    
            except sr.WaitTimeoutError:
                # Timeout normal - continuer
                pass
            except Exception as e:
                if self.listening:  # Ignorer les erreurs si on arrête
                    self.logger.error(f"Erreur écoute: {e}")
                    time.sleep(0.5)  # Éviter boucle d'erreur rapide
        
        self.logger.info("🎤 Écoute vocale arrêtée")
    
    def _process_command(self, text):
        """Traite la commande vocale reçue"""
        # Chercher correspondance
        for cmd, action in self.commands.items():
            if cmd in text:
                self.logger.info(f"✅ Commande reconnue: {cmd}")
                
                # Notification
                if hasattr(self.drawing_controller, 'view'):
                    self.drawing_controller.view.show_notification(f"🎤 {cmd}")
                
                # Exécuter
                action()
                return
        
        # Commande non reconnue
        self.logger.info(f"❓ Commande non reconnue: {text}")
        if hasattr(self.drawing_controller, 'view'):
            self.drawing_controller.view.show_notification("❓ Non reconnu", color=(0,0,255))
    
    # ===== COMMANDES =====
    
    def _cmd_clear(self):
        """Effacer le canvas"""
        if hasattr(self.drawing_controller, 'clear_canvas'):
            self.drawing_controller.clear_canvas()
    
    def _cmd_save(self):
        """Sauvegarder le dessin"""
        if hasattr(self.drawing_controller, 'save_canvas'):
            self.drawing_controller.save_canvas()
    
    def _cmd_pause(self):
        """Pause/Reprise"""
        if hasattr(self.drawing_controller, 'toggle_pause'):
            self.drawing_controller.toggle_pause()
    
    def _cmd_eraser(self):
        """Activer gomme"""
        if hasattr(self.drawing_controller, 'toggle_eraser'):
            self.drawing_controller.toggle_eraser()
    
    def _cmd_color(self, color_num):
        """Changer couleur"""
        if hasattr(self.drawing_controller, 'change_color'):
            self.drawing_controller.change_color(color_num)
    
    def _cmd_help(self):
        """Afficher aide vocale"""
        help_text = """
╔════════════════════════════════════╗
║    COMMANDES VOCALES DISPONIBLES   ║
╠════════════════════════════════════╣
║ • effacer                          ║
║ • sauvegarder                       ║
║ • pause                             ║
║ • gomme                             ║
║ • rouge, vert, bleu, jaune          ║
║ • violet, blanc                      ║
║ • aide                              ║
║ • quitter                           ║
╚════════════════════════════════════╝
        """
        print(help_text)
        
        if hasattr(self.drawing_controller, 'view'):
            self.drawing_controller.view.show_notification("📖 Aide vocale")
    
    def _cmd_quit(self):
        """Quitter l'application"""
        if hasattr(self.drawing_controller, 'quit'):
            self.drawing_controller.quit()
    
    def stop_listening(self):
        """Arrête l'écoute vocale"""
        self.listening = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        self.logger.info("🎤 Écoute vocale arrêtée")
    
    def is_available(self):
        """Vérifie si la reconnaissance vocale est disponible"""
        return self.available