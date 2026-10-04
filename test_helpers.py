# -*- coding: utf-8 -*-
"""
Script to add Section 6 and Section 6.a (Análisis de Datos) to Finanzas Trabajo Parcial.docx
"""
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def set_cell_border_and_shading(cell, fill_hex=None, border_color="bfbfbf", border_sz="4"):
    tcPr = cell._tc.get_or_add_tcPr()
    
    # Border XML
    tcBorders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="single" w:sz="{border_sz}" w:space="0" w:color="{border_color}"/>\n'
        f'  <w:left w:val="single" w:sz="{border_sz}" w:space="0" w:color="{border_color}"/>\n'
        f'  <w:bottom w:val="single" w:sz="{border_sz}" w:space="0" w:color="{border_color}"/>\n'
        f'  <w:right w:val="single" w:sz="{border_sz}" w:space="0" w:color="{border_color}"/>\n'
        f'</w:tcBorders>'
    )
    tcPr.append(tcBorders)
    
    # Shading
    if fill_hex:
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}" w:val="clear"/>')
        tcPr.append(shd)
        
    # Margins (padding)
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>\n'
        f'  <w:top w:w="80" w:type="dxa"/>\n'
        f'  <w:left w:w="120" w:type="dxa"/>\n'
        f'  <w:bottom w:w="80" w:type="dxa"/>\n'
        f'  <w:right w:w="120" w:type="dxa"/>\n'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)
    
    # Vertical alignment
    vAlign = parse_xml(f'<w:vAlign {nsdecls("w")} w:val="top"/>')
    tcPr.append(vAlign)

def set_table_properties(table, col_widths, total_width_dxa=9360):
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    tblPr = table._tbl.tblPr
    
    # Table borders nil at table level
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="nil" w:sz="0" w:space="0" w:color="000000"/>\n'
        f'  <w:left w:val="nil" w:sz="0" w:space="0" w:color="000000"/>\n'
        f'  <w:bottom w:val="nil" w:sz="0" w:space="0" w:color="000000"/>\n'
        f'  <w:right w:val="nil" w:sz="0" w:space="0" w:color="000000"/>\n'
        f'  <w:insideH w:val="nil" w:sz="0" w:space="0" w:color="000000"/>\n'
        f'  <w:insideV w:val="nil" w:sz="0" w:space="0" w:color="000000"/>\n'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)
    
    tblW = parse_xml(f'<w:tblW {nsdecls("w")} w:w="{total_width_dxa}" w:type="dxa"/>')
    tblPr.append(tblW)
    
    layout = parse_xml(f'<w:tblLayout {nsdecls("w")} w:type="fixed"/>')
    tblPr.append(layout)
    
    # Set explicit widths for columns in each row
    for row in table.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = width

print("Helper definitions loaded successfully.")
