"""
URL Validator
=============
Valida todas las URLs de un corpus antes de ejecutar los spiders.
Verifica códigos HTTP, acceso a contenido, SSL, y genera reportes.
"""

import warnings
import certifi
import requests
import urllib3
import time
import re
from urllib.parse import urlparse
from datetime import datetime
from typing import Dict, List, Tuple
import argparse

# Colores para terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class URLValidator:
    """Validador de URLs con retry y detección de problemas."""
    
    def __init__(self, timeout=15, retries=2):
        self.timeout = timeout
        self.retries = retries
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,es;q=0.8'
        }
        
        self.results = {
            'valid': [],
            'invalid': [],
            'warnings': []
        }
    
    def validate_url(self, url: str, context: str = "") -> Dict:
        """
        Valida una URL individual.
        
        Returns:
            Dict con: status, code, accessible, size, error, redirects
        """
        result = {
            'url': url,
            'context': context,
            'status': 'unknown',
            'code': None,
            'accessible': False,
            'size_bytes': 0,
            'error': None,
            'redirects': [],
            'ssl_valid': True
        }
        
        for attempt in range(self.retries):
            try:
                # Intentar con verificación SSL
                try:
                    response = requests.get(
                        url,
                        headers=self.headers,
                        timeout=self.timeout,
                        allow_redirects=True,
                        verify=certifi.where()
                    )
                except requests.exceptions.SSLError:
                    # Fallback sin verificación SSL para detectar URLs accesibles con cert inválido
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", urllib3.exceptions.InsecureRequestWarning)
                        response = requests.get(
                            url,
                            headers=self.headers,
                            timeout=self.timeout,
                            allow_redirects=True,
                            verify=False
                        )
                    result['ssl_valid'] = False
                
                result['code'] = response.status_code
                result['size_bytes'] = len(response.content)
                
                # Detectar redirecciones
                if response.history:
                    result['redirects'] = [r.url for r in response.history]
                
                # Validar respuesta
                if response.status_code == 200:
                    if result['size_bytes'] < 500:
                        result['status'] = 'warning'
                        result['error'] = f"Contenido muy pequeño ({result['size_bytes']} bytes)"
                        self.results['warnings'].append(result)
                    else:
                        result['status'] = 'valid'
                        result['accessible'] = True
                        self.results['valid'].append(result)
                
                elif response.status_code in [301, 302, 307, 308]:
                    result['status'] = 'warning'
                    result['error'] = f"Redirección permanente a {response.url}"
                    self.results['warnings'].append(result)
                
                else:
                    result['status'] = 'invalid'
                    result['error'] = f"HTTP {response.status_code}"
                    self.results['invalid'].append(result)
                
                return result
                
            except requests.exceptions.Timeout:
                result['error'] = f"Timeout (intento {attempt + 1}/{self.retries})"
                if attempt == self.retries - 1:
                    result['status'] = 'invalid'
                    self.results['invalid'].append(result)
                else:
                    time.sleep(2)
                    
            except requests.exceptions.ConnectionError:
                result['error'] = "Error de conexión"
                result['status'] = 'invalid'
                self.results['invalid'].append(result)
                return result
                
            except Exception as e:
                result['error'] = str(e)
                result['status'] = 'invalid'
                self.results['invalid'].append(result)
                return result
        
        return result
    
    def extract_urls_from_corpus(self, corpus_path: str) -> List[Tuple[str, str]]:
        """
        Extrae URLs de un archivo de corpus markdown.
        
        Returns:
            Lista de tuplas (url, contexto)
        """
        urls = []
        
        with open(corpus_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar todas las URLs HTTP/HTTPS
        url_pattern = r'https?://[^\s<>"{}|\\^\[\]`]+'
        matches = re.finditer(url_pattern, content)
        
        for match in matches:
            url = match.group(0).rstrip('.,;:)\'"')
            
            # Extraer contexto (línea donde aparece la URL)
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 50)
            context = content[start:end].replace('\n', ' ').strip()
            
            # Limpiar el contexto
            if len(context) > 100:
                context = context[:97] + "..."
            
            urls.append((url, context))
        
        # Eliminar duplicados manteniendo el orden
        seen = set()
        unique_urls = []
        for url, ctx in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append((url, ctx))
        
        return unique_urls
    
    def generate_report(self, output_path: str = None):
        """Genera un reporte en formato Markdown."""
        
        total = len(self.results['valid']) + len(self.results['invalid']) + len(self.results['warnings'])
        valid_count = len(self.results['valid'])
        invalid_count = len(self.results['invalid'])
        warning_count = len(self.results['warnings'])
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# Reporte de Validación de URLs

**Fecha**: {timestamp}  
**Total URLs analizadas**: {total}

## Resumen

- ✅ **URLs válidas**: {valid_count} ({valid_count/total*100:.1f}%)
- ⚠️ **URLs con advertencias**: {warning_count} ({warning_count/total*100:.1f}%)
- ❌ **URLs inválidas**: {invalid_count} ({invalid_count/total*100:.1f}%)

---

