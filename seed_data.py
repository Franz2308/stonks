# -*- coding: utf-8 -*-
"""
seed_data.py
Inserta datos iniciales de demostración para el sistema Stonks.
"""

from werkzeug.security import generate_password_hash
from database import get_db_connection
from financial_engine import calcular_metodo_frances_con_gracia, calcular_compra_fin_de_mes

def seed():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Limpiar tablas existentes en orden inverso de dependencias
    tablas = [
        "pagos_abonos", "liquidaciones_corte", "cuotas_cronograma", 
        "venta_detalles", "ventas", "clientes", "productos", "tiendas", "usuarios"
    ]
    for t in tablas:
        cursor.execute(f"DELETE FROM {t};")
        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{t}';")
        
    print("Tablas limpiadas. Creando usuarios iniciales...")
    
    # 1. Usuarios del sistema
    usuarios_data = [
        ("admin", generate_password_hash("admin123"), "Administrador del Sistema", "admin@stonks.pe", "999888777", "admin_sistema"),
        ("bodega_don_pepe", generate_password_hash("tienda123"), "José 'Don Pepe' Ramírez", "donpepe@bodega.pe", "987654321", "admin_tienda"),
        ("panaderia_espiga", generate_password_hash("espiga123"), "Rosa Gómez Salazar", "contacto@laespiga.pe", "987111222", "admin_tienda"),
        ("spa_belladonna", generate_password_hash("spa123"), "Carla Flores Benítez", "citas@belladonna.pe", "987333444", "admin_tienda"),
        ("cliente_juan", generate_password_hash("cliente123"), "Juan Pérez Gómez", "juan.perez@gmail.com", "981234567", "cliente"),
        ("cliente_maria", generate_password_hash("cliente123"), "María Rodríguez Silva", "maria.rodriguez@gmail.com", "982345678", "cliente"),
        ("cliente_carlos", generate_password_hash("cliente123"), "Carlos Mendoza López", "carlos.mendoza@gmail.com", "983456789", "cliente")
    ]
    
    for u in usuarios_data:
        cursor.execute("""
            INSERT INTO usuarios (username, password_hash, nombre_completo, email, telefono, rol)
            VALUES (?, ?, ?, ?, ?, ?);
        """, u)
        
    admin_pepe_id = cursor.execute("SELECT id FROM usuarios WHERE username='bodega_don_pepe'").fetchone()[0]
    admin_espiga_id = cursor.execute("SELECT id FROM usuarios WHERE username='panaderia_espiga'").fetchone()[0]
    admin_spa_id = cursor.execute("SELECT id FROM usuarios WHERE username='spa_belladonna'").fetchone()[0]
    
    user_juan_id = cursor.execute("SELECT id FROM usuarios WHERE username='cliente_juan'").fetchone()[0]
    user_maria_id = cursor.execute("SELECT id FROM usuarios WHERE username='cliente_maria'").fetchone()[0]
    user_carlos_id = cursor.execute("SELECT id FROM usuarios WHERE username='cliente_carlos'").fetchone()[0]
    
    # 2. Tiendas
    print("Creando tiendas comerciales...")
    tiendas_data = [
        (admin_pepe_id, "Bodega y Abarrotes Don Pepe S.A.C.", "Bodega Don Pepe", "10458923411", "Bodega", "Jr. Los Olivos 245, San Miguel", "987654321", "donpepe@bodega.pe"),
        (admin_espiga_id, "Panadería y Pastelería La Espiga E.I.R.L.", "Panadería La Espiga", "20601234567", "Panadería", "Av. San Martín 890, Pueblo Libre", "987111222", "contacto@laespiga.pe"),
        (admin_spa_id, "Bella Donna Salón & Spa E.I.R.L.", "Spa Bella Donna", "10256789123", "Peluquería / Spa", "Calle Las Begonias 312, Jesús María", "987333444", "citas@belladonna.pe")
    ]
    
    for t in tiendas_data:
        cursor.execute("""
            INSERT INTO tiendas (admin_usuario_id, razon_social, nombre_comercial, ruc, giro, direccion, telefono, correo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, t)
        
    tienda_pepe_id = cursor.execute("SELECT id FROM tiendas WHERE nombre_comercial='Bodega Don Pepe'").fetchone()[0]
    tienda_espiga_id = cursor.execute("SELECT id FROM tiendas WHERE nombre_comercial='Panadería La Espiga'").fetchone()[0]
    
    # 3. Productos para Bodega Don Pepe
    print("Registrando catálogo de productos...")
    productos_pepe = [
        (tienda_pepe_id, "PROD-001", "Leche Evaporada Gloria Azul 400g", "Gloria", "Distribuidora Lima", "Lata", 4.20, 4.50, "Ambas", "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=200"),
        (tienda_pepe_id, "PROD-002", "Arroz Costeño Extra 1kg", "Costeño", "Costeño Alimentos", "Bolsa", 4.80, 5.20, "Ambas", "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=200"),
        (tienda_pepe_id, "PROD-003", "Aceite Vegetal Primor Clásico 1L", "Primor", "Alicorp", "Botella", 8.50, 9.20, "Ambas", "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=200"),
        (tienda_pepe_id, "PROD-004", "Azúcar Rubia Cartavio 1kg", "Cartavio", "Cartavio S.A.", "Bolsa", 3.80, 4.20, "Solo_Fin_De_Mes", "https://images.unsplash.com/photo-1622484214472-e1d1e4cfb06b?w=200"),
        (tienda_pepe_id, "PROD-005", "Detergente Ariel Doble Poder 1kg", "Ariel", "P&G", "Bolsa", 11.00, 12.00, "Ambas", "https://images.unsplash.com/photo-1583947215259-38e31be8751f?w=200"),
        (tienda_pepe_id, "PROD-006", "Cerveza Cusqueña Trigo Six Pack", "Cusqueña", "Backus", "Pack", 32.00, 36.00, "Solo_Fin_De_Mes", "https://images.unsplash.com/photo-1608270191871-331e84d436a1?w=200"),
        (tienda_pepe_id, "PROD-007", "Canasta Básica Familiar Familiar Quincenal", "Varios", "Bodega Don Pepe", "Paquete", 150.00, 165.00, "Solo_Cuotas", "https://images.unsplash.com/photo-1542838132-92c53300491e?w=200"),
        (tienda_pepe_id, "PROD-008", "Saco de Arroz Paisana Superior 50kg", "Paisana", "Agroindustrias", "Saco", 180.00, 200.00, "Solo_Cuotas", "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=200")
    ]
    for p in productos_pepe:
        cursor.execute("""
            INSERT INTO productos (tienda_id, codigo, descripcion, marca, proveedor, unidad_medida, precio_contado, precio_lista, modalidad_permitida, imagen_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, p)
        
    # 4. Clientes de Bodega Don Pepe
    print("Registrando clientes y políticas de crédito...")
    clientes_pepe = [
        # (tienda_id, usuario_id, tipo_doc, num_doc, nombres, apellidos, dir, tel, correo, mon, limite, plazo, corte, pago, tipo_comp, tasa_comp, cap_comp, tipo_mora, tasa_mora, cap_mora, cok)
        (tienda_pepe_id, user_juan_id, "DNI", "45891234", "Juan", "Pérez Gómez", "Calle Los Sauces 142, San Miguel", "981234567", "juan.perez@gmail.com", "PEN", 800.0, 6, 20, 26, "TEA", 0.24, "Diaria", "TEA", 0.05, "Diaria", 0.15),
        (tienda_pepe_id, user_maria_id, "DNI", "72345678", "María", "Rodríguez Silva", "Av. La Paz 650 Dpto 302, San Miguel", "982345678", "maria.rodriguez@gmail.com", "PEN", 500.0, 3, 20, 26, "TNA", 0.22, "Diaria", "TEA", 0.05, "Diaria", 0.15),
        (tienda_pepe_id, user_carlos_id, "DNI", "10234567", "Carlos", "Mendoza López", "Pasaje San Lorenzo 118, San Miguel", "983456789", "carlos.mendoza@gmail.com", "PEN", 1200.0, 12, 15, 22, "TEA", 0.26, "Diaria", "TEA", 0.06, "Diaria", 0.15)
    ]
    for c in clientes_pepe:
        cursor.execute("""
            INSERT INTO clientes (tienda_id, usuario_id, tipo_documento, num_documento, nombres, apellidos, direccion, telefono, correo, moneda, limite_credito, plazo_maximo_meses, dia_corte, dia_pago, tipo_tasa_comp, tasa_comp, cap_comp, tipo_tasa_mora, tasa_mora, cap_mora, cok_anual)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, c)
        
    cliente_juan_id = cursor.execute("SELECT id FROM clientes WHERE num_documento='45891234'").fetchone()[0]
    cliente_maria_id = cursor.execute("SELECT id FROM clientes WHERE num_documento='72345678'").fetchone()[0]
    
    # 5. Ventas de Demostración
    print("Generando ventas a crédito con cálculo financiero exacto...")
    
    # Caso A: El ejemplo exacto del enunciado del curso:
    # "si se indica, por ejemplo 3 meses y su fecha de pago son los 26 de cada mes y si la compra se realizara el 15 de setiembre, 
    # que es anterior a la fecha de corte (que la fecha de corte sea por ejemplo el 20 de setiembre) se deberá tomar en cuenta 
    # que desde el 15 hasta el día 26 de setiembre existen 11 días de período de gracia total y por tanto la deuda deberá ser 
    # capitalizada antes de calcular la cuota mensual, por ejemplo si es a 3 meses, comenzando en el siguientes mes, o sea por el 26 de octubre, 
    # luego el 26 de noviembre y finalmente el 26 de diciembre."
    calc_frances = calcular_metodo_frances_con_gracia(
        capital_inicial=300.0,
        fecha_compra="2026-09-15",
        fecha_corte="2026-09-20",
        primer_dia_pago_pactado="2026-09-26",
        num_cuotas=3,
        tipo_tasa_comp="TEA",
        tasa_comp=0.24,
        cok_anual=0.15
    )
    
    cursor.execute("""
        INSERT INTO ventas (
            tienda_id, cliente_id, num_ticket, fecha_compra, hora_compra, modalidad, num_cuotas,
            monto_total_lista, interes_gracia, capital_financiado, cuota_mensual, total_intereses,
            total_a_pagar, saldo_pendiente, estado, es_post_corte, fecha_corte_aplicada, fecha_pago_pactada
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        tienda_pepe_id, cliente_juan_id, "TKT-000101", "2026-09-15", "10:30:00", "Cuotas", 3,
        300.0, calc_frances["interes_gracia"], calc_frances["capital_capitalizado"],
        calc_frances["cuota_mensual_fija"], calc_frances["total_intereses"],
        calc_frances["total_a_pagar"], calc_frances["total_a_pagar"], "Pendiente", 0, "2026-09-20", "2026-09-26"
    ))
    venta_cuotas_id = cursor.lastrowid
    
    # Detalle de cuotas francesas
    for cuota in calc_frances["cronograma"]:
        cursor.execute("""
            INSERT INTO cuotas_cronograma (
                venta_id, numero_cuota, fecha_vencimiento, saldo_inicial, cuota, interes, amortizacion, saldo_final, estado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pendiente');
        """, (
            venta_cuotas_id, cuota["numero_cuota"], cuota["fecha_vencimiento"],
            cuota["saldo_inicial"], cuota["cuota"], cuota["interes"], cuota["amortizacion"], cuota["saldo_final"]
        ))
        
    # Caso B: Compra a fin de mes (un solo pago) antes de corte
    # Compra 12 de setiembre, corte 20 de setiembre, pago 26 de setiembre.
    calc_mes = calcular_compra_fin_de_mes(
        capital=85.0,
        fecha_compra="2026-09-12",
        fecha_corte="2026-09-20",
        fecha_pago_pactada="2026-09-26",
        tipo_tasa_comp="TEA",
        tasa_comp=0.24
    )
    cursor.execute("""
        INSERT INTO ventas (
            tienda_id, cliente_id, num_ticket, fecha_compra, hora_compra, modalidad, num_cuotas,
            monto_total_lista, interes_gracia, capital_financiado, cuota_mensual, total_intereses,
            total_a_pagar, saldo_pendiente, estado, es_post_corte, fecha_corte_aplicada, fecha_pago_pactada
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        tienda_pepe_id, cliente_juan_id, "TKT-000102", "2026-09-12", "16:45:00", "Fin_De_Mes", 1,
        85.0, 0.0, 85.0, calc_mes["total_pactado"], calc_mes["interes_compensatorio"],
        calc_mes["total_pactado"], calc_mes["total_pactado"], "Pendiente", 0, "2026-09-20", "2026-09-26"
    ))
    
    # Caso C: Compra POST-CORTE (numeral 5 del enunciado: obligación de pago pasa al mes siguiente)
    # Compra 22 de setiembre (posterior al corte del día 20) -> pasa al 26 de octubre.
    calc_post = calcular_compra_fin_de_mes(
        capital=54.0,
        fecha_compra="2026-09-22",
        fecha_corte="2026-09-20",
        fecha_pago_pactada="2026-09-26",
        tipo_tasa_comp="TEA",
        tasa_comp=0.24
    )
    cursor.execute("""
        INSERT INTO ventas (
            tienda_id, cliente_id, num_ticket, fecha_compra, hora_compra, modalidad, num_cuotas,
            monto_total_lista, interes_gracia, capital_financiado, cuota_mensual, total_intereses,
            total_a_pagar, saldo_pendiente, estado, es_post_corte, fecha_corte_aplicada, fecha_pago_pactada
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        tienda_pepe_id, cliente_juan_id, "TKT-000103", "2026-09-22", "11:15:00", "Fin_De_Mes", 1,
        54.0, 0.0, 54.0, calc_post["total_pactado"], calc_post["interes_compensatorio"],
        calc_post["total_pactado"], calc_post["total_pactado"], "Pendiente", 1, "2026-10-20", calc_post["fecha_pago_pactada"]
    ))
    
    # 6. Generación de Liquidación de Corte (Listado de Pago para Juan Pérez - Setiembre 2026)
    # Suma de compras de fin de mes pre-corte (TKT-102 = 85.0 + 0.72)
    cursor.execute("""
        INSERT INTO liquidaciones_corte (
            tienda_id, cliente_id, periodo_mes_anio, fecha_corte, fecha_pago_pactada,
            subtotal_capital, total_interes_compensatorio, total_interes_mora, total_exigible, estado
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        tienda_pepe_id, cliente_juan_id, "2026-09", "2026-09-20", "2026-09-26",
        85.0, calc_mes["interes_compensatorio"], 0.0, calc_mes["total_pactado"], "Pendiente"
    ))
    
    conn.commit()
    conn.close()
    print("Seed data completada con éxito.")

if __name__ == "__main__":
    seed()
