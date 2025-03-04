from flask import render_template
from werkzeug.exceptions import HTTPException

def init_error_handlers(app):
    """
    Inicializa los manejadores de errores para la aplicación Flask.

    Esta función registra manejadores personalizados para diferentes códigos de error HTTP,
    asegurando que se muestren páginas de error apropiadas al usuario.

    Args:
        app (Flask): La instancia de la aplicación Flask.
    """
    @app.errorhandler(403)
    def forbidden_error(error):
        """
        Maneja errores 403 (Acceso Prohibido).

        Args:
            error: El objeto de error capturado.

        Returns:
            tuple: Un tuple conteniendo la plantilla renderizada y el código de estado 403.
        """
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        """
        Maneja errores 404 (Página No Encontrada).

        Args:
            error: El objeto de error capturado.

        Returns:
            tuple: Un tuple conteniendo la plantilla renderizada y el código de estado 404.
        """
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """
        Maneja errores 500 (Error Interno del Servidor).

        Args:
            error: El objeto de error capturado.

        Returns:
            tuple: Un tuple conteniendo la plantilla renderizada y el código de estado 500.
        """
        return render_template('errors/500.html'), 500

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        """
        Maneja cualquier excepción no capturada.

        Este manejador actúa como un catch-all para cualquier error no manejado específicamente.
        Si es una excepción HTTP, renderiza una plantilla genérica con el código de error correspondiente.
        Para cualquier otra excepción, renderiza la página de error 500.

        Args:
            e: La excepción capturada.

        Returns:
            tuple: Un tuple conteniendo la plantilla renderizada y el código de estado apropiado.
        """
        if isinstance(e, HTTPException):
            return render_template('errors/generic.html', error=e), e.code
        return render_template('errors/500.html'), 500