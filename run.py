import sys
import os

# Adicione o caminho do diretório pai
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flaskr import create_app, socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
