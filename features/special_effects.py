# features/special_effects.py
import cv2
import numpy as np
import math
import random
from utils.logger import Logger

class SpecialEffects:
    def __init__(self):
        self.logger = Logger()
        self.effects = {
            'glow': self.apply_glow,
            'rainbow': self.apply_rainbow,
            'sparkle': self.apply_sparkle,
            'trail': self.apply_trail,
            'neon': self.apply_neon,
            'fire': self.apply_fire,
            'water': self.apply_water,
            'particles': self.apply_particles
        }
        self.active_effect = None
        self.particle_system = ParticleSystem()
        self.time = 0
    
    def apply_glow(self, canvas, points, color, size):
        if len(points) < 2:
            return canvas
        
        h, w = canvas.shape[:2]
        glow = np.zeros((h, w, 3), dtype=np.uint8)
        
        for i in range(len(points)-1):
            pt1 = points[i]
            pt2 = points[i+1]
            
            for r in range(size, size*3, 2):
                cv2.line(glow, pt1, pt2, color, r)
        
        glow = cv2.GaussianBlur(glow, (21, 21), 0)
        
        mask = cv2.cvtColor(glow, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(mask, 1, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)
        
        bg = cv2.bitwise_and(canvas, canvas, mask=mask_inv)
        fg = cv2.bitwise_and(glow, glow, mask=mask)
        
        return cv2.add(bg, fg)
    
    def apply_rainbow(self, canvas, points, color, size):
        if len(points) < 2:
            return canvas
        
        rainbow_colors = [
            (0, 0, 255),   # Rouge
            (0, 165, 255), # Orange
            (0, 255, 255), # Jaune
            (0, 255, 0),   # Vert
            (255, 0, 0),   # Bleu
            (255, 0, 255)  # Violet
        ]
        
        for i in range(len(points)-1):
            pt1 = points[i]
            pt2 = points[i+1]
            color_idx = i % len(rainbow_colors)
            cv2.line(canvas, pt1, pt2, rainbow_colors[color_idx], size)
        
        return canvas
    
    def apply_sparkle(self, canvas, points, color, size):
        if len(points) < 2:
            return canvas
        
        h, w = canvas.shape[:2]
        
        for i in range(len(points)-1):
            pt1 = points[i]
            pt2 = points[i+1]
            
            cv2.line(canvas, pt1, pt2, color, size)
            
            for _ in range(3):
                x = random.randint(min(pt1[0], pt2[0]), max(pt1[0], pt2[0]))
                y = random.randint(min(pt1[1], pt2[1]), max(pt1[1], pt2[1]))
                
                if 0 <= x < w and 0 <= y < h:
                    cv2.circle(canvas, (x, y), 2, (255, 255, 255), -1)
                    cv2.line(canvas, (x-3, y), (x+3, y), (255, 255, 255), 1)
                    cv2.line(canvas, (x, y-3), (x, y+3), (255, 255, 255), 1)
        
        return canvas
    
    def apply_trail(self, canvas, points, color, size):
        if len(points) < 3:
            return canvas
        
        for i in range(len(points)-1):
            alpha = i / len(points)
            faded_color = tuple(int(c * alpha) for c in color)
            
            if i > 0:
                cv2.line(canvas, points[i-1], points[i], faded_color, size)
        
        return canvas
    
    def apply_neon(self, canvas, points, color, size):
        if len(points) < 2:
            return canvas
        
        for layer in range(3):
            layer_size = size + layer * 2
            layer_color = tuple(min(255, int(c * (1 - layer * 0.3))) for c in color)
            
            for i in range(len(points)-1):
                pt1 = points[i]
                pt2 = points[i+1]
                cv2.line(canvas, pt1, pt2, layer_color, layer_size)
        
        return canvas
    
    def apply_fire(self, canvas, points, color, size):
        if len(points) < 2:
            return canvas
        
        fire_colors = [
            (0, 0, 255),   # Rouge
            (0, 69, 255),  # Orange-rouge
            (0, 165, 255), # Orange
            (0, 255, 255)  # Jaune
        ]
        
        for i in range(len(points)-1):
            pt1 = points[i]
            pt2 = points[i+1]
            
            for j, fire_color in enumerate(fire_colors):
                offset = j * 2
                cv2.line(canvas, 
                        (pt1[0] - offset, pt1[1]), 
                        (pt2[0] - offset, pt2[1]), 
                        fire_color, size - j)
        
        return canvas
    
    def apply_water(self, canvas, points, color, size):
        if len(points) < 2:
            return canvas
        
        h, w = canvas.shape[:2]
        
        for i in range(len(points)-1):
            pt1 = points[i]
            pt2 = points[i+1]
            
            dx = pt2[0] - pt1[0]
            dy = pt2[1] - pt1[1]
            length = math.sqrt(dx*dx + dy*dy)
            
            if length > 0:
                for wave in range(3):
                    offset = int(5 * math.sin(i * 0.5 + wave))
                    perp_x = -dy / length * offset
                    perp_y = dx / length * offset
                    
                    cv2.line(canvas,
                            (int(pt1[0] + perp_x), int(pt1[1] + perp_y)),
                            (int(pt2[0] + perp_x), int(pt2[1] + perp_y)),
                            (255, 255, 255), 1)
        
        for i in range(len(points)-1):
            cv2.line(canvas, points[i], points[i+1], (255, 255, 255), size)
        
        return canvas
    
    def apply_particles(self, canvas, points, color, size):
        """Applique l'effet de particules"""
        if points:
            last_point = points[-1]
            self.particle_system.emit(last_point[0], last_point[1], color, 3)
        
        self.particle_system.update()
        self.particle_system.draw(canvas)
        return canvas
    
    def apply_effect(self, effect_name, canvas, points, color, size):
        """Applique un effet par son nom"""
        if effect_name in self.effects:
            return self.effects[effect_name](canvas, points, color, size)
        return canvas
    
    def set_effect(self, effect_name):
        if effect_name in self.effects:
            self.active_effect = effect_name
            self.logger.info(f"✨ Effet activé: {effect_name}")
            return True
        return False
    
    def get_effect_names(self):
        return list(self.effects.keys())


class ParticleSystem:
    """Système de particules simple"""
    
    def __init__(self):
        self.particles = []
    
    def emit(self, x, y, color, count=5):
        """Émet des particules"""
        for _ in range(count):
            self.particles.append({
                'x': x + random.randint(-15, 15),
                'y': y + random.randint(-15, 15),
                'vx': random.uniform(-2, 2),
                'vy': random.uniform(-2, 2),
                'life': 1.0,
                'color': color,
                'size': random.randint(2, 5)
            })
    
    def update(self):
        """Met à jour les particules"""
        for p in self.particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 0.02
            if p['life'] <= 0:
                self.particles.remove(p)
    
    def draw(self, canvas):
        """Dessine les particules"""
        for p in self.particles:
            if p['life'] > 0:
                alpha = p['life']
                color = tuple(int(c * alpha) for c in p['color'])
                cv2.circle(canvas, (int(p['x']), int(p['y'])), 
                          int(p['size'] * p['life']), color, -1)