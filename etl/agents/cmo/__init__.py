"""
CMO Agent - Orchestrator
=========================
Orquestador principal para todos los spiders del CMO.
Ejecuta blogs, frameworks y case studies de forma coordinada.
"""

import sys
import os
from datetime import datetime

# Asegurar que el path esté configurado
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Importar spiders
try:
    from .blogs_spider import (
        ReforgeSpider,
        AndrewChenSpider,
        MozBlogSpider,
        AhrefsBlogSpider,
        KellblogSpider
    )
    from .frameworks_spider import MarketingFrameworkSpider, WebFrameworkSpider
    from .case_studies_spider import CaseStudySpider
    SPIDERS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Error importando spiders: {e}")
    SPIDERS_AVAILABLE = False


class CMOOrchestrator:
    """
    Orquestador de spiders del CMO.
    Coordina la ejecución de todos los spiders y genera reportes.
    """
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.results = {
            'blogs': 0,
            'frameworks': 0,
            'case_studies': 0,
            'errors': []
        }
    
    def run_all(self, blog_limit=5, framework_limit=5, case_study_limit=None):
        """
        Ejecuta todos los spiders del CMO.
        
        Args:
            blog_limit: Número de artículos por blog
            framework_limit: Número de frameworks a procesar
            case_study_limit: Número de casos de estudio (None = todos)
        """
        if not SPIDERS_AVAILABLE:
            print("❌ Spiders no disponibles. Verificar importaciones.")
            return
        
        self.start_time = datetime.now()
        
        print("=" * 80)
        print("  CMO KNOWLEDGE PIPELINE - Iniciando ingesta de datos")
        print("=" * 80)
        print(f"\n🕐 Inicio: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 1. Blogs
        print("\n" + "="*80)
        print("  FASE 1: BLOGS DE MARKETING")
        print("="*80 + "\n")
        
        try:
            self._run_blogs(blog_limit)
        except Exception as e:
            print(f"❌ Error en blogs: {e}")
            self.results['errors'].append(f"Blogs: {e}")
        
        # 2. Frameworks
        print("\n" + "="*80)
        print("  FASE 2: FRAMEWORKS ESTRATÉGICOS")
        print("="*80 + "\n")
        
        try:
            self._run_frameworks(framework_limit)
        except Exception as e:
            print(f"❌ Error en frameworks: {e}")
            self.results['errors'].append(f"Frameworks: {e}")
        
        # 3. Case Studies
        print("\n" + "="*80)
        print("  FASE 3: CASOS DE ESTUDIO (WAR ROOM)")
        print("="*80 + "\n")
        
        try:
            self._run_case_studies(case_study_limit)
        except Exception as e:
            print(f"❌ Error en case studies: {e}")
            self.results['errors'].append(f"Case Studies: {e}")
        
        # Resumen final
        self.end_time = datetime.now()
        self._print_summary()
    
    def _run_blogs(self, limit):
        """Ejecuta spiders de blogs."""
        blogs = [
            ("Reforge", ReforgeSpider),
            ("Andrew Chen", AndrewChenSpider),
            ("Moz", MozBlogSpider),
            ("Ahrefs", AhrefsBlogSpider),
            ("Kellblog", KellblogSpider)
        ]
        
        for blog_name, SpiderClass in blogs:
            try:
                print(f"\n--- {blog_name} ---")
                spider = SpiderClass(agent_name="CMO")
                spider.run(limit=limit)
                # No hay forma directa de contar docs guardados, estimamos
                self.results['blogs'] += limit
            except Exception as e:
                print(f"   ❌ Error en {blog_name}: {e}")
                self.results['errors'].append(f"{blog_name}: {e}")
    
    def _run_frameworks(self, limit):
        """Ejecuta spiders de frameworks."""
        # PDF Frameworks
        print("\n--- PDF Frameworks ---")
        try:
            pdf_spider = MarketingFrameworkSpider(agent_name="CMO")
            pdf_spider.run(limit=limit)
            self.results['frameworks'] += limit if limit else 5
        except Exception as e:
            print(f"   ❌ Error en PDF frameworks: {e}")
            self.results['errors'].append(f"PDF Frameworks: {e}")
        
        # Web Frameworks
        print("\n--- Web Frameworks ---")
        try:
            web_spider = WebFrameworkSpider(agent_name="CMO")
            web_spider.run(limit=limit)
            self.results['frameworks'] += limit if limit else 5
        except Exception as e:
            print(f"   ❌ Error en web frameworks: {e}")
            self.results['errors'].append(f"Web Frameworks: {e}")
    
    def _run_case_studies(self, limit):
        """Ejecuta spider de casos de estudio."""
        try:
            spider = CaseStudySpider(agent_name="CMO")
            spider.run(limit=limit)
            self.results['case_studies'] = spider.processed_count
        except Exception as e:
            print(f"   ❌ Error en case studies: {e}")
            self.results['errors'].append(f"Case Studies: {e}")
    
    def _print_summary(self):
        """Imprime resumen de la ejecución."""
        duration = (self.end_time - self.start_time).total_seconds()
        
        print("\n" + "="*80)
        print("  RESUMEN DE EJECUCIÓN")
        print("="*80)
        print(f"\n🕐 Inicio:    {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🕐 Fin:       {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Duración:  {duration/60:.1f} minutos ({duration:.0f} segundos)")
        
        print(f"\n📊 DOCUMENTOS PROCESADOS (estimado):")
        print(f"   📰 Blogs:          {self.results['blogs']}")
        print(f"   📚 Frameworks:     {self.results['frameworks']}")
        print(f"   🎯 Case Studies:   {self.results['case_studies']}")
        print(f"   {'─'*40}")
        print(f"   📦 TOTAL:          {sum([self.results['blogs'], self.results['frameworks'], self.results['case_studies']])}")
        
        if self.results['errors']:
            print(f"\n⚠️ ERRORES ({len(self.results['errors'])}):")
            for error in self.results['errors'][:5]:
                print(f"   - {error[:70]}...")
        else:
            print(f"\n✅ Ejecución sin errores")
        
        print(f"\n{'='*80}\n")


def run_cmo_pipeline(blog_limit=5, framework_limit=5, case_study_limit=None):
    """
    Función conveniente para ejecutar el pipeline completo.
    
    Args:
        blog_limit: Artículos por blog (default: 5)
        framework_limit: Frameworks a procesar (default: 5)
        case_study_limit: Case studies (default: None = todos)
    """
    orchestrator = CMOOrchestrator()
    orchestrator.run_all(
        blog_limit=blog_limit,
        framework_limit=framework_limit,
        case_study_limit=case_study_limit
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='CMO Knowledge Pipeline')
    parser.add_argument('--blogs', type=int, default=5, help='Artículos por blog (default: 5)')
    parser.add_argument('--frameworks', type=int, default=5, help='Frameworks a procesar (default: 5)')
    parser.add_argument('--case-studies', type=int, default=None, help='Case studies (default: todos)')
    parser.add_argument('--quick', action='store_true', help='Modo rápido (2 por fuente)')
    
    args = parser.parse_args()
    
    if args.quick:
        run_cmo_pipeline(blog_limit=2, framework_limit=2, case_study_limit=2)
    else:
        run_cmo_pipeline(
            blog_limit=args.blogs,
            framework_limit=args.frameworks,
            case_study_limit=args.case_studies
        )
