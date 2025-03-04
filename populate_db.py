from main import create_app
from extensions import db
from models import User, Product, Supplier, Sale, Purchase, Category, SaleItem, PurchaseItem
from datetime import datetime, timedelta, UTC
import random
from werkzeug.security import generate_password_hash

def create_realistic_suppliers():
    """
    Crea una lista de proveedores realistas con datos aleatorios.
    """
    suppliers = [
        {"name": "TechnoGlobal Solutions", "contact": "María García"},
        {"name": "InnovaSoft Systems", "contact": "Carlos Rodríguez"},
        {"name": "DataCore Enterprises", "contact": "Ana Martínez"},
        {"name": "NetWave Communications", "contact": "Javier López"},
        {"name": "CyberTech Industries", "contact": "Laura Sánchez"},
        {"name": "SmartByte Solutions", "contact": "Diego Fernández"},
        {"name": "QuantumLink Technologies", "contact": "Elena Gómez"},
        {"name": "FusionTech Innovations", "contact": "Pablo Ruiz"},
        {"name": "NexGen Systems", "contact": "Isabel Torres"},
        {"name": "AlphaByte Corporation", "contact": "Andrés Navarro"}
    ]

    for supplier_data in suppliers:
        supplier = Supplier(
            company_name=supplier_data["name"],
            contact_name=supplier_data["contact"],
            email=f"contact@{supplier_data['name'].lower().replace(' ', '')}.com",
            phone="+" + ''.join([str(random.randint(0, 9)) for _ in range(10)]),
            address=f"Calle {random.randint(1, 100)}, {random.choice(['Madrid', 'Barcelona', 'Valencia', 'Sevilla'])}",
            city=random.choice(['Madrid', 'Barcelona', 'Valencia', 'Sevilla']),
            country="España",
            postal_code=str(random.randint(10000, 99999)),
            cif='B' + ''.join([str(random.randint(0, 9)) for _ in range(8)]),
            discount=round(random.uniform(1, 15), 2),
            iva=21.0,
            payment_method=random.choice(
                ["Transferencia bancaria", "Tarjeta de crédito", "PayPal", "Domiciliación bancaria"]),
            bank_account=f"ES{random.randint(10, 99)}{random.randint(1000, 9999)}{random.randint(1000, 9999)}{random.randint(1000, 9999)}{random.randint(1000, 9999)}",
            notes=f"Proveedor especializado en {random.choice(['hardware', 'software', 'periféricos', 'redes', 'componentes'])}"
        )
        db.session.add(supplier)

    db.session.commit()

def generate_product(category):
    """
    Genera datos aleatorios para un producto basado en la categoría proporcionada.

    :param category: Objeto Category al que pertenecerá el producto.
    :return: Diccionario con los datos del producto generado.
    """
    product_types = {
        'Ordenadores': ['Laptop', 'Desktop', 'Tablet', 'All-in-One'],
        'Periféricos': ['Monitor', 'Teclado', 'Ratón', 'Impresora', 'Escáner'],
        'Componentes': ['Tarjeta Gráfica', 'Procesador', 'Memoria RAM', 'Placa Base', 'Fuente de Alimentación'],
        'Accesorios': ['Funda para Laptop', 'Soporte para Monitor', 'Alfombrilla para Ratón', 'Adaptador USB'],
        'Redes': ['Router', 'Switch', 'Punto de Acceso Wi-Fi', 'Cable Ethernet'],
        'Software': ['Sistema Operativo', 'Suite Ofimática', 'Antivirus', 'Diseño Gráfico'],
        'Almacenamiento': ['Disco Duro', 'SSD', 'Memoria USB', 'Tarjeta SD'],
        'Audio y Video': ['Auriculares', 'Altavoces', 'Micrófono', 'Webcam']
    }

    manufacturers = ['TechCorp', 'InnovaSystems', 'ElectroGlobal', 'MegaBytes', 'SmartTech', 'FutureTech',
                     'QuantumComputers', 'CyberSolutions', 'NexGen', 'AlphaTech']

    product_type = random.choice(product_types[category.name])

    return {
        "name": f"{product_type} {random.choice(manufacturers)}",
        "description": f"Producto de alta calidad en la categoría de {category.name.lower()}",
        "price": round(random.uniform(10, 500), 2),
        "stock": random.randint(10, 500),
        "min_stock": random.randint(5, 50),
        "location": f'Almacén {random.choice(["A", "B", "C", "D", "E"])}',
        "reference_number": f'REF{random.randint(10000, 99999)}',
        "category": category,
        "color": random.choice(['Negro', 'Blanco', 'Gris', 'Azul', 'Rojo', 'Plata', 'Oro']),
        "weight": round(random.uniform(0.1, 20), 2),
        "dimensions": f'{random.randint(1, 100)}x{random.randint(1, 100)}x{random.randint(1, 100)} cm',
        "manufacturer": random.choice(manufacturers)
    }

