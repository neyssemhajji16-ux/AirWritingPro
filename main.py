# main.py
"""
AIR WRITING - Version Ingénieur
Projet professionnel avec architecture MVC complète
"""
import sys
import os
import cv2

# Ajouter le chemin au PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from controllers.drawing_controller import DrawingController
from utils.logger import Logger
from utils.config import Config

def setup_environment():
    """Prépare l'environnement"""
    # Créer les dossiers nécessaires
    for path in Config.PATHS.values():
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"📁 Dossier créé: {path}")

def print_banner():
    """Affiche la bannière de démarrage"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     █████╗ ██╗██████╗     ██╗    ██╗██████╗ ██╗████████╗    ║
║    ██╔══██╗██║██╔══██╗    ██║    ██║██╔══██╗██║╚══██╔══╝    ║
║    ███████║██║██████╔╝    ██║ █╗ ██║██████╔╝██║   ██║       ║
║    ██╔══██║██║██╔══██╗    ██║███╗██║██╔══██╗██║   ██║       ║
║    ██║  ██║██║██║  ██║    ╚███╔███╔╝██║  ██║██║   ██║       ║
║    ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝     ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝   ╚═╝       ║
║                                                              ║
║              ÉCRITURE EN L'AIR - NIVEAU INGÉNIEUR           ║
║                    Version 2.0 - Architecture MVC           ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  ▶️  Instructions:                                           ║
║     • Montrez votre index pour dessiner                      ║
║     • Utilisez les touches 1-8 pour changer de couleur      ║
║     • Appuyez sur 'h' pour l'aide                            ║
║     • Echap pour quitter                                     ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    """Fonction principale"""
    try:
        # Setup
        setup_environment()
        print_banner()
        
        # Créer et lancer l'application
        app = DrawingController()
        
        # Configurer la souris si nécessaire
        # cv2.setMouseCallback("AIR WRITING - NIVEAU INGENIEUR", app.view.handle_mouse)
        
        # Lancer la boucle principale
        app.run()
        
    except KeyboardInterrupt:
        print("\n👋 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n" + "="*60)
        print("🏁 Application terminée")
        print("📁 Les dessins sont dans le dossier 'sauvegardes/'")
        print("📁 Les logs sont dans le dossier 'logs/'")
        print("="*60)
        
        # Petite pause pour lire les messages
        cv2.waitKey(1000)

if __name__ == "__main__":
    main()