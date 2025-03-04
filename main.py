from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from extensions import db, migrate, login_manager, csrf, mail
from models import User
from routes import init_routes
from error_handlers import init_error_handlers
import logging
from logging.handlers import RotatingFileHandler
import os

def create_app():
    """
    Crea y configura la aplicación Flask.

    Esta función es el punto de entrada principal para configurar la aplicación Flask.
    Configura la base de datos, el sistema de logging, las extensiones de Flask,
    y registra las rutas y los manejadores de errores.

    Returns:
        Flask: La aplicación Flask configurada.
    """
    # Crear la instancia de la aplicación Flask
    app = Flask(__name__)

    # Configuración básica de la aplicación
    app.config['DEBUG'] = True
    app.config['SECRET_KEY'] = 'una_clave_secreta_muy_segura'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///suministros.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['ITEMS_PER_PAGE'] = 10

    # Configuración de Flask-Mail
    # Nota: Estos valores deben ser reemplazados con la configuración real del servidor SMTP
    app.config['MAIL_SERVER'] = 'smtp.example.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'your-email@example.com'
    app.config['MAIL_PASSWORD'] = 'your-password'

    # Configuración del sistema de logging
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Aplicación iniciada')

    # Inicialización de extensiones con la aplicación
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    csrf.init_app(app)
    mail.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        """
        Carga un usuario desde la base de datos.

        Esta función es utilizada por Flask-Login para cargar el usuario actual.

        Args:
            user_id (int): El ID del usuario a cargar.

        Returns:
            User: El objeto User correspondiente al user_id, o None si no se encuentra.
        """
        return db.session.get(User, int(user_id))

    @app.before_request
    def before_request():
        """
        Se ejecuta antes de cada solicitud.

        Verifica si la solicitud es una solicitud AJAX y establece una bandera en consecuencia.
        """
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            request.wants_json = True

    @app.after_request
    def after_request(response):
        """
        Se ejecuta después de cada solicitud.

        Establece el tipo de contenido de la respuesta a JSON para solicitudes AJAX.

        Args:
            response (Response): El objeto de respuesta Flask.

        Returns:
            Response: El objeto de respuesta modificado.
        """
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            response.headers['Content-Type'] = 'application/json'
        return response

    # Inicializar rutas, manejadores de errores y crear tablas de la base de datos
    with app.app_context():
        init_routes(app)
        init_error_handlers(app)
        db.create_all()

    return app

if __name__ == '__main__':
    # Crear y ejecutar la aplicación si este script se ejecuta directamente
    app = create_app()
    app.run(debug=True)