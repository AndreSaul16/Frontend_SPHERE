"""
CFO Spiders - SaaS Metrics
===========================
Spiders para recursos sobre métricas SaaS y unit economics.
Incluye: CAC, LTV, Churn, NDR, Rule of 40, Cohort Analysis.
"""

import os
import sys
import time
from bs4 import BeautifulSoup
import requests

# Importar clase base
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core.base_spider import BaseTechSpider


class SaaSMetricsSpider(BaseTechSpider):
    """
    Spider base para recursos de métricas SaaS.
    Filtra por keywords financieros y de métricas.
    """
    
    FINANCE_KEYWORDS = [
        # Métricas Core
        'cac', 'ltv', 'churn', 'retention', 'arr', 'mrr',
        'ndr', 'net dollar retention', 'gross margin', 'burn rate',
        
        # Frameworks
        'rule of 40', 'magic number', 'unit economics',
        'cohort analysis', 'payback period',
        
        # Financiero
        'dcf', 'wacc', 'roic', 'ebitda', 'cash flow',
        'valuation', 'revenue recognition'
    ]
    
    def matches_finance_keywords(self, title, content=""):
        """Verifica si contiene keywords financieros."""
        combined = (title + " " + content).lower()
        return any(keyword in combined for keyword in self.FINANCE_KEYWORDS)


class DavidSkokSpider(SaaSMetricsSpider):
    """Spider para blog de David Skok - The Bible of SaaS Metrics."""
    
    ARTICLES = [
        {
            "title": "SaaS Metrics 2.0 - A Guide to Measuring and Improving",
            "url": "https://www.forentrepreneurs.com/saas-metrics-2/",
            "concept": "CAC, LTV, Churn, Unit Economics"
        },
        {
            "title": "The SaaS Adventure",
            "url": "https://www.forentrepreneurs.com/tag/saas/",
            "concept": "Growth strategies and metrics"
        }
    ]
    
    def run(self, limit=2):
        print(f"\n📊 [{self.__class__.__name__}] David Skok - SaaS Metrics...")
        
        count = 0
        for article in self.ARTICLES[:limit]:
            try:
                print(f"\n📄 Procesando: {article['title']}")
                
                if self.url_exists(article['url']):
                    print(f"   💤 Ya existe")
                    continue
                
                markdown = self.extract_content(article['url'])
                
                if not markdown or len(markdown) < 1000:
                    print(f"   ⚠️ Contenido insuficiente")
                    continue
                
                filepath = self.save_raw_html(article['url'], article['title'], agent_subdir="cfo/metrics")
                
                enhanced_markdown = f"""# {article['title']}

**Concepto clave**: {article['concept']}  
**Fuente**: David Skok (For Entrepreneurs)

---

{markdown}
"""
                
                doc = {
                    "source": "David Skok - For Entrepreneurs",
                    "title": article['title'],
                    "url": article['url'],
                    "file_path": filepath,
                    "content_markdown": enhanced_markdown,
                    "tags": ["saas-metrics", "unit-economics", "david-skok", "cac", "ltv"],
                    "curated_category": "saas_metrics",
                    "core_concept": article['concept'],
                    "agent_target": "CFO"
                }
                
                self.save_knowledge(doc)
                count += 1
                print(f"   ✅ Guardado")
                time.sleep(2)
                
            except Exception as e:
                print(f"   🔥 Error: {e}")
        
        print(f"\n📊 David Skok: {count} artículos procesados")


