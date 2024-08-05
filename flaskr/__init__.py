import os
from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS

socketio = SocketIO()
cors = CORS()

def create_app(test_config=None):
    # Cria e configura o aplicativo
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # Carrega a configuração da instância, se existir, quando não estiver em teste
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Carrega a configuração de teste, se passada
        app.config.from_mapping(test_config)

    # Garante que a pasta de instância exista
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import json
    app.register_blueprint(json.bp)

    # Inicializa o CORS e o SocketIO
    cors.init_app(app, resources={r"/*": {"origins": "*"}})  # Permite qualquer origem
    socketio.init_app(app, cors_allowed_origins="*")  # Permite qualquer origem para o Socket.IO

    return app
