import cv2
import base64
import time
from socketio import Client

# Configurações do servidor
SERVER_URL = 'http://127.0.0.1:5001'  # Substitua pelo IP do servidor

# Inicialização do cliente SocketIO
sio = Client()

# Função para capturar e enviar frames
def send_frames():
    cap = cv2.VideoCapture(0)  # Abre a webcam
    while True:
        success, frame = cap.read()
        if not success:
            break
        # Codifica o frame em JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        # Converte para base64 e envia
        frame_b64 = base64.b64encode(buffer).decode('utf-8')
        sio.emit('video_frame', frame_b64)
        time.sleep(0.02)  # Pequeno delay para reduzir a taxa de frames

@sio.event
def connect():
    print("Conectado ao servidor")
    send_frames()

@sio.event
def disconnect():
    print("Desconectado do servidor")

if __name__ == '__main__':
    sio.connect(SERVER_URL)
    sio.wait()