class OpenViewSpider(SaaSMetricsSpider):
    """Spider para OpenView Partners - Rule of 40, Expansion Revenue."""
    
    RESOURCES = [
        {
            "title": "The Rule of 40",
            "url": "https://openviewpartners.com/blog/rule-of-40/",
            "concept": "Growth vs Profitability tradeoff"
        },
        {
            "title": "Product-Led Growth Benchmarks",
            "url": "https://openviewpartners.com/product-led-growth-benchmarks/",
            "concept": "PLG metrics and benchmarks"
        }
    ]
    
    def run(self, limit=2):
        print(f"\n📈 [{self.__class__.__name__}] OpenView Partners...")
        
        count = 0
        for resource in self.RESOURCES[:limit]:
            try:
                print(f"\n📄 {resource['title']}")
                
                if self.url_exists(resource['url']):
                    print(f"   💤 Ya existe")
                    continue
                
                markdown = self.extract_content(resource['url'])
                
                if not markdown or len(markdown) < 500:
                    print(f"   ⚠️ Contenido insuficiente")
                    continue
                
                filepath = self.save_raw_html(resource['url'], resource['title'], agent_subdir="cfo/metrics")
                
                doc = {
                    "source": "OpenView Partners",
                    "title": resource['title'],
                    "url": resource['url'],
                    "file_path": filepath,
                    "content_markdown": f"# {resource['title']}\n\n**Concepto**: {resource['concept']}\n\n---\n\n{markdown}",
                    "tags": ["rule-of-40", "plg", "saas-benchmarks", "growth"],
                    "curated_category": "saas_metrics",
                    "core_concept": resource['concept'],
                    "agent_target": "CFO"
                }
                
                self.save_knowledge(doc)
                count += 1
                print(f"   ✅ Guardado")
                time.sleep(2)
                
            except Exception as e:
                print(f"   🔥 Error: {e}")
        
        print(f"\n📊 OpenView: {count} recursos procesados")


class ChartMogulSpider(SaaSMetricsSpider):
    """Spider para ChartMogul - NDR, MRR, Cohort Analysis."""
    
    def run(self, limit=2):
        print(f"\n📊 [{self.__class__.__name__}] ChartMogul Blog...")
        
        # URLs específicas de guías importantes
        guides = [
            {
                "title": "Net Revenue Retention (NRR) - The Ultimate Guide",
                "url": "https://chartmogul.com/blog/net-revenue-retention-nrr/",
                "concept": "NDR > 120% as growth engine"
            },
            {
                "title": "Cohort Analysis for SaaS",
                "url": "https://chartmogul.com/blog/what-is-cohort-analysis/",
                "concept": "Retention analysis by cohort"
            }
        ]
        
        count = 0
        for guide in guides[:limit]:
            try:
                print(f"\n📄 {guide['title'][:50]}...")
                
                if self.url_exists(guide['url']):
                    print(f"   💤 Ya existe")
                    continue
                
                markdown = self.extract_content(guide['url'])
                
                if not markdown or len(markdown) < 800:
                    print(f"   ⚠️ Contenido insuficiente")
                    continue
                
                filepath = self.save_raw_html(guide['url'], guide['title'], agent_subdir="cfo/metrics", prefix="ChartMogul_")
                
                doc = {
                    "source": "ChartMogul",
                    "title": guide['title'],
                    "url": guide['url'],
                    "file_path": filepath,
                    "content_markdown": f"# {guide['title']}\n\n**Concepto**: {guide['concept']}\n\n---\n\n{markdown}",
                    "tags": ["ndr", "cohort-analysis", "mrr", "saas-analytics"],
                    "curated_category": "saas_metrics",
                    "agent_target": "CFO"
                }
                
                self.save_knowledge(doc)
                count += 1
                print(f"   ✅ Guardado")
                time.sleep(2)
                
            except Exception as e:
                print(f"   🔥 Error: {e}")
        
        print(f"\n📊 ChartMogul: {count} guías procesadas")


if __name__ == "__main__":
    print("🚀 Iniciando spiders de SaaS Metrics...\n")
    
    skok = DavidSkokSpider(agent_name="CFO")
    skok.run(limit=2)
    
    openview = OpenViewSpider(agent_name="CFO")
    openview.run(limit=2)
    
    chartmogul = ChartMogulSpider(agent_name="CFO")
    chartmogul.run(limit=2)
    
    print("\n✅ SaaS Metrics completado")
