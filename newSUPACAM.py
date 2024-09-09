import cv2
import base64
import time
import threading
import numpy as np
import os
import requests
from socketio import Client
from queue import Queue

# Configurações do servidor
SERVER_URL = 'http://127.0.0.1:5001'  # Substitua pelo IP do servidor

# Inicialização do cliente SocketIO
sio = Client()
frame_queue = Queue()
piece_detected = False
last_detection_time = 0
DETECTION_DELAY = 5  # Tempo em segundos para considerar uma peça como nova

def capture_frames(queue):
    """Função para capturar frames da câmera e colocá-los em uma fila."""
    cap = cv2.VideoCapture(1)  # Abre a webcam

    if not cap.isOpened():
        print("Erro: Não foi possível abrir a câmera.")
        return

    while True:
        success, frame = cap.read()
        if not success:
            print("Erro: Não foi possível capturar o frame.")
            break
        queue.put(frame)
        time.sleep(0.01)  # Pequeno delay para reduzir a taxa de frames

    cap.release()

def send_frames(queue):
    """Função para enviar frames capturados para o servidor via SocketIO."""
    while True:
        if not queue.empty():
            frame = queue.get()
            # Codifica o frame em JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            # Converte para base64 e envia
            frame_b64 = base64.b64encode(buffer).decode('utf-8')
            sio.emit('video_frame', {'camera_id': 'camera_1', 'frame': frame_b64})
        time.sleep(0.01)  # Pequeno delay para sincronização

def send_image_to_server(image_path):
    """Função para enviar a imagem processada para análise da IA."""
    url = 'http://127.0.0.1:5000/json/'  # Atualize com o endereço do seu servidor
    with open(image_path, 'rb') as image_file:
        files = {'image': image_file}
        response = requests.post(url, files=files)
    
    if response.status_code == 200:
        print(f"Server response: {response.json()}")
    else:
        print(f"Failed to get response from server. Status code: {response.status_code}")

def process_frames(queue):
    """Função para processar frames capturados e enviar para análise."""
    global piece_detected, last_detection_time
    save_dir = 'captured_images/prediction_test'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    counter = 0

    while True:
        if not queue.empty():
            frame = queue.get()
            image_path = os.path.join(save_dir, '0.png')
            cv2.imwrite(image_path, frame)
            
            # Chame a função de processamento de imagem
            processed_image_path = resize_and_process_image(image_path, save_dir, counter)
            
            if processed_image_path is not None: 
                send_image_to_server(processed_image_path)
                counter += 1
            else:
                print("Erro ao processar a imagem. O caminho da imagem processada é None.")
        
        # Resetar a variável de detecção após um período sem detectar uma peça
        if piece_detected and (time.time() - last_detection_time >= DETECTION_DELAY):
            piece_detected = False
        
        time.sleep(0.1)

def resize_and_process_image(image_path, output_dir, counter, size=(128, 72)):
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)

    if img is None:
        print(f"Erro ao ler a imagem: {image_path}")
        return None  # Retorna None se a imagem não puder ser lida

    img_blur = cv2.GaussianBlur(img, (5, 5), 0)
    img_hsv = cv2.cvtColor(img_blur, cv2.COLOR_BGR2HSV)

    # Define the color ranges
    color_ranges = {
        'red1': (np.array([0, 100, 100]), np.array([10, 255, 255])),
        'red2': (np.array([160, 100, 100]), np.array([180, 255, 255])),
        'light_blue': (np.array([85, 100, 100]), np.array([110, 255, 255]))
    }

    # Create masks for each color
    masks = {}
    for key in color_ranges:
        lower_bound, upper_bound = color_ranges[key]
        masks[key] = create_color_mask(img_hsv, lower_bound, upper_bound)

    # Combine red masks
    masks['red'] = masks['red1'] + masks['red2']
    del masks['red1']
    del masks['red2']

    # Filter the image with each mask
    filtered_images = filter_color(img, masks)

    # Determine which color has the most presence
    dominant_color = max(filtered_images.keys(), key=lambda color: np.sum(masks[color]))

    # Get the filtered image for the dominant color
    dominant_filtered_image = filtered_images[dominant_color]
    
    # Resize and maintain aspect ratio
    resized_image = resize_and_maintain_aspect_ratio(dominant_filtered_image, size)
    
    output_path = os.path.join(output_dir, '0.png')
    cv2.imwrite(output_path, resized_image, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    
    # Verifique se a imagem foi salva corretamente
    if not os.path.exists(output_path):
        print(f"Erro ao salvar a imagem processada: {output_path}")
        return None

    return output_path

def create_color_mask(img_hsv, lower_bound, upper_bound):
    mask = cv2.inRange(img_hsv, lower_bound, upper_bound)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask

def filter_color(img, color_masks):
    filtered_images = {}
    for color, mask in color_masks.items():
        filtered_image = cv2.bitwise_and(img, img, mask=mask)
        filtered_images[color] = filtered_image
    return filtered_images

def resize_and_maintain_aspect_ratio(image, size=(128, 72)):
    h, w = image.shape[:2]
    aspect_ratio = w / h

    if aspect_ratio > 16 / 9:
        new_w = size[1] * 16 // 9
        new_h = size[1]
    else:
        new_w = size[0]
        new_h = size[0] * 9 // 16

    resized_image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    delta_w = size[0] - new_w
    delta_h = size[1] - new_h
    top, bottom = delta_h // 2, delta_h - (delta_h // 2)
    left, right = delta_w // 2, delta_w - (delta_w // 2)

    color = [0, 0, 0]
    new_image = cv2.copyMakeBorder(resized_image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return new_image

# Conectar ao servidor SocketIO
sio.connect(SERVER_URL)

# Criar e iniciar threads
capture_thread = threading.Thread(target=capture_frames, args=(frame_queue,))
send_thread = threading.Thread(target=send_frames, args=(frame_queue,))
process_thread = threading.Thread(target=process_frames, args=(frame_queue,))

capture_thread.start()
send_thread.start()
process_thread.start()

# Aguarde o término das threads
capture_thread.join()
send_thread.join()
process_thread.join()
