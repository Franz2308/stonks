# -*- coding: utf-8 -*-
"""
app.py
Aplicación Web Principal Stonks - Control de Cuenta Corriente y Crédito Comercial.
Desarrollada para el curso SI642 Finanzas e Ingeniería Económica.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, date, timedelta
import sqlite3
import os

from database import get_db_connection, init_db
from financial_engine import (
    convertir_a_ted, convertir_a_tem, convertir_ted_a_tea,
    calcular_compra_fin_de_mes, calcular_metodo_frances_con_gracia,
    imputar_pago_segun_prelacion, calcular_van, calcular_tir
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "stonks_super_secret_financial_key_2026")

# Filtro para formateo de moneda en plantillas Jinja2
@app.template_filter('moneda')
def formato_moneda(valor, simbolo="S/"):
    if valor is None:
        return f"{simbolo} 0.00"
    try:
        val = float(valor)
        return f"{simbolo} {val:,.2f}"
    except (ValueError, TypeError):
        return f"{simbolo} 0.00"

@app.template_filter('porcentaje')
def formato_porcentaje(valor, decimales=4):
    if valor is None:
        return "0.00%"
    try:
        val = float(valor) * 100.0
        return f"{val:.{decimales}f}%"
    except (ValueError, TypeError):
        return "0.00%"

# Decoradores de autenticación y autorización
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Debe iniciar sesión para acceder al sistema.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if session.get("rol") not in allowed_roles:
                flash("No cuenta con privilegios suficientes para acceder a esta sección.", "danger")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Contexto global para plantillas
@app.context_processor
def inject_global_data():
    tienda = None
    if "tienda_id" in session and session["tienda_id"]:
        conn = get_db_connection()
        t = conn.execute("SELECT * FROM tiendas WHERE id = ?", (session["tienda_id"],)).fetchone()
        conn.close()
        if t:
            tienda = dict(t)
    return {
        "current_user": session.get("username"),
        "user_role": session.get("rol"),
        "user_name": session.get("nombre_completo"),
        "current_tienda": tienda,
        "now": datetime.now()
    }

# -------------------------------------------------------------
# RUTAS DE AUTENTICACIÓN Y REGISTRO
# -------------------------------------------------------------
@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    rol = session.get("rol")
    if rol == "admin_sistema":
        return redirect(url_for("admin_dashboard"))
    elif rol == "admin_tienda":
        return redirect(url_for("store_dashboard"))
    elif rol == "cliente":
        return redirect(url_for("customer_portal"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM usuarios WHERE username = ? AND activo = 1", (username,)).fetchone()
        
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["nombre_completo"] = user["nombre_completo"]
            session["rol"] = user["rol"]
            
            # Si es admin_tienda, asociar la tienda
            if user["rol"] == "admin_tienda":
                tienda = conn.execute("SELECT id FROM tiendas WHERE admin_usuario_id = ? AND activa = 1", (user["id"],)).fetchone()
                if tienda:
                    session["tienda_id"] = tienda["id"]
                else:
                    session["tienda_id"] = None
            elif user["rol"] == "cliente":
                # Asociar datos de cliente si existen
                cliente = conn.execute("SELECT id, tienda_id FROM clientes WHERE usuario_id = ?", (user["id"],)).fetchone()
                if cliente:
                    session["cliente_id"] = cliente["id"]
                    session["tienda_id"] = cliente["tienda_id"]
                    
            conn.close()
            flash(f"¡Bienvenido(a), {user['nombre_completo']}!", "success")
            return redirect(url_for("index"))
        else:
            conn.close()
            flash("Usuario o contraseña incorrectos. Intente nuevamente.", "danger")
            
    return render_template("login.html")

@app.route("/demo-login/<rol>")
def demo_login(rol):
    """Acceso rápido con 1-click para demostraciones y corrección docente"""
    cuentas_demo = {
        "admin": ("admin", "admin123"),
        "tienda": ("bodega_don_pepe", "tienda123"),
        "espiga": ("panaderia_espiga", "espiga123"),
        "cliente": ("cliente_juan", "cliente123")
    }
    if rol in cuentas_demo:
        usr, pwd = cuentas_demo[rol]
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM usuarios WHERE username = ?", (usr,)).fetchone()
        if user:
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["nombre_completo"] = user["nombre_completo"]
            session["rol"] = user["rol"]
            if user["rol"] == "admin_tienda":
                t = conn.execute("SELECT id FROM tiendas WHERE admin_usuario_id = ?", (user["id"],)).fetchone()
                session["tienda_id"] = t["id"] if t else None
            elif user["rol"] == "cliente":
                c = conn.execute("SELECT id, tienda_id FROM clientes WHERE usuario_id = ?", (user["id"],)).fetchone()
                if c:
                    session["cliente_id"] = c["id"]
                    session["tienda_id"] = c["tienda_id"]
            conn.close()
            flash(f"Sesión demo iniciada como: {user['nombre_completo']} ({user['rol']})", "info")
            return redirect(url_for("index"))
        conn.close()
    flash("Cuenta demo no encontrada.", "danger")
    return redirect(url_for("login"))

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        tipo_registro = request.form.get("tipo_registro") # 'tienda' o 'cliente'
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        nombre = request.form.get("nombre_completo", "").strip()
        email = request.form.get("email", "").strip()
        telefono = request.form.get("telefono", "").strip()
        
        if not (username and password and nombre and email):
            flash("Todos los campos obligatorios deben completarse.", "danger")
            return render_template("login.html", registro_active=True)
            
        conn = get_db_connection()
        try:
            # Validar existencia previa de usuario
            existe = conn.execute("SELECT id FROM usuarios WHERE username = ? OR email = ?", (username, email)).fetchone()
            if existe:
                flash("El nombre de usuario o correo electrónico ya se encuentra registrado.", "warning")
                conn.close()
                return render_template("login.html", registro_active=True)
                
            pwd_hash = generate_password_hash(password)
            rol = "admin_tienda" if tipo_registro == "tienda" else "cliente"
            
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO usuarios (username, password_hash, nombre_completo, email, telefono, rol)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (username, pwd_hash, nombre, email, telefono, rol))
            nuevo_user_id = cursor.lastrowid
            
            # Si se registra como tienda, registrar también el comercio
            if tipo_registro == "tienda":
                ruc = request.form.get("ruc", "").strip()
                razon_social = request.form.get("razon_social", "").strip()
                nombre_comercial = request.form.get("nombre_comercial", "").strip()
                giro = request.form.get("giro", "Bodega").strip()
                direccion = request.form.get("direccion_tienda", "").strip()
                
                cursor.execute("""
                    INSERT INTO tiendas (admin_usuario_id, razon_social, nombre_comercial, ruc, giro, direccion, telefono, correo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (nuevo_user_id, razon_social, nombre_comercial, ruc, giro, direccion, telefono, email))
                
            conn.commit()
            conn.close()
            flash("Registro exitoso. Ya puede iniciar sesión con sus credenciales.", "success")
            return redirect(url_for("login"))
            
        except Exception as e:
            conn.rollback()
            conn.close()
            flash(f"Ocurrió un error al procesar el registro: {str(e)}", "danger")
            return render_template("login.html", registro_active=True)
            
    return render_template("login.html", registro_active=True)

