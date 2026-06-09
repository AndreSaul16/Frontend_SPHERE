"""
CTO Spiders - GitHub Governance
================================
Spider especializado en extraer documentación de gobernanza y arquitectura
de repositorios críticos de GitHub.
"""

import os
import sys
import time
import requests
import base64

# Importar clase base
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core.base_spider import BaseTechSpider


class GitHubGovernanceSpider(BaseTechSpider):
    """
    Spider especializado en extraer documentación de gobernanza y arquitectura
    de repositorios críticos de GitHub.
    
    Solo busca archivos .md de alto nivel, NO código.
    """
    
    # Lista de repositorios curados manualmente (La Lista de Oro)
    CRITICAL_REPOS = [
        {
            'owner': 'kubernetes',
            'repo': 'kubernetes',
            'paths': ['docs/design-proposals', 'docs/architecture'],
            'files': ['ARCHITECTURE.md', 'CONTRIBUTING.md', 'GOVERNANCE.md']
        },
        {
            'owner': 'elastic',
            'repo': 'elasticsearch',
            'paths': ['docs/reference/setup'],
            'files': ['CONTRIBUTING.md']
        },
        {
            'owner': 'pytorch',
            'repo': 'pytorch',
            'paths': ['docs/source/notes'],
            'files': ['CONTRIBUTING.md']
        },
        {
            'owner': 'facebook',
            'repo': 'react',
            'paths': ['docs/design'],
            'files': ['CONTRIBUTING.md']
        },
        {
            'owner': 'torvalds',
            'repo': 'linux',
            'paths': ['Documentation/process'],
            'files': ['README', 'MAINTAINERS']
        }
    ]
    
    def __init__(self):
        super().__init__(agent_name="CTO")
        # Token de GitHub (opcional, aumenta rate limit)
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.api_headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'SPHERE-Tech-Monitor'
        }
        if self.github_token:
            self.api_headers['Authorization'] = f'token {self.github_token}'
    
    def fetch_github_file(self, owner, repo, path):
        """Descarga un archivo específico de GitHub usando la API."""
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        
        try:
            response = requests.get(api_url, headers=self.api_headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # GitHub devuelve el contenido en base64
                if 'content' in data:
                    content = base64.b64decode(data['content']).decode('utf-8')
                    return content, data.get('download_url')
                elif 'download_url' in data:
                    # Fallback: descargar directamente
                    dl_response = requests.get(data['download_url'], timeout=15)
                    return dl_response.text, data['download_url']
            
            return None, None
            
        except Exception as e:
            print(f"      ⚠️ Error descargando {path}: {e}")
            return None, None
    
    def run(self, limit_per_repo=10):
        print(f"\n🏛️ [{self.__class__.__name__}] Extrayendo Gobernanza de GitHub...")
        
        total_docs = 0
        
        for repo_config in self.CRITICAL_REPOS:
            owner = repo_config['owner']
            repo = repo_config['repo']
            
            print(f"\n   📦 Repositorio: {owner}/{repo}")
            
            # 1. Buscar archivos específicos en la raíz
            for filename in repo_config.get('files', []):
                if total_docs >= limit_per_repo * len(self.CRITICAL_REPOS):
                    break
                
                file_url = f"https://github.com/{owner}/{repo}/blob/main/{filename}"
                
                if self.url_exists(file_url):
                    print(f"      💤 Ya existe: {filename}")
                    continue
                
                print(f"      📄 Descargando: {filename}")
                content, download_url = self.fetch_github_file(owner, repo, filename)
                
                if content and len(content) > 200:
                    # ✅ Guardar como .md puro (Bronze Layer)
                    filepath = self.save_raw_markdown(
                        content, 
                        f"{owner}_{repo}_{filename}",
                        agent_subdir="cto/github",
                        prefix=""
                    )
                    
                    doc = {
                        "source": f"GitHub - {owner}/{repo}",
                        "title": f"{repo}: {filename}",
                        "url": file_url,
                        "github_raw_url": download_url,
                        "file_path": filepath,  # ✅ Referencia al .md local
                        "content_markdown": content,
                        "tags": ["governance", "architecture", repo, owner],
                        "repo_full_name": f"{owner}/{repo}",
                        "file_type": "governance_document"
                    }
                    self.save_knowledge(doc)
                    total_docs += 1
                    time.sleep(1)
            
            # 2. Buscar en carpetas específicas
            for path in repo_config.get('paths', []):
                if total_docs >= limit_per_repo * len(self.CRITICAL_REPOS):
                    break
                
                api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
                
                try:
                    response = requests.get(api_url, headers=self.api_headers, timeout=15)
                    
                    if response.status_code == 200:
                        files = response.json()
                        
                        # Filtrar solo archivos .md
                        md_files = [f for f in files if isinstance(f, dict) and f.get('name', '').endswith('.md')]
                        
                        for md_file in md_files[:5]:  # Limitar a 5 por carpeta
                            file_url = md_file.get('html_url')
                            file_path = md_file.get('path')
                            
                            if self.url_exists(file_url):
                                continue
                            
                            print(f"      📄 Descargando: {file_path}")
                            content, download_url = self.fetch_github_file(owner, repo, file_path)
                            
                            if content and len(content) > 200:
                                # ✅ Guardar como .md puro (Bronze Layer)
                                filepath = self.save_raw_markdown(
                                    content,
                                    f"{owner}_{repo}_{md_file.get('name')}",
                                    agent_subdir="cto/github",
                                    prefix=""
                                )
                                
                                doc = {
                                    "source": f"GitHub - {owner}/{repo}",
                                    "title": f"{repo}: {md_file.get('name')}",
                                    "url": file_url,
                                    "github_raw_url": download_url,
                                    "file_path": filepath,  # ✅ Referencia al .md local
                                    "content_markdown": content,
                                    "tags": ["design-proposal", "architecture", repo],
                                    "repo_full_name": f"{owner}/{repo}",
                                    "file_type": "design_document"
                                }
                                self.save_knowledge(doc)
                                total_docs += 1
                                time.sleep(1)
                    
                except Exception as e:
                    print(f"      ⚠️ Error explorando {path}: {e}")
        
        print(f"\n   ✅ Total de documentos de gobernanza extraídos: {total_docs}")


if __name__ == "__main__":
    spider = GitHubGovernanceSpider()
    spider.run(limit_per_repo=10)
