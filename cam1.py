import cv2
import base64
import time
import threading
from socketio import Client
from queue import Queue

# Configurações do servidor
SERVER_URL = 'http://127.0.0.1:5001'  # Substitua pelo IP do servidor

# Inicialização do cliente SocketIO
sio = Client()
frame_queue = Queue()

def capture_frames(queue):
    cap = cv2.VideoCapture(0)  # Abre a câmera 0 

    if not cap.isOpened():
        print("Erro: Não foi possível abrir a câmera.")
        return

    while True:
        success, frame = cap.read()
        if not success:
            print("Erro: Não foi possível capturar o frame.")
            break
        queue.put(frame)
        time.sleep(0.05)  # Ajuste o tempo para diminuir o processamento

    cap.release()

def send_frames(queue):
    while True:
        if not queue.empty():
            frame = queue.get()
            _, buffer = cv2.imencode('.jpg', frame)
            frame_b64 = base64.b64encode(buffer).decode('utf-8')
            sio.emit('video_frame', {'camera_id': 'camera', 'frame': frame_b64})
        time.sleep(0.05)  # Ajuste o tempo para diminuir o processamento

@sio.event
def connect():
    print("Conectado ao servidor")

@sio.event
def disconnect():
    print("Desconectado do servidor")

if __name__ == '__main__':
    capture_thread = threading.Thread(target=capture_frames, args=(frame_queue,))
    send_thread = threading.Thread(target=send_frames, args=(frame_queue,))

    capture_thread.start()
    send_thread.start()

    sio.connect(SERVER_URL)
    sio.wait()
