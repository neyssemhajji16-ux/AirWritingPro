# utils/logger.py
"""
Système de logging professionnel avec couleurs
"""
from datetime import datetime
import os
import traceback
import inspect

class Logger:
    _instance = None
    
    # Codes couleur ANSI
    COLORS = {
        'INFO': '\033[92m',      # Vert
        'WARNING': '\033[93m',    # Jaune
        'ERROR': '\033[91m',      # Rouge
        'DEBUG': '\033[94m',      # Bleu
        'RESET': '\033[0m'        # Reset
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.logs = []
        self.log_file = None
        self.session_start = datetime.now()
        self.log_count = {'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'DEBUG': 0}
        
    def start_session(self):
        """Démarre une nouvelle session"""
        self.session_start = datetime.now()
        timestamp = self.session_start.strftime("%Y%m%d_%H%M%S")
        
        # Créer dossier logs si nécessaire
        if not os.path.exists("logs"):
            os.makedirs("logs")
            
        self.log_file = open(f"logs/session_{timestamp}.log", "w", encoding='utf-8')
        
        # Bannière de démarrage
        self._print_banner()
        self.info("="*50)
        self.info("🚀 NOUVELLE SESSION DÉMARRÉE")
        self.info(f"📅 Date: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}")
        self.info("="*50)
    
    def _print_banner(self):
        """Affiche une bannière colorée"""
        banner = """
╔══════════════════════════════════════════════════════════╗
║           AIR WRITING - LOGGING SYSTEM v2.0              ║
║            Niveau Ingénieur - Session Active             ║
╚══════════════════════════════════════════════════════════╝
        """
        print(f"\033[96m{banner}\033[0m")
    
    def info(self, message):
        """Log niveau information"""
        self._log("INFO", message)
    
    def warning(self, message):
        """Log niveau avertissement"""
        self._log("WARNING", message)
    
    def error(self, message):
        """Log niveau erreur"""
        self._log("ERROR", message)
        # Afficher la trace en cas d'erreur
        traceback.print_exc()
    
    def debug(self, message):
        """Log niveau debug"""
        self._log("DEBUG", message)
    
    def _log(self, level, message):
        """Méthode interne pour logger"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Informations sur l'appelant
        caller = inspect.stack()[2]
        filename = os.path.basename(caller.filename)
        line = caller.lineno
        
        # Formatage du message
        log_entry = f"[{timestamp}] [{level}] [{filename}:{line}] {message}"
        
        # Version colorée pour console
        color = self.COLORS.get(level, '')
        reset = self.COLORS['RESET']
        console_entry = f"{color}{log_entry}{reset}"
        
        # Affichage
        print(console_entry)
        
        # Sauvegarde
        self.logs.append(log_entry)
        self.log_count[level] = self.log_count.get(level, 0) + 1
        
        if self.log_file:
            self.log_file.write(log_entry + "\n")
            self.log_file.flush()
    
    def get_session_stats(self):
        """Retourne les statistiques de la session"""
        duration = datetime.now() - self.session_start
        return {
            'duration': str(duration).split('.')[0],
            'logs': self.log_count,
            'total': sum(self.log_count.values())
        }
    
    def end_session(self):
        """Termine la session"""
        stats = self.get_session_stats()
        
        self.info("="*50)
        self.info("👋 FIN DE SESSION")
        self.info(f"⏱️ Durée: {stats['duration']}")
        self.info(f"📊 Logs: INFO={stats['logs']['INFO']}, "
                 f"WARNING={stats['logs']['WARNING']}, "
                 f"ERROR={stats['logs']['ERROR']}")
        self.info("="*50)
        
        if self.log_file:
            self.log_file.close()