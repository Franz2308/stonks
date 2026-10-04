# -*- coding: utf-8 -*-
"""
financial_engine.py
Módulo de cálculo financiero para el sistema de control de cuenta corriente comercial.
Cumple con las directrices del curso SI642 y el Anexo A:
- Base de días: 360, mes comercial de 30 días.
- Conversión explícita entre tasas nominales y efectivas.
- Método francés vencido simple ordinario con capitalización de periodo de gracia total.
- Cálculo de intereses moratorios e imputación legal de pagos (mora -> compensatorio -> capital).
- Evaluación financiera: VAN, TIR y TCEA.
- Redondeo monetario a 2 decimales y tasas con precisión de al menos 7 decimales.
"""

import math
from datetime import datetime, date, timedelta

BASE_DIAS_ANUAL = 360
DIAS_MES_COMERCIAL = 30
DECIMALES_MONEDA = 2
DECIMALES_TASA = 8

def convertir_a_ted(tipo_tasa, valor_tasa_anual, capitalizacion="Diaria"):
    """
    Convierte una tasa anual (nominal o efectiva) a Tasa Efectiva Diaria (TED) base 360.
    valor_tasa_anual: decimal (ej. 0.24 para 24%)
    """
    tasa = float(valor_tasa_anual)
    tipo = str(tipo_tasa).upper().strip()
    
    if tipo in ["TEA", "EFECTIVA"]:
        # TED = (1 + TEA)^(1/360) - 1
        ted = math.pow(1.0 + tasa, 1.0 / BASE_DIAS_ANUAL) - 1.0
    elif tipo in ["TNA", "NOMINAL"]:
        cap = str(capitalizacion).lower().strip()
        if "diaria" in cap or cap == "360":
            # Si capitaliza diario: TED = TNA / 360
            ted = tasa / BASE_DIAS_ANUAL
        elif "mensual" in cap or cap == "12":
            # TNA capitalizable mensualmente: TEM = TNA / 12, TED = (1 + TEM)^(1/30) - 1
            tem = tasa / 12.0
            ted = math.pow(1.0 + tem, 1.0 / DIAS_MES_COMERCIAL) - 1.0
        elif "semestral" in cap or cap == "2":
            tes = tasa / 2.0
            ted = math.pow(1.0 + tes, 1.0 / 180.0) - 1.0
        elif "trimestral" in cap or cap == "4":
            tet = tasa / 4.0
            ted = math.pow(1.0 + tet, 1.0 / 90.0) - 1.0
        else:
            ted = tasa / BASE_DIAS_ANUAL
    else:
        ted = math.pow(1.0 + tasa, 1.0 / BASE_DIAS_ANUAL) - 1.0
        
    return round(ted, DECIMALES_TASA)

def convertir_a_tem(tipo_tasa, valor_tasa_anual, capitalizacion="Diaria"):
    """
    Convierte una tasa anual a Tasa Efectiva Mensual (TEM) para mes comercial de 30 días.
    """
    ted = convertir_a_ted(tipo_tasa, valor_tasa_anual, capitalizacion)
    # TEM = (1 + TED)^30 - 1
    tem = math.pow(1.0 + ted, DIAS_MES_COMERCIAL) - 1.0
    return round(tem, DECIMALES_TASA)

def convertir_ted_a_tea(ted):
    """
    Convierte una TED a TEA anual: TEA = (1 + TED)^360 - 1
    """
    tea = math.pow(1.0 + float(ted), BASE_DIAS_ANUAL) - 1.0
    return round(tea, DECIMALES_TASA)

