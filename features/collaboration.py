
import socket
import threading
import json
import pickle
import cv2
import numpy as np
from utils.logger import Logger

class CollaborationServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.logger = Logger()
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []
        self.running = False
        self.canvas_state = None
        self.thread = None
        
    def start(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            self.thread = threading.Thread(target=self._accept_clients)
            self.thread.daemon = True
            self.thread.start()
            
            self.logger.info(f"🌐 Serveur démarré sur {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage serveur: {e}")
            return False
    
    def _accept_clients(self):
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                self.logger.info(f"👤 Nouveau client: {address}")
                
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
                
                self.clients.append({
                    'socket': client_socket,
                    'address': address,
                    'thread': client_thread
                })
                
            except Exception as e:
                if self.running:
                    self.logger.error(f"Erreur accept client: {e}")
    
    def _handle_client(self, client_socket, address):
        try:
            while self.running:
                data = client_socket.recv(4096)
                if not data:
                    break
                
                message = json.loads(data.decode('utf-8'))
                
                if message['type'] == 'draw':
                    self._broadcast_draw(message['data'], exclude=address)
                elif message['type'] == 'canvas_request':
                    self._send_canvas(client_socket)
                    
        except Exception as e:
            self.logger.error(f"Erreur client {address}: {e}")
        finally:
            self._remove_client(client_socket)
            client_socket.close()
    
    def _broadcast_draw(self, draw_data, exclude=None):
        message = json.dumps({
            'type': 'draw',
            'data': draw_data
        }).encode('utf-8')
        
        for client in self.clients:
            if client['address'] != exclude:
                try:
                    client['socket'].send(message)
                except:
                    pass
    
    def _send_canvas(self, client_socket):
        if self.canvas_state is not None:
            try:
                _, encoded = cv2.imencode('.jpg', self.canvas_state, [cv2.IMWRITE_JPEG_QUALITY, 80])
                data = pickle.dumps(encoded)
                
                message = json.dumps({
                    'type': 'canvas',
                    'data': data.hex()
                }).encode('utf-8')
                
                client_socket.send(message)
                
            except Exception as e:
                self.logger.error(f"Erreur envoi canvas: {e}")
    
    def _remove_client(self, client_socket):
        self.clients = [c for c in self.clients if c['socket'] != client_socket]
    
    def update_canvas(self, canvas):
        self.canvas_state = canvas.copy()
    
    def stop(self):
        self.running = False
        
        for client in self.clients:
            try:
                client['socket'].close()
            except:
                pass
        
        if self.server_socket:
            self.server_socket.close()
        
        self.logger.info("🌐 Serveur arrêté")


class CollaborationClient:
    def __init__(self, host='localhost', port=5000, callback=None):
        self.logger = Logger()
        self.host = host
        self.port = port
        self.callback = callback
        self.socket = None
        self.running = False
        self.thread = None
    
    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.running = True
            
            self.thread = threading.Thread(target=self._receive_data)
            self.thread.daemon = True
            self.thread.start()
            
            self._send_message('canvas_request', {})
            
            self.logger.info(f"🌐 Connecté à {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur connexion: {e}")
            return False
    
    def _receive_data(self):
        while self.running:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                
                message = json.loads(data.decode('utf-8'))
                
                if message['type'] == 'draw' and self.callback:
                    self.callback('draw', message['data'])
                elif message['type'] == 'canvas' and self.callback:
                    encoded = pickle.loads(bytes.fromhex(message['data']))
                    img = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
                    self.callback('canvas', img)
                    
            except Exception as e:
                if self.running:
                    self.logger.error(f"Erreur réception: {e}")
    
    def send_draw(self, draw_data):
        self._send_message('draw', draw_data)
    
    def _send_message(self, msg_type, data):
        try:
            message = json.dumps({
                'type': msg_type,
                'data': data
            }).encode('utf-8')
            self.socket.send(message)
        except Exception as e:
            self.logger.error(f"Erreur envoi: {e}")
    
    def disconnect(self):
        self.running = False
        if self.socket:
            self.socket.close()
        self.logger.info("🌐 Déconnecté")
