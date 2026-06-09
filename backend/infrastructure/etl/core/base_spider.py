"""
ETL Core - Base Spider
======================
Clase base compartida entre todos los spiders de vigilancia tecnológica.
"""

import os
import requests
import time
import re
import ssl
from pymongo import MongoClient
from dotenv import load_dotenv
from abc import ABC, abstractmethod
import trafilatura
import certifi

# Configuración global
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

MONGODB_URL = os.getenv("MONGODB_URL")
DB_NAME = os.getenv("DB_NAME", "sphere_db")

# Rutas del proyecto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw")


class BaseTechSpider(ABC):
    """
    Clase base para todos los spiders de vigilancia tecnológica.
    Maneja conexión DB, detección de duplicados y guardado estandarizado.
    """
    
    def __init__(self, agent_name="CTO"):
        self.agent_name = agent_name
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9,es;q=0.8'
        }
        
        # Conexión DB compartida
        try:
            self.client = MongoClient(
                MONGODB_URL,
                tls=True,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=30000,
                connectTimeoutMS=30000,
                socketTimeoutMS=30000
            )
            self.db = self.client[DB_NAME]
            self.collection = self.db["knowledge_base"]
            # Ping para verificar
            self.client.admin.command('ping')
            print(f"✅ [{self.__class__.__name__}] Conectado a MongoDB ({DB_NAME})")
        except Exception as e:
            print(f"❌ Error crítico DB en {self.__class__.__name__}: {e}")
            raise

    def url_exists(self, url):
        """
        Verifica si ya tenemos este artículo para no duplicar trabajo.
        Vital para ejecuciones periódicas (CRON).
        """
        return self.collection.count_documents({"url": url}, limit=1) > 0

    def save_knowledge(self, data):
        """
        Guarda en MongoDB estandarizando el formato.
        Añade metadata automática: timestamp, agente objetivo.
        """
        if not data: 
            return
        
        # Metadata automática
        data["ingested_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        data["agent_target"] = self.agent_name
        
        try:
            self.collection.update_one(
                {"url": data["url"]}, 
                {"$set": data}, 
                upsert=True
            )
            print(f"   ✅ [NUEVO] {data['title'][:50]}...")
        except Exception as e:
            print(f"   ❌ Error guardando: {e}")

    def extract_content(self, url):
        """
        Usa Trafilatura para extraer contenido limpio del HTML.
        
        CRÍTICO: Usamos requests con headers primero porque algunos sitios  
        (Medium, etc.) bloquean el User-Agent por defecto de Trafilatura.
        
        Retorna markdown con tablas incluidas.
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=15, verify=certifi.where())
            response.raise_for_status()
            html_content = response.text
            
            # ✅ Extraer con Trafilatura
            markdown = trafilatura.extract(
                html_content,
                output_format="markdown", 
                include_tables=True,
                include_links=True
            )
            
            return markdown
            
        except Exception as e:
            print(f"   ⚠️ Error extrayendo contenido: {e}")
            return None

    def save_raw_html(self, url, title, agent_subdir="", prefix=""):
        """
        Guarda el HTML raw en disco (Capa Bronze).
        
        Args:
            url: URL del contenido
            title: Título del documento
            agent_subdir: Subdirectorio específico del agente (ej: "cto/github")
            prefix: Prefijo para el archivo (ej: "Netflix_")
        
        Returns:
            filepath: Ruta completa del archivo guardado
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=15, verify=certifi.where())
            response.raise_for_status()

            # Sanitizar nombre de archivo
            clean_title = re.sub(r'[^\w\s-]', '', title).strip().lower()
            clean_title = re.sub(r'[-\s]+', '-', clean_title)[:50]
            filename = f"{prefix}{clean_title}.html"
            
            # Determinar directorio de guardado
            if agent_subdir:
                save_dir = os.path.join(RAW_DATA_DIR, agent_subdir)
            else:
                save_dir = os.path.join(RAW_DATA_DIR, self.agent_name.lower())
            
            os.makedirs(save_dir, exist_ok=True)
            filepath = os.path.join(save_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            return filepath
        except Exception as e:
            print(f"   ⚠️ Error guardando HTML: {e}")
            return None

    def save_raw_markdown(self, content, title, agent_subdir="", prefix=""):
        """
        Guarda contenido Markdown puro en disco (Capa Bronze).
        
        CRÍTICO: Usa esto para documentación de GitHub donde queremos
        preservar la estructura markdown (#, ##, etc.) sin etiquetas HTML.
        
        Args:
            content: Contenido markdown en texto plano
            title: Título del documento
            agent_subdir: Subdirectorio específico del agente (ej: "cto/github")
            prefix: Prefijo para el archivo (ej: "kubernetes_")
        
        Returns:
            filepath: Ruta completa del archivo guardado
        """
        try:
            # Sanitizar nombre de archivo
            clean_title = re.sub(r'[^\w\s-]', '', title).strip().lower()
            clean_title = re.sub(r'[-\s]+', '-', clean_title)[:50]
            filename = f"{prefix}{clean_title}.md"  # ✅ Extensión .md
            
            # Determinar directorio de guardado
            if agent_subdir:
                save_dir = os.path.join(RAW_DATA_DIR, agent_subdir)
            else:
                save_dir = os.path.join(RAW_DATA_DIR, self.agent_name.lower())
            
            os.makedirs(save_dir, exist_ok=True)
            filepath = os.path.join(save_dir, filename)
            
            # Guardar contenido markdown puro
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return filepath
        except Exception as e:
            print(f"   ⚠️ Error guardando Markdown: {e}")
            return None

    @abstractmethod
    def run(self):
        """
        Cada spider hijo debe implementar su propia lógica de búsqueda.
        Este método es llamado por el orquestador.
        """
        pass
