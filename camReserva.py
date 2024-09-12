import cv2
import base64
import requests
import json

# URL do servidor Flask
SERVER_URL = 'http://localhost:5001'

def send_frame(frame, camera_id):
    """Envia um frame de vídeo para o servidor Flask."""
    _, buffer = cv2.imencode('.jpg', frame)
    encoded_frame = base64.b64encode(buffer).decode('utf-8')

    payload = {
        'camera_id': camera_id,
        'frame': encoded_frame
    }

    headers = {'Content-Type': 'application/json'}
    requests.post(f'{SERVER_URL}/video_frame', data=json.dumps(payload), headers=headers)

def capture_video(camera_id):
    """Captura vídeo de uma câmera e envia os frames para o servidor."""
    cap = cv2.VideoCapture(0)  # 0 para a câmera padrão

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        send_frame(frame, camera_id)

    cap.release()

if __name__ == '__main__':
    capture_video('camera')
