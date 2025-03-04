from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField, TextAreaField, FloatField, IntegerField, SelectField, HiddenField, SelectMultipleField
from wtforms.validators import DataRequired, Optional, Email, EqualTo, Length, NumberRange, Regexp, ValidationError
import re

def validate_username(form, field):
    """
    Valida que el nombre de usuario contenga solo letras, números y guiones bajos.

    Args:
        form: El formulario que contiene el campo.
        field: El campo a validar.

    Raises:
        ValidationError: Si el nombre de usuario no cumple con el formato requerido.
    """
    if not re.match(r'^[A-Za-z0-9_]+$', field.data):
        raise ValidationError('El nombre de usuario solo puede contener letras, números y guiones bajos.')

def validate_email(form, field):
    """
    Valida que la dirección de correo electrónico tenga un formato válido.

    Args:
        form: El formulario que contiene el campo.
        field: El campo a validar.

    Raises:
        ValidationError: Si la dirección de correo electrónico no tiene un formato válido.
    """
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", field.data):
        raise ValidationError('Por favor, introduce una dirección de correo electrónico válida.')

class LoginForm(FlaskForm):
    """
    Formulario para el inicio de sesión de usuarios.
    """
    username = StringField('Usuario', validators=[DataRequired(message='El nombre de usuario es obligatorio.')])
    password = PasswordField('Contraseña', validators=[DataRequired(message='La contraseña es obligatoria.')])
    submit = SubmitField('Iniciar Sesión')

class CheckoutForm(FlaskForm):
    """
    Formulario para el proceso de pago (checkout).
    """
    name = StringField('Nombre completo', validators=[DataRequired()], default="Juan Pérez")
    email = StringField('Email', validators=[DataRequired(), Email()], default="juan.perez@example.com")
    address = StringField('Dirección de envío', validators=[DataRequired()], default="Calle Principal 123, Ciudad")
    card_number = StringField('Número de tarjeta', validators=[DataRequired(), Length(min=16, max=16)], default="4111111111111111")
    expiration_date = StringField('Fecha de expiración (MM/YY)', validators=[DataRequired(), Length(min=5, max=5)], default="12/25")
    cvv = StringField('CVV', validators=[DataRequired(), Length(min=3, max=4)], default="123")
    submit = SubmitField('Realizar compra')

class RegistrationForm(FlaskForm):
    """
    Formulario para el registro de nuevos usuarios.
    """
    username = StringField('Usuario', validators=[
        DataRequired(message='El nombre de usuario es obligatorio.'),
        Length(min=3, max=64, message='El nombre de usuario debe tener entre 3 y 64 caracteres.'),
        validate_username
    ])
    email = EmailField('Email', validators=[
        DataRequired(message='El correo electrónico es obligatorio.'),
        Email(message='Por favor, introduce una dirección de correo electrónico válida.'),
        validate_email
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es obligatoria.'),
        Length(min=6, message='La contraseña debe tener al menos 6 caracteres.')
    ])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(message='Por favor, confirma tu contraseña.'),
        EqualTo('password', message='Las contraseñas deben coincidir.')
    ])
    submit = SubmitField('Registrarse')

class ProductForm(FlaskForm):
    """
    Formulario para la creación y edición de productos.
    """

    name = StringField('Nombre', validators=[DataRequired()])
    description = TextAreaField('Descripción')
    price = FloatField('Precio', validators=[DataRequired(), NumberRange(min=0)])
    stock = IntegerField('Stock', validators=[DataRequired(), NumberRange(min=0)])
    min_stock = IntegerField('Stock Mínimo', validators=[DataRequired(), NumberRange(min=0)])
    location = StringField('Ubicación')
    reference_number = StringField('Número de Referencia', validators=[DataRequired()])
    color = StringField('Color')
    weight = FloatField('Peso', validators=[Optional(), NumberRange(min=0)])
    dimensions = StringField('Dimensiones')
    category_id = SelectField('Categoría', coerce=int, validators=[DataRequired()])
    manufacturer = StringField('Fabricante', validators=[DataRequired()])
    supplier = SelectField('Proveedor', validators=[DataRequired()])

    # Campos para nuevo proveedor
    new_supplier_company_name = StringField('Nombre de la Empresa')
    new_supplier_contact_name = StringField('Nombre de Contacto')
    new_supplier_phone = StringField('Teléfono')
    new_supplier_email = EmailField('Email', validators=[Optional(), Email()])
    new_supplier_address = StringField('Dirección')
    new_supplier_city = StringField('Ciudad')
    new_supplier_country = StringField('País')
    new_supplier_postal_code = StringField('Código Postal')
    new_supplier_cif = StringField('CIF')
    new_supplier_discount = FloatField('Descuento (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    new_supplier_iva = FloatField('IVA (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    new_supplier_payment_method = StringField('Método de Pago')
    new_supplier_bank_account = StringField('Cuenta Bancaria')
    new_supplier_notes = TextAreaField('Notas')

    submit = SubmitField('Guardar Producto')

class SupplierForm(FlaskForm):
    """
    Formulario para la creación y edición de proveedores.
    """
    company_name = StringField('Nombre de la Empresa', validators=[DataRequired(), Length(min=3)])
    contact_name = StringField('Nombre de Contacto', validators=[DataRequired()])
    phone = StringField('Teléfono', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    address = StringField('Dirección', validators=[DataRequired()])
    city = StringField('Ciudad', validators=[DataRequired()])
    country = StringField('País', validators=[DataRequired()])
    postal_code = StringField('Código Postal', validators=[DataRequired()])
    cif = StringField('CIF', validators=[DataRequired()])
    discount = FloatField('Descuento (%)', validators=[NumberRange(min=0, max=100)])
    iva = FloatField('IVA (%)', validators=[NumberRange(min=0, max=100)])
    payment_method = StringField('Método de Pago')
    bank_account = StringField('Cuenta Bancaria')
    notes = TextAreaField('Notas')
    submit = SubmitField('Guardar Proveedor')

class AddToCartForm(FlaskForm):
    """
    Formulario para añadir productos al carrito de compras.
    """
    quantity = IntegerField('Cantidad', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Añadir al Carrito')

class DeleteForm(FlaskForm):
    """
    Formulario simple para confirmar la eliminación de elementos.
    """
    submit = SubmitField('Eliminar')

class RemoveFromCartForm(FlaskForm):
    """
    Formulario simple para eliminar productos del carrito de compras.
    """
    submit = SubmitField('Remove')