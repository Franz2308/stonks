# -*- coding: utf-8 -*-
"""
generate_complete_report_sections.py
Genera las secciones 6.b, 6.c y 6.d en 'Finanzas Trabajo Parcial_Completo.docx'
y actualiza 'Finanzas Trabajo Parcial.docx'.

Ajustes y refinamientos aplicados:
1. Eliminadas todas las etiquetas redundantes '(Fórmula 6.c.xx)'.
2. Limpieza y desahogo visual en las fórmulas: todas convertidas a OMML nativo de Word
   con espaciado amplio y elegante.
3. Separación vertical amplia entre líneas y viñetas (espacio_before=2pt..4pt, space_after=6pt..9pt).
   Eliminados los bloques de texto apretados que usaban saltos de línea internos (\n).
4. Todas las tablas en 6.d (Tablas 6.d.1, 6.d.2, 6.d.3, 6.d.4 y la nueva 6.d.5 de Flujos)
   usan el encabezado rojo oficial UPC (#C8102E), texto blanco en negrita,
   filas alternadas en #F2F2F2 y bordes #BFBFBF, idénticas al resto del informe.
5. Formato desglosado, espacioso y enriquecido para la evaluación económica de flujos,
   VAN, TIR y TCEA, culminando en una caja destacada con borde rojo UPC para el diagnóstico.
"""

import os
import sys
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
import latex2mathml.converter
import lxml.etree as ET

XSL_PATH = r"C:\Program Files\Microsoft Office\root\Office16\MML2OMML.XSL"
xslt_doc = ET.parse(XSL_PATH)
transform_omml = ET.XSLT(xslt_doc)

UPC_RED = RGBColor(200, 16, 46)      # #C8102E (Rojo institucional UPC)
TEXT_DARK = RGBColor(30, 41, 59)     # #1E293B
MUTED_GRAY = RGBColor(100, 116, 139) # #64748B
BORDER_COLOR = "BFBFBF"              # Borde estándar de tablas del informe

def set_cell_margins_and_borders(cell, top=100, bottom=100, left=130, right=130, border_color="BFBFBF", fill_hex=None):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>\n'
        f'  <w:top w:w="{top}" w:type="dxa"/>\n'
        f'  <w:bottom w:w="{bottom}" w:type="dxa"/>\n'
        f'  <w:left w:w="{left}" w:type="dxa"/>\n'
        f'  <w:right w:w="{right}" w:type="dxa"/>\n'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)
    tcBorders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>\n'
        f'  <w:left w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>\n'
        f'  <w:bottom w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>\n'
        f'  <w:right w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>\n'
        f'</w:tcBorders>'
    )
    tcPr.append(tcBorders)
    if fill_hex:
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}" w:val="clear"/>')
        tcPr.append(shd)

def add_native_equation(doc, latex_str, space_before=6, space_after=6):
    """Convierte fórmula LaTeX a OMML nativo de Word y la añade centrada con espaciado limpio."""
    try:
        mathml = latex2mathml.converter.convert(latex_str)
        dom = ET.fromstring(mathml)
        new_dom = transform_omml(dom)
        omml_str = ET.tostring(new_dom, encoding="utf-8").decode("utf-8")
        
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        
        omml_elem = parse_xml(omml_str)
        p._p.append(omml_elem)
        return p
    except Exception as e:
        print(f"Error generando ecuacion: {latex_str}, Error: {e}")
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(latex_str)
        r.font.bold = True
        return p

def add_image_placeholder_box(doc, fig_id, fig_title, fig_desc):
    """Crea un recuadro estético reservado para la captura de pantalla con acentos sobrios."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="dashed" w:sz="8" w:space="0" w:color="C8102E"/>\n'
        f'  <w:left w:val="dashed" w:sz="8" w:space="0" w:color="C8102E"/>\n'
        f'  <w:bottom w:val="dashed" w:sz="8" w:space="0" w:color="C8102E"/>\n'
        f'  <w:right w:val="dashed" w:sz="8" w:space="0" w:color="C8102E"/>\n'
        f'</w:tcBorders>'
    )
    tcPr.append(tcBorders)
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="FAF5F5" w:val="clear"/>')
    tcPr.append(shd)
    
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(24)
    p.paragraph_format.space_after = Pt(4)
    run1 = p.add_run(f"[ESPACIO RESERVADO PARA IMAGEN {fig_id}: {fig_title.upper()}]")
    run1.font.bold = True
    run1.font.size = Pt(10)
    run1.font.color.rgb = UPC_RED
    
    p_sub = cell.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(24)
    run_sub = p_sub.add_run("Captura de pantalla de la interfaz desarrollada en Stonks • Formato PNG • Vista 100%")
    run_sub.font.size = Pt(8.5)
    run_sub.font.color.rgb = MUTED_GRAY
    
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(4)
    p_cap.paragraph_format.space_after = Pt(14)
    run_cap = p_cap.add_run(f"Figura {fig_id}: {fig_title} - {fig_desc}.")
    run_cap.font.size = Pt(9)
    run_cap.font.italic = True
    run_cap.font.color.rgb = RGBColor(70, 70, 70)

def add_heading_2(doc, text):
    h = doc.add_paragraph()
    h.style = 'Heading 2'
    h.paragraph_format.space_before = Pt(18)
    h.paragraph_format.space_after = Pt(6)
    r = h.add_run(text)
    r.font.size = Pt(15)
    r.font.bold = True
    r.font.color.rgb = UPC_RED
    return h

def add_heading_3(doc, text):
    h = doc.add_paragraph()
    h.style = 'Heading 3'
    h.paragraph_format.space_before = Pt(14)
    h.paragraph_format.space_after = Pt(5)
    r = h.add_run(text)
    r.font.size = Pt(12.5)
    r.font.bold = True
    r.font.color.rgb = UPC_RED
    return h

def add_heading_4(doc, text):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(10)
    h.paragraph_format.space_after = Pt(4)
    r = h.add_run(text)
    r.font.size = Pt(11)
    r.font.bold = True
    r.font.color.rgb = TEXT_DARK
    return h

def add_body_paragraph(doc, text, bold_prefix=None, space_after=7):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.bold = True
        r_pre.font.size = Pt(10)
    r = p.add_run(text)
    r.font.size = Pt(10)
    return p

def add_bullet_item(doc, bold_title, description, space_after=6):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.left_indent = Pt(20)
    p.paragraph_format.first_line_indent = Pt(-12)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    
    r_dot = p.add_run("• ")
    r_dot.font.bold = True
    r_dot.font.size = Pt(9.5)
    r_dot.font.color.rgb = UPC_RED
    
    if bold_title:
        r_b = p.add_run(bold_title)
        r_b.font.bold = True
        r_b.font.size = Pt(9.5)
    
    if description:
        r_t = p.add_run(description)
        r_t.font.size = Pt(9.5)
    return p

def add_where_block(doc, items, space_after_last=8):
    """
    Inserta el encabezado 'Donde:' y cada variable como viñeta independiente
    con sangría francesa y espaciado vertical desahogado.
    """
    p_lead = doc.add_paragraph()
    p_lead.paragraph_format.left_indent = Pt(10)
    p_lead.paragraph_format.space_before = Pt(3)
    p_lead.paragraph_format.space_after = Pt(2)
    p_lead.paragraph_format.line_spacing = 1.15
    r_lead = p_lead.add_run("Donde:")
    r_lead.font.size = Pt(9.5)
    r_lead.font.italic = True
    r_lead.font.bold = True
    r_lead.font.color.rgb = TEXT_DARK
    
    for i, (var_name, var_desc) in enumerate(items):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.left_indent = Pt(22)
        p.paragraph_format.first_line_indent = Pt(-12)
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(space_after_last if i == len(items) - 1 else 3)
        p.paragraph_format.line_spacing = 1.15
        
        r_bullet = p.add_run("• ")
        r_bullet.font.size = Pt(9.5)
        r_bullet.font.bold = True
        r_bullet.font.color.rgb = UPC_RED
        
        r_var = p.add_run(var_name)
        r_var.font.size = Pt(9.5)
        r_var.font.bold = True
        
        r_desc = p.add_run(var_desc)
        r_desc.font.size = Pt(9.5)

def add_callout_box(doc, bold_prefix, text):
    """Crea una caja de texto destacada con borde izquierdo rojo UPC y fondo gris perla suave."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="none"/>\n'
        f'  <w:left w:val="single" w:sz="18" w:space="0" w:color="C8102E"/>\n'
        f'  <w:bottom w:val="none"/>\n'
        f'  <w:right w:val="none"/>\n'
        f'</w:tcBorders>'
    )
    tcPr.append(tcBorders)
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F8FAFC" w:val="clear"/>')
    tcPr.append(shd)
    
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>\n'
        f'  <w:top w:w="120" w:type="dxa"/>\n'
        f'  <w:bottom w:w="120" w:type="dxa"/>\n'
        f'  <w:left w:w="180" w:type="dxa"/>\n'
        f'  <w:right w:w="150" w:type="dxa"/>\n'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)
    
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.15
    
    r_pre = p.add_run(bold_prefix)
    r_pre.font.bold = True
    r_pre.font.size = Pt(10)
    r_pre.font.color.rgb = UPC_RED
    
    r = p.add_run(text)
    r.font.size = Pt(10)