def calcular_compra_fin_de_mes(capital, fecha_compra, fecha_corte, fecha_pago_pactada, 
                               tipo_tasa_comp, tasa_comp, cap_comp="Diaria",
                               fecha_pago_real=None, tipo_tasa_mora="TEA", tasa_mora=0.05, cap_mora="Diaria"):
    """
    Calcula los intereses de una compra realizada para pagar a fin de mes / fecha de corte.
    Regla del enunciado:
    - Si se realiza antes/hasta fecha de corte: se paga en la fecha de pago pactada del ciclo.
    - Si se realiza después de fecha de corte: su obligación pasa al ciclo siguiente (+30 días).
    - Se cobran intereses por los días transcurridos entre fecha de compra y fecha de pago pactada.
    - Si se paga después de fecha pactada (mora), se cobran intereses moratorios por los días en exceso.
    """
    if isinstance(fecha_compra, str):
        fecha_compra = datetime.strptime(fecha_compra, "%Y-%m-%d").date()
    if isinstance(fecha_corte, str):
        fecha_corte = datetime.strptime(fecha_corte, "%Y-%m-%d").date()
    if isinstance(fecha_pago_pactada, str):
        fecha_pago_pactada = datetime.strptime(fecha_pago_pactada, "%Y-%m-%d").date()
    if fecha_pago_real and isinstance(fecha_pago_real, str):
        fecha_pago_real = datetime.strptime(fecha_pago_real, "%Y-%m-%d").date()

    es_post_corte = fecha_compra > fecha_corte
    
    # Si es post corte, la fecha de pago pactada pasa al mes siguiente
    fecha_pago_efectiva_pactada = fecha_pago_pactada
    if es_post_corte:
        # Añade 30 días de ciclo comercial
        fecha_pago_efectiva_pactada = fecha_pago_pactada + timedelta(days=30)
        
    dias_credito = max(0, (fecha_pago_efectiva_pactada - fecha_compra).days)
    
    ted_comp = convertir_a_ted(tipo_tasa_comp, tasa_comp, cap_comp)
    # Interés compensatorio = Capital * ((1 + TED)^dias - 1)
    factor_comp = math.pow(1.0 + ted_comp, dias_credito) - 1.0
    interes_compensatorio = round(capital * factor_comp, DECIMALES_MONEDA)
    
    total_a_pagar_pactado = round(capital + interes_compensatorio, DECIMALES_MONEDA)
    
    # Evaluación de Mora
    dias_mora = 0
    interes_mora = 0.0
    if fecha_pago_real and fecha_pago_real > fecha_pago_efectiva_pactada:
        dias_mora = (fecha_pago_real - fecha_pago_efectiva_pactada).days
        ted_mora = convertir_a_ted(tipo_tasa_mora, tasa_mora, cap_mora)
        # Mora se calcula sobre la deuda vencida exigible (capital + compensatorio)
        factor_mora = math.pow(1.0 + ted_mora, dias_mora) - 1.0
        interes_mora = round(total_a_pagar_pactado * factor_mora, DECIMALES_MONEDA)
        
    total_exigible_con_mora = round(total_a_pagar_pactado + interes_mora, DECIMALES_MONEDA)
    
    return {
        "capital": capital,
        "es_post_corte": es_post_corte,
        "fecha_compra": fecha_compra.strftime("%Y-%m-%d"),
        "fecha_pago_pactada": fecha_pago_efectiva_pactada.strftime("%Y-%m-%d"),
        "dias_credito": dias_credito,
        "ted_compensatoria": ted_comp,
        "interes_compensatorio": interes_compensatorio,
        "total_pactado": total_a_pagar_pactado,
        "dias_mora": dias_mora,
        "interes_mora": interes_mora,
        "total_con_mora": total_exigible_con_mora
    }