@app.route("/logout")
def logout():
    session.clear()
    flash("Ha cerrado sesión correctamente.", "info")
    return redirect(url_for("login"))

# -------------------------------------------------------------
# MÓDULO 1: ADMINISTRADOR DEL SISTEMA
# -------------------------------------------------------------
@app.route("/admin")
@login_required
@role_required("admin_sistema")
def admin_dashboard():
    conn = get_db_connection()
    tiendas = conn.execute("""
        SELECT t.*, u.nombre_completo as admin_nombre, u.email as admin_email,
               (SELECT COUNT(*) FROM clientes c WHERE c.tienda_id = t.id) as total_clientes,
               (SELECT COUNT(*) FROM ventas v WHERE v.tienda_id = t.id) as total_ventas,
               (SELECT COALESCE(SUM(v.total_a_pagar), 0) FROM ventas v WHERE v.tienda_id = t.id) as volumen_credito
        FROM tiendas t
        JOIN usuarios u ON t.admin_usuario_id = u.id
        ORDER BY t.fecha_creacion DESC
    """).fetchall()
    
    stats = {
        "total_tiendas": len(tiendas),
        "tiendas_activas": sum(1 for t in tiendas if t["activa"] == 1),
        "total_clientes": sum(t["total_clientes"] for t in tiendas),
        "volumen_total": sum(t["volumen_credito"] for t in tiendas)
    }
    conn.close()
    return render_template("admin_system.html", tiendas=tiendas, stats=stats)