# -----------------------------------------------------------------------------
# SECCIÓN 6.B: DISEÑO DE LA INTERFAZ
# -----------------------------------------------------------------------------
def build_section_6b(doc):
    add_heading_2(doc, "b) Diseño de la Interfaz")
    
    add_body_paragraph(
        doc,
        "El diseño de la interfaz de usuario de la plataforma Stonks ha sido concebido para transformar la tradicional "
        "gestión de libretas de fiado en una experiencia digital eficiente, rápida y transparente para pequeños comercios "
        "urbanos (bodegas, panaderías, carnicerías, boticas y negocios de cercanía). Se ha implementado un lenguaje visual "
        "de tipo 'workstation' financiera de alta densidad inspirado en la estética retro-moderna de utilidades profesionales "
        "(estilo BundleRock), caracterizado por una cabecera corporativa azul marino (#1a365d), botones utilitarios Win32 con "
        "relieve sutil, tarjetas con bordes nítidos de alta visibilidad y una tipografía optimizada con Inter para textos "
        "descriptivos y JetBrains Mono con cifras tabulares para la alineación rigurosa de importes monetarios y cronogramas.\n\n"
        "En estricto cumplimiento con el requerimiento de la rúbrica de evaluación del curso, cada una de las pantallas y "
        "ventanas de diálogo del sistema integra de forma nativa un medio electrónico de ayuda e indicaciones de uso, "
        "compuesto por tooltips flotantes en cada control de entrada, badges explicativos de reglas financieras (Anexo A), "
        "medidores dinámicos de saldo crediticio disponible, alertas tempranas por sobregiro y un desglose interactivo previo "
        "que exhibe la imputación legal de pagos antes de ejecutar cualquier cobranza en caja.",
        space_after=9
    )
    
    screens = [
        {
            "id": "6.b.1",
            "name": "Pantalla de Inicio de Sesión y Autenticación con Accesos de Demostración",
            "short_desc": "Acceso seguro y selección de roles con credenciales de prueba rápida",
            "func": "Constituye el punto de acceso inicial a la plataforma. Permite la autenticación segura de usuarios mediante credenciales encriptadas (SHA-256) y delimita los permisos de navegación según el rol asignado (Administrador del Sistema, Administrador de Tienda o Cliente Vecino).",
            "elements": [
                ("Campo 'Identificador de Usuario': ", "Caja de texto para el nombre de usuario único del operador o cliente."),
                ("Campo 'Clave de Acceso': ", "Entrada oculta para la contraseña de seguridad."),
                ("Botón 'Ingresar a la Plataforma': ", "Ejecuta la verificación de credenciales contra la base de datos relacional."),
                ("Panel 'Perfiles de Demostración Rápida': ", "Botones de acceso en un clic para perfiles de evaluación (Bodega Don Pepe, Cliente Juan, Panadería Espiga Dorada, Admin Sistema).")
            ],
            "help": "Debajo de cada campo se incluyen textos de asistencia en color atenuado. Además, el panel lateral izquierdo sintetiza las políticas matemáticas vigentes en el sistema (base 360, método francés con gracia y prelación legal), garantizando que el usuario comprenda el alcance financiero antes de iniciar sesión."
        },
        {
            "id": "6.b.2",
            "name": "Pantalla de Registro de Nuevos Comercios y Clientes",
            "short_desc": "Empadronamiento de nuevos usuarios y creación de cuentas comerciales",
            "func": "Permite el auto-registro guiado de nuevos clientes o comercios en la plataforma, asignando de manera inmediata un perfil operativo y solicitando los datos obligatorios de contacto y documento de identidad.",
            "elements": [
                ("Selector de Tipo de Registro: ", "Pestañas para alternar entre perfil 'Cliente' o 'Comercio Independiente'."),
                ("Campos de Identificación: ", "Nombre completo, correo electrónico, documento oficial (DNI o RUC) y teléfono."),
                ("Campos de Seguridad: ", "Definición de nombre de usuario y contraseña con confirmación."),
                ("Botón 'Crear Cuenta en Stonks': ", "Valida la unicidad del documento y persiste la entidad en la base de datos.")
            ],
            "help": "Cada campo cuenta con validadores de longitud (8 dígitos para DNI, 11 dígitos para RUC) que emiten alertas visuales instantáneas si el formato es inválido, así como tooltips explicativos sobre el uso exclusivo de los datos con fines de liquidación crediticia."
        },
        {
            "id": "6.b.3",
            "name": "Tablero Principal de Control Financiero de la Tienda (Dashboard)",
            "short_desc": "Métricas consolidadas de cartera, cuentas por cobrar y gráfico de colocación",
            "func": "Proporciona al dueño del establecimiento comercial una vista panorámica integral de la salud de su cartera crediticia, consolidando en tiempo real las cuentas por cobrar, los intereses devengados acumulados y el total de vecinos bajo línea autorizada.",
            "elements": [
                ("Cuatro Indicadores Clave (KPIs): ", "Capital Colocado, Intereses Compensatorios Devengados, Cartera Activa y Clientes en Mora."),
                ("Barra de Utilización Global de Crédito: ", "Termómetro gráfico del porcentaje de línea total ocupada por los clientes."),
                ("Tabla de Cuentas por Cobrar Críticas: ", "Listado priorizado de clientes ordenados por proximidad a la fecha de vencimiento o mora."),
                ("Accesos Rápidos a Operaciones: ", "Botonera Win32 para 'Aperturar Cuenta', 'Registrar Compra', 'Ver Liquidaciones' y 'Simulador'.")
            ],
            "help": "Al posar el cursor sobre cada KPI se despliega una ventana flotante con la fórmula de cálculo aplicada y la referencia al Anexo A del curso. En caso existan clientes en mora, una tarjeta ámbar superior muestra la advertencia con el monto total exigible vencido."
        },
        {
            "id": "6.b.4",
            "name": "Pantalla de Registro y Apertura de Cuentas Corrientes para Clientes",
            "short_desc": "Configuración contractual de línea de crédito, tasas TEA/TNA y fechas de ciclo",
            "func": "Permite al comerciante empadronar formalmente a un cliente vecino, asignándole un límite de endeudamiento seguro y estableciendo las cláusulas financieras de su contrato crediticio (régimen de tasa, periodicidad y fechas de corte/pago).",
            "elements": [
                ("Selector de Cliente: ", "Lista desplegable para asociar el cliente vecino a la tienda actual."),
                ("Campo 'Límite de Crédito Autorizado (S/)': ", "Importe máximo de financiamiento asignado al cliente."),
                ("Selector 'Tipo de Tasa Compensatoria': ", "Alternador entre Tasa Efectiva Anual (TEA) y Tasa Nominal Anual (TNA)."),
                ("Campos de Valor de Tasa y Capitalización: ", "Porcentaje pactado y frecuencia de capitalización (diaria m=360 o mensual m=12)."),
                ("Campo 'Tasa de Mora Anual (%)': ", "Tasa efectiva aplicada exclusivamente en caso de pago extemporáneo."),
                ("Día de Corte y Día de Pago: ", "Selectores numéricos para el ciclo mensual (ej. corte 20 y pago 26).")
            ],
            "help": "Debajo del selector de tasa un texto de ayuda indica: 'Base Anual: 360 días. Toda TNA se convertirá automáticamente a TED y TEM según la periodicidad de capitalización elegida'. Un cálculo en vivo previsualiza la TED y TEM resultantes antes de confirmar la apertura."
        },
        {
            "id": "6.b.5",
            "name": "Pantalla de Catálogo de Productos y Precios del Comercio",
            "short_desc": "Administración del inventario de bienes disponibles para venta al contado y fiado",
            "func": "Módulo donde el comerciante gestiona los artículos de consumo básico que ofrece a su clientela, especificando categoría, unidad de medida, precio de lista en Soles y stock de seguridad disponible.",
            "elements": [
                ("Tabla de Inventario Vigente: ", "Lista de productos con SKU, nombre, categoría, unidad, stock disponible y precio unitario."),
                ("Formulario de Alta de Producto: ", "Entradas para denominación comercial, categoría, unidad de medida y precio en Soles."),
                ("Filtros Dinámicos: ", "Buscador instantáneo por nombre y selector por familias (Abarrotes, Panadería, Bebidas, etc.).")
            ],
            "help": "La interfaz advierte que el precio registrado corresponde al valor de venta final de lista que se cargará como capital de la compra, y sobre el cual el sistema liquidará los intereses de financiamiento según la modalidad pactada."
        },
        {
            "id": "6.b.6",
            "name": "Pantalla de Punto de Venta (POS) y Registro de Consumos a Crédito",
            "short_desc": "Terminal de venta rápida con validación de línea disponible y selección de modalidad",
            "func": "Constituye la herramienta operativa principal de despacho en mostrador. Permite seleccionar un cliente con cuenta activa, agregar productos al carrito de compras, verificar en tiempo real que no se sobregire la línea autorizada y seleccionar entre la modalidad 'Fin de Mes' o 'Cuotas Francesas'.",
            "elements": [
                ("Selector de Cliente con Línea Activa: ", "Desplegable con búsqueda rápida de clientes habilitados."),
                ("Monitor de Crédito en Tiempo Real: ", "Muestra Límite Aprobado, Saldo Deudor Actual y Saldo Disponible Disponible."),
                ("Selector de Modalidad de Pago: ", "Opciones 'A Fin de Mes' (un solo cobro acumulado) o 'En Cuotas' (amortización francesa)."),
                ("Parrilla de Selección de Productos y Cantidades: ", "Permite añadir múltiples ítems calculando el subtotal de venta."),
                ("Botón 'Procesar Venta a Crédito': ", "Ejecuta la transacción y genera el ticket de consumo.")
            ],
            "help": "El sistema implementa una barra de capacidad visual: si el monto de la compra excede el saldo disponible, el botón de confirmación se bloquea de manera preventiva y un badge rojo destaca: 'Operación denegada: Excede el límite de crédito disponible'."
        },
        {
            "id": "6.b.7",
            "name": "Pantalla de Configuración de Créditos en Cuotas y Cronograma Francés",
            "short_desc": "Parametrización de compras en cuotas con período de gracia total y proyección financiera",
            "func": "Permite estructurar compras mayores en pagos diferidos mensuales. Si la compra se efectúa a mitad de ciclo, el sistema computa de forma transparente los días que median hasta el primer vencimiento como gracia total, capitaliza los intereses devengados y calcula la cuota fija mensual.",
            "elements": [
                ("Campos de Monto y Cuotas: ", "Capital de la compra e ingreso de número de meses a financiar (n)."),
                ("Campos de Fechas de Operación: ", "Fecha de retiro de la mercadería y fecha pactada del primer vencimiento."),
                ("Panel de Métricas Previas: ", "Exhibe días de gracia (dg), interés de gracia devengado (Ig) y capital inicial capitalizado (P')."),
                ("Tabla de Cronograma Preliminar: ", "Proyección de cuota fija (R), interés mensual, amortización y saldo deudor período a período."),
                ("Botón 'Emitir y Formalizar Crédito': ", "Guarda el crédito e imprime el cronograma de pagos del cliente.")
            ],
            "help": "Un banner informativo detalla el fundamento del cálculo: 'Método Francés Vencido Simple Ordinario. Los intereses devengados durante los días de gracia total se capitalizan íntegramente al saldo deudor de conformidad con el Anexo A del curso'."
        },
        {
            "id": "6.b.8",
            "name": "Pantalla de Cierre Mensual, Listados de Pago y Facturación de Cuentas Corrientes",
            "short_desc": "Generación del estado de cuenta al corte, compras pre/post corte y monto exigible",
            "func": "Módulo administrativo que ejecuta el proceso de corte de ciclo para cada cliente. Consolida las compras efectuadas hasta la fecha de corte, calcula los intereses compensatorios diarios exactos hasta la fecha de pago y difiere las compras posteriores al mes siguiente.",
            "elements": [
                ("Selector de Cliente y Ciclo: ", "Permite escoger la cuenta del vecino y el período mensual a liquidar."),
                ("Botonera de Ejecución: ", "Botón 'Generar Estado de Cuenta' y botón 'Simular Cierre de Período'."),
                ("Tabla de Compras Liquidadas del Ciclo: ", "Lista de consumos pre-corte con fecha, capital, días de crédito e interés compensatorio."),
                ("Tarjeta de Resumen Exigible: ", "Subtotal de Capital, Total de Intereses Compensatorios y Total a Pagar en Fecha Pactada."),
                ("Panel de Compras Diferidas: ", "Sección separada que lista las compras post-corte trasladadas al ciclo siguiente.")
            ],
            "help": "Un tooltip sobre las compras post-corte explica: 'Regla de Corte: Las compras registradas después del día 20 pasan automáticamente a la cuenta del mes subsiguiente sin devengar mora en el ciclo actual'."
        },
        {
            "id": "6.b.9",
            "name": "Pantalla de Caja, Cobranzas y Aplicación de Prelación Legal de Pagos",
            "short_desc": "Recepción de pagos en efectivo, cómputo automático de mora e imputación legal",
            "func": "Interfaz de ventanilla para procesar las cancelaciones de deuda. Compara la fecha en que el cliente se acerca a pagar contra la fecha pactada: si existe retraso, calcula el ítem diferenciado de intereses moratorios y aplica de inmediato el orden legal de imputación (1° Mora, 2° Intereses Compensatorios, 3° Capital).",
            "elements": [
                ("Selector de Cuenta con Deuda Exigible: ", "Búsqueda del cliente y visualización del listado liquidado."),
                ("Campo 'Fecha Efectiva de Pago': ", "Fecha en que se recibe el dinero en caja (por defecto fecha actual, configurable)."),
                ("Panel de Cálculo de Recargo Moratorio: ", "Muestra días de mora transcurridos (dm) y el monto exacto de 'Intereses por mora'."),
                ("Panel Dinámico de Imputación Legal: ", "Desglose visible en tres renglones: 1° Intereses por Mora, 2° Interés Compensatorio y 3° Amortización de Capital."),
                ("Campo 'Monto a Cobrar': ", "Cifra monetaria prellenada con el total exigible liquidado."),
                ("Botón 'Efectuar Cobranza e Imputar Pago': ", "Registra el abono, extingue la deuda del ciclo y emite el recibo formal de caja."),
                ("Tabla de Recibos Emitidos: ", "Historial auditor de comprobantes con el desglose imputado a cada concepto.")
            ],
            "help": "El formulario exhibe de forma fija la regla operativa del curso: 'Regla: No se admiten pagos parciales. El monto debe cubrir exactamente el total exigible'. Si la fecha ingresada es posterior a la pactada, un badge alerta: 'Se detectaron X días de mora. Se ha calculado el recargo legal correspondiente'."
        },
        {
            "id": "6.b.10",
            "name": "Portal de Autoservicio del Cliente Vecino y Calendario de Cuotas",
            "short_desc": "Consulta transparente de línea de crédito, deuda actual y cronograma francés",
            "func": "Interfaz diseñada para que el cliente vecino consulte con total transparencia desde su teléfono móvil o computadora el estado de su cuenta corriente, sus compras registradas, su cupo disponible y el cronograma de amortización francesa de sus créditos en cuotas.",
            "elements": [
                ("Tarjeta de Identidad y Tienda: ", "Nombre del comercio emisor, nombre del vecino y fechas asignadas de corte y pago."),
                ("Tríada de Balances: ", "Tres tarjetas informativas: Límite Aprobado, Deuda Pendiente y Crédito Disponible."),
                ("Tabla de Compras Registradas: ", "Historial de consumos a crédito con fecha, modalidad, importe y estado de cancelación."),
                ("Calendario de Cuotas Mensuales: ", "Tabla de amortización detallando para cada cuota el vencimiento, la cuota fija, amortización de capital, interés compensatorio y saldo insoluto restante.")
            ],
            "help": "Debajo del balance se indica: 'El saldo disponible se actualiza inmediatamente después de cada compra o cobro registrado en caja. Los pagos puntuales garantizan la mantención o ampliación de su línea crediticia'."
        },
        {
            "id": "6.b.11",
            "name": "Simulador y Motor Matemático-Financiero Avanzado",
            "short_desc": "Herramienta interactiva de conversión de tasas, amortización francesa y mora",
            "func": "Módulo técnico para auditar y verificar con rigor matemático todas las fórmulas del Anexo A del curso. Cuenta con tres pestañas especializadas: 1) Amortización Francesa con Período de Gracia Total y evaluación TIR/VAN; 2) Conversor de Tasas con 7 decimales; 3) Simulador de compras pre/post corte y mora diferenciada.",
            "elements": [
                ("Pestaña 1 - Método Francés: ", "Entrada de capital, fechas de compra y primer pago (para gracia), número de cuotas, tasa TEA/TNA y tasa COK del comercio. Genera las métricas de gracia, capital capitalizado, cuota fija, VAN, TIR anual y la tabla mes a mes."),
                ("Pestaña 2 - Conversor de Tasas: ", "Conversión bidireccional entre TEA, TNA (capitalización diaria o mensual), TEM y TED con al menos 7 decimales de precisión."),
                ("Pestaña 3 - Compras Fin de Mes y Mora: ", "Simulador de fecha de compra vs. fecha de corte para evaluar el diferimiento a mes M+1 y el cómputo de mora tras la fecha pactada.")
            ],
            "help": "Cada pestaña incluye cuadros de texto explicativo que citan las ecuaciones del marco conceptual, permitiendo contrastar los resultados arrojados por el software con cálculos manuales paso a paso."
        },
        {
            "id": "6.b.12",
            "name": "Consola de Administración Global del Sistema (Multitienda)",
            "short_desc": "Gestión general de establecimientos comerciales adheridos y auditoría",
            "func": "Permite al Administrador General de la plataforma supervisar el ecosistema multitienda, dar de alta nuevos negocios de barrio (bodegas, panaderías, carnicerías, etc.), asignarles credenciales de acceso y suspender o reactivar cuentas comerciales.",
            "elements": [
                ("KPIs Globales: ", "Total de tiendas activas, clientes globales empadronados, volumen total de financiamiento colocado y tasa de aislamiento multiempresa (100%)."),
                ("Directorio de Tiendas: ", "Tabla con nombre comercial, RUC, giro, administrador responsable, zona de influencia y recuento de clientes/ventas."),
                ("Modal 'Alta de Nueva Tienda': ", "Formulario integral para crear el usuario administrador y registrar el establecimiento comercial."),
                ("Acciones de Control: ", "Botones para activar o suspender tiendas de forma inmediata.")
            ],
            "help": "La ventana modal de alta exige RUC de 11 dígitos y correo corporativo válido, mostrando indicaciones en línea sobre la segregación lógica de datos: 'Cada comercio administra de manera estrictamente privada sus productos, clientes y finanzas'."
        }
    ]
    
    for s in screens:
        add_heading_3(doc, f"{s['id']}. {s['name']}")
        add_body_paragraph(doc, s['func'], bold_prefix="Función y Alcance: ", space_after=6)
        
        add_heading_4(doc, "Componentes y Elementos de Interacción:")
        for title, desc in s['elements']:
            add_bullet_item(doc, title, desc, space_after=5)
            
        add_heading_4(doc, "Mecanismo de Ayuda e Indicaciones Integradas (Obligatorio de la Rúbrica):")
        add_body_paragraph(doc, s['help'], space_after=8)
        
        add_image_placeholder_box(doc, s['id'], s['name'], s['short_desc'])
        
    print("Sección 6.b construida con éxito.")

