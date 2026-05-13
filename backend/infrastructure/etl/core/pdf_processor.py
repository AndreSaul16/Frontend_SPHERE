"""
ETL Core - PDF Processor
========================
Utilidad para extraer texto y metadata de archivos PDF.
"""

import os
try:
    import PyPDF2
    import pdfplumber
    PDF_LIBS_AVAILABLE = True
except ImportError:
    PDF_LIBS_AVAILABLE = False
    print("⚠️ PyPDF2 o pdfplumber no instalados. Ejecuta: pip install PyPDF2 pdfplumber")


class PDFProcessor:
    """
    Procesador de PDFs con múltiples backends de extracción.
    """
    
    def __init__(self):
        if not PDF_LIBS_AVAILABLE:
            raise ImportError("Se requiere PyPDF2 y pdfplumber. Ejecuta: pip install PyPDF2==3.0.1 pdfplumber==0.10.3")
    
    def extract_text_pypdf2(self, pdf_path):
        """
        Extrae texto usando PyPDF2 (rápido pero menos preciso).
        
        Args:
            pdf_path: Ruta al archivo PDF
        
        Returns:
            str: Texto extraído
        """
        try:
            text_parts = []
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            return '\n\n'.join(text_parts)
        except Exception as e:
            print(f"   ⚠️ Error con PyPDF2: {e}")
            return None
    
    def extract_text_pdfplumber(self, pdf_path):
        """
        Extrae texto usando pdfplumber (más lento pero más preciso).
        
        Args:
            pdf_path: Ruta al archivo PDF
        
        Returns:
            str: Texto extraído
        """
        try:
            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            return '\n\n'.join(text_parts)
        except Exception as e:
            print(f"   ⚠️ Error con pdfplumber: {e}")
            return None
    
    def extract_metadata(self, pdf_path):
        """
        Extrae metadata del PDF.
        
        Args:
            pdf_path: Ruta al archivo PDF
        
        Returns:
            dict: Metadata extraída
        """
        try:
            metadata = {}
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                # Metadata básica
                info = reader.metadata
                if info:
                    metadata['author'] = info.get('/Author', '')
                    metadata['title'] = info.get('/Title', '')
                    metadata['subject'] = info.get('/Subject', '')
                    metadata['creator'] = info.get('/Creator', '')
                
                # Número de páginas
                metadata['num_pages'] = len(reader.pages)
                
                # Tamaño del archivo
                metadata['file_size_kb'] = os.path.getsize(pdf_path) / 1024
                
            return metadata
        except Exception as e:
            print(f"   ⚠️ Error extrayendo metadata: {e}")
            return {}
    
    def process_pdf(self, pdf_path, method='pdfplumber'):
        """
        Procesa un PDF completo: extrae texto y metadata.
        
        Args:
            pdf_path: Ruta al archivo PDF
            method: 'pypdf2' o 'pdfplumber' (default)
        
        Returns:
            dict: Diccionario con texto y metadata
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")
        
        result = {
            'pdf_path': pdf_path,
            'text': None,
            'metadata': {},
            'success': False
        }
        
        # Extraer metadata
        result['metadata'] = self.extract_metadata(pdf_path)
        
        # Extraer texto
        if method == 'pypdf2':
            text = self.extract_text_pypdf2(pdf_path)
        else:  # pdfplumber por defecto
            text = self.extract_text_pdfplumber(pdf_path)
        
        # Si falla el método primario, intentar con el otro
        if not text or len(text.strip()) < 100:
            print(f"   🔄 Reintentando con método alternativo...")
            if method == 'pypdf2':
                text = self.extract_text_pdfplumber(pdf_path)
            else:
                text = self.extract_text_pypdf2(pdf_path)
        
        if text and len(text.strip()) > 100:
            result['text'] = text
            result['success'] = True
            result['char_count'] = len(text)
            result['word_count'] = len(text.split())
        
        return result
    
    def to_markdown(self, text):
        """
        Convierte texto plano a Markdown básico.
        
        Args:
            text: Texto extraído del PDF
        
        Returns:
            str: Texto en formato Markdown
        """
        if not text:
            return ""
        
        # Dividir en párrafos
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # Unir con doble salto de línea (formato Markdown)
        markdown = '\n\n'.join(paragraphs)
        
        return markdown


if __name__ == "__main__":
    # Ejemplo de uso
    processor = PDFProcessor()
    
    # Test con un PDF (si existe)
    test_pdf = "path/to/test.pdf"
    if os.path.exists(test_pdf):
        result = processor.process_pdf(test_pdf)
        if result['success']:
            print(f"✅ Texto extraído: {result['word_count']} palabras")
            print(f"📊 Metadata: {result['metadata']}")
        else:
            print("❌ Fallo en la extracción")
