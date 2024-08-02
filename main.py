# import cv2
# import os
# import time

# def main():
#     # Captura de vídeo da câmera padrão (0)
#     cap = cv2.VideoCapture(0)

#     if not cap.isOpened():
#         print("Erro: Não foi possível abrir a câmera.")
#         return

#     # Cria uma pasta para salvar as fotos
#     save_dir = 'captured_images'
#     if not os.path.exists(save_dir):
#         os.makedirs(save_dir)

#     # Configura o intervalo de tempo (em segundos) para tirar fotos
#     interval = 5  # 5 segundos
#     last_captured_time = time.time()
#     counter = 0

#     try:
#         while True:
#             # Captura frame a frame
#             ret, frame = cap.read()

#             if not ret:
#                 print("Erro: Não foi possível capturar o frame.")
#                 break

#             # Exibe o frame resultante
#             cv2.imshow('Câmera', frame)

#             # Verifica se o intervalo de tempo passou para capturar uma nova imagem
#             current_time = time.time()
#             if current_time - last_captured_time >= interval:
#                 image_path = os.path.join(save_dir, f'foto_{counter}.png')
#                 cv2.imwrite(image_path, frame)
#                 counter += 1
#                 last_captured_time = current_time

#             # Pressione 'q' no teclado para sair do loop
#             if cv2.waitKey(1) & 0xFF == ord('q'):
#                 break
#     except KeyboardInterrupt:
#         print("Interrompido pelo usuário")

#     # Libera a captura de vídeo
#     cap.release()
#     cv2.destroyAllWindows()

# if __name__ == "__main__":
#     main()