# -----------------------------------------------------------------------------
# SECCIÓN 6.C: MARCO CONCEPTUAL (FÓRMULAS) - LIMPIO Y SIN ETIQUETAS REDUNDANTES
# -----------------------------------------------------------------------------
def build_section_6c(doc):
    add_heading_2(doc, "c) Marco conceptual (fórmulas)")
    
    add_body_paragraph(
        doc,
        "En esta sección se expone formalmente el modelo matemático y financiero que rige todas las operaciones computacionales "
        "del sistema Stonks. De acuerdo con las instrucciones de la cátedra de Finanzas e Ingeniería Económica y las especificaciones "
        "de cumplimiento obligatorio estipuladas en el Anexo A del curso, todos los cálculos se estructuran bajo una base anual "
        "comercial de 360 días y meses comerciales de 30 días, aplicando conversiones explícitas de tasas de interés con un mínimo "
        "de 7 decimales de precisión, el método de amortización francés vencido simple ordinario con capitalización íntegra de intereses "
        "en períodos de gracia total, el cómputo independiente de intereses por mora y el estricto orden legal de imputación o prelación de pagos.",
        space_after=6
    )
    add_body_paragraph(
        doc,
        "A continuación se formulan de manera secuencial y desahogada todas las ecuaciones implementadas en el motor del software, "
        "desagregando rigurosamente el significado y unidad de cada variable:",
        space_after=9
    )
    
    # 6.c.1
    add_heading_3(doc, "6.c.1. Convenciones Base del Sistema y Mes Comercial (Anexo A)")
    add_body_paragraph(
        doc,
        "Todas las relaciones temporales entre fechas de compra, corte y pago se rigen bajo el estándar comercial financiero peruano:",
        space_after=4
    )
    add_bullet_item(doc, "Año comercial estándar: ", "360 días anuales uniformes.", space_after=4)
    add_bullet_item(doc, "Mes comercial estándar: ", "30 días uniformes (12 períodos mensuales exactos en el año).", space_after=4)
    add_bullet_item(doc, "Precisión mínima de cálculo: ", "Las tasas efectivas y nominales se procesan con un mínimo estricto de 7 decimales de precisión en el motor financiero.", space_after=4)
    add_bullet_item(doc, "Precisión monetaria: ", "Todos los saldos e importes monetarios en moneda nacional (PEN - Soles) se redondean a 2 decimales en el reporte final de caja.", space_after=8)
    
    # 6.c.2
    add_heading_3(doc, "6.c.2. Modelo Matemático de Conversión Explícita de Tasas de Interés")
    add_body_paragraph(
        doc,
        "Para transformar las tasas contractuales pactadas a las tasas efectivas del horizonte de financiamiento, se aplican las relaciones fundamentales de equivalencia financiera:",
        space_after=6
    )
    
    add_heading_4(doc, "1. Tasa Efectiva Diaria (TED) a partir de la Tasa Efectiva Anual (TEA):")
    add_native_equation(doc, r"TED = (1 + TEA)^{\frac{1}{360}} - 1")
    add_where_block(doc, [
        ("TED: ", "Tasa Efectiva Diaria en tanto por uno."),
        ("TEA: ", "Tasa Efectiva Anual pactada contractualmente en tanto por uno."),
        ("360: ", "Número de días del año comercial estándar.")
    ])
    
    add_heading_4(doc, "2. Tasa Efectiva Mensual (TEM, 30 días) a partir de la TEA:")
    add_native_equation(doc, r"TEM = (1 + TEA)^{\frac{30}{360}} - 1 = (1 + TED)^{30} - 1")
    add_where_block(doc, [
        ("TEM: ", "Tasa Efectiva Mensual para un período comercial de 30 días en tanto por uno."),
        ("TEA: ", "Tasa Efectiva Anual pactada contractualmente."),
        ("TED: ", "Tasa Efectiva Diaria equivalente del sistema.")
    ])
    
    add_heading_4(doc, "3. Conversión de Tasa Nominal Anual (TNA) con Capitalización Diaria (m = 360):")
    add_native_equation(doc, r"TED = \frac{TNA}{360}")
    add_native_equation(doc, r"TEA = \left(1 + \frac{TNA}{360}\right)^{360} - 1")
    add_where_block(doc, [
        ("TNA: ", "Tasa Nominal Anual con régimen de capitalización diaria."),
        ("360: ", "Frecuencia de capitalización diaria anual (períodos de capitalización por año).")
    ])
    
    add_heading_4(doc, "4. Conversión de Tasa Nominal Anual (TNA) con Capitalización Mensual (m = 12):")
    add_native_equation(doc, r"TEM = \frac{TNA}{12}")
    add_native_equation(doc, r"TEA = \left(1 + \frac{TNA}{12}\right)^{12} - 1")
    add_where_block(doc, [
        ("TNA: ", "Tasa Nominal Anual con régimen de capitalización mensual."),
        ("12: ", "Número de períodos mensuales de capitalización en el año comercial.")
    ])
    
    add_heading_4(doc, "5. Equivalencia General entre Tasas Efectivas de Distinta Periodicidad:")
    add_native_equation(doc, r"TEP_2 = (1 + TEP_1)^{\frac{n_2}{n_1}} - 1")
    add_where_block(doc, [
        ("TEP₁: ", "Tasa efectiva conocida correspondiente a un plazo base de n₁ días."),
        ("TEP₂: ", "Tasa efectiva equivalente requerida para el plazo objetivo de n₂ días.")
    ])
    
    # 6.c.3
    add_heading_3(doc, "6.c.3. Modelo Matemático para Ventas con Liquidación a Fin de Mes (Pago en Fecha Pactada)")
    add_body_paragraph(
        doc,
        "En la modalidad rotativa a fin de mes, cada consumo efectuado a crédito genera intereses compensatorios acumulados desde la fecha de retiro de mercadería hasta la fecha pactada de pago del ciclo:",
        space_after=6
    )
    
    add_heading_4(doc, "1. Regla Temporal de Clasificación de Compras (Corte y Diferimiento):")
    add_native_equation(doc, r"\text{Ciclo de Cobro} = \begin{cases} M \text{ (Ciclo en curso)}, & \text{si } F_{compra} \le F_{corte} \\ M+1 \text{ (Ciclo siguiente, diferido 30 días)}, & \text{si } F_{compra} > F_{corte} \end{cases}")
    add_where_block(doc, [
        ("F_compra: ", "Fecha en que el cliente vecino realiza el consumo o retiro de mercadería."),
        ("F_corte: ", "Día de corte mensual configurado en la cuenta corriente del cliente.")
    ])
    
    add_heading_4(doc, "2. Cómputo de Días de Financiamiento Regular (d):")
    add_native_equation(doc, r"d = F_{pago\_pactada} - F_{compra}")
    
    add_heading_4(doc, "3. Interés Compensatorio Devengado por Compra Individual:")
    add_native_equation(doc, r"I_{comp, j} = C_j \times \left[(1 + TED)^{d_j} - 1\right]")
    add_where_block(doc, [
        ("C_j: ", "Importe del capital correspondiente a la compra j (precio de lista en Soles)."),
        ("TED: ", "Tasa Efectiva Diaria compensatoria."),
        ("d_j: ", "Días de financiamiento transcurridos entre la fecha de compra j y la fecha pactada de pago.")
    ])
    
    add_heading_4(doc, "4. Monto Total Liquidado por Compra Individual:")
    add_native_equation(doc, r"M_{item, j} = C_j + I_{comp, j} = C_j \times (1 + TED)^{d_j}")
    
    add_heading_4(doc, "5. Total Exigible en el Listado de Pago a la Fecha de Corte (para N compras pre-corte):")
    add_native_equation(doc, r"Total_{exigible} = \sum_{j=1}^{N} C_j + \sum_{j=1}^{N} I_{comp, j} = Subtotal_{capital} + Total_{compensatorio}")
    add_where_block(doc, [
        ("Subtotal_capital: ", "Sumatoria del capital exigible de todas las compras pre-corte del ciclo."),
        ("Total_compensatorio: ", "Sumatoria de todos los intereses compensatorios devengados a la fecha pactada.")
    ])
    
    # 6.c.4
    add_heading_3(doc, "6.c.4. Modelo Matemático del Método Francés Vencido Simple Ordinario con Periodo de Gracia Total")
    add_body_paragraph(
        doc,
        "Cuando el cliente pacta una compra financiada en cuotas, el crédito se amortiza mediante el método francés vencido simple ordinario con cuotas mensuales constantes (cada 30 días). Si la compra ocurre a mitad de ciclo, los días transcurridos hasta el primer vencimiento configuran un período de gracia total en el cual no se exige pago de capital ni intereses, por lo que los intereses devengados se capitalizan íntegramente al saldo deudor:",
        space_after=6
    )
    
    add_heading_4(doc, "1. Días del Período de Gracia Total (dg):")
    add_native_equation(doc, r"d_g = F_{primer\_pago} - F_{compra}")
    
    add_heading_4(doc, "2. Interés de Gracia Capitalizado (Ig):")
    add_native_equation(doc, r"I_g = P \times \left[(1 + TED)^{d_g} - 1\right]")
    add_where_block(doc, [
        ("P: ", "Monto del capital financiado originalmente en cuotas (precio de lista en Soles)."),
        ("TED: ", "Tasa Efectiva Diaria compensatoria."),
        ("d_g: ", "Número de días calendario del período de gracia total transcurridos.")
    ])
    
    add_heading_4(doc, "3. Capital Inicial Capitalizado Base para el Cronograma (P'):")
    add_native_equation(doc, r"P' = P + I_g = P \times (1 + TED)^{d_g}")
    
    add_heading_4(doc, "4. Determinación de la Cuota Fija Mensual Francesa (R):")
    add_native_equation(doc, r"R = P' \times \left[ \frac{TEM \times (1 + TEM)^n}{(1 + TEM)^n - 1} \right] = P' \times \left[ \frac{TEM}{1 - (1 + TEM)^{-n}} \right]")
    add_where_block(doc, [
        ("R: ", "Valor constante de la cuota periódica mensual fija vencida ordinaria (en Soles)."),
        ("P': ", "Capital inicial capitalizado resultante tras la gracia total."),
        ("TEM: ", "Tasa Efectiva Mensual comercial (30 días)."),
        ("n: ", "Número total de cuotas mensuales pactadas en el contrato.")
    ])
    
    add_heading_4(doc, "5. Fórmulas de Desagregación Recursiva del Cronograma Mensual (período k = 1, 2, ..., n):")
    add_native_equation(doc, r"SI_1 = P', \quad SI_k = SF_{k-1} \quad (k > 1)")
    add_native_equation(doc, r"I_k = SI_k \times TEM")
    add_native_equation(doc, r"A_k = R - I_k")
    add_native_equation(doc, r"SF_k = SI_k - A_k")
    add_where_block(doc, [
        ("SI_k: ", "Saldo inicial o deuda viva insoluta al comenzar el período mensual k."),
        ("I_k: ", "Interés compensatorio devengado durante el período mensual k."),
        ("A_k: ", "Amortización de principal que reduce efectivamente la deuda en el período k."),
        ("SF_k: ", "Saldo final insoluto remanente al término del mes k (cumpliendo SF_n = 0 al liquidar).")
    ])
    
    # 6.c.5
    add_heading_3(doc, "6.c.5. Modelo de Cómputo de Intereses Moratorios (Ítem Diferenciado - Numeral 6 del Enunciado)")
    add_body_paragraph(
        doc,
        "En cumplimiento estricto del Numeral 6 de las bases del proyecto, cuando un cliente no cancela su obligación exigible en la fecha pactada, el sistema liquida de manera explícita y separada un ítem denominado 'Intereses por mora':",
        space_after=6
    )
    
    add_heading_4(doc, "1. Días de Retraso Transcurridos tras Vencimiento (dm):")
    add_native_equation(doc, r"d_m = \max(0, F_{pago\_real} - F_{pago\_pactada})")
    
    add_heading_4(doc, "2. Tasa Efectiva Diaria Moratoria (TED_mora):")
    add_native_equation(doc, r"TED_{mora} = (1 + TEA_{mora})^{\frac{1}{360}} - 1")
    
    add_heading_4(doc, "3. Cálculo del Ítem Diferenciado de Intereses por Mora:")
    add_native_equation(doc, r"I_{mora} = Total_{exigible} \times \left[(1 + TED_{mora})^{d_m} - 1\right]")
    add_where_block(doc, [
        ("Total_exigible: ", "Deuda total regular vencida no cancelada."),
        ("TED_mora: ", "Tasa moratoria diaria pactada contractualmente."),
        ("d_m: ", "Días de retraso efectivamente transcurridos tras la fecha pactada.")
    ])
    
    add_heading_4(doc, "4. Total Exigible en Ventanilla con Recargo Moratorio:")
    add_native_equation(doc, r"Total_{con\_mora} = Total_{exigible} + I_{mora}")
    
    # 6.c.6
    add_heading_3(doc, "6.c.6. Reglas de Imputación de Pagos y Orden Legal de Prelación (Anexo A)")
    add_body_paragraph(
        doc,
        "El Anexo A del curso establece que todo pago percibido debe imputarse obligatoriamente siguiendo el orden de prelación legal establecido por la normativa peruana: primero mora, luego interés compensatorio y finalmente amortización de capital:",
        space_after=6
    )
    add_native_equation(doc, r"Abono_{mora} = \min(Monto_{pagado}, I_{mora})")
    add_native_equation(doc, r"Abono_{comp} = \min(Monto_{pagado} - Abono_{mora}, Total_{compensatorio})")
    add_native_equation(doc, r"Abono_{cap} = \min(Monto_{pagado} - Abono_{mora} - Abono_{comp}, Subtotal_{capital})")
    add_body_paragraph(
        doc,
        "Por política operativa de control de cobro en Stonks, no se autorizan pagos parciales en ventanilla, por lo que: Monto_pagado = Total_con_mora (garantizando la extinción total del saldo exigible del período).",
        space_after=8
    )
    
    # 6.c.7
    add_heading_3(doc, "6.c.7. Fórmulas de Evaluación Financiera del Crédito (TIR, VAN, TCEA)")
    add_body_paragraph(
        doc,
        "Para evaluar la viabilidad y rentabilidad del crédito otorgado desde la perspectiva del comercio frente a su costo de oportunidad, se incorporan las métricas financieras clásicas de evaluación de proyectos:",
        space_after=6
    )
    
    add_heading_4(doc, "1. Valor Actual Neto (VAN) evaluado al Costo de Oportunidad del Capital (COK):")
    add_native_equation(doc, r"COK_{mes} = (1 + COK_{anual})^{\frac{30}{360}} - 1")
    add_native_equation(doc, r"VAN = -P + \sum_{k=1}^{n} \frac{FC_k}{(1 + COK_{mes})^k}")
    add_where_block(doc, [
        ("P: ", "Desembolso inicial (valor de la mercadería retirada a crédito en Soles)."),
        ("FC_k: ", "Flujo neto de efectivo percibido en el mes k (cuota pagada por el cliente)."),
        ("COK_mes: ", "Costo de oportunidad del capital del negocio expresado en base mensual.")
    ])
    
    add_heading_4(doc, "2. Tasa Interna de Retorno (TIR):")
    add_native_equation(doc, r"-P + \sum_{k=1}^{n} \frac{FC_k}{(1 + TIR_{mes})^k} = 0")
    add_native_equation(doc, r"TIR_{anual} = (1 + TIR_{mes})^{12} - 1")
    add_where_block(doc, [
        ("TIR_mes: ", "Tasa mensual que descuenta los flujos futuros de modo que el VAN sea exactamente cero."),
        ("TIR_anual: ", "Rendimiento efectivo anualizado compuesto que reporta el financiamiento al comercio.")
    ])
    
    add_heading_4(doc, "3. Tasa de Costo Efectivo Anual (TCEA para el Cliente):")
    add_native_equation(doc, r"TCEA = (1 + i_{efectivo\_mensual})^{12} - 1")
    add_where_block(doc, [
        ("i_efectivo_mensual: ", "Tasa periódica mensual implícita que iguala el desembolso con el valor presente de los pagos.")
    ], space_after_last=10)
    
    print("Sección 6.c construida con éxito con ecuaciones limpias.")