@app.route("/admin/tienda/alta", methods=["POST"])
@login_required
@role_required("admin_sistema")
def admin_tienda_alta():
    # Alta de tienda por el administrador del sistema
    username = request.form.get("username").strip()
    password = request.form.get("password").strip()
    nombre_admin = request.form.get("nombre_admin").strip()
    email_admin = request.form.get("email_admin").strip()
    telefono = request.form.get("telefono").strip()
    
    razon_social = request.form.get("razon_social").strip()
    nombre_comercial = request.form.get("nombre_comercial").strip()
    ruc = request.form.get("ruc").strip()
    giro = request.form.get("giro").strip()
    direccion = request.form.get("direccion").strip()
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        pwd_hash = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO usuarios (username, password_hash, nombre_completo, email, telefono, rol)
            VALUES (?, ?, ?, ?, ?, 'admin_tienda');
        """, (username, pwd_hash, nombre_admin, email_admin, telefono))
        admin_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO tiendas (admin_usuario_id, razon_social, nombre_comercial, ruc, giro, direccion, telefono, correo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (admin_id, razon_social, nombre_comercial, ruc, giro, direccion, telefono, email_admin))
        
        conn.commit()
        flash(f"Tienda '{nombre_comercial}' y su administrador registrados exitosamente.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al dar de alta la tienda: {str(e)}", "danger")
    finally:
        conn.close()
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/tienda/<int:tienda_id>/toggle-estado")
@login_required
@role_required("admin_sistema")
def admin_tienda_toggle(tienda_id):
    conn = get_db_connection()
    tienda = conn.execute("SELECT activa, nombre_comercial FROM tiendas WHERE id = ?", (tienda_id,)).fetchone()
    if tienda:
        nuevo_estado = 0 if tienda["activa"] == 1 else 1
        conn.execute("UPDATE tiendas SET activa = ? WHERE id = ?", (nuevo_estado, tienda_id))
        conn.commit()
        estado_txt = "activada" if nuevo_estado == 1 else "dada de baja (desactivada)"
        flash(f"La tienda '{tienda['nombre_comercial']}' ha sido {estado_txt}.", "info")
    conn.close()
    return redirect(url_for("admin_dashboard"))

# -------------------------------------------------------------
# MÓDULO 2: ADMINISTRADOR DE TIENDA (COMERCIO)
# -------------------------------------------------------------
@app.route("/dashboard")
@login_required
@role_required("admin_tienda")
def store_dashboard():
    tienda_id = session.get("tienda_id")
    if not tienda_id:
        flash("No tiene una tienda asignada.", "warning")
        return redirect(url_for("login"))
        
    conn = get_db_connection()
    
    # Métricas principales
    ventas = conn.execute("""
        SELECT v.*, c.nombres || ' ' || c.apellidos as cliente_nombre
        FROM ventas v
        JOIN clientes c ON v.cliente_id = c.id
        WHERE v.tienda_id = ?
        ORDER BY v.fecha_creacion DESC
    """, (tienda_id,)).fetchall()
    
    total_credito_otorgado = sum(v["monto_total_lista"] for v in ventas)
    total_saldo_por_cobrar = sum(v["saldo_pendiente"] for v in ventas)
    total_intereses_ganados = sum(v["total_intereses"] for v in ventas)
    
    # Clientes
    clientes = conn.execute("""
        SELECT c.*,
               COALESCE((SELECT SUM(v.saldo_pendiente) FROM ventas v WHERE v.cliente_id = c.id), 0) as deuda_actual
        FROM clientes c
        WHERE c.tienda_id = ? AND c.activo = 1
    """, (tienda_id,)).fetchall()
    
    # Liquidaciones pendientes
    liquidaciones = conn.execute("""
        SELECT l.*, c.nombres || ' ' || c.apellidos as cliente_nombre, c.telefono as cliente_telefono
        FROM liquidaciones_corte l
        JOIN clientes c ON l.cliente_id = c.id
        WHERE l.tienda_id = ?
        ORDER BY l.fecha_corte DESC
    """, (tienda_id,)).fetchall()
    
    conn.close()
    
    stats = {
        "total_clientes": len(clientes),
        "total_credito": total_credito_otorgado,
        "saldo_por_cobrar": total_saldo_por_cobrar,
        "intereses_ganados": total_intereses_ganados,
        "ventas_recientes": ventas[:5],
        "liquidaciones_pendientes": [l for l in liquidaciones if l["estado"] != "Pagado"]
    }
    
    return render_template("store_dashboard.html", stats=stats, clientes=clientes, ventas=ventas)

# --- Catálogo de Productos ---
@app.route("/productos")
@login_required
@role_required("admin_tienda")
def productos():
    tienda_id = session.get("tienda_id")
    conn = get_db_connection()
    prods = conn.execute("""
        SELECT * FROM productos WHERE tienda_id = ? ORDER BY descripcion ASC
    """, (tienda_id,)).fetchall()
    conn.close()
    return render_template("products.html", productos=prods)

@app.route("/productos/alta", methods=["POST"])
@login_required
@role_required("admin_tienda")
def productos_alta():
    tienda_id = session.get("tienda_id")
    codigo = request.form.get("codigo").strip()
    descripcion = request.form.get("descripcion").strip()
    marca = request.form.get("marca", "Genérico").strip()
    proveedor = request.form.get("proveedor", "Elaboración propia").strip()
    unidad = request.form.get("unidad_medida", "Unidad").strip()
    precio_contado = float(request.form.get("precio_contado", 0.0))
    precio_lista = float(request.form.get("precio_lista", precio_contado))
    modalidad = request.form.get("modalidad_permitida", "Ambas").strip()
    imagen_url = request.form.get("imagen_url", "").strip() or "https://images.unsplash.com/photo-1542838132-92c53300491e?w=200"
    
    if precio_lista < precio_contado:
        flash("El precio de lista (crédito) no puede ser inferior al precio al contado.", "warning")
        return redirect(url_for("productos"))
        
    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO productos (tienda_id, codigo, descripcion, marca, proveedor, unidad_medida, precio_contado, precio_lista, modalidad_permitida, imagen_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (tienda_id, codigo, descripcion, marca, proveedor, unidad, precio_contado, precio_lista, modalidad, imagen_url))
        conn.commit()
        flash(f"Producto '{descripcion}' agregado al catálogo con éxito.", "success")
    except Exception as e:
        flash(f"Error al registrar producto: {str(e)}", "danger")
    finally:
        conn.close()
    return redirect(url_for("productos"))

@app.route("/productos/<int:prod_id>/toggle")
@login_required
@role_required("admin_tienda")
def productos_toggle(prod_id):
    tienda_id = session.get("tienda_id")
    conn = get_db_connection()
    p = conn.execute("SELECT activo, descripcion FROM productos WHERE id = ? AND tienda_id = ?", (prod_id, tienda_id)).fetchone()
    if p:
        nuevo = 0 if p["activo"] == 1 else 1
        conn.execute("UPDATE productos SET activo = ? WHERE id = ?", (nuevo, prod_id))
        conn.commit()
        txt = "reactivado" if nuevo == 1 else "dado de baja"
        flash(f"Producto '{p['descripcion']}' {txt}.", "info")
    conn.close()
    return redirect(url_for("productos"))

# --- Gestión de Clientes y Políticas de Crédito ---
@app.route("/clientes")
@login_required
@role_required("admin_tienda")
def clientes():
    tienda_id = session.get("tienda_id")
    conn = get_db_connection()
    lista_clientes = conn.execute("""
        SELECT c.*,
               COALESCE((SELECT SUM(v.saldo_pendiente) FROM ventas v WHERE v.cliente_id = c.id AND v.estado != 'Pagado'), 0) as deuda_actual
        FROM clientes c
        WHERE c.tienda_id = ?
        ORDER BY c.apellidos ASC
    """, (tienda_id,)).fetchall()
    conn.close()
    return render_template("customers.html", clientes=lista_clientes)

@app.route("/clientes/alta", methods=["POST"])
@login_required
@role_required("admin_tienda")
def clientes_alta():
    tienda_id = session.get("tienda_id")
    
    tipo_doc = request.form.get("tipo_documento", "DNI")
    num_doc = request.form.get("num_documento").strip()
    nombres = request.form.get("nombres").strip()
    apellidos = request.form.get("apellidos").strip()
    direccion = request.form.get("direccion").strip()
    telefono = request.form.get("telefono").strip()
    correo = request.form.get("correo", "").strip()
    moneda = request.form.get("moneda", "PEN")
    
    limite = float(request.form.get("limite_credito", 500.0))
    plazo_max = int(request.form.get("plazo_maximo_meses", 6))
    dia_corte = int(request.form.get("dia_corte", 20))
    dia_pago = int(request.form.get("dia_pago", 26))
    
    tipo_comp = request.form.get("tipo_tasa_comp", "TEA")
    tasa_comp = float(request.form.get("tasa_comp", 24.0)) / 100.0
    cap_comp = request.form.get("cap_comp", "Diaria")
    
    tipo_mora = request.form.get("tipo_tasa_mora", "TEA")
    tasa_mora = float(request.form.get("tasa_mora", 5.0)) / 100.0
    cap_mora = request.form.get("cap_mora", "Diaria")
    cok_anual = float(request.form.get("cok_anual", 15.0)) / 100.0
    
    # Opcional: Crear usuario para el cliente
    crear_usuario = request.form.get("crear_usuario_web") == "on"
    user_id = None
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if crear_usuario:
            usr_cliente = f"cli_{num_doc}"
            pwd_cliente = generate_password_hash(f"cli{num_doc}")
            cursor.execute("""
                INSERT INTO usuarios (username, password_hash, nombre_completo, email, telefono, rol)
                VALUES (?, ?, ?, ?, ?, 'cliente');
            """, (usr_cliente, pwd_cliente, f"{nombres} {apellidos}", correo or f"{usr_cliente}@cliente.pe", telefono))
            user_id = cursor.lastrowid
            
        cursor.execute("""
            INSERT INTO clientes (
                tienda_id, usuario_id, tipo_documento, num_documento, nombres, apellidos, direccion, telefono, correo,
                moneda, limite_credito, plazo_maximo_meses, dia_corte, dia_pago,
                tipo_tasa_comp, tasa_comp, cap_comp, tipo_tasa_mora, tasa_mora, cap_mora, cok_anual
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            tienda_id, user_id, tipo_doc, num_doc, nombres, apellidos, direccion, telefono, correo,
            moneda, limite, plazo_max, dia_corte, dia_pago,
            tipo_comp, tasa_comp, cap_comp, tipo_mora, tasa_mora, cap_mora, cok_anual
        ))
        conn.commit()
        flash(f"Cliente '{nombres} {apellidos}' registrado con éxito con límite de S/ {limite:,.2f}.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al registrar cliente: {str(e)}", "danger")
    finally:
        conn.close()
    return redirect(url_for("clientes"))

