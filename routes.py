from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort, make_response, current_app
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func, or_, desc, extract
from datetime import datetime, timedelta, date
from models import User, Product, Supplier, Sale, Purchase, CartItem, Category, SaleItem, PurchaseItem
from flask_wtf import FlaskForm
from flask_wtf.csrf import generate_csrf
from extensions import db, csrf
from forms import LoginForm, RegistrationForm, ProductForm, SupplierForm, AddToCartForm, DeleteForm, RemoveFromCartForm, CheckoutForm
from sqlalchemy.exc import IntegrityError
import random
import string
import traceback
from werkzeug.security import check_password_hash, generate_password_hash
import re

# Definición de blueprints
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)

# Ruta principal
@main_bp.route('/')
def index():
    """
    Ruta principal que redirige al dashboard si el usuario está autenticado,
    o a la página de login si no lo está.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

# Ruta de login
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Maneja el proceso de inicio de sesión de usuarios.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        form.username.errors.append('Usuario o contraseña inválidos')
    return render_template('login.html', form=form)

# Ruta de logout
@auth_bp.route('/logout')
@login_required
def logout():
    """
    Cierra la sesión del usuario actual.
    """
    logout_user()
    return redirect(url_for('auth.login'))

# Ruta de registro
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Maneja el proceso de registro de nuevos usuarios.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Verificar si el usuario ya existe
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user:
                form.username.errors.append('Este nombre de usuario ya está en uso. Por favor, elige otro.')
                return render_template('register.html', form=form)

            # Verificar si el email ya está registrado
            existing_email = User.query.filter_by(email=form.email.data).first()
            if existing_email:
                form.email.errors.append('Este correo electrónico ya está registrado. Por favor, usa otro.')
                return render_template('register.html', form=form)

            # Crear nuevo usuario
            hashed_password = generate_password_hash(form.password.data)
            new_user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            # Almacenar el mensaje de éxito en la sesión
            flash('Registro exitoso. Por favor, inicia sesión.', 'success')

            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error durante el registro de usuario: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            if current_app.debug:
                return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500
            else:
                flash('Ocurrió un error durante el registro. Por favor, inténtalo de nuevo.', 'error')
                return render_template('register.html', form=form), 500

    return render_template('register.html', form=form)

# Ruta del dashboard
@main_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Muestra el dashboard apropiado según el tipo de usuario (admin o cliente).
    """
    try:
        if current_user.is_admin:
            return admin_dashboard()
        else:
            return client_dashboard()
    except Exception as e:
        current_app.logger.error(f"Error in dashboard route: {str(e)}")
        return render_template('error.html', error_message="Ocurrió un error al cargar el dashboard de administrador. Por favor, inténtalo de nuevo más tarde."), 500

# Función para el dashboard de administrador
def admin_dashboard():
    """
    Genera y muestra el dashboard para usuarios administradores.
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        # Obtener datos de ventas y compras de los últimos 30 días
        sales_data = db.session.query(
            func.date(Sale.date).label('date'),
            func.sum(Sale.total).label('total')
        ).filter(Sale.date.between(start_date, end_date)) \
            .group_by(func.date(Sale.date)).all()

        purchases_data = db.session.query(
            func.date(Purchase.date).label('date'),
            func.sum(Purchase.total).label('total')
        ).filter(Purchase.date.between(start_date, end_date)) \
            .group_by(func.date(Purchase.date)).all()

        # Crear un diccionario con todas las fechas y llenar con datos reales
        all_dates = {(start_date + timedelta(days=x)).strftime('%Y-%m-%d'): {"sales": 0, "purchases": 0} for x in range(31)}

        # Llenar el diccionario con los datos reales
        for sale in sales_data:
            date_str = sale.date.strftime('%Y-%m-%d') if isinstance(sale.date, datetime) else str(sale.date)
            all_dates[date_str]["sales"] = float(sale.total)

        for purchase in purchases_data:
            date_str = purchase.date.strftime('%Y-%m-%d') if isinstance(purchase.date, datetime) else str(purchase.date)
            all_dates[date_str]["purchases"] = float(purchase.total)

        # Calcular beneficios y preparar datos para los gráficos
        dates = []
        sales = []
        purchases = []
        profits = []
        for date_str, data in sorted(all_dates.items()):
            dates.append(date_str)
            sales.append(data["sales"])
            purchases.append(data["purchases"])
            profits.append(data["sales"] - data["purchases"])

        # Obtener productos más vendidos
        top_selling_products = db.session.query(
            Product.id,
            Product.name,
            func.sum(SaleItem.quantity).label('total_quantity')
        ).join(SaleItem).filter(Product.is_deleted == False).group_by(Product.id, Product.name) \
            .order_by(func.sum(SaleItem.quantity).desc()).limit(10).all()

        # Obtener productos más rentables
        most_profitable_products = db.session.query(
            Product.id,
            Product.name,
            func.sum(SaleItem.quantity * SaleItem.price).label('total_sales')
        ).join(SaleItem).filter(Product.is_deleted == False).group_by(Product.id, Product.name) \
            .order_by(func.sum(SaleItem.quantity * SaleItem.price).desc()).limit(10).all()

        return render_template('admin_dashboard.html',
                               dates=dates,
                               sales_data=sales,
                               purchases_data=purchases,
                               profits_data=profits,
                               top_selling_products=top_selling_products,
                               most_profitable_products=most_profitable_products)
    except Exception as e:
        current_app.logger.error(f"Error en admin_dashboard: {str(e)}")
        return render_template('error.html', error_message="Ocurrió un error al cargar el dashboard de administrador. Por favor, inténtalo de nuevo más tarde."), 500

# Función para el dashboard de cliente
def client_dashboard():
    """
    Genera y muestra el dashboard para usuarios clientes.
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        # Obtener compras recientes
        recent_purchases = db.session.query(
            Sale.id.label('sale_id'),
            Product.id.label('product_id'),
            Product.name,
            SaleItem.price,
            SaleItem.quantity,
            Sale.date,
            Sale.total.label('sale_total')
        ).select_from(Sale) \
            .join(SaleItem, Sale.id == SaleItem.sale_id) \
            .join(Product, SaleItem.product_id == Product.id) \
            .filter(Sale.user_id == current_user.id) \
            .order_by(Sale.date.desc()).limit(50).all()

        # Obtener datos de compras del usuario
        user_purchases = db.session.query(
            func.date(Sale.date).label('date'),
            func.sum(SaleItem.quantity * SaleItem.price).label('total')
        ).join(SaleItem).filter(Sale.user_id == current_user.id, Sale.date.between(start_date, end_date)) \
            .group_by(func.date(Sale.date)).order_by(func.date(Sale.date)).all()

        user_purchases_data = [
            {'date': item.date.strftime('%Y-%m-%d') if isinstance(item.date, datetime) else str(item.date),
             'total': float(item.total)} for item in user_purchases]

        # Asegurar que haya datos para todos los días
        all_dates = {(start_date + timedelta(days=x)).strftime('%Y-%m-%d'): 0 for x in range(31)}
        for purchase in user_purchases_data:
            all_dates[purchase['date']] = purchase['total']
        user_purchases_data = [{'date': date, 'total': total} for date, total in all_dates.items()]

        # Top 10 productos comprados por el usuario
        user_top_products = db.session.query(
            Product.id,
            Product.name,
            func.sum(SaleItem.quantity).label('total_quantity'),
            func.sum(SaleItem.quantity * SaleItem.price).label('total_sales')
        ).join(SaleItem, Product.id == SaleItem.product_id) \
            .join(Sale, SaleItem.sale_id == Sale.id) \
            .filter(Sale.user_id == current_user.id, Product.is_deleted == False) \
            .group_by(Product.id, Product.name) \
            .order_by(func.sum(SaleItem.quantity).desc()) \
            .limit(10).all()

        # Top 10 productos más vendidos en general
        top_sold_products = db.session.query(
            Product.id,
            Product.name,
            func.sum(SaleItem.quantity).label('total_quantity')
        ).join(SaleItem, Product.id == SaleItem.product_id) \
            .filter(Product.is_deleted == False) \
            .group_by(Product.id, Product.name) \
            .order_by(func.sum(SaleItem.quantity).desc()) \
            .limit(10).all()

        return render_template('client_dashboard.html',
                               recent_purchases=recent_purchases,
                               user_purchases_data=user_purchases_data,
                               user_top_products=user_top_products,
                               top_sold_products=top_sold_products)
    except Exception as e:
        current_app.logger.error(f"Error en client_dashboard: {str(e)}")
        return render_template('error.html',
                               error_message="Ocurrió un error al cargar el dashboard. Por favor, inténtalo de nuevo más tarde."), 500