# -----------------------------------------------------------------------------
# SECCIÓN 6.D: DISEÑO DE DATOS DE PRUEBA (TABLAS CON ENCABEZADO ROJO UPC #C8102E)
# -----------------------------------------------------------------------------
def build_section_6d(doc):
    add_heading_2(doc, "d) Diseño de Datos de prueba")
    
    add_body_paragraph(
        doc,
        "Con el objetivo de comprobar con rigurosidad la veracidad, precisión y consistencia del modelo desarrollado, "
        "se diseñan y resuelven a continuación dos juegos de datos de prueba completos que abarcan los dos regímenes de tasas "
        "(Tasa Efectiva Anual y Tasa Nominal Anual con capitalización diaria), las dos modalidades de crédito (Fin de Mes y "
        "Cuotas Francesas con período de gracia total), la verificación del diferimiento post-corte, el cálculo del ítem "
        "separado de mora y la aplicación estricta del orden legal de prelación de pagos.",
        space_after=9
    )
    
    # -------------------------------------------------------------------------
    # JUEGO DE DATOS DE PRUEBA 1
    # -------------------------------------------------------------------------
    add_heading_3(doc, "6.d.1. Juego de Datos de Prueba 1: Crédito en Cuenta Corriente con Tasa Efectiva Anual (TEA)")
    add_body_paragraph(
        doc,
        "Este primer caso valida el funcionamiento del crédito rotativo a fin de mes bajo régimen de Tasa Efectiva, verificando "
        "las compras pre-corte, el diferimiento de compras post-corte al mes M+1, la generación del listado de cobro al corte y "
        "dos escenarios de cancelación: uno puntual y otro con retraso para corroborar el cómputo del ítem separado de intereses por mora.",
        space_after=7
    )
    
    add_heading_4(doc, "a) Parámetros Contractuales y de Configuración:")
    add_bullet_item(doc, "Establecimiento Comercial: ", "Bodega Don Pepe (RUC: 10458923412, Giro: Minimarket de Barrio).", space_after=5)
    add_bullet_item(doc, "Cliente Vecino: ", "Juan Pérez Gómez (DNI: 09485721, Dirección: Jr. Las Flores 342, San Miguel).", space_after=5)
    add_bullet_item(doc, "Línea de Crédito Autorizada: ", "S/ 500.00.", space_after=5)
    add_bullet_item(doc, "Tasa Compensatoria Contractual: ", "TEA = 24.00% anual.", space_after=5)
    add_bullet_item(doc, "Tasa Moratoria Contractual: ", "TEA_mora = 5.00% anual.", space_after=5)
    add_bullet_item(doc, "Día de Corte Mensual: ", "20 de cada mes.", space_after=5)
    add_bullet_item(doc, "Día Pactado de Pago: ", "26 de cada mes.", space_after=8)
    
    add_heading_4(doc, "b) Conversión Explícita de Tasas (Base 360 Días):")
    add_bullet_item(doc, "Tasa Efectiva Diaria Compensatoria (TED): ", "TED = (1 + 0.24)^(1/360) - 1 = 0.000598083 (0.0598083% diario).", space_after=5)
    add_bullet_item(doc, "Tasa Efectiva Mensual Compensatoria (TEM): ", "TEM = (1 + 0.24)^(30/360) - 1 = 0.01808758 (1.808758% mensual).", space_after=5)
    add_bullet_item(doc, "Tasa Efectiva Diaria Moratoria (TED_mora): ", "TED_mora = (1 + 0.05)^(1/360) - 1 = 0.000135547 (0.0135547% diario).", space_after=8)
    
    add_heading_4(doc, "c) Registro Cronológico de Compras en el Ciclo:")
    add_body_paragraph(
        doc,
        "Durante el ciclo de setiembre de 2026, el cliente efectúa tres consumos a crédito en la bodega:",
        space_after=6
    )
    
    # Tabla 6.d.1 con rojo UPC
    tbl1 = doc.add_table(rows=4, cols=8)
    tbl1.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers1 = ["TICKET", "FECHA", "HORA", "DESCRIPCIÓN", "CAPITAL (S/)", "CLASIFICACIÓN", "DÍAS FINANC.", "TOTAL ÍTEM (S/)"]
    for col_idx, h in enumerate(headers1):
        cell = tbl1.cell(0, col_idx)
        cell.text = h
        set_cell_margins_and_borders(cell, fill_hex="C8102E")
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.bold = True
                r.font.size = Pt(8)
                r.font.color.rgb = RGBColor(255, 255, 255)
                
    rows1_data = [
        ["TKT-001", "12/09/2026", "10:15", "Arroz, aceite, leche evaporada", "100.00", "Pre-corte (Setiembre)", "14 días (12 al 26 sep)", "100.84"],
        ["TKT-002", "18/09/2026", "17:30", "Conservas, fideos, embutidos", "150.00", "Pre-corte (Setiembre)", "8 días (18 al 26 sep)", "150.72"],
        ["TKT-003", "22/09/2026", "19:40", "Gaseosas, galletas, snacks", "80.00", "Post-corte (Pasa a Octubre)", "34 días (22 sep al 26 oct)", "Diferido M+1"]
    ]
    for row_idx, data in enumerate(rows1_data):
        fill = "F2F2F2" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, val in enumerate(data):
            cell = tbl1.cell(row_idx + 1, col_idx)
            cell.text = val
            set_cell_margins_and_borders(cell, fill_hex=fill)
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if col_idx in [4, 7] else WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs:
                    r.font.size = Pt(8)
                    
    p_cap1 = doc.add_paragraph()
    p_cap1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap1.paragraph_format.space_before = Pt(3)
    p_cap1.paragraph_format.space_after = Pt(10)
    r_cap1 = p_cap1.add_run("Tabla 6.d.1: Detalle de compras registradas en el ciclo para el Juego de Datos 1.")
    r_cap1.font.size = Pt(8.5)
    r_cap1.font.italic = True
    
    add_heading_4(doc, "d) Generación del Listado de Pago en la Fecha de Corte (20 de Setiembre):")
    add_body_paragraph(
        doc,
        "Al efectuarse el corte el 20 de setiembre, el sistema consolida únicamente las compras TKT-001 y TKT-002 (la compra TKT-003 "
        "se difiere automáticamente al mes siguiente por ser posterior al día de corte). Se calcula el reporte exigible:",
        space_after=6
    )
    
    # Tabla 6.d.2 con rojo UPC
    tbl2 = doc.add_table(rows=5, cols=4)
    tbl2.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers2 = ["CONCEPTO FINANCIERO", "DETALLE MATEMÁTICO", "CÁLCULO EXACTO", "MONTO EXIGIBLE (S/)"]
    for col_idx, h in enumerate(headers2):
        cell = tbl2.cell(0, col_idx)
        cell.text = h
        set_cell_margins_and_borders(cell, fill_hex="C8102E")
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.bold = True
                r.font.size = Pt(8.5)
                r.font.color.rgb = RGBColor(255, 255, 255)
                
    rows2_data = [
        ["Subtotal Capital", "Compras TKT-001 + TKT-002", "100.00 + 150.00", "250.00"],
        ["Interés Comp. TKT-001", "100.00 × [(1 + 0.000598083)^14 - 1]", "14 días de crédito regular", "0.84"],
        ["Interés Comp. TKT-002", "150.00 × [(1 + 0.000598083)^8 - 1]", "8 días de crédito regular", "0.72"],
        ["TOTAL REGULAR EXIGIBLE", "Subtotal Capital + Intereses Compensatorios", "Fecha pactada de vencimiento: 26/09/2026", "251.56"]
    ]
    for row_idx, data in enumerate(rows2_data):
        fill = "F2F2F2" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, val in enumerate(data):
            cell = tbl2.cell(row_idx + 1, col_idx)
            cell.text = val
            set_cell_margins_and_borders(cell, fill_hex=fill)
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if col_idx == 3 else WD_ALIGN_PARAGRAPH.LEFT
                for r in p.runs:
                    r.font.size = Pt(8.5)
                    if row_idx == 3:
                        r.font.bold = True
                        
    p_cap2 = doc.add_paragraph()
    p_cap2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap2.paragraph_format.space_before = Pt(3)
    p_cap2.paragraph_format.space_after = Pt(10)
    r_cap2 = p_cap2.add_run("Tabla 6.d.2: Liquidación del Listado de Pago emitida en fecha de corte (20/09/2026).")
    r_cap2.font.size = Pt(8.5)
    r_cap2.font.italic = True
    
    add_heading_4(doc, "e) Escenario de Liquidación A: Pago Puntual (26 de Setiembre):")
    add_bullet_item(doc, "Días de Retraso: ", "0 días (el pago se efectúa exactamente en la fecha pactada).", space_after=5)
    add_bullet_item(doc, "Intereses por Mora: ", "S/ 0.00.", space_after=5)
    add_bullet_item(doc, "Monto Cobrado en Ventanilla: ", "S/ 251.56.", space_after=5)
    add_bullet_item(doc, "Imputación Legal de Pago: ", "1° Mora: S/ 0.00 | 2° Interés Compensatorio: S/ 1.56 | 3° Capital: S/ 250.00.", space_after=5)
    add_bullet_item(doc, "Saldo Deudor del Ciclo: ", "S/ 0.00 (Cuenta de setiembre 100% cancelada).", space_after=8)
    
    add_heading_4(doc, "f) Escenario de Liquidación B: Pago con Retraso (05 de Octubre - Cómputo de Mora):")
    add_bullet_item(doc, "Fecha Real de Pago en Caja: ", "05 de octubre de 2026.", space_after=5)
    add_bullet_item(doc, "Días de Mora Transcurridos (dm): ", "dm = 05/10/2026 - 26/09/2026 = 9 días.", space_after=5)
    add_bullet_item(doc, "Cálculo del Ítem Diferenciado de Intereses por Mora: ", "I_mora = 251.56 × [(1 + 0.000135547)^9 - 1] = S/ 0.31.", space_after=5)
    add_bullet_item(doc, "Monto Total Exigible en Ventanilla: ", "Total = S/ 251.56 + S/ 0.31 = S/ 251.87.", space_after=5)
    add_bullet_item(doc, "Imputación Rigurosa según Prelación Legal (Anexo A): ", "1° Intereses por Mora: S/ 0.31 | 2° Interés Compensatorio: S/ 1.56 | 3° Capital: S/ 250.00. Total cancelado: S/ 251.87.", space_after=10)
    
    # -------------------------------------------------------------------------
    # JUEGO DE DATOS DE PRUEBA 2
    # -------------------------------------------------------------------------
    add_heading_3(doc, "6.d.2. Juego de Datos de Prueba 2: Crédito en Cuotas con Tasa Nominal Anual (TNA) y Gracia Total")
    add_body_paragraph(
        doc,
        "Este segundo caso de prueba somete a verificación el motor de cálculo del Método Francés Vencido Simple Ordinario "
        "bajo régimen de Tasa Nominal Anual (TNA) con capitalización diaria, considerando una compra efectuada a mitad de ciclo "
        "con un período de gracia total de 11 días donde los intereses devengados se capitalizan, dando lugar a un cronograma "
        "de 3 cuotas mensuales constantes y la evaluación financiera de rentabilidad (TIR, VAN, TCEA).",
        space_after=7
    )
    
    add_heading_4(doc, "a) Parámetros Contractuales:")
    add_bullet_item(doc, "Establecimiento Comercial: ", "Panadería y Pastelería Espiga Dorada (RUC: 20561234891).", space_after=5)
    add_bullet_item(doc, "Cliente Vecina: ", "María Rodríguez López (DNI: 41258963).", space_after=5)
    add_bullet_item(doc, "Compra Financiada: ", "3 sacos de harina especial e insumos de pastelería por S/ 300.00.", space_after=5)
    add_bullet_item(doc, "Plazo de Pago: ", "3 cuotas mensuales.", space_after=5)
    add_bullet_item(doc, "Régimen de Tasa Pactado: ", "TNA = 24.00% con capitalización diaria (m = 360).", space_after=5)
    add_bullet_item(doc, "Fecha de Compra: ", "15 de setiembre de 2026.", space_after=5)
    add_bullet_item(doc, "Fecha del Primer Vencimiento: ", "26 de setiembre de 2026.", space_after=5)
    add_bullet_item(doc, "Costo de Oportunidad del Capital del Comercio (COK): ", "15.00% anual.", space_after=8)
    
    add_heading_4(doc, "b) Conversión de Tasas (Precisión de 7 Decimales según Anexo A):")
    
    # Tabla 6.d.3 con rojo UPC
    tbl3 = doc.add_table(rows=4, cols=4)
    tbl3.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers3 = ["TASA DE INTERÉS", "FÓRMULA APLICADA", "VALOR EN TANTO POR UNO", "EXPRESIÓN PORCENTUAL"]
    for col_idx, h in enumerate(headers3):
        cell = tbl3.cell(0, col_idx)
        cell.text = h
        set_cell_margins_and_borders(cell, fill_hex="C8102E")
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.bold = True
                r.font.size = Pt(8.5)
                r.font.color.rgb = RGBColor(255, 255, 255)
                
    rows3_data = [
        ["Tasa Efectiva Diaria (TED)", "0.24 / 360", "0.0006666667", "0.0666667% diario"],
        ["Tasa Efectiva Anual (TEA eq.)", "(1 + 0.0006666667)^360 - 1", "0.2711216", "27.11216% anual"],
        ["Tasa Efectiva Mensual (TEM, 30 d)", "(1 + 0.0006666667)^30 - 1", "0.0201972", "2.01972% mensual"]
    ]
    for row_idx, data in enumerate(rows3_data):
        fill = "F2F2F2" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, val in enumerate(data):
            cell = tbl3.cell(row_idx + 1, col_idx)
            cell.text = val
            set_cell_margins_and_borders(cell, fill_hex=fill)
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT if col_idx < 2 else WD_ALIGN_PARAGRAPH.RIGHT
                for r in p.runs:
                    r.font.size = Pt(8.5)
                    
    p_cap3 = doc.add_paragraph()
    p_cap3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap3.paragraph_format.space_before = Pt(3)
    p_cap3.paragraph_format.space_after = Pt(10)
    r_cap3 = p_cap3.add_run("Tabla 6.d.3: Conversión explícita de tasas de interés para el Juego de Datos 2.")
    r_cap3.font.size = Pt(8.5)
    r_cap3.font.italic = True
    
    add_heading_4(doc, "c) Cómputo del Período de Gracia Total Capitalizado:")
    add_bullet_item(doc, "Días de Gracia Total (dg): ", "dg = 26/09/2026 - 15/09/2026 = 11 días.", space_after=5)
    add_bullet_item(doc, "Interés de Gracia Devengado (Ig): ", "Ig = 300.00 × [(1 + 0.0006666667)^11 - 1] = S/ 2.21.", space_after=5)
    add_bullet_item(doc, "Capital Capitalizado Inicial Base para Cuotas (P'): ", "P' = S/ 300.00 + S/ 2.21 = S/ 302.21.", space_after=8)
    
    add_heading_4(doc, "d) Determinación de la Cuota Fija Mensual Francesa (R):")
    add_body_paragraph(
        doc,
        "Aplicando la fórmula de anualidad vencida ordinaria sobre el capital capitalizado de S/ 302.21 para n = 3 cuotas mensuales:",
        space_after=4
    )
    add_native_equation(doc, r"R = 302.21 \times \left[ \frac{0.0201972}{1 - (1 + 0.0201972)^{-3}} \right] = S/\ 104.81 \text{ mensual}", space_after=8)
    
    add_heading_4(doc, "e) Cronograma Detallado de Amortización Francesa:")
    
    # Tabla 6.d.4 con rojo UPC
    tbl4 = doc.add_table(rows=5, cols=7)
    tbl4.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers4 = ["N° CUOTA", "VENCIMIENTO", "SALDO INICIAL (S/)", "CUOTA FIJA (S/)", "INTERÉS COMP. (S/)", "AMORTIZACIÓN (S/)", "SALDO FINAL (S/)"]
    for col_idx, h in enumerate(headers4):
        cell = tbl4.cell(0, col_idx)
        cell.text = h
        set_cell_margins_and_borders(cell, fill_hex="C8102E")
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.bold = True
                r.font.size = Pt(8)
                r.font.color.rgb = RGBColor(255, 255, 255)
                
    rows4_data = [
        ["Cuota 1", "26/09/2026", "302.21", "104.81", "6.10", "98.71", "203.50"],
        ["Cuota 2", "26/10/2026", "203.50", "104.81", "4.11", "100.70", "102.80"],
        ["Cuota 3", "25/11/2026", "102.80", "104.88", "2.08", "102.80", "0.00"],
        ["TOTALES", "3 Períodos", "-", "314.50", "12.29", "302.21", "-"]
    ]
    for row_idx, data in enumerate(rows4_data):
        fill = "F2F2F2" if row_idx % 2 == 1 else "FFFFFF"
        if row_idx == 3:
            fill = "E2E8F0"
        for col_idx, val in enumerate(data):
            cell = tbl4.cell(row_idx + 1, col_idx)
            cell.text = val
            set_cell_margins_and_borders(cell, fill_hex=fill)
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if col_idx >= 2 else WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs:
                    r.font.size = Pt(8)
                    if row_idx == 3:
                        r.font.bold = True
                        
    p_cap4 = doc.add_paragraph()
    p_cap4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap4.paragraph_format.space_before = Pt(3)
    p_cap4.paragraph_format.space_after = Pt(6)
    r_cap4 = p_cap4.add_run("Tabla 6.d.4: Cronograma mensual de amortización por el Método Francés con Gracia Total.")
    r_cap4.font.size = Pt(8.5)
    r_cap4.font.italic = True
    
    add_body_paragraph(
        doc,
        "Nota de Ajuste de Cierre: En la cuota 3 se ajusta el redondeo final a S/ 104.88 para extinguir con exactitud "
        "el saldo insoluto remanente de S/ 102.80, tal como lo exige el reglamento del curso.",
        space_after=10
    )
    
    # SUBSECCIÓN F: EVALUACIÓN FINANCIERA COMPLETAMENTE DESAHOGADA, CON TABLA Y CAJA DE DIAGNÓSTICO
    add_heading_4(doc, "f) Flujo de Caja y Evaluación Financiera (TIR, VAN, TCEA):")
    add_body_paragraph(
        doc,
        "A continuación se presenta la evaluación integral de rentabilidad del financiamiento comercial otorgado, "
        "contrastando los flujos netos percibidos frente al costo de oportunidad del capital del establecimiento:",
        space_after=8
    )
    
    # 1. COK
    add_bullet_item(doc, "1. Costo de Oportunidad del Capital del Comercio (COK):", "", space_after=3)
    add_body_paragraph(
        doc,
        "La tasa mínima de rentabilidad anual exigida por la propietaria del negocio es del 15.00% anual (COK_anual = 15.00%). "
        "Su tasa mensual equivalente en base comercial de 360 días se formula como:",
        space_after=4
    )
    add_native_equation(doc, r"COK_{mes} = (1 + 0.15)^{\frac{30}{360}} - 1 = 1.17149\% \text{ mensual}", space_after=8)
    
    # 2. Vector de Flujo de Caja
    add_bullet_item(doc, "2. Vector Cronológico de Flujos de Caja Netos de la Operación:", "", space_after=4)
    add_body_paragraph(
        doc,
        "La corriente de liquidez real generada entre el desembolso inicial de insumos y los cobros mensuales en caja se detalla a continuación:",
        space_after=6
    )
    
    # Mini-tabla 6.d.5 de Flujo de Caja con rojo UPC
    tbl_fc = doc.add_table(rows=5, cols=4)
    tbl_fc.alignment = WD_TABLE_ALIGNMENT.CENTER
    fc_headers = ["PERÍODO (MES)", "FECHA DE LIQUIDACIÓN", "CONCEPTO FINANCIERO", "FLUJO NETO (S/)"]
    for col_idx, h in enumerate(fc_headers):
        cell = tbl_fc.cell(0, col_idx)
        cell.text = h
        set_cell_margins_and_borders(cell, fill_hex="C8102E")
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.bold = True
                r.font.size = Pt(8.5)
                r.font.color.rgb = RGBColor(255, 255, 255)
                
    fc_data = [
        ["Mes 0", "15/09/2026", "Desembolso inicial (3 sacos de harina especial e insumos)", "-300.00"],
        ["Mes 1 (Cuota 1)", "26/09/2026", "Cobro Cuota 1 (11 días de gracia total capitalizados)", "+104.81"],
        ["Mes 2 (Cuota 2)", "26/10/2026", "Cobro Cuota 2 ordinaria", "+104.81"],
        ["Mes 3 (Cuota 3)", "25/11/2026", "Cobro Cuota 3 y liquidación definitiva", "+104.88"]
    ]
    for row_idx, data in enumerate(fc_data):
        fill = "F2F2F2" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, val in enumerate(data):
            cell = tbl_fc.cell(row_idx + 1, col_idx)
            cell.text = val
            set_cell_margins_and_borders(cell, fill_hex=fill)
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if col_idx == 3 else (WD_ALIGN_PARAGRAPH.CENTER if col_idx < 2 else WD_ALIGN_PARAGRAPH.LEFT)
                for r in p.runs:
                    r.font.size = Pt(8.5)
                    if col_idx == 3:
                        r.font.bold = True
                        
    p_cap_fc = doc.add_paragraph()
    p_cap_fc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap_fc.paragraph_format.space_before = Pt(3)
    p_cap_fc.paragraph_format.space_after = Pt(10)
    r_cap_fc = p_cap_fc.add_run("Tabla 6.d.5: Vector de Flujos de Caja Netos de la operación de crédito comercial.")
    r_cap_fc.font.size = Pt(8.5)
    r_cap_fc.font.italic = True
    
    # 3. VAN
    add_bullet_item(doc, "3. Valor Actual Neto (VAN):", "", space_after=3)
    add_body_paragraph(
        doc,
        "Actualizando los flujos percibidos a la tasa de descuento mensual del negocio (COK_mes = 1.17149%):",
        space_after=4
    )
    add_native_equation(doc, r"VAN = -300.00 + \frac{104.81}{(1 + 0.0117149)^1} + \frac{104.81}{(1 + 0.0117149)^2} + \frac{104.88}{(1 + 0.0117149)^3}")
    add_native_equation(doc, r"VAN = -300.00 + 103.60 + 102.40 + 102.64 = +S/\ 8.64")
    add_body_paragraph(
        doc,
        "El Valor Actual Neto obtenido es de +S/ 8.64, lo cual confirma que el crédito supera la rentabilidad mínima exigida.",
        space_after=8
    )
    
    # 4. TIR
    add_bullet_item(doc, "4. Tasa Interna de Retorno (TIR):", "", space_after=3)
    add_body_paragraph(
        doc,
        "Determinando la tasa que equilibra el desembolso inicial con el valor presente de las cuotas percibidas:",
        space_after=4
    )
    add_native_equation(doc, r"-300.00 + \frac{104.81}{(1 + TIR_{mes})^1} + \frac{104.81}{(1 + TIR_{mes})^2} + \frac{104.88}{(1 + TIR_{mes})^3} = 0")
    add_native_equation(doc, r"TIR_{mes} = 2.2610\% \text{ mensual}")
    add_native_equation(doc, r"TIR_{anual} = (1 + 0.022610)^{12} - 1 = 30.72\% \text{ anual}")
    add_body_paragraph(
        doc,
        "La Tasa Interna de Retorno efectiva anualizada alcanza el 30.72% anual, superando ampliamente el costo de oportunidad del comercio.",
        space_after=8
    )
    
    # 5. TCEA
    add_bullet_item(doc, "5. Tasa de Costo Efectivo Anual (TCEA para el Cliente):", "", space_after=3)
    add_body_paragraph(
        doc,
        "Al no existir gastos administrativos adicionales, comisiones de estructuración ni seguros vinculados, "
        "la Tasa de Costo Efectivo Anual coincide con la TIR anualizada de la operación:",
        space_after=4
    )
    add_native_equation(doc, r"TCEA = 30.72\% \text{ anual}")
    add_body_paragraph(
        doc,
        "Este valor representa el costo financiero total real asumido por la clienta durante el horizonte del crédito.",
        space_after=10
    )
    
    # 6. Diagnóstico y Conclusión
    add_callout_box(
        doc,
        "Conclusión y Diagnóstico Financiero: ",
        "Como el Valor Actual Neto es estrictamente positivo (VAN = +S/ 8.64 > 0) y la Tasa Interna de Retorno "
        "(TIR = 30.72% anual) supera con amplitud el costo de oportunidad del capital del negocio (COK = 15.00% anual), "
        "se comprueba fehacientemente que el otorgamiento del crédito no solo es solvente y autosuficiente, sino que "
        "genera un excedente económico neto que incrementa el patrimonio comercial del establecimiento."
    )
    
    print("Sección 6.d construida con éxito con tablas rojas UPC.")

