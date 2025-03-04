from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail

# Inicialización de la extensión SQLAlchemy
# Esta extensión proporciona integración ORM (Object-Relational Mapping) para la aplicación Flask
db = SQLAlchemy()

# Inicialización de la extensión Migrate
# Esta extensión facilita la gestión de migraciones de base de datos
migrate = Migrate()

# Inicialización de la extensión LoginManager
# Esta extensión maneja la autenticación de usuarios y las sesiones
login_manager = LoginManager()

# Inicialización de la protección CSRF (Cross-Site Request Forgery)
# Esta extensión proporciona protección contra ataques CSRF
csrf = CSRFProtect()

# Inicialización de la extensión Mail
# Esta extensión facilita el envío de correos electrónicos desde la aplicación Flask
mail = Mail()

# Nota: Estas extensiones se inicializan aquí pero se configuran en la función create_app() en main.py
# Esto permite una mejor modularización y evita problemas de importación circular