# --- Punto de Venta a Crédito (POS) ---
@app.route("/pos", methods=["GET", "POST"])
@login_required
@role_required("admin_tienda")
def pos_credito():
    tienda_id = session.get("tienda_id")
    conn = get_db_connection()
    
    if request.method == "POST":
        cliente_id = int(request.form.get("cliente_id"))
        modalidad = request.form.get("modalidad") # 'Fin_De_Mes' o 'Cuotas'
        num_cuotas = int(request.form.get("num_cuotas", 1))
        fecha_compra_str = request.form.get("fecha_compra", datetime.now().strftime("%Y-%m-%d"))
        hora_compra_str = request.form.get("hora_compra", datetime.now().strftime("%H:%M:%S"))
        
        # Recuperar datos del cliente
        cliente = conn.execute("SELECT * FROM clientes WHERE id = ? AND tienda_id = ?", (cliente_id, tienda_id)).fetchone()
        if not cliente:
            flash("Cliente no válido.", "danger")
            conn.close()
            return redirect(url_for("pos_credito"))
            
        # Calcular deuda actual
        deuda_actual = conn.execute("""
            SELECT COALESCE(SUM(saldo_pendiente), 0) FROM ventas WHERE cliente_id = ? AND estado != 'Pagado'
        """, (cliente_id,)).fetchone()[0]
        
        # Extraer productos seleccionados
        prod_ids = request.form.getlist("prod_id[]")
        cantidades = request.form.getlist("cantidad[]")
        
        items_compra = []
        total_lista = 0.0
        
        for p_id, cant in zip(prod_ids, cantidades):
            c_val = float(cant)
            if c_val > 0:
                p = conn.execute("SELECT * FROM productos WHERE id = ? AND tienda_id = ?", (p_id, tienda_id)).fetchone()
                if p:
                    subt = round(p["precio_lista"] * c_val, 2)
                    total_lista += subt
                    items_compra.append({
                        "producto_id": p["id"],
                        "descripcion": p["descripcion"],
                        "precio_unitario": p["precio_lista"],
                        "cantidad": c_val,
                        "subtotal": subt
                    })
                    
        total_lista = round(total_lista, 2)
        if total_lista <= 0:
            flash("Debe seleccionar al menos un producto con cantidad válida.", "warning")
            conn.close()
            return redirect(url_for("pos_credito"))
            
        # REGLA DEL ENUNCIADO: NO PERMITIR COMPRAS QUE EXCEDAN EL LÍMITE DE CRÉDITO
        if (deuda_actual + total_lista) > cliente["limite_credito"]:
            exceso = (deuda_actual + total_lista) - cliente["limite_credito"]
            flash(f"OPERACIÓN DENEGADA: La compra (S/ {total_lista:,.2f}) excede el límite de crédito disponible del cliente en S/ {exceso:,.2f}. Límite: S/ {cliente['limite_credito']:,.2f}, Deuda actual: S/ {deuda_actual:,.2f}.", "danger")
            conn.close()
            return redirect(url_for("pos_credito"))
            
        # Calcular fechas de corte y de pago del ciclo
        fecha_compra_dt = datetime.strptime(fecha_compra_str, "%Y-%m-%d").date()
        anio = fecha_compra_dt.year
        mes = fecha_compra_dt.month
        
        # Fecha de corte del mes en curso
        dia_corte_val = min(cliente["dia_corte"], 28)
        dia_pago_val = min(cliente["dia_pago"], 28)
        fecha_corte_dt = date(anio, mes, dia_corte_val)
        fecha_pago_dt = date(anio, mes, dia_pago_val)
        
        # Generar número de ticket único
        count_v = conn.execute("SELECT COUNT(*) FROM ventas WHERE tienda_id = ?", (tienda_id,)).fetchone()[0]
        num_ticket = f"TKT-{tienda_id:02d}-{count_v + 101:05d}"
        
        cursor = conn.cursor()
        
        if modalidad == "Cuotas":
            # REGLA DEL ENUNCIADO: MÉTODO FRANCÉS VENCIDO SIMPLE ORDINARIO CON GRACIA TOTAL CAPITALIZADA
            res_calc = calcular_metodo_frances_con_gracia(
                capital_inicial=total_lista,
                fecha_compra=fecha_compra_str,
                fecha_corte=fecha_corte_dt.strftime("%Y-%m-%d"),
                primer_dia_pago_pactado=fecha_pago_dt.strftime("%Y-%m-%d"),
                num_cuotas=num_cuotas,
                tipo_tasa_comp=cliente["tipo_tasa_comp"],
                tasa_comp=cliente["tasa_comp"],
                cap_comp=cliente["cap_comp"],
                cok_anual=cliente["cok_anual"]
            )
            
            cursor.execute("""
                INSERT INTO ventas (
                    tienda_id, cliente_id, num_ticket, fecha_compra, hora_compra, modalidad, num_cuotas,
                    monto_total_lista, interes_gracia, capital_financiado, cuota_mensual, total_intereses,
                    total_a_pagar, saldo_pendiente, estado, es_post_corte, fecha_corte_aplicada, fecha_pago_pactada
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendiente', 0, ?, ?);
            """, (
                tienda_id, cliente_id, num_ticket, fecha_compra_str, hora_compra_str, "Cuotas", num_cuotas,
                total_lista, res_calc["interes_gracia"], res_calc["capital_capitalizado"],
                res_calc["cuota_mensual_fija"], res_calc["total_intereses"],
                res_calc["total_a_pagar"], res_calc["total_a_pagar"], fecha_corte_dt, fecha_pago_dt
            ))
            venta_id = cursor.lastrowid
            
            # Insertar cuotas en el cronograma
            for c in res_calc["cronograma"]:
                cursor.execute("""
                    INSERT INTO cuotas_cronograma (
                        venta_id, numero_cuota, fecha_vencimiento, saldo_inicial, cuota, interes, amortizacion, saldo_final, estado
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pendiente');
                """, (
                    venta_id, c["numero_cuota"], c["fecha_vencimiento"],
                    c["saldo_inicial"], c["cuota"], c["interes"], c["amortizacion"], c["saldo_final"]
                ))
        else:
            # REGLA DEL ENUNCIADO: COMPRA A FIN DE MES CON INTERÉS POR DÍAS TRANSCURRIDOS
            res_calc = calcular_compra_fin_de_mes(
                capital=total_lista,
                fecha_compra=fecha_compra_str,
                fecha_corte=fecha_corte_dt.strftime("%Y-%m-%d"),
                fecha_pago_pactada=fecha_pago_dt.strftime("%Y-%m-%d"),
                tipo_tasa_comp=cliente["tipo_tasa_comp"],
                tasa_comp=cliente["tasa_comp"],
                cap_comp=cliente["cap_comp"]
            )
            
            cursor.execute("""
                INSERT INTO ventas (
                    tienda_id, cliente_id, num_ticket, fecha_compra, hora_compra, modalidad, num_cuotas,
                    monto_total_lista, interes_gracia, capital_financiado, cuota_mensual, total_intereses,
                    total_a_pagar, saldo_pendiente, estado, es_post_corte, fecha_corte_aplicada, fecha_pago_pactada
                ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, 0.0, ?, ?, ?, ?, ?, 'Pendiente', ?, ?, ?);
            """, (
                tienda_id, cliente_id, num_ticket, fecha_compra_str, hora_compra_str, "Fin_De_Mes",
                total_lista, total_lista, res_calc["total_pactado"], res_calc["interes_compensatorio"],
                res_calc["total_pactado"], res_calc["total_pactado"],
                1 if res_calc["es_post_corte"] else 0, fecha_corte_dt, res_calc["fecha_pago_pactada"]
            ))
            venta_id = cursor.lastrowid
            
        # Registrar detalles
        for item in items_compra:
            cursor.execute("""
                INSERT INTO venta_detalles (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?);
            """, (venta_id, item["producto_id"], item["cantidad"], item["precio_unitario"], item["subtotal"]))
            
        conn.commit()
        conn.close()
        
        flash(f"¡Venta a crédito registrada exitosamente! Comprobante: {num_ticket}. Monto: S/ {total_lista:,.2f}.", "success")
        return redirect(url_for("pos_credito"))
        
    # GET: Cargar catálogo y clientes
    prods = conn.execute("SELECT * FROM productos WHERE tienda_id = ? AND activo = 1 ORDER BY descripcion ASC", (tienda_id,)).fetchall()
    clients = conn.execute("""
        SELECT c.*,
               COALESCE((SELECT SUM(v.saldo_pendiente) FROM ventas v WHERE v.cliente_id = c.id AND v.estado != 'Pagado'), 0) as deuda_actual
        FROM clientes c
        WHERE c.tienda_id = ? AND c.activo = 1
        ORDER BY c.apellidos ASC
    """, (tienda_id,)).fetchall()
    conn.close()
    
    return render_template("pos_credit.html", productos=prods, clientes=clients)

