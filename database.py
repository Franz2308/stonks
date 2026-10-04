# -*- coding: utf-8 -*-
"""
database.py
Capa de persistencia con SQLite3 para la plataforma Stonks.
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "stonks.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Usuarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        nombre_completo TEXT NOT NULL,
        email TEXT NOT NULL,
        telefono TEXT,
        rol TEXT NOT NULL CHECK(rol IN ('admin_sistema', 'admin_tienda', 'cliente')),
        activo INTEGER DEFAULT 1,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 2. Tiendas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tiendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_usuario_id INTEGER NOT NULL,
        razon_social TEXT NOT NULL,
        nombre_comercial TEXT NOT NULL,
        ruc TEXT UNIQUE NOT NULL,
        giro TEXT NOT NULL,
        direccion TEXT NOT NULL,
        telefono TEXT NOT NULL,
        correo TEXT,
        moneda_principal TEXT DEFAULT 'PEN',
        activa INTEGER DEFAULT 1,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (admin_usuario_id) REFERENCES usuarios (id)
    );
    """)
    
    # 3. Productos / Servicios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tienda_id INTEGER NOT NULL,
        codigo TEXT NOT NULL,
        descripcion TEXT NOT NULL,
        marca TEXT DEFAULT 'Genérico',
        proveedor TEXT DEFAULT 'Elaboración propia',
        unidad_medida TEXT DEFAULT 'Unidad',
        precio_contado REAL NOT NULL,
        precio_lista REAL NOT NULL,
        modalidad_permitida TEXT DEFAULT 'Ambas' CHECK(modalidad_permitida IN ('Solo_Fin_De_Mes', 'Solo_Cuotas', 'Ambas')),
        imagen_url TEXT,
        activo INTEGER DEFAULT 1,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (tienda_id) REFERENCES tiendas (id)
    );
    """)
    
    # 4. Clientes de la tienda
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tienda_id INTEGER NOT NULL,
        usuario_id INTEGER,
        tipo_documento TEXT DEFAULT 'DNI',
        num_documento TEXT NOT NULL,
        nombres TEXT NOT NULL,
        apellidos TEXT NOT NULL,
        direccion TEXT NOT NULL,
        telefono TEXT NOT NULL,
        correo TEXT,
        moneda TEXT DEFAULT 'PEN' CHECK(moneda IN ('PEN', 'USD')),
        limite_credito REAL NOT NULL DEFAULT 500.0,
        plazo_maximo_meses INTEGER NOT NULL DEFAULT 6,
        dia_corte INTEGER NOT NULL DEFAULT 20,
        dia_pago INTEGER NOT NULL DEFAULT 26,
        tipo_tasa_comp TEXT DEFAULT 'TEA' CHECK(tipo_tasa_comp IN ('TEA', 'TNA')),
        tasa_comp REAL NOT NULL DEFAULT 0.24,
        cap_comp TEXT DEFAULT 'Diaria',
        tipo_tasa_mora TEXT DEFAULT 'TEA' CHECK(tipo_tasa_mora IN ('TEA', 'TNA')),
        tasa_mora REAL NOT NULL DEFAULT 0.05,
        cap_mora TEXT DEFAULT 'Diaria',
        cok_anual REAL NOT NULL DEFAULT 0.15,
        activo INTEGER DEFAULT 1,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (tienda_id) REFERENCES tiendas (id),
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
        UNIQUE(tienda_id, num_documento)
    );
    """)
    
    # 5. Ventas a Crédito
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tienda_id INTEGER NOT NULL,
        cliente_id INTEGER NOT NULL,
        num_ticket TEXT UNIQUE NOT NULL,
        fecha_compra DATE NOT NULL,
        hora_compra TIME NOT NULL,
        modalidad TEXT NOT NULL CHECK(modalidad IN ('Fin_De_Mes', 'Cuotas')),
        num_cuotas INTEGER DEFAULT 1,
        monto_total_lista REAL NOT NULL,
        interes_gracia REAL DEFAULT 0.0,
        capital_financiado REAL NOT NULL,
        cuota_mensual REAL DEFAULT 0.0,
        total_intereses REAL DEFAULT 0.0,
        total_a_pagar REAL NOT NULL,
        saldo_pendiente REAL NOT NULL,
        estado TEXT DEFAULT 'Pendiente' CHECK(estado IN ('Pendiente', 'Pagado', 'En_Mora')),
        es_post_corte INTEGER DEFAULT 0,
        fecha_corte_aplicada DATE,
        fecha_pago_pactada DATE,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (tienda_id) REFERENCES tiendas (id),
        FOREIGN KEY (cliente_id) REFERENCES clientes (id)
    );
    """)
    
    # 6. Detalles de Venta
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS venta_detalles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venta_id INTEGER NOT NULL,
        producto_id INTEGER NOT NULL,
        cantidad REAL NOT NULL,
        precio_unitario REAL NOT NULL,
        subtotal REAL NOT NULL,
        FOREIGN KEY (venta_id) REFERENCES ventas (id),
        FOREIGN KEY (producto_id) REFERENCES productos (id)
    );
    """)
    
    # 7. Cronograma de Cuotas (Método Francés)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cuotas_cronograma (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venta_id INTEGER NOT NULL,
        numero_cuota INTEGER NOT NULL,
        fecha_vencimiento DATE NOT NULL,
        saldo_inicial REAL NOT NULL,
        cuota REAL NOT NULL,
        interes REAL NOT NULL,
        amortizacion REAL NOT NULL,
        saldo_final REAL NOT NULL,
        mora_acumulada REAL DEFAULT 0.0,
        estado TEXT DEFAULT 'Pendiente' CHECK(estado IN ('Pendiente', 'Pagada', 'En_Mora')),
        fecha_pago_real DATE,
        FOREIGN KEY (venta_id) REFERENCES ventas (id)
    );
    """)
    
    # 8. Liquidaciones de Corte (Listado de Pago Mensual)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS liquidaciones_corte (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tienda_id INTEGER NOT NULL,
        cliente_id INTEGER NOT NULL,
        periodo_mes_anio TEXT NOT NULL,
        fecha_corte DATE NOT NULL,
        fecha_pago_pactada DATE NOT NULL,
        subtotal_capital REAL NOT NULL,
        total_interes_compensatorio REAL NOT NULL,
        total_interes_mora REAL DEFAULT 0.0,
        total_exigible REAL NOT NULL,
        dias_mora INTEGER DEFAULT 0,
        estado TEXT DEFAULT 'Pendiente' CHECK(estado IN ('Pendiente', 'Pagado', 'En_Mora')),
        fecha_pago_real DATE,
        fecha_emision TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (tienda_id) REFERENCES tiendas (id),
        FOREIGN KEY (cliente_id) REFERENCES clientes (id),
        UNIQUE(tienda_id, cliente_id, periodo_mes_anio)
    );
    """)
    
    # 9. Pagos y Cobranzas (con Prelación)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pagos_abonos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tienda_id INTEGER NOT NULL,
        cliente_id INTEGER NOT NULL,
        liquidacion_id INTEGER,
        venta_id INTEGER,
        fecha_pago DATE NOT NULL,
        monto_total_pagado REAL NOT NULL,
        abono_mora REAL DEFAULT 0.0,
        abono_compensatorio REAL DEFAULT 0.0,
        abono_capital REAL DEFAULT 0.0,
        num_comprobante TEXT UNIQUE NOT NULL,
        observaciones TEXT,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (tienda_id) REFERENCES tiendas (id),
        FOREIGN KEY (cliente_id) REFERENCES clientes (id),
        FOREIGN KEY (liquidacion_id) REFERENCES liquidaciones_corte (id),
        FOREIGN KEY (venta_id) REFERENCES ventas (id)
    );
    """)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Base de datos SQLite inicializada exitosamente.")
