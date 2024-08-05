from flask import Blueprint, request, jsonify
from flask_socketio import emit
import base64
import numpy as np
import cv2
from . import socketio
import tensorflow as tf

# Carrega o modelo pré-treinado
model = tf.keras.models.load_model("flaskr/model5.keras")

bp = Blueprint('json', __name__, url_prefix='/json')

maybeResults = ["bad_blue", "bad_red", "good_blue", "good_red"]

@bp.route('/process', methods=['POST'])
def process_images():
    print("chegou")
    data = request.get_json()
    nImages = len(data['images'])
    wordResults = []

    for img_path in data['images']:
        img = img_path
        img_data = np.array([tf.keras.utils.load_img(img)])
        # Realiza a predição usando o modelo carregado
        wordResults.append(model.predict(img_data))

    results = ""
    for i in range(nImages):
        results += maybeResults[np.argmax(wordResults[i][0])]

    print(results)
    
    # Envia o comando ao Arduino
    if "good_blue" in results:
        print('A')  # Comando para "good_blue"
    elif "bad_blue" in results:
        print('B')  # Comando para "bad_blue"
    elif "good_red" in results:
        print('C')  # Comando para "good_red"
    elif "bad_red" in results:
        print('D')  # Comando para "bad_red"
    
    return jsonify(results)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('video_frame')
def handle_video_frame(frame_base64):
    frame_bytes = base64.b64decode(frame_base64)
    np_arr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    # Se necessário, processe o frame aqui

    _, buffer = cv2.imencode('.jpg', frame)
    frame_base64 = base64.b64encode(buffer).decode('utf-8')

    # Retransmite o frame para os clientes conectados
    socketio.emit('video_feed', frame_base64)
