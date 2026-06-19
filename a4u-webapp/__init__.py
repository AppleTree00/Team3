import os
from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge, HTTPException

from .models import db

def create_app(config_class='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app)
    db.init_app(app)

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    from .main_routes import main_bp
    app.register_blueprint(main_bp)

    from .admin_routes import admin_bp
    app.register_blueprint(admin_bp)

    # ── 오류 핸들러 ───────────────────────────────────────────────────────
    @app.errorhandler(413)
    @app.errorhandler(RequestEntityTooLarge)
    def handle_too_large(e):
        return jsonify(success=False, message=f'파일 크기는 {app.config["MAX_CONTENT_LENGTH"] / 1024 / 1024:.0f}MB를 초과할 수 없습니다.'), 413

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return e
        print(f"An error occurred: {e}")
        return jsonify(success=False, message='알 수 없는 오류가 발생했습니다.'), 500

    return app