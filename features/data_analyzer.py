
import numpy as np
import cv2
from datetime import datetime
import json
from utils.logger import Logger

class DataAnalyzer:
    def __init__(self):
        self.logger = Logger()
        self.data = {
            'timestamps': [],
            'positions_x': [],
            'positions_y': [],
            'speeds': [],
            'colors': [],
            'brush_sizes': []
        }
        self.session_start = datetime.now()
        self.last_position = None
        self.last_time = None
        
    def add_point(self, x, y, color, brush_size):
        timestamp = datetime.now()
        
        self.data['timestamps'].append(timestamp)
        self.data['positions_x'].append(x)
        self.data['positions_y'].append(y)
        self.data['colors'].append(str(color))
        self.data['brush_sizes'].append(brush_size)
        
        if self.last_position and self.last_time:
            dx = x - self.last_position[0]
            dy = y - self.last_position[1]
            dt = (timestamp - self.last_time).total_seconds()
            
            if dt > 0:
                speed = np.sqrt(dx*dx + dy*dy) / dt
                self.data['speeds'].append(speed)
        
        self.last_position = (x, y)
        self.last_time = timestamp
    
    def generate_heatmap(self, width, height):
        if len(self.data['positions_x']) < 10:
            return None
        
        heatmap = np.zeros((height, width), dtype=np.float32)
        
        for x, y in zip(self.data['positions_x'], self.data['positions_y']):
            if 0 <= x < width and 0 <= y < height:
                heatmap[y, x] += 1
        
        if np.max(heatmap) > 0:
            heatmap = heatmap / np.max(heatmap) * 255
        
        heatmap_colored = cv2.applyColorMap(heatmap.astype(np.uint8), cv2.COLORMAP_JET)
        return heatmap_colored
    
    def get_statistics(self):
        if len(self.data['positions_x']) < 2:
            return None
        
        stats = {
            'total_points': len(self.data['positions_x']),
            'session_duration': str(datetime.now() - self.session_start).split('.')[0],
            'avg_speed': np.mean(self.data['speeds']) if self.data['speeds'] else 0,
            'max_speed': np.max(self.data['speeds']) if self.data['speeds'] else 0,
            'drawing_area': self._calculate_drawing_area(),
            'color_distribution': self._analyze_colors(),
            'stroke_count': self._count_strokes()
        }
        
        return stats
    
    def _calculate_drawing_area(self):
        if len(self.data['positions_x']) < 10:
            return 0
        
        x_min = min(self.data['positions_x'])
        x_max = max(self.data['positions_x'])
        y_min = min(self.data['positions_y'])
        y_max = max(self.data['positions_y'])
        
        return (x_max - x_min) * (y_max - y_min)
    
    def _analyze_colors(self):
        color_counts = {}
        for color in self.data['colors']:
            color_counts[color] = color_counts.get(color, 0) + 1
        
        total = len(self.data['colors'])
        distribution = {c: count/total*100 for c, count in color_counts.items()}
        return distribution
    
    def _count_strokes(self):
        if len(self.data['speeds']) < 10:
            return 0
        
        strokes = 0
        speed_threshold = 10
        
        for i in range(1, len(self.data['speeds'])):
            if (self.data['speeds'][i-1] < speed_threshold and 
                self.data['speeds'][i] >= speed_threshold):
                strokes += 1
        
        return strokes
    
    def export_json(self, filename=None):
        if filename is None:
            filename = f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data_copy = self.data.copy()
        data_copy['timestamps'] = [ts.isoformat() for ts in data_copy['timestamps']]
        data_copy['statistics'] = self.get_statistics()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data_copy, f, indent=2)
        
        self.logger.info(f"📊 Données exportées: {filename}")
        return filename
