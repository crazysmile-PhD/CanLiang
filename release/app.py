from flask import Flask

import config
from routes import register_routes

app = Flask(__name__, static_folder='static')
register_routes(app)

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=config.web_port, use_reloader=False)
