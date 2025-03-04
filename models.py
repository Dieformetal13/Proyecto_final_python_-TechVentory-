from extensions import db
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import desc

# Tabla de asociación para la relación muchos a muchos entre Product y Supplier
supplier_product = db.Table('supplier_product',
    db.Column('supplier_id', db.Integer, db.ForeignKey('supplier.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True)
)

class SoftDeleteMixin:
    """
    Mixin para implementar borrado lógico en los modelos.
    """
    is_deleted = db.Column(db.Boolean, default=False)

    @classmethod
    def get_active(cls):
        """
        Devuelve una consulta para obtener solo los registros activos (no borrados).
        """
        return cls.query.filter_by(is_deleted=False)

class User(UserMixin, db.Model):
    """
    Modelo para representar a los usuarios del sistema.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    sales = db.relationship('Sale', back_populates='user', lazy='dynamic')

    def set_password(self, password):
        """
        Establece la contraseña del usuario, almacenándola como hash.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Verifica si la contraseña proporcionada coincide con el hash almacenado.
        """
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    """
    Modelo para representar las categorías de productos.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    products = db.relationship('Product', back_populates='category', lazy='dynamic')

class Product(SoftDeleteMixin, db.Model):
    """
    Modelo para representar los productos en el inventario.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    min_stock = db.Column(db.Integer, nullable=False, default=10)
    location = db.Column(db.String(100), nullable=True)
    reference_number = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(50), nullable=True)
    weight = db.Column(db.Float, nullable=True)
    dimensions = db.Column(db.String(100), nullable=True)
    manufacturer = db.Column(db.String(100), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', back_populates='products')
    suppliers = db.relationship('Supplier', secondary=supplier_product, back_populates='products',
                                primaryjoin="and_(Product.id==supplier_product.c.product_id, Supplier.is_deleted==False)")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sale_items = db.relationship('SaleItem', back_populates='product', cascade="all, delete-orphan")
    purchase_items = db.relationship('PurchaseItem', back_populates='product', cascade="all, delete-orphan")
    cart_items = db.relationship('CartItem', back_populates='product', cascade="all, delete-orphan")

    @hybrid_property
    def is_low_stock(self):
        """
        Propiedad híbrida que indica si el producto tiene stock bajo.
        """
        return self.stock <= self.min_stock

    @is_low_stock.expression
    def is_low_stock(cls):
        """
        Expresión SQL para la propiedad is_low_stock.
        """
        return cls.stock <= cls.min_stock

    @property
    def formatted_price(self):
        """
        Devuelve el precio formateado como una cadena con el símbolo de euro.
        """
        return f"€{self.price:.2f}"

    @property
    def formatted_weight(self):
        """
        Devuelve el peso formateado como una cadena con la unidad de medida.
        """
        return f"{self.weight:.2f} kg" if self.weight else "N/A"

    @property
    def stock_status(self):
        """
        Devuelve el estado del stock ('low' o 'normal').
        """
        if self.stock <= self.min_stock * 0.9:
            return 'low'
        return 'normal'

    def soft_delete(self):
        """
        Realiza un borrado lógico del producto y actualiza las relaciones necesarias.
        """
        self.is_deleted = True
        for cart_item in self.cart_items:
            db.session.delete(cart_item)
        for supplier in list(self.suppliers):  # Crear una copia de la lista
            if self in supplier.products:  # Verificar si el producto está en la lista del proveedor
                supplier.products.remove(self)
        db.session.commit()

class Supplier(SoftDeleteMixin, db.Model):
    """
    Modelo para representar a los proveedores.
    """
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    contact_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    cif = db.Column(db.String(20), unique=True, nullable=False)
    discount = db.Column(db.Float, nullable=True)
    iva = db.Column(db.Float, nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)
    bank_account = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    products = db.relationship('Product', secondary=supplier_product, back_populates='suppliers',
                               primaryjoin="and_(Supplier.id==supplier_product.c.supplier_id, Product.is_deleted==False)")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sales = db.relationship('Sale', back_populates='supplier')
    sale_items = db.relationship('SaleItem', back_populates='supplier')

    @property
    def formatted_discount(self):
        """
        Devuelve el descuento formateado como una cadena con el símbolo de porcentaje.
        """
        return f"{self.discount:.2f}%" if self.discount is not None else "N/A"

    @property
    def formatted_iva(self):
        """
        Devuelve el IVA formateado como una cadena con el símbolo de porcentaje.
        """
        return f"{self.iva:.2f}%" if self.iva is not None else "N/A"

    def soft_delete(self):
        """
        Realiza un borrado lógico del proveedor y actualiza las relaciones necesarias.
        """
        self.is_deleted = True
        for product in list(self.products):  # Crear una copia de la lista
            if self in product.suppliers:  # Verificar si el proveedor está en la lista del producto
                product.suppliers.remove(self)
        db.session.commit()

class Sale(db.Model):
    """
    Modelo para representar las ventas.
    """
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=True)
    user = db.relationship('User', back_populates='sales')
    supplier = db.relationship('Supplier', back_populates='sales')
    items = db.relationship('SaleItem', back_populates='sale', lazy=True, cascade="all, delete-orphan")
    shipping_address = db.Column(db.String(200), nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)

    @property
    def formatted_total(self):
        """
        Devuelve el total formateado como una cadena con el símbolo de euro.
        """
        return f"€{self.total:.2f}"

    @classmethod
    def limit_user_sales(cls, user_id):
        """
        Limita el número de ventas almacenadas por usuario a 50.
        """
        sales = cls.query.filter_by(user_id=user_id).order_by(desc(cls.date)).all()
        if len(sales) > 50:
            sales_to_delete = sales[50:]
            for sale in sales_to_delete:
                db.session.delete(sale)
            db.session.commit()

class SaleItem(db.Model):
    """
    Modelo para representar los items individuales en una venta.
    """
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    sale = db.relationship('Sale', back_populates='items')
    product = db.relationship('Product', back_populates='sale_items')
    supplier = db.relationship('Supplier', back_populates='sale_items')

    @property
    def subtotal(self):
        """
        Calcula el subtotal del item de venta.
        """
        return self.price * self.quantity

    @property
    def formatted_subtotal(self):
        """
        Devuelve el subtotal formateado como una cadena con el símbolo de euro.
        """
        return f"€{self.subtotal:.2f}"

class Purchase(db.Model):
    """
    Modelo para representar las compras a proveedores.
    """
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)
    items = db.relationship('PurchaseItem', back_populates='purchase', cascade='all, delete-orphan')

    supplier = db.relationship('Supplier', backref=db.backref('purchases', lazy=True))

    @property
    def formatted_total(self):
        """
        Devuelve el total formateado como una cadena con el símbolo de euro.
        """
        return f"€{self.total:.2f}"

class PurchaseItem(db.Model):
    """
    Modelo para representar los items individuales en una compra.
    """
    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchase.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    purchase = db.relationship('Purchase', back_populates='items')
    product = db.relationship('Product', back_populates='purchase_items')

    @property
    def subtotal(self):
        """
        Calcula el subtotal del item de compra.
        """
        return self.price * self.quantity

    @property
    def formatted_subtotal(self):
        """
        Devuelve el subtotal formateado como una cadena con el símbolo de euro.
        """
        return f"€{self.subtotal:.2f}"

class CartItem(db.Model):
    """
    Modelo para representar los items en el carrito de compras de un usuario.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    user = db.relationship('User', backref=db.backref('cart_items', lazy=True))
    product = db.relationship('Product', back_populates='cart_items')

    @property
    def subtotal(self):
        """
        Calcula el subtotal del item en el carrito.
        """
        return self.product.price * self.quantity

    @property
    def formatted_subtotal(self):
        """
        Devuelve el subtotal formateado como una cadena con el símbolo de euro.
        """
        return f"€{self.subtotal:.2f}"