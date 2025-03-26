INSTRUCCIONES PARA EL SISTEMA DE GESTIÓN DE INVENTARIO
======================================================

Descripción General
Este proyecto es un sistema completo de gestión de inventario desarrollado con Flask, que incluye autenticación de usuarios, gestión de productos y proveedores, carrito de compras, dashboard administrativo y cliente, y generación de reportes estadísticos.

Requisitos
Python 3.6 o superior

Bibliotecas requeridas (instaladas automáticamente mediante requirements.txt):

Flask

Flask-SQLAlchemy

Flask-Migrate

Flask-Login

Flask-WTF

Flask-Mail

Werkzeug

WTForms

alembic

blinker

Estructura de Archivos Principales
main.py: Punto de entrada principal de la aplicación Flask.

models.py: Define todos los modelos de la base de datos.

routes.py: Contiene todas las rutas y lógica de la aplicación.

forms.py: Define los formularios utilizados en la aplicación.

extensions.py: Inicializa las extensiones de Flask.

error_handlers.py: Maneja los errores de la aplicación.

populate_db.py: Script para poblar la base de datos con datos de prueba.

charts.js: Contiene la lógica para generar gráficos en el frontend.

requirements.txt: Lista de dependencias necesarias.

templates/: Directorio con todas las plantillas HTML.

Instrucciones de Ejecución
Preparación:

Instala las dependencias: pip install -r requirements.txt

Crea la base de datos ejecutando: python main.py (se creará automáticamente)

Población de datos inicial (opcional):

Para cargar datos de prueba ejecuta: python populate_db.py

Esto creará:

1 usuario administrador (admin/admin123)

10 usuarios normales (user0-user9/password0-password9)

8 categorías de productos

10 proveedores

100 productos

Ventas y compras de ejemplo

Ejecución:

Inicia la aplicación: python main.py

La aplicación estará disponible en: http://localhost:5000

Acceso:

Como administrador: usuario "admin", contraseña "admin123"

Como cliente: usuarios "user0" a "user9", contraseñas "password0" a "password9"

Descripción de los Archivos Principales
main.py
Crea y configura la aplicación Flask.

Configura la base de datos (SQLite por defecto).

Inicializa extensiones (SQLAlchemy, LoginManager, CSRFProtect, Mail).

Configura el sistema de logging.

Registra blueprints y manejadores de errores.

Crea las tablas de la base de datos.

models.py
Define todos los modelos de la base de datos:

User: Usuarios del sistema (admin/clientes)

Category: Categorías de productos

Product: Productos del inventario (con soft delete)

Supplier: Proveedores (con soft delete)

Sale y SaleItem: Ventas y sus items

Purchase y PurchaseItem: Compras a proveedores

CartItem: Productos en el carrito de compras

routes.py
Contiene toda la lógica de la aplicación organizada en blueprints:

Rutas de autenticación (login, logout, registro)

Dashboard (admin y cliente)

Gestión de productos (listar, añadir, editar, eliminar)

Gestión de proveedores (listar, añadir, editar, eliminar)

Carrito de compras y checkout

API para operaciones AJAX

Reportes estadísticos

forms.py
Define los formularios utilizados:

LoginForm: Para inicio de sesión

RegistrationForm: Para registro de usuarios

ProductForm: Para gestión de productos

SupplierForm: Para gestión de proveedores

AddToCartForm: Para añadir productos al carrito

CheckoutForm: Para finalizar compras

extensions.py
Inicializa las extensiones de Flask:

SQLAlchemy (para la base de datos)

Migrate (para migraciones)

LoginManager (para autenticación)

CSRFProtect (para protección CSRF)

Mail (para envío de emails)

error_handlers.py
Maneja los errores de la aplicación:

Error 403 (Acceso prohibido)

Error 404 (Página no encontrada)

Error 500 (Error interno del servidor)

Excepciones no manejadas

populate_db.py
Script para poblar la base de datos con datos de prueba realistas:

Usuarios, categorías, proveedores y productos

Ventas y compras de ejemplo

Productos con bajo stock

Características Principales
Autenticación y Autorización:

Login/logout para usuarios

Dos roles: administrador y cliente

Protección de rutas según roles

Gestión de Productos:

CRUD completo de productos

Soft delete (borrado lógico)

Búsqueda y filtrado

Control de stock y alertas de bajo stock

Gestión de Proveedores:

CRUD completo de proveedores

Soft delete (borrado lógico)

Relación muchos-a-muchos con productos

Carrito de Compras:

Añadir/eliminar productos

Actualizar cantidades

Proceso de checkout

Dashboard:

Para administradores: gráficos de ventas, compras y beneficios

Para clientes: historial de compras y productos recomendados

Reportes Estadísticos:

Ventas por categoría

Productos más vendidos

Proveedores más activos

Valor total del inventario

API:

Endpoints para operaciones AJAX

Actualización dinámica de datos

Gráficos interactivos

Posibles Problemas y Soluciones
Error al iniciar la aplicación:

Verifica que todas las dependencias estén instaladas (pip install -r requirements.txt)

Asegúrate de tener permisos de escritura en el directorio

Problemas con la base de datos:

Elimina el archivo suministros.db y vuelve a iniciar la aplicación

Ejecuta python populate_db.py para recrear los datos de prueba

Errores de importación:

Verifica que todos los archivos estén en el mismo directorio

No cambies los nombres de los archivos

Problemas con el correo electrónico:

Configura correctamente las variables MAIL_* en main.py

La configuración por defecto es para pruebas locales

Notas Adicionales
La aplicación usa SQLite por defecto para facilitar las pruebas. Para producción, considera usar PostgreSQL o MySQL.

El modo debug está activado por defecto. Desactívalo para producción.

Las credenciales de administrador son admin/admin123 (cámbialas en producción).

Los gráficos se generan con Chart.js en el frontend.
