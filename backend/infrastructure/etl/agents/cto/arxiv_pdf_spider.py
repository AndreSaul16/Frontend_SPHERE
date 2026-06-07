"""
CTO Spider - ArXiv PDF Downloader
==================================
Spider para descargar PDFs de ArXiv que están marcados como pendientes en MongoDB.
"""

import os
import sys
import time
import requests
import re
import certifi
from urllib.parse import urlparse

# Importar clase base
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core.base_spider import BaseTechSpider, RAW_DATA_DIR


class ArxivPDFSpider(BaseTechSpider):
    """
    Spider para descargar PDFs de ArXiv desde MongoDB.
    Lee documentos con needs_pdf_processing=True y descarga sus PDFs.
    """
    
    def __init__(self):
        super().__init__(agent_name="CTO")
        self.save_dir = os.path.join(RAW_DATA_DIR, "cto", "papers")
        os.makedirs(self.save_dir, exist_ok=True)
    
    def sanitize_filename(self, title):
        """Sanitiza el título para usarlo como nombre de archivo."""
        # Remover caracteres no permitidos
        clean_title = re.sub(r'[^\w\s-]', '', title).strip().lower()
        # Reemplazar espacios con guiones
        clean_title = re.sub(r'[-\s]+', '-', clean_title)
        # Limitar longitud
        return clean_title[:60]
    
    def download_pdf(self, pdf_url, title):
        """
        Descarga un PDF desde ArXiv.
        
        Args:
            pdf_url: URL del PDF
            title: Título del paper (para el nombre del archivo)
        
        Returns:
            filepath: Ruta completa del archivo descargado, o None si falla
        """
        try:
            print(f"      📥 Descargando PDF: {title[:50]}...")
            
            # Descargar PDF
            response = requests.get(pdf_url, headers=self.headers, timeout=30, verify=certifi.where())
            response.raise_for_status()
            
            # Validar que es un PDF
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower():
                print(f"      ⚠️ El contenido no es un PDF: {content_type}")
                return None
            
            # Generar nombre de archivo
            clean_title = self.sanitize_filename(title)
            filename = f"{clean_title}.pdf"
            filepath = os.path.join(self.save_dir, filename)
            
            # Guardar PDF
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            # Validar tamaño
            file_size = os.path.getsize(filepath) / 1024  # KB
            if file_size < 10:  # Menos de 10KB probablemente es un error
                print(f"      ⚠️ PDF muy pequeño ({file_size:.1f}KB), posible error")
                os.remove(filepath)
                return None
            
            print(f"      ✅ PDF descargado: {filename} ({file_size:.1f}KB)")
            return filepath
            
        except requests.exceptions.Timeout:
            print(f"      ⏱️ Timeout descargando PDF")
            return None
        except requests.exceptions.RequestException as e:
            print(f"      ❌ Error descargando PDF: {e}")
            return None
        except Exception as e:
            print(f"      🔥 Error inesperado: {e}")
            return None
    
    def run(self):
        """
        Ejecuta el spider:
        1. Consulta MongoDB por papers con needs_pdf_processing=True
        2. Descarga cada PDF
        3. Actualiza MongoDB con la ruta del PDF descargado
        """
        print(f"\n📄 [{self.__class__.__name__}] Descargando PDFs de ArXiv...")
        
        try:
            # Buscar papers pendientes de procesamiento
            pending_papers = list(self.collection.find(
                {
                    "agent_target": "CTO",
                    "needs_pdf_processing": True,
                    "pdf_url": {"$exists": True, "$ne": None}
                },
                {
                    "title": 1,
                    "pdf_url": 1,
                    "url": 1,
                    "_id": 0
                }
            ))
            
            if len(pending_papers) == 0:
                print("   ℹ️ No hay PDFs pendientes de descarga")
                return
            
            print(f"   📊 Encontrados {len(pending_papers)} PDFs pendientes")
            
            downloaded_count = 0
            failed_count = 0
            
            for paper in pending_papers:
                title = paper.get('title', 'untitled')
                pdf_url = paper.get('pdf_url')
                paper_id = paper.get('url')  # El ID de ArXiv se guarda en url
                
                print(f"\n   📄 Procesando: {title[:60]}...")
                
                # Descargar PDF
                filepath = self.download_pdf(pdf_url, title)
                
                if filepath:
                    # Actualizar MongoDB con la ruta del PDF
                    self.collection.update_one(
                        {"url": paper_id},
                        {
                            "$set": {
                                "raw_pdf_path": filepath,
                                "pdf_downloaded": True,
                                "pdf_downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S")
                            },
                            "$unset": {
                                "needs_pdf_processing": ""  # Remover el flag
                            }
                        }
                    )
                    downloaded_count += 1
                else:
                    print(f"      ⚠️ Fallo en la descarga, se reintentará más tarde")
                    failed_count += 1
                
                # Pausa para no saturar el servidor de ArXiv
                time.sleep(3)
            
            print(f"\n   📊 Resumen de descarga:")
            print(f"      ✅ Exitosas: {downloaded_count}")
            print(f"      ❌ Fallidas: {failed_count}")
            
        except Exception as e:
            print(f"   🔥 Error crítico en ArxivPDFSpider: {e}")


if __name__ == "__main__":
    spider = ArxivPDFSpider()
    spider.run()