# Ruta para refrescar datos del dashboard
@main_bp.route('/api/refresh_dashboard_data')
@login_required
def refresh_dashboard_data():
    """
    API para refrescar los datos del dashboard según el tipo de usuario.
    """
    if current_user.is_admin:
        return refresh_admin_dashboard_data()
    else:
        return refresh_client_dashboard_data()

# Función para refrescar datos del dashboard de administrador
def refresh_admin_dashboard_data():
    """
    Refresca y devuelve los datos actualizados para el dashboard de administrador.
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)

    # Ventas y compras de los últimos 30 días
    sales_data = db.session.query(
        func.date(Sale.date).label('date'),
        func.sum(Sale.total).label('total')
    ).filter(Sale.date.between(start_date, end_date)) \
        .group_by(func.date(Sale.date)).all()

    purchases_data = db.session.query(
        func.date(Purchase.date).label('date'),
        func.sum(Purchase.total).label('total')
    ).filter(Purchase.date.between(start_date, end_date)) \
        .group_by(func.date(Purchase.date)).all()

    # Crear un diccionario con todas las fechas
    all_dates = {(start_date + timedelta(days=x)).strftime('%Y-%m-%d'): {"sales": 0, "purchases": 0} for x in range(31)}

    # Llenar el diccionario con los datos reales
    for sale in sales_data:
        date_str = sale.date.strftime('%Y-%m-%d')
        all_dates[date_str]["sales"] = float(sale.total)

    for purchase in purchases_data:
        date_str = purchase.date.strftime('%Y-%m-%d')
        all_dates[date_str]["purchases"] = float(purchase.total)

    # Calcular beneficios y preparar datos para los gráficos
    chart_data = []
    for date_str, data in sorted(all_dates.items()):
        chart_data.append({
            'date': date_str,
            'sales': data["sales"],
            'purchases': data["purchases"],
            'profit': data["sales"] - data["purchases"]
        })

    # Productos más vendidos
    top_selling_products = db.session.query(
        Product.id,
        Product.name,
        func.sum(SaleItem.quantity).label('total_quantity')
    ).join(SaleItem).group_by(Product.id, Product.name) \
        .order_by(func.sum(SaleItem.quantity).desc()).limit(10).all()

    # Filtrar productos que ya no existen
    top_selling_products = [{'id': p.id, 'name': p.name, 'total_quantity': p.total_quantity}
                            for p in top_selling_products if p.name is not None]

    # Productos más rentables
    most_profitable_products = db.session.query(
        Product.id,
        Product.name,
        func.sum(SaleItem.quantity * SaleItem.price).label('total_sales')
    ).join(SaleItem).group_by(Product.id, Product.name) \
        .order_by(func.sum(SaleItem.quantity * SaleItem.price).desc()).limit(10).all()

    # Filtrar productos que ya no existen
    most_profitable_products = [{'id': p.id, 'name': p.name, 'total_sales': float(p.total_sales)}
                                for p in most_profitable_products if p.name is not None]

    return jsonify({
        'chart_data': chart_data,
        'top_selling_products': top_selling_products,
        'most_profitable_products': most_profitable_products
    })

# Función para refrescar datos del dashboard de cliente
def refresh_client_dashboard_data():
    """
    Refresca y devuelve los datos actualizados para el dashboard de cliente.
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)

    # Obtener compras recientes
    recent_purchases = db.session.query(
        Sale.id.label('sale_id'),
        Product.id.label('product_id'),
        Product.name,
        SaleItem.price,
        SaleItem.quantity,
        Sale.date,
        Sale.total.label('sale_total')
    ).select_from(Sale) \
        .join(SaleItem, Sale.id == SaleItem.sale_id) \
        .join(Product, SaleItem.product_id == Product.id) \
        .filter(Sale.user_id == current_user.id) \
        .order_by(Sale.date.desc()).limit(50).all()

    recent_purchases_data = [{
        'sale_id': purchase.sale_id,
        'product_id': purchase.product_id,
        'name': purchase.name,
        'price': float(purchase.price),
        'quantity': purchase.quantity,
        'date': purchase.date.isoformat(),
        'sale_total': float(purchase.sale_total)
    } for purchase in recent_purchases]

    # Obtener datos de compras del usuario
    user_purchases = db.session.query(
        func.date(Sale.date).label('date'),
        func.sum(SaleItem.quantity * SaleItem.price).label('total')
    ).join(SaleItem).filter(Sale.user_id == current_user.id, Sale.date.between(start_date, end_date)) \
        .group_by(func.date(Sale.date)).order_by(func.date(Sale.date)).all()

    user_purchases_data = [
        {'date': item.date.strftime('%Y-%m-%d'),
         'total': float(item.total)} for item in user_purchases]

    # Asegurarse de que haya datos para todos los días
    all_dates = {(start_date + timedelta(days=x)).strftime('%Y-%m-%d'): 0 for x in range(31)}
    for purchase in user_purchases_data:
        all_dates[purchase['date']] = purchase['total']
    user_purchases_data = [{'date': date, 'total': total} for date, total in all_dates.items()]

    # Top 10 productos comprados por el usuario
    user_top_products = db.session.query(
        Product.id,
        Product.name,
        func.sum(SaleItem.quantity).label('total_quantity'),
        func.sum(SaleItem.quantity * SaleItem.price).label('total_sales')
    ).join(SaleItem, Product.id == SaleItem.product_id) \
        .join(Sale, SaleItem.sale_id == Sale.id) \
        .filter(Sale.user_id == current_user.id) \
        .group_by(Product.id, Product.name) \
        .order_by(func.sum(SaleItem.quantity).desc()) \
        .limit(10).all()

    user_top_products_data = [{
        'id': product.id,
        'name': product.name,
        'total_quantity': product.total_quantity,
        'total_sales': float(product.total_sales)
    } for product in user_top_products]

    # Top 10 productos más vendidos en general
    top_sold_products = db.session.query(
        Product.id,
        Product.name,
        func.sum(SaleItem.quantity).label('total_quantity')
    ).join(SaleItem, Product.id == SaleItem.product_id) \
        .group_by(Product.id, Product.name) \
        .order_by(func.sum(SaleItem.quantity).desc()) \
        .limit(10).all()

    top_sold_products_data = [{
        'id': product.id,
        'name': product.name,
        'total_quantity': product.total_quantity
    } for product in top_sold_products]

    return jsonify({
        'recent_purchases': recent_purchases_data,
        'user_purchases_data': user_purchases_data,
        'user_top_products': user_top_products_data,
        'top_sold_products': top_sold_products_data
    })

