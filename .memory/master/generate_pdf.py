#!/usr/bin/env python3
"""
KAOS Multi-Agent Architecture Report - PDF Generator
Converts CONTENIDO-PDF.txt into a professional PDF using fpdf2.
"""

import re
import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos

FONT_DIR = "C:\\Windows\\Fonts"

class KAOSReport(FPDF):
    def __init__(self):
        super().__init__()
        self.section_counters = {}
        self.in_table = False
        self.table_cols = 0
        self.table_align = []
        self.table_header_done = False
        self._register_unicode_fonts()

    def _register_unicode_fonts(self):
        self.add_font('Arial', '', os.path.join(FONT_DIR, 'arial.ttf'), uni=True)
        self.add_font('Arial', 'B', os.path.join(FONT_DIR, 'arialbd.ttf'), uni=True)
        self.add_font('Arial', 'I', os.path.join(FONT_DIR, 'ariali.ttf'), uni=True)
        self.add_font('Arial', 'BI', os.path.join(FONT_DIR, 'arialbi.ttf'), uni=True)
        self.F = 'Arial'  # Default font family

    def header(self):
        if self.page_no() > 1:
            self.set_font(self.F, 'I', 7)
            self.set_text_color(120, 120, 120)
            self.cell(0, 4, 'KAOS - Ecosistema Multi-Agente 2026 | Mayo 2026 | v1.0', align='C')
            self.ln(1)
            self.set_draw_color(200, 200, 200)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(4)

    def footer(self):
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font(self.F, 'I', 7)
            self.set_text_color(120, 120, 120)
            self.cell(0, 10, f'Pagina {self.page_no() - 1}', align='C')

    def add_title_page(self):
        self.add_page()
        self.ln(40)
        self.set_font(self.F, 'B', 24)
        self.set_text_color(20, 60, 120)
        self.multi_cell(0, 10, 'ARQUITECTURAS MULTI-AGENTE', align='C')
        self.ln(3)
        self.set_font(self.F, 'B', 20)
        self.set_text_color(40, 100, 180)
        self.multi_cell(0, 9, 'ECOSISTEMA COMPLETO 2026', align='C')
        self.ln(8)
        self.set_font(self.F, '', 13)
        self.set_text_color(60, 60, 60)
        self.multi_cell(0, 7, 'OpenAI | Anthropic | Google Gemini | Alibaba Qwen | Moonshot Kimi', align='C')
        self.ln(15)
        self.set_draw_color(40, 100, 180)
        self.set_line_width(0.5)
        self.line(60, self.get_y(), 150, self.get_y())
        self.ln(10)
        self.set_font(self.F, '', 10)
        self.set_text_color(80, 80, 80)
        self.cell(0, 6, 'Fecha: Mayo 2026', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.cell(0, 6, 'Version: 1.0 - Consolidacion Estrategica KAOS', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.cell(0, 6, 'Investigacion: Aletheia | Arquitectura: Kosmos | Estrategia: Metis', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(10)
        self.set_font(self.F, '', 8)
        self.set_text_color(100, 100, 100)
        self.multi_cell(0, 4, 'Este documento consolida las investigaciones masivas de los 5 grandes laboratorios de IA, '
                      'analizando sus arquitecturas multi-agente, modelos, precios, benchmarks, patrones de orquestacion, '
                      'protocolos de comunicacion, estrategias de caching, seguridad, y ecosistemas completos. '
                      'Incluye el analisis del source leak de Claude Code (31 Marzo 2026) y su aplicacion a KAOS.', align='C')

    def add_toc_page(self):
        self.add_page()
        self.set_font(self.F, 'B', 16)
        self.set_text_color(20, 60, 120)
        self.cell(0, 10, 'INDICE', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(5)
        toc_items = [
            ('PARTE 1: Mapa del Ecosistema', []),
            ('  1.1 OpenAI - Ficha Completa', []),
            ('  1.2 Anthropic - Ficha Completa', []),
            ('  1.3 Google Gemini - Ficha Completa', []),
            ('  1.4 Alibaba Qwen - Ficha Completa', []),
            ('  1.5 Moonshot Kimi - Ficha Completa', []),
            ('  1.6 Tablas Comparativas Globales', []),
            ('  1.7 Taxonomia de Conceptos Tecnicos', []),
            ('PARTE 2: Source Leak de Claude Code', []),
            ('PARTE 3: Conexion con KAOS', []),
            ('PARTE 4: Costos y Proyecciones', []),
            ('PARTE 5: Roadmap 4 Fases', []),
            ('PARTE 6: Anti-Recomendaciones', []),
            ('PARTE 7: Preguntas Abiertas', []),
            ('Apendice: Referencias y Fuentes', []),
        ]
        for item, _ in toc_items:
            is_main = item.startswith('PARTE')
            self.set_font(self.F, 'B' if is_main else '', 10 if is_main else 9)
            self.set_text_color(20, 60, 120 if is_main else 60)
            indent = 0 if is_main else 5
            x = 15 + indent
            self.set_x(x)
            self.cell(0, 6, item, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def render_content(self, content_path):
        with open(content_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            i += 1

            # Skip empty lines
            if not line:
                continue

            # Page break
            if '--- pagebreak ---' in line:
                self.add_page()
                continue

            # Separator
            if line.startswith('---') and 'pagebreak' not in line:
                self.set_draw_color(180, 180, 180)
                self.set_line_width(0.3)
                y = self.get_y()
                if y > 260:
                    self.add_page()
                else:
                    self.line(15, y, 195, y)
                    self.ln(3)
                continue

            # H1 title
            if line.startswith('# ') and not line.startswith('## '):
                text = line[2:].strip()
                self.set_font(self.F, 'B', 16)
                self.set_text_color(20, 60, 120)
                if self.get_y() > 240:
                    self.add_page()
                self.multi_cell(0, 8, text, align='L')
                self.ln(2)
                continue

            # H2 title
            if line.startswith('## '):
                text = line[3:].strip()
                self.set_font(self.F, 'B', 13)
                self.set_text_color(40, 100, 180)
                if self.get_y() > 250:
                    self.add_page()
                self.multi_cell(0, 7, text, align='L')
                self.ln(1)
                continue

            # H3 title
            if line.startswith('### '):
                text = line[4:].strip()
                self.set_font(self.F, 'B', 11)
                self.set_text_color(60, 60, 60)
                if self.get_y() > 260:
                    self.add_page()
                self.multi_cell(0, 6, text, align='L')
                self.ln(1)
                continue

            # Quote
            if line.startswith('>'):
                text = line[1:].strip()
                self.set_font(self.F, 'I', 9)
                self.set_text_color(80, 80, 80)
                x = self.get_x()
                self.set_x(x + 10)
                self.multi_cell(0, 4.5, text, align='L')
                self.set_x(x)
                self.ln(1)
                continue

            # Note
            if line.startswith('[NOTA:'):
                text = line.strip()
                self.set_font(self.F, 'I', 8)
                self.set_text_color(100, 100, 60)
                self.set_fill_color(255, 255, 230)
                self.multi_cell(0, 4, text, align='L', fill=True)
                self.ln(1)
                continue

            # Table row
            if line.startswith('|') and line.endswith('|'):
                self.render_table_row(line)
                continue

            # Regular text - handle bold (**text**), etc.
            if line and not line.startswith('|') and not line.startswith('#'):
                self.render_text_line(line)
                continue

    def render_text_line(self, line):
        self.set_font(self.F, '', 9)
        self.set_text_color(40, 40, 40)
        if self.get_y() > 265:
            self.add_page()
        parts = re.split(r'(\*\*.*?\*\*)', line)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                bold_text = part[2:-2]
                self.set_font(self.F, 'B', 9)
                self.write(4.5, bold_text)
                self.set_font(self.F, '', 9)
            else:
                self.write(4.5, part + ' ')
        self.ln(4.5)

    def render_table_row(self, line):
        cells = [c.strip() for c in line.strip('|').split('|')]
        num_cols = len(cells)
        
        # Check if this is a separator row (---)
        if all(re.match(r'^-+$', c) for c in cells):
            self.in_table = False
            self.table_header_done = True
            return

        col_width = min(175 / max(num_cols, 1), 50)
        
        if not self.table_header_done:
            self.set_font(self.F, 'B', 7.5)
            self.set_fill_color(40, 100, 180)
            self.set_text_color(255, 255, 255)
        else:
            self.set_font(self.F, '', 7.5)
            self.set_text_color(40, 40, 40)
            if hasattr(self, '_row_counter'):
                self._row_counter += 1
            else:
                self._row_counter = 0
            if self._row_counter % 2 == 0:
                self.set_fill_color(245, 248, 255)
            else:
                self.set_fill_color(255, 255, 255)

        if self.get_y() > 260:
            self.add_page()
            self.table_header_done = True
            self.set_font(self.F, '', 7.5)
            self.set_text_color(40, 40, 40)
            self.set_fill_color(245, 248, 255)

        max_lines = 1
        for cell in cells:
            text_width = self.get_string_width(cell)
            needed_lines = max(1, int(text_width / col_width) + (1 if text_width % col_width > 0 else 0))
            max_lines = max(max_lines, needed_lines)

        row_height = max(5, max_lines * 4)
        
        for j, cell in enumerate(cells):
            x = self.get_x()
            self.set_font(self.F, 'B' if not self.table_header_done else '', 7.5)
            self.cell(col_width, row_height, cell, border=1, 
                     fill=True, align='L' if j == 0 else 'C')
            self.set_x(x + col_width)
        
        self.ln(row_height)


def main():
    content_path = os.path.join(os.path.dirname(__file__), 'CONTENIDO-PDF.txt')
    output_path = os.path.join(os.path.dirname(__file__), 'MASTER-ECOSISTEMA-MULTI-AGENTE-2026.pdf')
    
    if not os.path.exists(content_path):
        print(f"ERROR: Content file not found at {content_path}")
        return

    print(f"Generating PDF from {content_path}...")
    pdf = KAOSReport()
    pdf.set_auto_page_break(auto=True, margin=18)
    
    # Title page
    pdf.add_title_page()
    
    # Table of contents
    pdf.add_toc_page()
    
    # Content
    pdf.render_content(content_path)
    
    # Output
    pdf.output(output_path)
    print(f"PDF generated successfully: {output_path}")
    print(f"Pages: {pdf.page_no() - 1}")  # Subtract title page


if __name__ == '__main__':
    main()