def populate_db():
    """
    Función principal para poblar la base de datos con datos de ejemplo.
    """
    # Limpiar la base de datos
    db.drop_all()
    db.create_all()

    # Crear usuario administrador
    admin = User(username='admin', email='admin@example.com', is_admin=True)
    admin.password_hash = generate_password_hash('admin123')
    db.session.add(admin)

    # Crear usuarios normales
    for i in range(10):
        user = User(username=f'user{i}', email=f'user{i}@example.com', is_admin=False)
        user.password_hash = generate_password_hash(f'password{i}')
        db.session.add(user)

    db.session.commit()
    print("Usuarios creados.")

    # Crear categorías
    categories = ['Ordenadores', 'Periféricos', 'Componentes', 'Accesorios', 'Redes', 'Software', 'Almacenamiento',
                  'Audio y Video']
    category_objects = []
    for category_name in categories:
        category = Category(name=category_name)
        db.session.add(category)
        category_objects.append(category)
    db.session.commit()
    print("Categorías creadas.")

    # Crear proveedores realistas
    create_realistic_suppliers()
    print("Proveedores realistas creados.")

    # Crear 100 productos nuevos
    for _ in range(100):
        category = random.choice(category_objects)
        product_data = generate_product(category)
        new_product = Product(
            name=product_data['name'],
            description=product_data['description'],
            price=product_data['price'],
            stock=product_data['stock'],
            min_stock=product_data['min_stock'],
            location=product_data['location'],
            reference_number=product_data['reference_number'],
            category=product_data['category'],
            color=product_data['color'],
            weight=product_data['weight'],
            dimensions=product_data['dimensions'],
            manufacturer=product_data['manufacturer']
        )
        db.session.add(new_product)
    db.session.commit()
    print("100 productos nuevos creados.")

    # Vincular productos a proveedores
    products = Product.query.all()
    suppliers = Supplier.query.all()
    for product in products:
        supplier = random.choice(suppliers)
        product.suppliers.append(supplier)
    db.session.commit()
    print("Productos vinculados a proveedores.")

    # Modificar algunos productos existentes para tener stock bajo
    low_stock_products = random.sample(products, 20)  # Seleccionar 20 productos al azar
    for product in low_stock_products:
        product.stock = random.randint(0,
                                       int(product.min_stock * 0.9))  # Establecer stock por debajo del 90% del min_stock
    db.session.commit()
    print("20 productos modificados para tener stock bajo.")

    # Crear ventas y compras de ejemplo
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=30)

    users = User.query.filter_by(is_admin=False).all()

    # Crear ventas y elementos de venta
    for _ in range(100):  # Crear 100 ventas aleatorias
        sale_date = start_date + timedelta(seconds=random.randint(0, int((end_date - start_date).total_seconds())))
        user = random.choice(users)
        sale = Sale(date=sale_date, total=0, user_id=user.id)
        db.session.add(sale)
        db.session.flush()

        for _ in range(random.randint(1, 3)):  # 1-3 items por venta
            product = random.choice(products)
            quantity = random.randint(1, 5)
            supplier = random.choice(product.suppliers) if product.suppliers else None
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                supplier_id=supplier.id if supplier else None,
                quantity=quantity,
                price=product.price
            )
            db.session.add(sale_item)
            sale.total += quantity * product.price

            # Actualizar el stock del producto
            product.stock = max(0, product.stock - quantity)

        db.session.add(sale)

    # Crear compras y elementos de compra
    for _ in range(50):  # Crear 50 compras aleatorias
        purchase_date = start_date + timedelta(seconds=random.randint(0, int((end_date - start_date).total_seconds())))
        supplier = random.choice(suppliers)
        purchase = Purchase(date=purchase_date, supplier_id=supplier.id, total=0)
        db.session.add(purchase)
        db.session.flush()

        for _ in range(random.randint(1, 5)):  # 1-5 items por compra
            product = random.choice(products)
            quantity = random.randint(10, 50)
            purchase_item = PurchaseItem(
                purchase_id=purchase.id,
                product_id=product.id,
                quantity=quantity,
                price=product.price * (1 - supplier.discount / 100)
            )
            db.session.add(purchase_item)
            purchase.total += quantity * purchase_item.price

            # Actualizar el stock del producto
            product.stock += quantity

        db.session.add(purchase)

    db.session.commit()
    print("Ventas y compras de ejemplo añadidas a la base de datos.")

    print("Proceso de población de la base de datos completado.")


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        populate_db()
        print("Base de datos poblada con éxito.")