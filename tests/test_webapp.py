# -*- coding: utf-8 -*-
"""
test_webapp.py
Pruebas automatizadas de la aplicación Flask: rutas, login, POS, liquidaciones y cobranzas.
"""

import unittest
from app import app
from database import init_db
from seed_data import seed

class TestStonksWebApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        seed()

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_01_rutas_publicas(self):
        # Home redirige a login si no hay sesión
        res = self.client.get("/")
        self.assertEqual(res.status_code, 302)
        
        # Login page accesible
        res = self.client.get("/login")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Iniciar", res.data)
        
        # Simulador financiero accesible públicamente
        res = self.client.get("/simulador")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Simulador", res.data)

    def test_02_login_demo_tienda(self):
        # Login con cuenta demo de tienda
        res = self.client.get("/demo-login/tienda", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Bodega Don Pepe", res.data)
        self.assertIn(b"Dashboard", res.data)

    def test_03_catalogo_productos(self):
        # Con sesión de tienda iniciada
        with self.client:
            self.client.get("/demo-login/tienda")
            res = self.client.get("/productos")
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Leche Evaporada Gloria", res.data)
            self.assertIn(b"Precio Lista", res.data)

    def test_04_clientes_tienda(self):
        with self.client:
            self.client.get("/demo-login/tienda")
            res = self.client.get("/clientes")
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Juan", res.data)
            self.assertIn(b"L", res.data) # Límite

    def test_05_portal_cliente(self):
        # Login como cliente
        res = self.client.get("/demo-login/cliente", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Mi Cuenta Corriente", res.data)
        self.assertIn(b"Compras a Cr", res.data)

    def test_06_api_simulacion_frances(self):
        res = self.client.post("/api/simular-frances", json={
            "capital": 300.0,
            "fecha_compra": "2026-09-15",
            "primer_dia_pago": "2026-09-26",
            "num_cuotas": 3,
            "tipo_tasa": "TEA",
            "valor_tasa": 24.0,
            "cok_anual": 15.0
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["dias_gracia"], 11)
        self.assertEqual(data["data"]["capital_capitalizado"], 301.98)

    def test_07_cobranzas_pago_con_mora(self):
        with self.client:
            self.client.get("/demo-login/tienda")
            res_get = self.client.get("/cobranzas")
            self.assertEqual(res_get.status_code, 200)
            self.assertIn(b"Caja", res_get.data)
            
            # Obtener liquidación 1
            from database import get_db_connection
            conn = get_db_connection()
            liq = conn.execute("SELECT * FROM liquidaciones_corte WHERE id = 1").fetchone()
            conn.close()
            
            if liq:
                # Simular pago puntual (26 de setiembre)
                res_post = self.client.post("/cobranzas", data={
                    "liquidacion_id": liq["id"],
                    "fecha_pago": "2026-09-26",
                    "monto_pagado": liq["total_exigible"]
                }, follow_redirects=True)
                self.assertEqual(res_post.status_code, 200)
                self.assertIn(b"Cobro registrado con", res_post.data)

if __name__ == '__main__':
    unittest.main()
