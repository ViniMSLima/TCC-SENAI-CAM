import cv2
import base64
import time
import socketio

# Conecta ao servidor Flask via WebSocket
sio = socketio.Client()

@sio.event
def connect():
    print('Conectado ao servidor Flask.')

@sio.event
def disconnect():
    print('Desconectado do servidor Flask.')

@sio.event
def connect_error(data):
    print(f'Falha na conexão: {data}')

try:
    sio.connect('http://localhost:5000')
except Exception as e:
    print(f'Erro ao conectar ao servidor: {e}')
    exit()

def main():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Erro: Não foi possível abrir a câmera.")
        return

    print("Câmera conectada com sucesso.")

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                print("Erro: Não foi possível capturar o frame.")
                break

            # Codifica o frame como JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')

            # Envia o frame para o servidor
            sio.emit('video_frame', frame_base64)
            print("Frame enviado para o servidor.")

            time.sleep(0.1)  # Ajuste a taxa de quadros, se necessário

    except KeyboardInterrupt:
        print("Interrompido pelo usuário")

    finally:
        cap.release()
        sio.disconnect()

if __name__ == "__main__":
    main()