# --- Liquidaciones de Corte y Listado de Pagos ---
@app.route("/liquidaciones")
@login_required
@role_required("admin_tienda")
def liquidaciones():
    tienda_id = session.get("tienda_id")
    conn = get_db_connection()
    
    # Liquidaciones existentes
    liqs = conn.execute("""
        SELECT l.*, c.nombres || ' ' || c.apellidos as cliente_nombre, c.num_documento, c.telefono,
               c.tasa_mora, c.tipo_tasa_mora
        FROM liquidaciones_corte l
        JOIN clientes c ON l.cliente_id = c.id
        WHERE l.tienda_id = ?
        ORDER BY l.fecha_corte DESC
    """, (tienda_id,)).fetchall()
    
    # Clientes disponibles para generar liquidación
    clientes = conn.execute("SELECT * FROM clientes WHERE tienda_id = ? AND activo = 1", (tienda_id,)).fetchall()
    conn.close()
    
    return render_template("settlement.html", liquidaciones=liqs, clientes=clientes)

@app.route("/liquidaciones/generar", methods=["POST"])
@login_required
@role_required("admin_tienda")
def liquidaciones_generar():
    tienda_id = session.get("tienda_id")
    cliente_id = int(request.form.get("cliente_id"))
    periodo = request.form.get("periodo", datetime.now().strftime("%Y-%m"))
    
    conn = get_db_connection()
    cliente = conn.execute("SELECT * FROM clientes WHERE id = ? AND tienda_id = ?", (cliente_id, tienda_id)).fetchone()
    if not cliente:
        flash("Cliente no encontrado.", "danger")
        conn.close()
        return redirect(url_for("liquidaciones"))
        
    # Obtener todas las compras de fin de mes pendientes que entren en este ciclo (anteriores o iguales a fecha de corte)
    # y las cuotas de financiamiento que venzan en este ciclo
    ventas_pendientes = conn.execute("""
        SELECT * FROM ventas
        WHERE cliente_id = ? AND tienda_id = ? AND estado != 'Pagado' AND modalidad = 'Fin_De_Mes' AND es_post_corte = 0
    """, (cliente_id, tienda_id)).fetchall()
    
    subtotal_cap = sum(v["monto_total_lista"] for v in ventas_pendientes)
    total_int_comp = sum(v["total_intereses"] for v in ventas_pendientes)
    total_exigible = round(subtotal_cap + total_int_comp, 2)
    
    # Fecha de corte y pago del periodo
    partes = periodo.split("-")
    anio, mes = int(partes[0]), int(partes[1])
    dia_corte_val = min(cliente["dia_corte"], 28)
    dia_pago_val = min(cliente["dia_pago"], 28)
    f_corte = date(anio, mes, dia_corte_val)
    f_pago = date(anio, mes, dia_pago_val)
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO liquidaciones_corte (
                tienda_id, cliente_id, periodo_mes_anio, fecha_corte, fecha_pago_pactada,
                subtotal_capital, total_interes_compensatorio, total_interes_mora, total_exigible, estado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0.0, ?, 'Pendiente')
            ON CONFLICT(tienda_id, cliente_id, periodo_mes_anio) DO UPDATE SET
                subtotal_capital = excluded.subtotal_capital,
                total_interes_compensatorio = excluded.total_interes_compensatorio,
                total_exigible = excluded.total_exigible;
        """, (tienda_id, cliente_id, periodo, f_corte, f_pago, subtotal_cap, total_int_comp, total_exigible))
        conn.commit()
        flash(f"Listado de pago generado exitosamente para {cliente['nombres']} {cliente['apellidos']} ({periodo}). Total: S/ {total_exigible:,.2f}.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al generar listado de pago: {str(e)}", "danger")
    finally:
        conn.close()
    return redirect(url_for("liquidaciones"))

@app.route("/liquidaciones/<int:liq_id>/detalle")
@login_required
def liquidacion_detalle(liq_id):
    conn = get_db_connection()
    liq = conn.execute("""
        SELECT l.*, c.nombres || ' ' || c.apellidos as cliente_nombre, c.num_documento, c.direccion, c.telefono,
               c.tipo_tasa_comp, c.tasa_comp, c.tipo_tasa_mora, c.tasa_mora, t.nombre_comercial, t.ruc as tienda_ruc
        FROM liquidaciones_corte l
        JOIN clientes c ON l.cliente_id = c.id
        JOIN tiendas t ON l.tienda_id = t.id
        WHERE l.id = ?
    """, (liq_id,)).fetchone()
    
    if not liq:
        conn.close()
        flash("Liquidación no encontrada.", "danger")
        return redirect(url_for("liquidaciones"))
        
    # Evaluar si hoy hay días de mora
    fecha_pago_pactada = datetime.strptime(liq["fecha_pago_pactada"], "%Y-%m-%d").date()
    hoy = date.today()
    dias_mora = 0
    interes_mora = 0.0
    if hoy > fecha_pago_pactada and liq["estado"] != "Pagado":
        dias_mora = (hoy - fecha_pago_pactada).days
        ted_mora = convertir_a_ted(liq["tipo_tasa_mora"], liq["tasa_mora"])
        factor_mora = math.pow(1.0 + ted_mora, dias_mora) - 1.0
        interes_mora = round(liq["total_exigible"] * factor_mora, 2)
        
    total_con_mora = round(liq["total_exigible"] + interes_mora, 2)
    
    # Compras asociadas
    ventas = conn.execute("""
        SELECT v.* FROM ventas v
        WHERE v.cliente_id = ? AND v.tienda_id = ? AND v.fecha_compra <= ?
        ORDER BY v.fecha_compra ASC, v.hora_compra ASC
    """, (liq["cliente_id"], liq["tienda_id"], liq["fecha_corte"])).fetchall()
    
    conn.close()
    return render_template("settlement_detail.html", liq=liq, ventas=ventas, dias_mora=dias_mora, interes_mora=interes_mora, total_con_mora=total_con_mora)

# --- Caja y Cobranzas (Prelación de Pagos) ---
@app.route("/cobranzas", methods=["GET", "POST"])
@login_required
@role_required("admin_tienda")
def cobranzas():
    tienda_id = session.get("tienda_id")
    conn = get_db_connection()
    
    if request.method == "POST":
        liq_id = int(request.form.get("liquidacion_id"))
        monto_pagado = float(request.form.get("monto_pagado", 0.0))
        fecha_pago_str = request.form.get("fecha_pago", datetime.now().strftime("%Y-%m-%d"))
        
        liq = conn.execute("SELECT * FROM liquidaciones_corte WHERE id = ? AND tienda_id = ?", (liq_id, tienda_id)).fetchone()
        if not liq:
            flash("Liquidación no válida.", "danger")
            conn.close()
            return redirect(url_for("cobranzas"))
            
        cliente = conn.execute("SELECT * FROM clientes WHERE id = ?", (liq["cliente_id"],)).fetchone()
        
        # Calcular mora si aplica a la fecha de pago real
        f_pactada = datetime.strptime(liq["fecha_pago_pactada"], "%Y-%m-%d").date()
        f_real = datetime.strptime(fecha_pago_str, "%Y-%m-%d").date()
        dias_mora = max(0, (f_real - f_pactada).days)
        
        ted_mora = convertir_a_ted(cliente["tipo_tasa_mora"], cliente["tasa_mora"])
        int_mora = 0.0
        if dias_mora > 0:
            int_mora = round(liq["total_exigible"] * (math.pow(1.0 + ted_mora, dias_mora) - 1.0), 2)
            
        total_a_liquidar = round(liq["total_exigible"] + int_mora, 2)
        
        # REGLA DEL ENUNCIADO: NO SE PERMITEN PAGOS PARCIALES
        if abs(monto_pagado - total_a_liquidar) > 0.05:
            flash(f"POLÍTICA DE CRÉDITO: No se permiten pagos parciales. El importe a cancelar debe ser exactamente el total exigible liquidado: S/ {total_a_liquidar:,.2f}.", "warning")
            conn.close()
            return redirect(url_for("cobranzas"))
            
        # APLICAR ORDEN DE IMPUTACIÓN O PRELACIÓN (ANEXO A): 1° Mora, 2° Interés Compensatorio, 3° Capital
        imputacion = imputar_pago_segun_prelacion(
            monto_pago=monto_pagado,
            saldo_mora=int_mora,
            saldo_compensatorio=liq["total_interes_compensatorio"],
            saldo_capital=liq["subtotal_capital"]
        )
        
        # Generar comprobante
        count_p = conn.execute("SELECT COUNT(*) FROM pagos_abonos WHERE tienda_id = ?", (tienda_id,)).fetchone()[0]
        num_comp = f"REC-{tienda_id:02d}-{count_p + 1:06d}"
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO pagos_abonos (
                tienda_id, cliente_id, liquidacion_id, fecha_pago, monto_total_pagado,
                abono_mora, abono_compensatorio, abono_capital, num_comprobante, observaciones
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            tienda_id, liq["cliente_id"], liq_id, fecha_pago_str, monto_pagado,
            imputacion["abono_mora"], imputacion["abono_compensatorio"], imputacion["abono_capital"],
            num_comp, f"Pago con prelación: Mora S/{imputacion['abono_mora']}, Comp S/{imputacion['abono_compensatorio']}, Cap S/{imputacion['abono_capital']}"
        ))
        
        # Actualizar estado de la liquidación
        estado_liq = "Pagado_Con_Mora" if dias_mora > 0 else "Pagado"
        cursor.execute("""
            UPDATE liquidaciones_corte
            SET estado = ?, fecha_pago_real = ?, total_interes_mora = ?, dias_mora = ?
            WHERE id = ?;
        """, (estado_liq, fecha_pago_str, int_mora, dias_mora, liq_id))
        
        # Actualizar ventas asociadas a Pagadas
        cursor.execute("""
            UPDATE ventas
            SET estado = 'Pagado', saldo_pendiente = 0.0
            WHERE cliente_id = ? AND tienda_id = ? AND fecha_compra <= ?;
        """, (liq["cliente_id"], tienda_id, liq["fecha_corte"]))
        
        conn.commit()
        conn.close()
        
        flash(f"Cobro registrado con éxito (Comprobante {num_comp}). Prelación aplicada: Mora S/ {imputacion['abono_mora']:,.2f}, Interés S/ {imputacion['abono_compensatorio']:,.2f}, Capital S/ {imputacion['abono_capital']:,.2f}.", "success")
        return redirect(url_for("cobranzas"))
        
    # GET: Listado de cobros pendientes y últimos pagos
    liqs_pendientes = conn.execute("""
        SELECT l.*, c.nombres || ' ' || c.apellidos as cliente_nombre, c.num_documento, c.tipo_tasa_mora, c.tasa_mora
        FROM liquidaciones_corte l
        JOIN clientes c ON l.cliente_id = c.id
        WHERE l.tienda_id = ? AND l.estado != 'Pagado'
        ORDER BY l.fecha_pago_pactada ASC
    """, (tienda_id,)).fetchall()
    
    ultimos_pagos = conn.execute("""
        SELECT p.*, c.nombres || ' ' || c.apellidos as cliente_nombre
        FROM pagos_abonos p
        JOIN clientes c ON p.cliente_id = c.id
        WHERE p.tienda_id = ?
        ORDER BY p.fecha_registro DESC LIMIT 10
    """, (tienda_id,)).fetchall()
    conn.close()
    
    return render_template("payment.html", pendientes=liqs_pendientes, pagos=ultimos_pagos)

# -------------------------------------------------------------
# MÓDULO 3: PORTAL DEL CLIENTE (VECINO)
# -------------------------------------------------------------
@app.route("/mi-cuenta")
@login_required
def customer_portal():
    user_id = session.get("user_id")
    conn = get_db_connection()
    
    # Obtener el registro de cliente asociado
    cliente = conn.execute("""
        SELECT c.*, t.nombre_comercial as tienda_nombre, t.direccion as tienda_direccion, t.telefono as tienda_telefono
        FROM clientes c
        JOIN tiendas t ON c.tienda_id = t.id
        WHERE c.usuario_id = ?
    """, (user_id,)).fetchone()
    
    if not cliente:
        conn.close()
        flash("Usted no está registrado como cliente en ninguna tienda.", "info")
        return render_template("customer_portal.html", cliente=None)
        
    # Compras del cliente
    ventas = conn.execute("""
        SELECT v.* FROM ventas v
        WHERE v.cliente_id = ?
        ORDER BY v.fecha_compra DESC
    """, (cliente["id"],)).fetchall()
    
    # Cuotas activas en compras financiadas
    cuotas = conn.execute("""
        SELECT cq.*, v.num_ticket
        FROM cuotas_cronograma cq
        JOIN ventas v ON cq.venta_id = v.id
        WHERE v.cliente_id = ?
        ORDER BY cq.fecha_vencimiento ASC
    """, (cliente["id"],)).fetchall()
    
    # Liquidaciones emitidas
    liquidaciones = conn.execute("""
        SELECT * FROM liquidaciones_corte WHERE cliente_id = ? ORDER BY fecha_corte DESC
    """, (cliente["id"],)).fetchall()
    
    # Cálculos de balance
    deuda_total = sum(v["saldo_pendiente"] for v in ventas)
    credito_disponible = max(0.0, round(cliente["limite_credito"] - deuda_total, 2))
    
    conn.close()
    
    return render_template(
        "customer_portal.html",
        cliente=cliente,
        deuda_total=deuda_total,
        credito_disponible=credito_disponible,
        ventas=ventas,
        cuotas=cuotas,
        liquidaciones=liquidaciones
    )

# -------------------------------------------------------------
# MÓDULO 4: SIMULADOR FINANCIERO Y CALCULADORA
# -------------------------------------------------------------
@app.route("/simulador")
def simulator():
    return render_template("simulator.html")

# --- APIs AJAX para Cálculos en Tiempo Real ---
@app.route("/api/simular-frances", methods=["POST"])
def api_simular_frances():
    data = request.get_json() or {}
    try:
        capital = float(data.get("capital", 300.0))
        fecha_compra = data.get("fecha_compra", datetime.now().strftime("%Y-%m-%d"))
        fecha_corte = data.get("fecha_corte", (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"))
        dia_pago = data.get("primer_dia_pago", (datetime.now() + timedelta(days=11)).strftime("%Y-%m-%d"))
        cuotas = int(data.get("num_cuotas", 3))
        tipo_tasa = data.get("tipo_tasa", "TEA")
        tasa_val = float(data.get("valor_tasa", 24.0)) / 100.0
        cap_val = data.get("capitalizacion", "Diaria")
        cok_val = float(data.get("cok_anual", 15.0)) / 100.0
        
        resultado = calcular_metodo_frances_con_gracia(
            capital_inicial=capital,
            fecha_compra=fecha_compra,
            fecha_corte=fecha_corte,
            primer_dia_pago_pactado=dia_pago,
            num_cuotas=cuotas,
            tipo_tasa_comp=tipo_tasa,
            tasa_comp=tasa_val,
            cap_comp=cap_val,
            cok_anual=cok_val
        )
        return jsonify({"success": True, "data": resultado})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/simular-fin-de-mes", methods=["POST"])
def api_simular_fin_de_mes():
    data = request.get_json() or {}
    try:
        capital = float(data.get("capital", 100.0))
        fecha_compra = data.get("fecha_compra", datetime.now().strftime("%Y-%m-%d"))
        fecha_corte = data.get("fecha_corte", (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"))
        fecha_pago = data.get("fecha_pago_pactada", (datetime.now() + timedelta(days=11)).strftime("%Y-%m-%d"))
        tipo_tasa = data.get("tipo_tasa", "TEA")
        tasa_val = float(data.get("valor_tasa", 24.0)) / 100.0
        cap_val = data.get("capitalizacion", "Diaria")
        
        # Mora
        fecha_real = data.get("fecha_pago_real")
        tasa_mora = float(data.get("tasa_mora", 5.0)) / 100.0
        
        resultado = calcular_compra_fin_de_mes(
            capital=capital,
            fecha_compra=fecha_compra,
            fecha_corte=fecha_corte,
            fecha_pago_pactada=fecha_pago,
            tipo_tasa_comp=tipo_tasa,
            tasa_comp=tasa_val,
            cap_comp=cap_val,
            fecha_pago_real=fecha_real,
            tipo_tasa_mora="TEA",
            tasa_mora=tasa_mora
        )
        return jsonify({"success": True, "data": resultado})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/convertir-tasas", methods=["POST"])
def api_convertir_tasas():
    data = request.get_json() or {}
    try:
        tipo = data.get("tipo", "TEA")
        tasa = float(data.get("tasa", 24.0)) / 100.0
        cap = data.get("capitalizacion", "Diaria")
        
        ted = convertir_a_ted(tipo, tasa, cap)
        tem = convertir_a_tem(tipo, tasa, cap)
        tea_equiv = convertir_ted_a_tea(ted)
        
        return jsonify({
            "success": True,
            "ted": ted,
            "ted_pct": f"{ted * 100:.6f}%",
            "tem": tem,
            "tem_pct": f"{tem * 100:.4f}%",
            "tea_equivalente": tea_equiv,
            "tea_pct": f"{tea_equiv * 100:.4f}%"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

# Inicialización al arrancar
init_db()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