def calcular_metodo_frances_con_gracia(capital_inicial, fecha_compra, fecha_corte, primer_dia_pago_pactado,
                                       num_cuotas, tipo_tasa_comp, tasa_comp, cap_comp="Diaria",
                                       cok_anual=0.15):
    """
    Calcula el plan de pagos bajo el Método Francés Vencido Simple Ordinario (meses de 30 días).
    Incorpora la capitalización del periodo de gracia total entre fecha de compra y fecha de corte/pago
    tal como especifica el numeral 4 del enunciado:
    Ejemplo: compra 15 sept, corte 20 sept, pago 26 sept -> 11 días de gracia total (15 al 26).
    La deuda se capitaliza: P_cap = P_0 * (1 + TED)^11
    Luego se calculan las N cuotas mensuales empezando en el mes siguiente.
    """
    if isinstance(fecha_compra, str):
        fecha_compra = datetime.strptime(fecha_compra, "%Y-%m-%d").date()
    if isinstance(fecha_corte, str):
        fecha_corte = datetime.strptime(fecha_corte, "%Y-%m-%d").date()
    if isinstance(primer_dia_pago_pactado, str):
        primer_dia_pago_pactado = datetime.strptime(primer_dia_pago_pactado, "%Y-%m-%d").date()
        
    # Validar periodo de gracia total (días entre compra y primera fecha pactada de pago)
    dias_gracia = max(0, (primer_dia_pago_pactado - fecha_compra).days)
    
    ted_comp = convertir_a_ted(tipo_tasa_comp, tasa_comp, cap_comp)
    tem_comp = convertir_a_tem(tipo_tasa_comp, tasa_comp, cap_comp)
    
    # Capitalización de periodo de gracia total
    interes_gracia = 0.0
    capital_capitalizado = capital_inicial
    if dias_gracia > 0:
        factor_gracia = math.pow(1.0 + ted_comp, dias_gracia) - 1.0
        interes_gracia = round(capital_inicial * factor_gracia, DECIMALES_MONEDA)
        capital_capitalizado = round(capital_inicial + interes_gracia, DECIMALES_MONEDA)
        
    # Método francés: Cuota C = P_cap * [TEM * (1 + TEM)^N] / [(1 + TEM)^N - 1]
    n = int(num_cuotas)
    if tem_comp > 0:
        factor_recuperacion = (tem_comp * math.pow(1.0 + tem_comp, n)) / (math.pow(1.0 + tem_comp, n) - 1.0)
    else:
        factor_recuperacion = 1.0 / n
        
    cuota_fija = round(capital_capitalizado * factor_recuperacion, DECIMALES_MONEDA)
    
    # Construcción de la tabla de amortización
    cronograma = []
    saldo_vivo = capital_capitalizado
    total_intereses = interes_gracia
    total_amortizado = 0.0
    
    # Fechas de pago: mes a mes comenzando 1 mes después del día de gracia
    # Según enunciado: compra 15 sept, gracia hasta 26 sept -> cuotas el 26 oct, 26 nov, 26 dic.
    fecha_base = primer_dia_pago_pactado
    
    for k in range(1, n + 1):
        # Fecha de la cuota k (+30 días comerciales acumulados)
        fecha_cuota = fecha_base + timedelta(days=30 * k)
        
        interes_k = round(saldo_vivo * tem_comp, DECIMALES_MONEDA)
        
        if k == n:
            # En la última cuota se amortiza exactamente el saldo remanente para cerrar en 0.00
            amortizacion_k = saldo_vivo
            cuota_k = round(amortizacion_k + interes_k, DECIMALES_MONEDA)
            saldo_final = 0.0
        else:
            amortizacion_k = round(cuota_fija - interes_k, DECIMALES_MONEDA)
            cuota_k = cuota_fija
            saldo_final = round(saldo_vivo - amortizacion_k, DECIMALES_MONEDA)
            
        total_intereses += interes_k
        total_amortizado += amortizacion_k
        
        cronograma.append({
            "numero_cuota": k,
            "fecha_vencimiento": fecha_cuota.strftime("%Y-%m-%d"),
            "saldo_inicial": round(saldo_vivo, DECIMALES_MONEDA),
            "cuota": cuota_k,
            "interes": interes_k,
            "amortizacion": amortizacion_k,
            "saldo_final": round(saldo_final, DECIMALES_MONEDA)
        })
        saldo_vivo = saldo_final
        
    # Flujos de caja para VAN y TIR (desde la perspectiva del comercio)
    # Flujo 0 = -capital_inicial (el comercio entrega la mercadería)
    # Flujos k = +cuota_k
    flujos = [-capital_inicial] + [c["cuota"] for c in cronograma]
    
    # Cálculo de TIR mensual y anualizada
    tir_mensual = calcular_tir(flujos)
    tir_anual = math.pow(1.0 + tir_mensual, 12.0) - 1.0 if tir_mensual is not None else None
    
    # Cálculo de VAN usando el COK mensual del comerciante
    tem_cok = math.pow(1.0 + float(cok_anual), 30.0 / BASE_DIAS_ANUAL) - 1.0
    van = calcular_van(tem_cok, flujos)
    
    # TCEA: Costo efectivo para el cliente (coincide con TIR anualizada del crédito)
    tcea = tir_anual if tir_anual is not None else convertir_ted_a_tea(ted_comp)
    
    return {
        "capital_original": capital_inicial,
        "dias_gracia": dias_gracia,
        "interes_gracia": interes_gracia,
        "capital_capitalizado": capital_capitalizado,
        "num_cuotas": n,
        "ted_compensatoria": ted_comp,
        "tem_compensatoria": tem_comp,
        "cuota_mensual_fija": cuota_fija,
        "total_intereses": round(total_intereses, DECIMALES_MONEDA),
        "total_a_pagar": round(sum(c["cuota"] for c in cronograma), DECIMALES_MONEDA),
        "cronograma": cronograma,
        "flujos_caja": flujos,
        "tir_mensual": round(tir_mensual, DECIMALES_TASA) if tir_mensual is not None else None,
        "tir_anual": round(tir_anual, 6) if tir_anual is not None else None,
        "van": round(van, DECIMALES_MONEDA),
        "tcea": round(tcea, 6)
    }