"""
        
        # URLs inválidas
        if self.results['invalid']:
            report += "## ❌ URLs Inválidas\n\n"
            report += "| URL | Código | Error |\n"
            report += "|-----|--------|-------|\n"
            for r in self.results['invalid']:
                code = r['code'] if r['code'] else 'N/A'
                error = r['error'] if r['error'] else 'Desconocido'
                report += f"| {r['url'][:60]}... | {code} | {error} |\n"
            report += "\n---\n\n"
        
        # URLs con advertencias
        if self.results['warnings']:
            report += "## ⚠️ URLs con Advertencias\n\n"
            report += "| URL | Código | Advertencia |\n"
            report += "|-----|--------|-------------|\n"
            for r in self.results['warnings']:
                code = r['code'] if r['code'] else 'N/A'
                error = r['error'] if r['error'] else 'N/A'
                report += f"| {r['url'][:60]}... | {code} | {error} |\n"
            report += "\n---\n\n"
        
        # URLs válidas
        if self.results['valid']:
            report += "## ✅ URLs Válidas\n\n"
            report += f"Total: {len(self.results['valid'])} URLs\n\n"
            
            # Agrupar por dominio
            by_domain = {}
            for r in self.results['valid']:
                domain = urlparse(r['url']).netloc
                if domain not in by_domain:
                    by_domain[domain] = []
                by_domain[domain].append(r)
            
            for domain, urls in sorted(by_domain.items()):
                report += f"### {domain} ({len(urls)} URLs)\n\n"
                for r in urls[:5]:  # Mostrar solo las primeras 5
                    size_kb = r['size_bytes'] / 1024
                    report += f"- ✅ [{size_kb:.1f} KB] {r['url'][:80]}\n"
                if len(urls) > 5:
                    report += f"- ... y {len(urls) - 5} más\n"
                report += "\n"
        
        # Guardar reporte
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n📄 Reporte guardado en: {output_path}")
        
        return report
    
    def print_summary(self):
        """Imprime resumen en consola con colores."""
        
        total = len(self.results['valid']) + len(self.results['invalid']) + len(self.results['warnings'])
        valid_count = len(self.results['valid'])
        invalid_count = len(self.results['invalid'])
        warning_count = len(self.results['warnings'])
        
        print(f"\n{Colors.BOLD}=== RESUMEN DE VALIDACIÓN ==={Colors.RESET}\n")
        print(f"📊 Total URLs analizadas: {Colors.BOLD}{total}{Colors.RESET}")
        print(f"{Colors.GREEN}✅ URLs válidas: {valid_count} ({valid_count/total*100:.1f}%){Colors.RESET}")
        print(f"{Colors.YELLOW}⚠️  URLs con advertencias: {warning_count} ({warning_count/total*100:.1f}%){Colors.RESET}")
        print(f"{Colors.RED}❌ URLs inválidas: {invalid_count} ({invalid_count/total*100:.1f}%){Colors.RESET}")
        
        # Mostrar URLs problemáticas
        if self.results['invalid']:
            print(f"\n{Colors.RED}{Colors.BOLD}URLs Inválidas:{Colors.RESET}")
            for r in self.results['invalid'][:5]:
                print(f"  {Colors.RED}❌{Colors.RESET} {r['url'][:70]}...")
                print(f"     Error: {r['error']}")
        
        if self.results['warnings']:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}URLs con Advertencias:{Colors.RESET}")
            for r in self.results['warnings'][:5]:
                print(f"  {Colors.YELLOW}⚠️{Colors.RESET}  {r['url'][:70]}...")
                print(f"     Advertencia: {r['error']}")


def main():
    parser = argparse.ArgumentParser(description='Validador de URLs para corpus de conocimiento')
    parser.add_argument('--corpus', type=str, required=True, help='Ruta al archivo de corpus')
    parser.add_argument('--output', type=str, help='Ruta para guardar el reporte')
    parser.add_argument('--timeout', type=int, default=15, help='Timeout en segundos')
    parser.add_argument('--retries', type=int, default=2, help='Número de reintentos')
    
    args = parser.parse_args()
    
    print(f"{Colors.BLUE}{Colors.BOLD}")
    print("=" * 70)
    print("  URL VALIDATOR - Verificador de URLs del Corpus")
    print("=" * 70)
    print(f"{Colors.RESET}\n")
    
    print(f"📂 Corpus: {args.corpus}")
    
    # Crear validador
    validator = URLValidator(timeout=args.timeout, retries=args.retries)
    
    # Extraer URLs del corpus
    print(f"\n🔍 Extrayendo URLs del corpus...")
    urls = validator.extract_urls_from_corpus(args.corpus)
    print(f"   Encontradas {len(urls)} URLs únicas\n")
    
    # Validar cada URL
    print(f"🚀 Iniciando validación...\n")
    for i, (url, context) in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] Validando: {url[:60]}...")
        result = validator.validate_url(url, context)
        
        # Mostrar resultado
        if result['status'] == 'valid':
            print(f"  {Colors.GREEN}✅ OK{Colors.RESET} [{result['code']}] {result['size_bytes']/1024:.1f} KB")
        elif result['status'] == 'warning':
            print(f"  {Colors.YELLOW}⚠️  Advertencia{Colors.RESET} [{result['code']}] {result['error']}")
        else:
            print(f"  {Colors.RED}❌ Error{Colors.RESET} {result['error']}")
        
        time.sleep(1)  # Rate limiting
    
    # Mostrar resumen
    validator.print_summary()
    
    # Generar reporte
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d")
        output_path = f"etl/reports/url_validation_{timestamp}.md"
    
    validator.generate_report(output_path)
    
    print(f"\n{Colors.GREEN}✅ Validación completada{Colors.RESET}\n")


if __name__ == "__main__":
    main()