# Ruta de estadísticas
@main_bp.route('/statistics')
@login_required
def statistics():
    """
    Muestra estadísticas detalladas del sistema (solo para administradores).
    """
    if not current_user.is_admin:
        current_app.logger.warning(f"Usuario no administrador {current_user.id} intentó acceder a estadísticas")
        abort(403)

    try:
        current_app.logger.info(f"Generando estadísticas para el usuario {current_user.id}")

        # Inicializar variables
        total_products = 0
        total_suppliers = 0
        total_users = 0
        total_inventory_value = 0
        low_stock_products = []
        sales_by_category = []
        top_suppliers = []
        order_history = None

        # Obtener estadísticas generales
        try:
            total_products = Product.query.filter(Product.is_deleted == False).count()
            current_app.logger.debug(f"Total de productos: {total_products}")

            total_suppliers = Supplier.query.filter(Supplier.is_deleted == False).count()
            current_app.logger.debug(f"Total de proveedores: {total_suppliers}")

            total_users = User.query.filter(User.is_admin == False).count()
            current_app.logger.debug(f"Total de usuarios no administrador: {total_users}")
        except Exception as e:
            current_app.logger.error(f"Error al consultar estadísticas generales: {str(e)}")

        # Calcular valor total del inventario
        try:
            total_inventory_value = db.session.query(func.sum(Product.price * Product.stock)).filter(Product.is_deleted == False).scalar() or 0
            current_app.logger.debug(f"Valor total del inventario: {total_inventory_value}")
        except Exception as e:
            current_app.logger.error(f"Error al calcular el valor total del inventario: {str(e)}")

        # Obtener productos con bajo stock
        try:
            low_stock_products = Product.query.filter(Product.stock <= Product.min_stock, Product.is_deleted == False).all()
            low_stock_products = [
                {'id': p.id, 'name': p.name, 'stock': p.stock, 'min_stock': p.min_stock} for p in low_stock_products
            ]
            current_app.logger.debug(f"Número de productos con bajo stock: {len(low_stock_products)}")
        except Exception as e:
            current_app.logger.error(f"Error al consultar productos con bajo stock: {str(e)}")

        # Obtener ventas por categoría (top 10)
        try:
            sales_by_category = db.session.query(
                Category.name,
                func.sum(SaleItem.quantity * SaleItem.price).label('total_sales')
            ).join(Product, SaleItem.product_id == Product.id) \
                .join(Category, Product.category_id == Category.id) \
                .filter(Product.is_deleted == False) \
                .group_by(Category.name) \
                .order_by(func.sum(SaleItem.quantity * SaleItem.price).desc()) \
                .limit(10).all()

            sales_by_category = [{'name': row.name, 'total_sales': float(row.total_sales)} for row in sales_by_category]
            current_app.logger.debug(f"Número de categorías en top ventas: {len(sales_by_category)}")
        except Exception as e:
            current_app.logger.error(f"Error al consultar ventas por categoría: {str(e)}")

        # Obtener proveedores más activos (top 5)
        try:
            top_suppliers = db.session.query(
                Supplier.id,
                Supplier.company_name.label('name'),
                func.sum(Product.stock).label('total_stock')
            ).join(Supplier.products) \
                .filter(Supplier.is_deleted == False, Product.is_deleted == False) \
                .group_by(Supplier.id, Supplier.company_name) \
                .order_by(func.sum(Product.stock).desc()) \
                .limit(5).all()

            top_suppliers = [{'id': row.id, 'name': row.name, 'total_stock': row.total_stock} for row in top_suppliers]
            current_app.logger.debug(f"Número de proveedores principales: {len(top_suppliers)}")
        except Exception as e:
            current_app.logger.error(f"Error al consultar los proveedores más activos: {str(e)}")

        # Obtener historial de pedidos a proveedores con paginación
        try:
            page = request.args.get('page', 1, type=int)
            per_page = 10

            order_history = db.session.query(
                Purchase.id,
                Purchase.date,
                Supplier.company_name.label('supplier'),
                Product.name.label('product'),
                PurchaseItem.price,
                PurchaseItem.quantity,
                (PurchaseItem.price * PurchaseItem.quantity).label('total')
            ).join(Supplier, Purchase.supplier_id == Supplier.id) \
                .join(PurchaseItem, Purchase.id == PurchaseItem.purchase_id) \
                .join(Product, PurchaseItem.product_id == Product.id) \
                .filter(Supplier.is_deleted == False, Product.is_deleted == False) \
                .order_by(Purchase.date.desc(), Purchase.id.desc()) \
                .paginate(page=page, per_page=per_page, error_out=False)

            current_app.logger.debug(f"Número de pedidos en la historia: {order_history.total}")
        except Exception as e:
            current_app.logger.error(f"Error al consultar el historial de pedidos: {str(e)}")

        current_app.logger.info("Estadísticas generadas exitosamente")

        return render_template('statistics.html',
                               total_products=total_products,
                               total_suppliers=total_suppliers,
                               total_users=total_users,
                               total_inventory_value=total_inventory_value,
                               low_stock_products=low_stock_products,
                               sales_by_category=sales_by_category,
                               top_suppliers=top_suppliers,
                               order_history=order_history)

    except Exception as e:
        current_app.logger.error(f"Error inesperado en la ruta de estadísticas: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return render_template('500.html'), 500

# Ruta para refrescar estadísticas
@main_bp.route('/api/refresh_statistics')
@login_required
def refresh_statistics():
    """
    API para refrescar las estadísticas (solo para administradores).
    """
    if not current_user.is_admin:
        abort(403)

    # Actualizar conteos para elementos activos
    total_products = Product.query.filter(Product.is_deleted == False).count()
    total_suppliers = Supplier.query.filter(Supplier.is_deleted == False).count()
    total_users = User.query.filter(User.is_admin == False).count()
    total_inventory_value = db.session.query(func.sum(Product.price * Product.stock)).filter(Product.is_deleted == False).scalar() or 0

    low_stock_products = Product.query.filter(Product.stock <= Product.min_stock, Product.is_deleted == False).all()
    low_stock_products = [
        {'id': p.id, 'name': p.name, 'stock': p.stock, 'min_stock': p.min_stock} for p in low_stock_products
    ]

    sales_by_category = db.session.query(
        Category.name,
        func.sum(SaleItem.quantity * SaleItem.price).label('total_sales')
    ).join(Product, SaleItem.product_id == Product.id) \
        .join(Category, Product.category_id == Category.id) \
        .filter(Product.is_deleted == False) \
        .group_by(Category.name) \
        .order_by(func.sum(SaleItem.quantity * SaleItem.price).desc()) \
        .limit(10).all()

    sales_by_category = [{'name': row.name, 'total_sales': float(row.total_sales)} for row in sales_by_category]

    top_suppliers = db.session.query(
        Supplier.id,
        Supplier.company_name.label('name'),
        func.sum(Product.stock).label('total_stock')
    ).join(Supplier.products) \
        .filter(Supplier.is_deleted == False, Product.is_deleted == False) \
        .group_by(Supplier.id, Supplier.company_name) \
        .order_by(func.sum(Product.stock).desc()) \
        .limit(5).all()

    top_suppliers = [{'id': row.id, 'name': row.name, 'total_stock': row.total_stock} for row in top_suppliers]

    order_history = db.session.query(
        Purchase.id,
        Purchase.date,
        Supplier.company_name.label('supplier'),
        Product.name.label('product'),
        PurchaseItem.price,
        PurchaseItem.quantity,
        (PurchaseItem.price * PurchaseItem.quantity).label('total')
    ).join(Supplier, Purchase.supplier_id == Supplier.id) \
        .join(PurchaseItem, Purchase.id == PurchaseItem.purchase_id) \
        .join(Product, PurchaseItem.product_id == Product.id) \
        .order_by(Purchase.date.desc(), Purchase.id.desc()) \
        .limit(50).all()

    # Eliminar registros antiguos si hay más de 50
    if len(order_history) > 50:
        oldest_purchase_id = order_history[-1].id
        Purchase.query.filter(Purchase.id <= oldest_purchase_id).delete()
        db.session.commit()

    order_history_data = [
        {
            'date': order.date.strftime('%Y-%m-%d %H:%M:%S'),
            'supplier': order.supplier,
            'product': order.product,
            'price': float(order.price),
            'quantity': order.quantity,
            'total': float(order.total)
        } for order in order_history
    ]

    return jsonify({
        'total_products': total_products,
        'total_suppliers': total_suppliers,
        'total_users': total_users,
        'total_inventory_value': total_inventory_value,
        'low_stock_products': low_stock_products,
        'sales_by_category': sales_by_category,
        'top_suppliers': top_suppliers,
        'order_history': order_history_data
    })

# Ruta para obtener el historial de compras del cliente
@main_bp.route('/api/client_purchase_history')
@login_required
def api_client_purchase_history():
    """
    API para obtener el historial de compras del cliente actual.
    """
    if current_user.is_admin:
        abort(403)

    page = request.args.get('page', 1, type=int)
    per_page = 10

    purchase_history = db.session.query(
        Sale.id,
        Sale.date,
        Product.name.label('product'),
        SaleItem.quantity,
        SaleItem.price,
        (SaleItem.quantity * SaleItem.price).label('total')
    ).join(SaleItem, Sale.id == SaleItem.sale_id) \
        .join(Product, SaleItem.product_id == Product.id) \
        .filter(Sale.user_id == current_user.id) \
        .order_by(Sale.date.desc(), Sale.id.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    purchase_history_data = [
        {
            'id': purchase.id,
            'date': purchase.date.strftime('%Y-%m-%d %H:%M:%S'),
            'product': purchase.product,
            'quantity': purchase.quantity,
            'price': float(purchase.price),
            'total': float(purchase.total)
        } for purchase in purchase_history.items
    ]

    return jsonify({
        'purchases': purchase_history_data,
        'total_pages': purchase_history.pages,
        'current_page': purchase_history.page
    })

# Ruta para obtener ventas por fecha
@main_bp.route('/api/sales_by_date/<date>')
@login_required
def sales_by_date(date):
    """
    API para obtener las ventas de una fecha específica (solo para administradores).
    """
    if not current_user.is_admin:
        abort(403)

    try:
        selected_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Formato de fecha inválido'}), 400

    page = request.args.get('page', 1, type=int)
    per_page = 10

    sales = db.session.query(
        Sale.id,
        Sale.date,
        User.username,
        User.email,
        Product.name.label('product'),
        Supplier.company_name.label('supplier'),
        SaleItem.quantity,
        SaleItem.price,
        (SaleItem.quantity * SaleItem.price).label('total')
    ).join(User, Sale.user_id == User.id) \
        .join(SaleItem, Sale.id == SaleItem.sale_id) \
        .join(Product, SaleItem.product_id == Product.id) \
        .outerjoin(Supplier, SaleItem.supplier_id == Supplier.id) \
        .filter(func.date(Sale.date) == selected_date) \
        .order_by(Sale.date.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    sales_data = [
        {
            'id': sale.id,
            'date': sale.date.strftime('%Y-%m-%d %H:%M:%S'),
            'username': sale.username,
            'email': sale.email,
            'product': sale.product,
            'supplier': sale.supplier or 'N/A',
            'quantity': sale.quantity,
            'price': float(sale.price),
            'total': float(sale.total)
        } for sale in sales.items
    ]

    return jsonify({
        'sales': sales_data,
        'total_pages': sales.pages,
        'current_page': sales.page
    })

# Ruta para obtener el historial de pedidos
@main_bp.route('/api/order_history')
@login_required
def api_order_history():
    """
    API para obtener el historial de pedidos (solo para administradores).
    """
    if not current_user.is_admin:
        abort(403)

    page = request.args.get('page', 1, type=int)
    per_page = 10

    order_history = db.session.query(
        Purchase.id,
        Purchase.date,
        Supplier.company_name.label('supplier'),
        Product.name.label('product'),
        PurchaseItem.price,
        PurchaseItem.quantity,
        (PurchaseItem.price * PurchaseItem.quantity).label('total')
    ).join(Supplier, Purchase.supplier_id == Supplier.id) \
        .join(PurchaseItem, Purchase.id == PurchaseItem.purchase_id) \
        .join(Product, PurchaseItem.product_id == Product.id) \
        .order_by(Purchase.date.desc(), Purchase.id.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    order_history_data = [
        {
            'id': order.id,
            'date': order.date.strftime('%Y-%m-%d %H:%M:%S'),
            'supplier': order.supplier,
            'product': order.product,
            'price': float(order.price),
            'quantity': order.quantity,
            'total': float(order.total)
        } for order in order_history.items
    ]

    return jsonify({
        'orders': order_history_data,
        'total_pages': order_history.pages,
        'current_page': order_history.page
    })

# Ruta para notificar a un proveedor
@main_bp.route('/api/notify_supplier', methods=['POST'])
@login_required
def notify_supplier():
    """
    API para notificar a un proveedor sobre un pedido (solo para administradores).
    """
    if not current_user.is_admin:
        abort(403)

    product_id = request.form.get('productId')
    supplier_id = request.form.get('supplier')
    quantity = request.form.get('quantity')
    message = request.form.get('message')

    product = Product.query.get_or_404(product_id)
    supplier = Supplier.query.get_or_404(supplier_id)

    # Calcular el total para la compra
    total = float(quantity) * product.price

    # Crear un nuevo pedido
    new_purchase = Purchase(supplier_id=supplier.id, date=datetime.utcnow(), total=total)
    db.session.add(new_purchase)

    # Crear un nuevo ítem de pedido
    purchase_item = PurchaseItem(purchase=new_purchase, product_id=product.id, quantity=int(quantity), price=product.price)
    db.session.add(purchase_item)

    # Actualizar el stock del producto
    product.stock += int(quantity)

    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Notificación enviada y stock actualizado'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

# Ruta para mostrar productos
@main_bp.route('/products')
@login_required
def products():
    """
    Muestra la lista de productos con opciones de filtrado y paginación.
    """
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    low_stock = request.args.get('low_stock') == 'on'

    query = Product.get_active()

    if search:
        query = query.filter(or_(Product.name.ilike(f'%{search}%'), Product.description.ilike(f'%{search}%')))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if low_stock:
        query = query.filter(Product.stock <= Product.min_stock)

    query = query.order_by(Product.name)

    # Obtener el número total de elementos
    total_items = query.count()

    # Calcular el número de páginas
    total_pages = (total_items + per_page - 1) // per_page

    # Asegurar que la página solicitada esté dentro de los límites
    page = max(1, min(page, total_pages))

    # Paginar los resultados
    products = query.paginate(page=page, per_page=per_page, error_out=False)

    if not products.items and page != 1:
        # Si la página actual está vacía y no es la primera página, redirigir a la última página válida
        return redirect(url_for('main.products', page=total_pages, search=search, category=category_id, low_stock='on' if low_stock else None))

    return render_template('products.html',
                           products=products,
                           categories=Category.query.all(),
                           current_category=category_id,
                           low_stock=low_stock,
                           search=search)

# Ruta para obtener información de un producto
@main_bp.route('/api/product_info/<int:product_id>')
@login_required
def get_product_info(product_id):
    """
    API para obtener información detallada de un producto específico.
    """
    product = Product.query.get_or_404(product_id)
    suppliers = [{'id': s.id, 'name': s.company_name} for s in product.suppliers]
    return jsonify({
        'price': float(product.price),
        'suppliers': suppliers
    })

# Ruta para mostrar detalles de un producto
@main_bp.route('/products/<int:product_id>')
@login_required
def product_detail(product_id):
    """
    Muestra los detalles de un producto específico.
    """
    try:
        product = Product.query.get_or_404(product_id)
        form = AddToCartForm() if not current_user.is_admin else None
        show_stock = current_user.is_admin  # Only show stock info to admins
        return render_template('product_detail.html', product=product, form=form, show_stock=show_stock)
    except Exception as e:
        current_app.logger.error(f"Error en product_detail: {str(e)}")
        return "Ha ocurrido un error", 500

# Ruta para añadir un nuevo producto
@main_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    """
    Maneja la adición de un nuevo producto (solo para administradores).
    """
    if not current_user.is_admin:
        flash('No tienes permiso para realizar esta acción', 'error')
        return redirect(url_for('main.products'))

    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    form.supplier.choices = [('', 'Seleccione un proveedor')] + [(str(s.id), s.company_name) for s in Supplier.query.all()]
    form.supplier.choices.append(('new', 'Crear nuevo proveedor'))

    if form.validate_on_submit():
        new_product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            stock=form.stock.data,
            min_stock=form.min_stock.data,
            category_id=form.category_id.data,
            location=form.location.data,
            reference_number=form.reference_number.data,
            color=form.color.data,
            weight=form.weight.data,
            dimensions=form.dimensions.data,
            manufacturer=form.manufacturer.data
        )

        if form.supplier.data == 'new':
            new_supplier = Supplier(
                company_name=form.new_supplier_company_name.data,
                contact_name=form.new_supplier_contact_name.data,
                phone=form.new_supplier_phone.data,
                email=form.new_supplier_email.data,
                address=form.new_supplier_address.data,
                city=form.new_supplier_city.data,
                country=form.new_supplier_country.data,
                postal_code=form.new_supplier_postal_code.data,
                cif=form.new_supplier_cif.data,
                discount=form.new_supplier_discount.data,
                iva=form.new_supplier_iva.data,
                payment_method=form.new_supplier_payment_method.data,
                bank_account=form.new_supplier_bank_account.data,
                notes=form.new_supplier_notes.data
            )
            db.session.add(new_supplier)
            db.session.flush()  # Esto asigna un ID a new_supplier
            new_product.suppliers.append(new_supplier)
        else:
            supplier = Supplier.query.get(form.supplier.data)
            if supplier:
                new_product.suppliers.append(supplier)

        try:
            db.session.add(new_product)
            db.session.commit()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'redirect': url_for('main.products')})
            flash('Producto añadido con éxito', 'success')
            return redirect(url_for('main.products'))
        except IntegrityError:
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'errors': {'reference_number': ['El número de referencia ya existe']}})
            flash('Error: El número de referencia ya existe', 'error')
        except Exception as e:
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'errors': {'general': [str(e)]}})
            flash(f'Error al añadir el producto: {str(e)}', 'error')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': False, 'errors': form.errors})
    return render_template('add_product.html', form=form)

