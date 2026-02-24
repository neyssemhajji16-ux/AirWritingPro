
import numpy as np
import cv2
from utils.logger import Logger

class AIAssistant:
    def __init__(self):
        self.logger = Logger()
        self.shapes_database = self._load_shapes_database()
        self.suggestions_enabled = True
        
    def _load_shapes_database(self):
        return {
            'smiley': self._create_smiley,
            'heart': self._create_heart,
            'star': self._create_star,
            'cloud': self._create_cloud,
            'tree': self._create_tree,
            'house': self._create_house,
            'car': self._create_car,
            'flower': self._create_flower
        }
    
    def suggest_shape(self, points):
        if len(points) < 10:
            return None
        
        analysis = self._analyze_points(points)
        
        best_match = None
        best_score = 0
        
        for shape_name, shape_func in self.shapes_database.items():
            score = self._compare_with_shape(analysis, shape_name)
            if score > best_score and score > 0.6:
                best_score = score
                best_match = shape_name
        
        if best_match:
            return {
                'name': best_match,
                'confidence': best_score,
                'points': self.shapes_database[best_match]()
            }
        
        return None
    
    def _analyze_points(self, points):
        points = np.array(points)
        
        center = np.mean(points, axis=0)
        std = np.std(points, axis=0)
        
        width = np.max(points[:,0]) - np.min(points[:,0])
        height = np.max(points[:,1]) - np.min(points[:,1])
        aspect_ratio = width / height if height > 0 else 0
        
        area = width * height
        perimeter = self._calculate_perimeter(points)
        compactness = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
        
        return {
            'center': center,
            'std': std,
            'aspect_ratio': aspect_ratio,
            'compactness': compactness,
            'width': width,
            'height': height,
            'num_points': len(points)
        }
    
    def _calculate_perimeter(self, points):
        if len(points) < 2:
            return 0
        
        perimeter = 0
        for i in range(len(points)-1):
            perimeter += np.linalg.norm(points[i+1] - points[i])
        
        return perimeter
    
    def _compare_with_shape(self, analysis, shape_name):
        shape_profiles = {
            'smiley': {'aspect_ratio': 1.0, 'compactness': 0.8},
            'heart': {'aspect_ratio': 0.9, 'compactness': 0.6},
            'star': {'aspect_ratio': 1.0, 'compactness': 0.4},
            'cloud': {'aspect_ratio': 1.5, 'compactness': 0.3},
            'tree': {'aspect_ratio': 0.5, 'compactness': 0.5},
            'house': {'aspect_ratio': 1.2, 'compactness': 0.7},
            'car': {'aspect_ratio': 2.0, 'compactness': 0.8},
            'flower': {'aspect_ratio': 1.0, 'compactness': 0.5}
        }
        
        if shape_name not in shape_profiles:
            return 0
        
        profile = shape_profiles[shape_name]
        
        score_aspect = 1 - abs(analysis['aspect_ratio'] - profile['aspect_ratio']) / 2
        score_compact = 1 - abs(analysis['compactness'] - profile['compactness'])
        
        return (score_aspect + score_compact) / 2
    
    def _create_smiley(self):
        points = []
        center = (250, 250)
        radius = 100
        
        for angle in range(0, 360, 10):
            x = int(center[0] + radius * np.cos(np.radians(angle)))
            y = int(center[1] + radius * np.sin(np.radians(angle)))
            points.append((x, y))
        
        return points
    
    def _create_heart(self):
        points = []
        for t in np.linspace(0, 2*np.pi, 50):
            x = 250 + 100 * (16 * np.sin(t)**3)
            y = 250 - 100 * (13 * np.cos(t) - 5 * np.cos(2*t) - 2 * np.cos(3*t) - np.cos(4*t))
            points.append((int(x/4), int(y/4)))
        return points
    
    def _create_star(self):
        points = []
        center = (250, 250)
        outer_radius = 100
        inner_radius = 40
        num_points = 5
        
        for i in range(num_points * 2):
            angle = i * np.pi / num_points
            radius = outer_radius if i % 2 == 0 else inner_radius
            x = int(center[0] + radius * np.cos(angle))
            y = int(center[1] + radius * np.sin(angle))
            points.append((x, y))
        
        return points
    
    def _create_cloud(self):
        points = []
        centers = [(200, 250), (300, 230), (250, 200), (350, 250), (280, 280)]
        
        for cx, cy in centers:
            for angle in range(0, 360, 30):
                x = int(cx + 40 * np.cos(np.radians(angle)))
                y = int(cy + 30 * np.sin(np.radians(angle)))
                points.append((x, y))
        
        return points
    
    def _create_tree(self):
        points = []
        
        for y in range(300, 400):
            points.append((250, y))
        
        for angle in range(0, 360, 20):
            x = 250 + int(80 * np.cos(np.radians(angle)))
            y = 250 + int(60 * np.sin(np.radians(angle)))
            points.append((x, y))
        
        return points
    
    def _create_house(self):
        points = []
        
        for x in range(150, 351):
            points.append((x, 350))
        
        for x in range(150, 351):
            y = 200 + abs(x - 250)
            points.append((x, y))
        
        return points
    
    def _create_car(self):
        points = []
        
        for x in range(150, 351):
            points.append((x, 300))
        
        for x in range(180, 321):
            points.append((x, 250))
        
        for cx in [200, 300]:
            for angle in range(0, 360, 30):
                x = cx + 30 * np.cos(np.radians(angle))
                y = 330 + 30 * np.sin(np.radians(angle))
                points.append((int(x), int(y)))
        
        return points
    
    def _create_flower(self):
        points = []
        center = (250, 250)
        
        for petal in range(6):
            angle = petal * 60
            for r in range(30, 60, 5):
                x = center[0] + r * np.cos(np.radians(angle))
                y = center[1] + r * np.sin(np.radians(angle))
                for sub_angle in range(0, 360, 30):
                    sx = x + 20 * np.cos(np.radians(sub_angle))
                    sy = y + 20 * np.sin(np.radians(sub_angle))
                    points.append((int(sx), int(sy)))
        
        return points
