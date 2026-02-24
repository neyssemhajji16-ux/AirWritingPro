# features/export_features.py
"""
Module d'export avancé
Exporte les dessins dans différents formats
"""
import cv2
import numpy as np
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import json
import zipfile
from utils.logger import Logger
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.utils import ImageReader

class ExportManager:
    """Gère l'export des dessins dans multiples formats"""
    
    def __init__(self):
        self.logger = Logger()
        self.logger.info("📤 ExportManager initialisé")
        
        self.export_dir = "exports"
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)
        
        # Formats supportés
        self.formats = {
            'png': self.export_png,
            'jpg': self.export_jpg,
            'pdf': self.export_pdf,
            'svg': self.export_svg,
            'json': self.export_json,
            'txt': self.export_txt,
            'zip': self.export_zip
        }
    
    def export(self, canvas, metadata=None, formats=None):
        """
        Exporte le dessin dans plusieurs formats
        """
        if formats is None:
            formats = ['png', 'pdf']
        
        if metadata is None:
            metadata = self._create_metadata()
        
        results = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"dessin_{timestamp}"
        
        for fmt in formats:
            if fmt in self.formats:
                try:
                    filename = f"{base_name}.{fmt}"
                    path = os.path.join(self.export_dir, filename)
                    self.formats[fmt](canvas, path, metadata)
                    results[fmt] = path
                    self.logger.info(f"✅ Export {fmt}: {path}")
                except Exception as e:
                    self.logger.error(f"❌ Erreur export {fmt}: {e}")
        
        return results
    
    def export_png(self, canvas, path, metadata=None):
        """Export en PNG (haute qualité)"""
        cv2.imwrite(path, canvas, [cv2.IMWRITE_PNG_COMPRESSION, 0])
    
    def export_jpg(self, canvas, path, metadata=None):
        """Export en JPG (compressé)"""
        cv2.imwrite(path, canvas, [cv2.IMWRITE_JPEG_QUALITY, 95])
    
    def export_pdf(self, canvas, path, metadata=None):
        """Export en PDF"""
        # Convertir OpenCV en PIL
        rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        
        # Créer PDF
        c = pdf_canvas.Canvas(path, pagesize=A4)
        
        # Adapter à la page
        img_width, img_height = pil_img.size
        page_width, page_height = A4
        
        scale = min(page_width / img_width, page_height / img_height)
        new_width = img_width * scale
        new_height = img_height * scale
        
        # Centrer sur la page
        x = (page_width - new_width) / 2
        y = (page_height - new_height) / 2
        
        # Sauvegarder temporairement
        temp_path = path.replace('.pdf', '_temp.png')
        pil_img.save(temp_path)
        
        # Ajouter au PDF
        c.drawImage(temp_path, x, y, width=new_width, height=new_height)
        
        # Ajouter métadonnées
        if metadata:
            c.setFont("Helvetica", 10)
            c.drawString(50, 50, f"Créé le: {metadata['date']}")
            c.drawString(50, 35, f"Taille pinceau: {metadata['brush_size']}")
        
        c.save()
        
        # Nettoyer
        os.remove(temp_path)
    
    def export_svg(self, canvas, path, metadata=None):
        """Export en SVG (vectoriel)"""
        h, w = canvas.shape[:2]
        
        # Créer SVG
        svg_content = [f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">']
        
        # Convertir les pixels en chemins SVG (simplifié)
        gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
        
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            if cv2.contourArea(cnt) > 10:
                # Simplifier le contour
                epsilon = 0.01 * cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, epsilon, True)
                
                # Convertir en path SVG
                points = approx.reshape(-1, 2)
                path_data = "M " + " L ".join([f"{p[0]},{p[1]}" for p in points]) + " Z"
                
                svg_content.append(f'<path d="{path_data}" stroke="black" fill="none" />')
        
        svg_content.append('</svg>')
        
        # Sauvegarder
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(svg_content))
    
    def export_json(self, canvas, path, metadata=None):
        """Export en JSON (données brutes)"""
        h, w = canvas.shape[:2]
        
        # Convertir en données sérialisables
        data = {
            'metadata': metadata,
            'dimensions': {'width': w, 'height': h},
            'pixels': []
        }
        
        # Option: encoder les pixels en base64 (simplifié ici)
        # Pour un vrai projet, on utiliserait numpy.tolist()
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def export_txt(self, canvas, path, metadata=None):
        """Export en texte (ASCII art)"""
        h, w = canvas.shape[:2]
        gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
        
        # Caractères pour ASCII art (du plus clair au plus foncé)
        chars = " .:-=+*#%@"
        
        ascii_art = []
        scale = max(1, h // 50)  # Redimensionner pour texte
        
        for y in range(0, h, scale):
            line = ""
            for x in range(0, w, scale):
                # Moyenne de la zone
                zone = gray[y:min(y+scale, h), x:min(x+scale, w)]
                avg = np.mean(zone)
                
                # Convertir en caractère
                char_idx = int(avg / 255 * (len(chars) - 1))
                line += chars[char_idx]
            ascii_art.append(line)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(ascii_art))
    
    def export_zip(self, canvas, path, metadata=None):
        """Export en ZIP (tous formats)"""
        with zipfile.ZipFile(path, 'w') as zipf:
            # Exporter tous les formats
            for fmt in ['png', 'jpg', 'json', 'txt']:
                temp_path = path.replace('.zip', f'_temp.{fmt}')
                self.formats[fmt](canvas, temp_path, metadata)
                zipf.write(temp_path, os.path.basename(temp_path))
                os.remove(temp_path)
    
    def _create_metadata(self):
        """Crée les métadonnées par défaut"""
        return {
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'app_version': '2.0',
            'brush_size': 5,
            'colors_used': []
        }
    
    def batch_export(self, canvas_list, names=None):
        """Exporte plusieurs dessins en lot"""
        results = []
        for i, canvas in enumerate(canvas_list):
            name = names[i] if names and i < len(names) else f"dessin_{i}"
            res = self.export(canvas, formats=['png', 'pdf'])
            results.append(res)
        return results
