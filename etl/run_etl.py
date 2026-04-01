"""
SPHERE ETL - Orquestador Principal
===================================
Script principal para ejecutar spiders organizados por agente.

Uso:
    python run_etl.py --agent cto           # Solo spiders del CTO
    python run_etl.py --agent ceo           # Solo spiders del CEO
    python run_etl.py --agent all           # Todos los agentes
    python run_etl.py --spider github       # Spider específico
"""

import sys
import argparse

# Importar spiders del CTO
from agents.cto.github_spider import GitHubGovernanceSpider
from agents.cto.blogs_spider import NetflixEngineeringSpider, UberEngineeringSpider, DiscordEngineeringSpider
from agents.cto.papers_spider import ArxivFoundationalSpider
from agents.cto.arxiv_pdf_spider import ArxivPDFSpider
from agents.cto.books_synthetic_spider import BooksSyntheticSpider

# Importar spiders del CEO
from agents.ceo.mckinsey_spider import McKinseySpider


def run_cto_spiders():
    """Ejecuta todos los spiders del CTO."""
    print("\n" + "=" * 70)
    print("🔧 EJECUTANDO SPIDERS DEL CTO (Chief Technology Officer)")
    print("=" * 70)
    
    try:
        print("\n--- GitHub Governance ---")
        github_spider = GitHubGovernanceSpider()
        github_spider.run(limit_per_repo=10)
    except Exception as e:
        print(f"⚠️ Error en GitHub spider: {e}")
    
    try:
        print("\n--- Engineering Blogs ---")
        netflix_spider = NetflixEngineeringSpider()
        netflix_spider.run(limit=10)
    except Exception as e:
        print(f"⚠️ Error en Netflix spider: {e}")
    
    try:
        uber_spider = UberEngineeringSpider()
        uber_spider.run(limit=5)
    except Exception as e:
        print(f"⚠️ Error en Uber spider: {e}")
    
    try:
        discord_spider = DiscordEngineeringSpider()
        discord_spider.run(limit=10)
    except Exception as e:
        print(f"⚠️ Error en Discord spider: {e}")
    
    try:
        print("\n--- ArXiv Papers ---")
        arxiv_spider = ArxivFoundationalSpider()
        arxiv_spider.run(include_recent_llm=True)
    except Exception as e:
        print(f"⚠️ Error en ArXiv spider: {e}")
    
    try:
        print("\n--- ArXiv PDFs Download ---")
        pdf_spider = ArxivPDFSpider()
        pdf_spider.run()
    except Exception as e:
        print(f"⚠️ Error en ArXiv PDF spider: {e}")
    
    try:
        print("\n--- Synthetic Books Integration ---")
        books_spider = BooksSyntheticSpider()
        books_spider.run()
    except Exception as e:
        print(f"⚠️ Error en Books spider: {e}")


def run_ceo_spiders():
    """Ejecuta todos los spiders del CEO."""
    print("\n" + "=" * 70)
    print("👔 EJECUTANDO SPIDERS DEL CEO (Chief Executive Officer)")
    print("=" * 70)
    
    try:
        mckinsey_spider = McKinseySpider()
        mckinsey_spider.run(limit=5)
    except Exception as e:
        print(f"⚠️ Error en McKinsey spider: {e}")


def run_specific_spider(spider_name):
    """Ejecuta un spider específico por nombre."""
    spider_map = {
        'github': GitHubGovernanceSpider,
        'netflix': NetflixEngineeringSpider,
        'uber': UberEngineeringSpider,
        'discord': DiscordEngineeringSpider,
        'arxiv': ArxivFoundationalSpider,
        'arxiv_pdfs': ArxivPDFSpider,
        'books': BooksSyntheticSpider,
        'mckinsey': McKinseySpider
    }
    
    if spider_name not in spider_map:
        print(f"❌ Spider '{spider_name}' no encontrado.")
        print(f"Spiders disponibles: {', '.join(spider_map.keys())}")
        return
    
    print(f"\n🎯 Ejecutando spider: {spider_name}")
    spider_class = spider_map[spider_name]
    spider = spider_class()
    spider.run()


def main():
    parser = argparse.ArgumentParser(description='SPHERE ETL - Sistema de vigilancia tecnológica')
    parser.add_argument('--agent', choices=['cto', 'ceo', 'cfo', 'cmo', 'all'], default='all',
                      help='Agente para ejecutar spiders (default: all)')
    parser.add_argument('--spider', type=str,
                      help='Ejecutar un spider específico (github, netflix, uber, discord, arxiv, mckinsey)')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🌐 SPHERE ETL - Sistema de Vigilancia Tecnológica")
    print("=" * 70)
    
    # Si se especifica un spider, ejecutar solo ese
    if args.spider:
        run_specific_spider(args.spider)
        return
    
    # Ejecutar por agente
    if args.agent == 'cto' or args.agent == 'all':
        run_cto_spiders()
    
    if args.agent == 'ceo' or args.agent == 'all':
        run_ceo_spiders()
    
    if args.agent == 'cfo':
        print("\n⚠️ CFO spiders aún no implementados")
    
    if args.agent == 'cmo':
        print("\n⚠️ CMO spiders aún no implementados")
    
    print("\n" + "=" * 70)
    print("✅ EJECUCIÓN COMPLETADA")
    print("=" * 70)


if __name__ == "__main__":
    main()