# Ruta para editar un producto
@main_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """
    Maneja la edición de un producto existente (solo para administradores).
    """
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'No tienes permiso para realizar esta acción'}), 403

    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    form.supplier.choices = [('', 'Seleccione un proveedor')] + [(str(s.id), s.company_name) for s in
                                                                 Supplier.query.all()]

    if request.method == 'GET':
        if product.suppliers:
            form.supplier.data = str(product.suppliers[0].id)

    if form.validate_on_submit():
        try:
            form.populate_obj(product)

            # Actualizar el proveedor
            if form.supplier.data:
                supplier = Supplier.query.get(form.supplier.data)
                if supplier:
                    product.suppliers = [supplier]  # Reemplazar los proveedores existentes con el seleccionado
                else:
                    product.suppliers = []

            db.session.commit()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'message': 'Producto actualizado con éxito'})
            flash('Producto actualizado con éxito', 'success')
            return redirect(url_for('main.products'))
        except Exception as e:
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': str(e)}), 400
            flash(f'Error al actualizar el producto: {str(e)}', 'error')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': False, 'errors': form.errors}), 400
    return render_template('edit_product.html', form=form, product=product)

# Ruta para eliminar un producto
@main_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    """
    Maneja la eliminación (soft delete) de un producto (solo para administradores).
    """
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'No tienes permiso para realizar esta acción'}), 403

    product = Product.query.get_or_404(product_id)
    try:
        product.soft_delete()
        return jsonify({
            'success': True,
            'message': 'Producto eliminado con éxito',
            'redirect': url_for('main.products')
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

# Ruta para mostrar proveedores
@main_bp.route('/suppliers')
@login_required
def suppliers():
    """
    Muestra la lista de proveedores (solo para administradores).
    """
    if not current_user.is_admin:
        flash('No tienes permiso para acceder a esta página', 'error')
        return redirect(url_for('main.dashboard'))

    page = request.args.get('page', 1, type=int)
    per_page = 10
    search = request.args.get('search', '')

    query = Supplier.get_active()

    if search:
        query = query.filter(or_(
            Supplier.company_name.ilike(f'%{search}%'),
            Supplier.contact_name.ilike(f'%{search}%'),
            Supplier.email.ilike(f'%{search}%')
        ))

    suppliers = query.order_by(Supplier.company_name).paginate(page=page, per_page=per_page, error_out=False)
    total_pages = suppliers.pages

    return render_template('suppliers.html', suppliers=suppliers, search=search, total_pages=total_pages)

# Ruta para añadir un nuevo proveedor
@main_bp.route('/suppliers/add', methods=['GET', 'POST'])
@login_required
def add_supplier():
    """
    Maneja la adición de un nuevo proveedor (solo para administradores).
    """
    if not current_user.is_admin:
        flash('No tienes permiso para realizar esta acción', 'error')
        return redirect(url_for('main.suppliers'))

    form = SupplierForm()

    if form.validate_on_submit():
        new_supplier = Supplier(
            company_name=form.company_name.data,
            contact_name=form.contact_name.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data,
            city=form.city.data,
            country=form.country.data,
            postal_code=form.postal_code.data,
            cif=form.cif.data,
            discount=form.discount.data,
            iva=form.iva.data,
            payment_method=form.payment_method.data,
            bank_account=form.bank_account.data,
            notes=form.notes.data
        )

        try:
            db.session.add(new_supplier)
            db.session.commit()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'redirect': url_for('main.suppliers')})
            flash('Proveedor añadido con éxito', 'success')
            return redirect(url_for('main.suppliers'))
        except IntegrityError:
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'errors': {'cif': ['El CIF ya existe']}})
            flash('Error: El CIF ya existe', 'error')
        except Exception as e:
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'errors': {'general': [str(e)]}})
            flash(f'Error al añadir el proveedor: {str(e)}', 'error')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': False, 'errors': form.errors})
    return render_template('add_supplier.html', form=form)

