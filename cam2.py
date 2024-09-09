import cv2
import numpy as np
import os
import time
import requests
import serial

# Set up serial communication with Arduino
ser = serial.Serial('/dev/cu.usbserial-14330', 9600)
time.sleep(2)  # Wait for the serial connection to initialize

def send_command(command):
    ser.write(command.encode())

def save_image(frame, save_dir, counter):
    image_path = os.path.join(save_dir, '0.png')
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
        'light_blue': (np.array([85, 100, 100]), np.array([110, 255, 255]))  # Adjusted for light blue
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
    return output_path

def send_image_to_server(image_path):
    url = 'http://127.0.0.1:5000/json/'  # Update with your server address
    with open(image_path, 'rb') as image_file:
        files = {'image': image_file}
        response = requests.post(url, files=files)
    
    if response.status_code == 200:
        print(f"Server response: {response.json()}")
        return response.json()
    else:
        print(f"Failed to get response from server. Status code: {response.status_code}")
        return None

def main():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Erro: Não foi possível abrir a câmera.")
        return

    save_dir = 'captured_images/prediction_test'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    counter = 0
    flash_frames = 0
    flash_color = (255, 255, 255)
    red_detected = False
    white_detected = False
    light_blue_detected = False
    color_last_detected = False

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                print("Erro: Não foi possível capturar o frame.")
                break

            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '):
                image_path = save_image(frame, save_dir, counter)
                processed_image_path = resize_and_process_image(image_path, save_dir, counter)
                server_response = send_image_to_server(processed_image_path)
                if server_response:
                    # Map server response to Arduino commands
                    if "good_blue" in server_response:
                        send_command('A')  # Command for "good_blue"
                    elif "bad_blue" in server_response:
                        send_command('B')  # Command for "bad_blue"
                    elif "good_red" in server_response:
                        send_command('C')  # Command for "good_red"
                    elif "bad_red" in server_response:
                        send_command('D')  # Command for "bad_red"
                counter += 1
                flash_frames = 5
                flash_color = (0, 255, 0)

            img_blur = cv2.GaussianBlur(frame, (5, 5), 0)
            img_hsv = cv2.cvtColor(img_blur, cv2.COLOR_BGR2HSV)
            
            # Create masks for each color
            mask_red1 = create_color_mask(img_hsv, np.array([0, 100, 100]), np.array([10, 255, 255]))
            mask_red2 = create_color_mask(img_hsv, np.array([160, 100, 100]), np.array([180, 255, 255]))
            mask_red = mask_red1 + mask_red2
            mask_light_blue = create_color_mask(img_hsv, np.array([85, 100, 100]), np.array([110, 255, 255]))

            # Calculate the presence of each color
            red_pixels = np.sum(mask_red > 0)
            light_blue_pixels = np.sum(mask_light_blue > 0)

            red_detected = red_pixels > 10000
            light_blue_detected = light_blue_pixels > 10000

            # Combine the detections
            color_detected = red_detected or light_blue_detected

            if color_detected and not color_last_detected:
                for i in range(3, 0, -1):
                    countdown_frame = frame.copy()
                    cv2.putText(countdown_frame, f'Tirando foto em {i}s', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1,
                                (0, 255, 0), 2, cv2.LINE_AA)
                    cv2.imshow('CAM', countdown_frame)
                    cv2.waitKey(500)

                ret, frame = cap.read()
                if ret:
                    image_path = save_image(frame, save_dir, counter)
                    processed_image_path = resize_and_process_image(image_path, save_dir, counter)
                    server_response = send_image_to_server(processed_image_path)
                    if server_response:
                        # Map server response to Arduino commands
                        if "good_blue" in server_response:
                            send_command('A')  # Command for "good_blue"
                        elif "bad_blue" in server_response:
                            send_command('B')  # Command for "bad_blue"
                        elif "good_red" in server_response:
                            send_command('C') 
                        elif "bad_red" in server_response:
                            send_command('D')  # Command for "bad_red"
                    counter += 1
                    flash_frames = 5
                    flash_color = (0, 255, 0)

            color_last_detected = color_detected

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
        ser.close()  # Close the serial port

if __name__ == "__main__":
    main()
