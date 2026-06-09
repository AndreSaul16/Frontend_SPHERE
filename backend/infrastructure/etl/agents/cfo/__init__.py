"""
CFO Agent - Orchestrator
=========================
Orquestador principal para todos los spiders del CFO.
Ejecuta métricas SaaS, regulación y macroeconomía.
"""

import sys
import os
from datetime import datetime

# Asegurar que el path esté configurado
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Importar spiders
try:
    from .saas_metrics_spider import DavidSkokSpider, OpenViewSpider, ChartMogulSpider
    from .regulatory_spider import AnnualReportsSpider, AccountingStandardsSpider, BoardDeckSpider
    from .macro_spider import HowardMarksSpider, DamodaranSpider, SequoiaSpider, RayDalioSpider
    SPIDERS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Error importando spiders: {e}")
    SPIDERS_AVAILABLE = False


class CFOOrchestrator:
    """
    Orquestador de spiders del CFO.
    Coordina la ejecución de métricas, regulación y macro.
    """
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.results = {
            'saas_metrics': 0,
            'regulatory': 0,
            'macro': 0,
            'errors': []
        }
    
    def run_all(self, limit_per_spider=2):
        """
        Ejecuta todos los spiders del CFO.
        
        Args:
            limit_per_spider: Documentos por spider individual
        """
        if not SPIDERS_AVAILABLE:
            print("❌ Spiders no disponibles. Verificar importaciones.")
            return
        
        self.start_time = datetime.now()
        
        print("=" * 80)
        print("  CFO KNOWLEDGE PIPELINE - Iniciando ingesta de datos")
        print("=" * 80)
        print(f"\n🕐 Inicio: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 1. SaaS Metrics
        print("\n" + "="*80)
        print("  FASE 1: MÉTRICAS SAAS")
        print("="*80 + "\n")
        
        try:
            self._run_saas_metrics(limit_per_spider)
        except Exception as e:
            print(f"❌ Error en SaaS metrics: {e}")
            self.results['errors'].append(f"SaaS Metrics: {e}")
        
        # 2. Regulatory
        print("\n" + "="*80)
        print("  FASE 2: REGULACIÓN Y REPORTING")
        print("="*80 + "\n")
        
        try:
            self._run_regulatory(limit_per_spider)
        except Exception as e:
            print(f"❌ Error en regulatory: {e}")
            self.results['errors'].append(f"Regulatory: {e}")
        
        # 3. Macro
        print("\n" + "="*80)
        print("  FASE 3: MACROECONOMÍA")
        print("="*80 + "\n")
        
        try:
            self._run_macro(limit_per_spider)
        except Exception as e:
            print(f"❌ Error en macro: {e}")
            self.results['errors'].append(f"Macro: {e}")
        
        # Resumen final
        self.end_time = datetime.now()
        self._print_summary()
    
    def _run_saas_metrics(self, limit):
        """Ejecuta spiders de métricas SaaS."""
        spiders = [
            ("David Skok", DavidSkokSpider),
            ("OpenView", OpenViewSpider),
            ("ChartMogul", ChartMogulSpider)
        ]
        
        for name, SpiderClass in spiders:
            try:
                print(f"\n--- {name} ---")
                spider = SpiderClass(agent_name="CFO")
                spider.run(limit=limit)
                self.results['saas_metrics'] += limit
            except Exception as e:
                print(f"   ❌ Error en {name}: {e}")
                self.results['errors'].append(f"{name}: {e}")
    
    def _run_regulatory(self, limit):
        """Ejecuta spiders de regulación."""
        spiders = [
            ("Annual Reports", AnnualReportsSpider),
            ("Accounting Standards", AccountingStandardsSpider),
            ("Board Decks", BoardDeckSpider)
        ]
        
        for name, SpiderClass in spiders:
            try:
                print(f"\n--- {name} ---")
                spider = SpiderClass(agent_name="CFO")
                spider.run(limit=1 if "Annual" in name else limit)  # Solo 1 annual report
                self.results['regulatory'] += (1 if "Annual" in name else limit)
            except Exception as e:
                print(f"   ❌ Error en {name}: {e}")
                self.results['errors'].append(f"{name}: {e}")
    
    def _run_macro(self, limit):
        """Ejecuta spiders de macroeconomía."""
        spiders = [
            ("Howard Marks", HowardMarksSpider),
            ("Aswath Damodaran", DamodaranSpider),
            ("Sequoia Capital", SequoiaSpider),
            ("Ray Dalio", RayDalioSpider)
        ]
        
        for name, SpiderClass in spiders:
            try:
                print(f"\n--- {name} ---")
                spider = SpiderClass(agent_name="CFO")
                spider.run(limit=1)  # Memos suelen ser únicos
                self.results['macro'] += 1
            except Exception as e:
                print(f"   ❌ Error en {name}: {e}")
                self.results['errors'].append(f"{name}: {e}")
    
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
        print(f"   📈 SaaS Metrics:  {self.results['saas_metrics']}")
        print(f"   ⚖️  Regulatory:    {self.results['regulatory']}")
        print(f"   🌍 Macro:          {self.results['macro']}")
        print(f"   {'─'*40}")
        print(f"   📦 TOTAL:          {sum([self.results['saas_metrics'], self.results['regulatory'], self.results['macro']])}")
        
        if self.results['errors']:
            print(f"\n⚠️ ERRORES ({len(self.results['errors'])}):")
            for error in self.results['errors'][:5]:
                print(f"   - {error[:70]}...")
        else:
            print(f"\n✅ Ejecución sin errores")
        
        print(f"\n{'='*80}\n")


def run_cfo_pipeline(limit_per_spider=2):
    """
    Función conveniente para ejecutar el pipeline completo.
    
    Args:
        limit_per_spider: Documentos por spider (default: 2)
    """
    orchestrator = CFOOrchestrator()
    orchestrator.run_all(limit_per_spider=limit_per_spider)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='CFO Knowledge Pipeline')
    parser.add_argument('--limit', type=int, default=2, help='Docs por spider (default: 2)')
    parser.add_argument('--quick', action='store_true', help='Modo rápido (1 por spider)')
    
    args = parser.parse_args()
    
    if args.quick:
        run_cfo_pipeline(limit_per_spider=1)
    else:
        run_cfo_pipeline(limit_per_spider=args.limit)