# Ruta para mostrar detalles de un proveedor
@main_bp.route('/suppliers/<int:supplier_id>')
@login_required
def supplier_detail(supplier_id):
    """
    Muestra los detalles de un proveedor específico (solo para administradores).
    """
    if not current_user.is_admin:
        flash('No tienes permiso para acceder a esta página', 'error')
        return redirect(url_for('main.dashboard'))

    supplier = Supplier.query.get_or_404(supplier_id)
    return render_template('supplier_detail.html', supplier=supplier)

# Ruta para editar un proveedor
@main_bp.route('/suppliers/<int:supplier_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_supplier(supplier_id):
    """
    Maneja la edición de un proveedor existente (solo para administradores).
    """
    if not current_user.is_admin:
        flash('No tienes permiso para realizar esta acción', 'error')
        return redirect(url_for('main.suppliers'))

    supplier = Supplier.query.get_or_404(supplier_id)
    form = SupplierForm(obj=supplier)

    if form.validate_on_submit():
        try:
            form.populate_obj(supplier)
            db.session.commit()
            flash('Proveedor actualizado con éxito', 'success')
            return redirect(url_for('main.suppliers'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el proveedor: {str(e)}', 'error')

    return render_template('edit_supplier.html', form=form, supplier=supplier)

# Ruta para eliminar un proveedor
@main_bp.route('/suppliers/<int:supplier_id>/delete', methods=['POST'])
@login_required
def delete_supplier(supplier_id):
    """
    Maneja la eliminación (soft delete) de un proveedor (solo para administradores).
    """
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'No tienes permiso para realizar esta acción'}), 403

    supplier = Supplier.query.get_or_404(supplier_id)
    try:
        supplier.soft_delete()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Proveedor eliminado con éxito'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al eliminar proveedor: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400

# Ruta para mostrar el carrito
@main_bp.route('/cart')
@login_required
def cart():
    """
    Muestra el carrito de compras del usuario actual (solo para clientes).
    """
    if current_user.is_admin:
        flash('Los administradores no pueden acceder al carrito', 'error')
        return redirect(url_for('main.dashboard'))

    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

# Ruta para añadir un producto al carrito
@main_bp.route('/add-to-cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    """
    Maneja la adición de un producto al carrito del usuario (solo para clientes).
    """
    if current_user.is_admin:
        return jsonify({'success': False, 'error': 'Los administradores no pueden añadir productos al carrito'}), 403

    product = Product.query.get_or_404(product_id)
    form = AddToCartForm()

    if form.validate_on_submit():
        quantity = form.quantity.data
        if quantity <= 0:
            return jsonify({'success': False, 'error': 'La cantidad debe ser mayor que cero'}), 400

        if product.stock <= 0:
            return jsonify({'success': False, 'error': 'No hay stock disponible para este producto'}), 400

        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product.id).first()

        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(user_id=current_user.id, product_id=product.id, quantity=quantity)
            db.session.add(cart_item)

        try:
            db.session.commit()
            return jsonify({'success': True, 'message': 'Producto añadido al carrito'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    return jsonify({'success': False, 'errors': form.errors}), 400

# Ruta para actualizar la cantidad de un producto en el carrito
@main_bp.route('/update-cart/<int:product_id>', methods=['POST'])
@login_required
def update_cart(product_id):
    """
    Maneja la actualización de la cantidad de un producto en el carrito (solo para clientes).
    """
    if current_user.is_admin:
        return jsonify({'success': False, 'error': 'Los administradores no pueden modificar el carrito'}), 403

    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first_or_404()
    form = AddToCartForm()

    if form.validate_on_submit():
        new_quantity = form.quantity.data
        if new_quantity <= 0:
            return jsonify({'success': False, 'error': 'La cantidad debe ser mayor que cero'}), 400

        if cart_item.product.stock <= 0:
            return jsonify({'success': False, 'error': 'No hay stock disponible para este producto'}), 400

        cart_item.quantity = new_quantity
        try:
            db.session.commit()
            return jsonify({'success': True, 'message': 'Cantidad actualizada'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    return jsonify({'success': False, 'errors': form.errors}), 400

# Ruta para eliminar un producto del carrito
@main_bp.route('/remove-from-cart/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    """
    Maneja la eliminación de un producto del carrito (solo para clientes).
    """
    if current_user.is_admin:
        return jsonify({'success': False, 'error': 'Los administradores no pueden modificar el carrito'}), 403

    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first_or_404()

    try:
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Producto eliminado del carrito'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Ruta para obtener el total del carrito
@main_bp.route('/api/cart-total')
@login_required
def get_cart_total():
    """
    API para obtener el total actual del carrito del usuario (solo para clientes).
    """
    if current_user.is_admin:
        return jsonify({'success': False, 'error': 'Los administradores no pueden acceder al carrito'}), 403

    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return jsonify({'total': total})

# Ruta para el proceso de checkout
@main_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """
    Maneja el proceso de checkout para finalizar una compra (solo para clientes).
    """
    if current_user.is_admin:
        flash('Los administradores no pueden realizar compras', 'error')
        return redirect(url_for('main.dashboard'))

    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Tu carrito está vacío', 'error')
        return redirect(url_for('main.cart'))

    total = sum(item.product.price * item.quantity for item in cart_items)
    form = CheckoutForm()

    if form.validate_on_submit():
        try:
            # Crear una nueva venta
            sale = Sale(user_id=current_user.id, total=total, date=datetime.utcnow())
            db.session.add(sale)

            # Crear items de venta y actualizar stock
            for cart_item in cart_items:
                if cart_item.product.stock <= 0:
                    raise ValueError(f"No hay stock disponible para {cart_item.product.name}")

                # Obtener el proveedor del producto
                supplier = cart_item.product.suppliers[0] if cart_item.product.suppliers else None

                sale_item = SaleItem(
                    sale=sale,
                    product_id=cart_item.product_id,
                    supplier_id=supplier.id if supplier else None,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price
                )
                db.session.add(sale_item)

                # Actualizar el stock del producto
                cart_item.product.stock -= cart_item.quantity

            # Eliminar items del carrito
            CartItem.query.filter_by(user_id=current_user.id).delete()

            db.session.commit()
            flash('Compra realizada con éxito', 'success')
            return redirect(url_for('main.order_confirmation', order_id=sale.id))
        except ValueError as e:
            db.session.rollback()
            flash(str(e), 'error')
            return redirect(url_for('main.cart'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error al procesar la compra: {str(e)}')
            flash('Ha ocurrido un error al procesar la compra. Por favor, inténtelo de nuevo.', 'error')
            return redirect(url_for('main.cart'))

    return render_template('checkout.html', cart_items=cart_items, total=total, form=form)

# Ruta para la confirmación de pedido
@main_bp.route('/order-confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    """
    Muestra la confirmación de un pedido realizado (solo para clientes).
    """
    if current_user.is_admin:
        flash('Los administradores no pueden ver confirmaciones de pedidos', 'error')
        return redirect(url_for('main.dashboard'))

    try:
        sale = Sale.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
        sale_items = SaleItem.query.filter_by(sale_id=sale.id).all()
        return render_template('order_confirmation.html', sale=sale, sale_items=sale_items)
    except Exception as e:
        current_app.logger.error(f'Error al mostrar la confirmación del pedido: {str(e)}')
        flash('Ha ocurrido un error al mostrar la confirmación del pedido. Por favor, contacte con el soporte.', 'error')
        return redirect(url_for('main.dashboard'))

# Ruta para mostrar productos con bajo stock
@main_bp.route('/low-stock-products')
@login_required
def low_stock_products():
    """
    Muestra una lista de productos con bajo stock (solo para administradores).
    """
    if not current_user.is_admin:
        flash('No tienes permiso para acceder a esta página', 'error')
        return redirect(url_for('main.dashboard'))

    low_stock_products = Product.query.filter(Product.stock <= Product.min_stock).all()
    return render_template('low_stock_products.html', products=low_stock_products)

# Ruta para obtener un token CSRF
@main_bp.route('/api/csrf-token', methods=['GET'])
def get_csrf_token():
    """
    API para obtener un token CSRF.
    """
    return jsonify({'csrf_token': generate_csrf()})

# Función para inicializar las rutas
def init_routes(app):
    """
    Inicializa todas las rutas para la aplicación.
    """
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
