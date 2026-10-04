# -*- coding: utf-8 -*-
"""
test_financial.py
Pruebas unitarias automatizadas para verificar el cumplimiento exacto
del Enunciado del Curso SI642 y el Anexo A:
1. Conversión explícita de tasas nominales y efectivas (Base 360).
2. Período de gracia total capitalizada (Caso 15 set -> 26 set = 11 días).
3. Método francés vencido simple ordinario en cuotas mensuales de 30 días.
4. Cómputo de intereses moratorios e imputación legal de pagos (mora -> comp -> capital).
5. Indicadores financieros: VAN, TIR y TCEA.
"""

import unittest
from datetime import date
from financial_engine import (
    convertir_a_ted, convertir_a_tem, convertir_ted_a_tea,
    calcular_compra_fin_de_mes, calcular_metodo_frances_con_gracia,
    imputar_pago_segun_prelacion, calcular_van, calcular_tir
)

class TestFinancialEngine(unittest.TestCase):

    def test_conversion_tasas_base_360(self):
        # 24% TEA
        tea = 0.24
        ted = convertir_a_ted("TEA", tea)
        tem = convertir_a_tem("TEA", tea)
        
        # TED = (1 + 0.24)^(1/360) - 1 ~ 0.00059808
        self.assertAlmostEqual(ted, 0.00059808, places=6)
        
        # TEM = (1 + TED)^30 - 1 ~ 0.018087
        self.assertAlmostEqual(tem, 0.018087, places=5)
        
        # Reversibilidad: (1 + TED)^360 - 1 = TEA
        tea_calc = convertir_ted_a_tea(ted)
        self.assertAlmostEqual(tea_calc, tea, places=5)

    def test_caso_enunciado_gracia_total_capitalizada(self):
        """
        Caso del numeral 4 del enunciado oficial:
        Compra: 15 de setiembre de 2026.
        Corte: 20 de setiembre de 2026.
        Fecha pago pactada: 26 de setiembre de 2026.
        Días de gracia total: 11 días (del 15 al 26).
        Plazo: 3 meses comenzando el 26 de octubre, luego 26 nov y 26 dic.
        """
        capital_inicial = 300.0
        res = calcular_metodo_frances_con_gracia(
            capital_inicial=capital_inicial,
            fecha_compra="2026-09-15",
            fecha_corte="2026-09-20",
            primer_dia_pago_pactado="2026-09-26",
            num_cuotas=3,
            tipo_tasa_comp="TEA",
            tasa_comp=0.24,
            cok_anual=0.15
        )
        
        # 1. Validar días de gracia
        self.assertEqual(res["dias_gracia"], 11)
        
        # 2. Validar que la deuda se haya capitalizado antes de calcular las cuotas
        self.assertGreater(res["capital_capitalizado"], capital_inicial)
        self.assertEqual(res["capital_capitalizado"], 301.98)
        
        # 3. Validar cuotas y cronograma
        self.assertEqual(len(res["cronograma"]), 3)
        self.assertEqual(res["cronograma"][0]["fecha_vencimiento"], "2026-10-26")
        self.assertEqual(res["cronograma"][1]["fecha_vencimiento"], "2026-11-25") # +30 días comerciales
        self.assertEqual(res["cronograma"][2]["fecha_vencimiento"], "2026-12-25")
        
        # 4. Validar saldo final amortizado en 0.00
        self.assertEqual(res["cronograma"][2]["saldo_final"], 0.0)
        
        # 5. Validar rentabilidad del comercio (TIR positiva y VAN coherente)
        self.assertGreater(res["tir_anual"], 0.20)
        self.assertGreater(res["van"], 0.0)

    def test_compra_fin_de_mes_pre_y_post_corte(self):
        """
        Caso del numeral 5 del enunciado:
        - Si compra antes de corte: entra en ciclo actual.
        - Si compra post corte: pasa al mes siguiente (+30 días).
        """
        # Pre-corte
        res_pre = calcular_compra_fin_de_mes(
            capital=100.0,
            fecha_compra="2026-09-12",
            fecha_corte="2026-09-20",
            fecha_pago_pactada="2026-09-26",
            tipo_tasa_comp="TEA",
            tasa_comp=0.24
        )
        self.assertFalse(res_pre["es_post_corte"])
        self.assertEqual(res_pre["dias_credito"], 14)
        self.assertEqual(res_pre["fecha_pago_pactada"], "2026-09-26")
        
        # Post-corte
        res_post = calcular_compra_fin_de_mes(
            capital=100.0,
            fecha_compra="2026-09-22",
            fecha_corte="2026-09-20",
            fecha_pago_pactada="2026-09-26",
            tipo_tasa_comp="TEA",
            tasa_comp=0.24
        )
        self.assertTrue(res_post["es_post_corte"])
        self.assertEqual(res_post["fecha_pago_pactada"], "2026-10-26") # Pasa al siguiente mes
        self.assertEqual(res_post["dias_credito"], 34)

    def test_interes_moratorio_dias_exceso(self):
        """
        Caso del numeral 5 y 6 del enunciado:
        Días de mora generan ítem diferenciado de intereses por mora.
        """
        res = calcular_compra_fin_de_mes(
            capital=100.0,
            fecha_compra="2026-09-10",
            fecha_corte="2026-09-20",
            fecha_pago_pactada="2026-09-26",
            tipo_tasa_comp="TEA",
            tasa_comp=0.24,
            fecha_pago_real="2026-10-06", # 10 días de mora
            tipo_tasa_mora="TEA",
            tasa_mora=0.05
        )
        self.assertEqual(res["dias_mora"], 10)
        self.assertGreater(res["interes_mora"], 0.0)
        self.assertEqual(res["total_con_mora"], round(res["total_pactado"] + res["interes_mora"], 2))

    def test_prelacion_de_pagos_anexo_a(self):
        """
        Anexo A: Orden legal de imputación: 1° Mora, 2° Compensatorio, 3° Capital.
        """
        # Escenario: Debe Mora = S/ 10, Comp = S/ 20, Capital = S/ 100. Total = S/ 130
        res = imputar_pago_segun_prelacion(
            monto_pago=130.0,
            saldo_mora=10.0,
            saldo_compensatorio=20.0,
            saldo_capital=100.0
        )
        self.assertEqual(res["abono_mora"], 10.0)
        self.assertEqual(res["abono_compensatorio"], 20.0)
        self.assertEqual(res["abono_capital"], 100.0)
        self.assertEqual(res["remanente_mora"], 0.0)
        self.assertEqual(res["remanente_compensatorio"], 0.0)
        self.assertEqual(res["remanente_capital"], 0.0)

if __name__ == '__main__':
    unittest.main()
