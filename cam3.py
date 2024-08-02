import cv2
import base64
import time
import socketio
import numpy as np
import os

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

def save_image(frame, save_dir, counter):
    image_path = os.path.join(save_dir, '{}.png'.format(counter))
    cv2.imwrite(image_path, frame)
    return image_path

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

    if aspect_ratio > 16/9:
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

def resize_and_process_image(image_path, output_dir, counter, size=(128, 72)):
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)

    if img is None:
        print(f"Erro ao ler a imagem: {image_path}")
        return

    img_blur = cv2.GaussianBlur(img, (5, 5), 0)
    img_hsv = cv2.cvtColor(img_blur, cv2.COLOR_BGR2HSV)

    # Define the color ranges
    color_ranges = {
        'red1': (np.array([0, 100, 100]), np.array([10, 255, 255])),
        'red2': (np.array([160, 100, 100]), np.array([180, 255, 255])),
        'light_blue': (np.array([85, 100, 100]), np.array([110, 255, 255])),  # Adjusted for light blue
        'white': (np.array([0, 0, 200]), np.array([180, 30, 255]))
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
    
    output_path = os.path.join(output_dir, '{}.png'.format(counter))
    cv2.imwrite(output_path, resized_image, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    return output_path

def main():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Erro: Não foi possível abrir a câmera.")
        return

    print("Câmera conectada com sucesso.")
    
    save_dir = 'testing_dataset'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    counter = 0
    flash_frames = 0
    flash_color = (255, 255, 255)

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

            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '):
                image_path = save_image(frame, save_dir, counter)
                resize_and_process_image(image_path, save_dir, counter, size=(128, 72))
                counter += 1
                flash_frames = 5
                flash_color = (0, 255, 0)

            if flash_frames > 0:
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), flash_color, -1)
                alpha = 0.5
                frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
                flash_frames -= 1

            cv2.imshow('CAM', frame)

            if key == ord('q'):
                break

    except KeyboardInterrupt:
        print("Interrompido pelo usuário")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        sio.disconnect()

if __name__ == "__main__":
    main()