# -----------------------------------------------------------------------------
# EJECUCIÓN PRINCIPAL
# -----------------------------------------------------------------------------
def main():
    base_dir = r"C:\Users\Frank\Documents\antigravity\happy-carson\stonks"
    doc_path = os.path.join(base_dir, "Finanzas Trabajo Parcial_backup.docx")
    target_path = os.path.join(base_dir, "Finanzas Trabajo Parcial.docx")
    output_complete = os.path.join(base_dir, "Finanzas Trabajo Parcial_Completo.docx")
    
    print(f"Cargando documento base: {doc_path}")
    doc = docx.Document(doc_path)
    
    print("Construyendo Sección 6.b (Diseño de la Interfaz)...")
    build_section_6b(doc)
    
    print("Construyendo Sección 6.c (Marco conceptual - Fórmulas limpias en OMML)...")
    build_section_6c(doc)
    
    print("Construyendo Sección 6.d (Diseño de Datos de prueba con tablas rojas UPC)...")
    build_section_6d(doc)
    
    print(f"Guardando documento completo en: {output_complete}")
    doc.save(output_complete)
    print("¡Finanzas Trabajo Parcial_Completo.docx guardado con éxito!")
    
    try:
        doc.save(target_path)
        print(f"¡{target_path} actualizado exitosamente!")
    except Exception as e:
        print(f"Aviso: No se pudo sobrescribir directamente '{target_path}' porque Word lo tiene abierto ({e}).")
        print(f"El documento completo y actualizado está disponible en: '{output_complete}'.")

if __name__ == "__main__":
    main()