def calcular_van(tasa_descuento_periodica, flujos):
    """
    Calcula el Valor Actual Neto (VAN): VAN = sum(CF_t / (1 + r)^t)
    """
    r = float(tasa_descuento_periodica)
    van = 0.0
    for t, cf in enumerate(flujos):
        van += cf / math.pow(1.0 + r, t)
    return van

def calcular_tir(flujos, max_iter=200, tolerancia=1e-7):
    """
    Calcula la Tasa Interna de Retorno (TIR) mediante el método de Newton-Raphson con fallback a bisección.
    """
    # Verificación de cambio de signo
    tiene_pos = any(f > 0 for f in flujos)
    tiene_neg = any(f < 0 for f in flujos)
    if not (tiene_pos and tiene_neg):
        return None
        
    # Aproximación inicial
    r = 0.05
    for _ in range(max_iter):
        npv = 0.0
        d_npv = 0.0
        for t, cf in enumerate(flujos):
            factor = math.pow(1.0 + r, t)
            npv += cf / factor
            if t > 0:
                d_npv -= (t * cf) / (factor * (1.0 + r))
                
        if abs(npv) < tolerancia:
            return r
            
        if abs(d_npv) < 1e-12:
            break
            
        r_nuevo = r - npv / d_npv
        if r_nuevo <= -1.0 or r_nuevo > 10.0:
            break
        r = r_nuevo

    # Fallback por bisección en [-0.5, 3.0]
    low, high = -0.5, 3.0
    f_low = calcular_van(low, flujos)
    f_high = calcular_van(high, flujos)
    
    if f_low * f_high > 0:
        return None
        
    for _ in range(100):
        mid = (low + high) / 2.0
        f_mid = calcular_van(mid, flujos)
        if abs(f_mid) < tolerancia or (high - low) < tolerancia:
            return mid
        if f_low * f_mid < 0:
            high = mid
            f_high = f_mid
        else:
            low = mid
            f_low = f_mid
            
    return mid

def imputar_pago_segun_prelacion(monto_pago, saldo_mora, saldo_compensatorio, saldo_capital):
    """
    Aplica el orden de imputación legal obligatorio según Anexo A:
    1° Mora
    2° Interés compensatorio
    3° Capital
    """
    pago = float(monto_pago)
    
    # 1° Mora
    abono_mora = min(pago, float(saldo_mora))
    pago -= abono_mora
    remanente_mora = round(float(saldo_mora) - abono_mora, DECIMALES_MONEDA)
    
    # 2° Interés compensatorio
    abono_comp = min(pago, float(saldo_compensatorio))
    pago -= abono_comp
    remanente_comp = round(float(saldo_compensatorio) - abono_comp, DECIMALES_MONEDA)
    
    # 3° Capital
    abono_capital = min(pago, float(saldo_capital))
    pago -= abono_capital
    remanente_capital = round(float(saldo_capital) - abono_capital, DECIMALES_MONEDA)
    
    return {
        "abono_mora": round(abono_mora, DECIMALES_MONEDA),
        "abono_compensatorio": round(abono_comp, DECIMALES_MONEDA),
        "abono_capital": round(abono_capital, DECIMALES_MONEDA),
        "remanente_mora": remanente_mora,
        "remanente_compensatorio": remanente_comp,
        "remanente_capital": remanente_capital,
        "excedente_no_aplicado": round(pago, DECIMALES_MONEDA)
    }

if __name__ == "__main__":
    print("Probando financial_engine...")
    # Test caso del enunciado: compra 300 soles, 3 meses, compra 15 set, corte 20 set, pago 26 set (11 días gracia)
    res = calcular_metodo_frances_con_gracia(
        capital_inicial=300.0,
        fecha_compra="2026-09-15",
        fecha_corte="2026-09-20",
        primer_dia_pago_pactado="2026-09-26",
        num_cuotas=3,
        tipo_tasa_comp="TEA",
        tasa_comp=0.24, # 24% TEA
        cok_anual=0.15
    )
    print(f"Capital capitalizado con 11 días gracia: S/ {res['capital_capitalizado']}")
    print(f"Cuota fija mensual: S/ {res['cuota_mensual_fija']}")
    print(f"Total a pagar: S/ {res['total_a_pagar']}")
    print(f"TIR anualizada comercio: {res['tir_anual'] * 100:.2f}%")
    print(f"VAN al 15% COK: S/ {res['van']}")
    for c in res['cronograma']:
        print(f"  Cuota {c['numero_cuota']} ({c['fecha_vencimiento']}): S/ {c['cuota']} (Amort: {c['amortizacion']}, Int: {c['interes']}, Saldo: {c['saldo_final']})")
