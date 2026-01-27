"""
CTO Spiders - ArXiv Foundational Papers
========================================
Spider para papers fundacionales de ArXiv.
NO busca lo último, busca los clásicos que fundaron la industria.
"""

import os
import sys
import time
import requests
from bs4 import BeautifulSoup

# Importar clase base
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core.base_spider import BaseTechSpider


class ArxivFoundationalSpider(BaseTechSpider):
    """
    Spider para papers fundacionales de ArXiv.
    NO busca lo último, busca los clásicos que fundaron la industria.
    """
    
    # Papers fundacionales (lista manual curada)
    # ✅ CRÍTICO: Usar IDs directos, NO keywords
    # La búsqueda por keywords encuentra papers que CITAN al original, no el original mismo
    FOUNDATIONAL_PAPERS = [
        {
            'title': 'The Google File System',
            'arxiv_id': None,  # No está en ArXiv, es de SOSP 2003
            'direct_url': 'https://static.googleusercontent.com/media/research.google.com/en//archive/gfs-sosp2003.pdf'
        },
        {
            'title': 'MapReduce: Simplified Data Processing on Large Clusters',
            'arxiv_id': None,  # No está en ArXiv, es de OSDI 2004
            'direct_url': 'https://static.googleusercontent.com/media/research.google.com/en//archive/mapreduce-osdi04.pdf'
        },
        {
            'title': 'Dynamo: Amazon\'s Highly Available Key-value Store',
            'arxiv_id': None,  # No está en ArXiv, es de SOSP 2007
            'direct_url': 'https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf'
        },
        {
            'title': 'Kafka: a Distributed Messaging System for Log Processing',
            'arxiv_id': None,  # Paper de LinkedIn, no en ArXiv
            'direct_url': None  # No es de acceso público directo
        },
        {
            'title': 'Attention Is All You Need',
            'arxiv_id': '1706.03762',  # ✅ ID directo
            'direct_url': None
        },
        {
            'title': 'BERT: Pre-training of Deep Bidirectional Transformers',
            'arxiv_id': '1810.04805',  # ✅ ID directo
            'direct_url': None
        },
        {
            'title': 'Raft: In Search of an Understandable Consensus Algorithm',
            'arxiv_id': None,
            'direct_url': 'https://raft.github.io/raft.pdf'
        },
        {
            'title': 'The Chubby lock service for loosely-coupled distributed systems',
            'arxiv_id': None,  # Google OSDI 2006
            'direct_url': 'https://static.googleusercontent.com/media/research.google.com/en//archive/chubby-osdi06.pdf'
        }
    ]
    
    
    def fetch_arxiv_by_id(self, arxiv_id):
        """Obtiene un paper específico de ArXiv por su ID."""
        api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
        
        try:
            response = requests.get(api_url, timeout=15)
            soup = BeautifulSoup(response.text, 'xml')
            entry = soup.find('entry')
            return entry
        except Exception as e:
            print(f"      ⚠️ Error obteniendo paper {arxiv_id}: {e}")
            return None
    
    
    def run(self, include_recent_llm=True):
        print(f"\n🎓 [{self.__class__.__name__}] Papers Fundacionales de ArXiv...")
        
        # 1. Buscar papers fundacionales QUE ESTÁN EN ARXIV
        print("\n   📚 Papers Fundacionales (IDs directos):")
        for paper in self.FOUNDATIONAL_PAPERS:
            # ✅ SOLO procesar si tiene arxiv_id
            if not paper.get('arxiv_id'):
                print(f"   ⏭️  Saltando '{paper['title']}' (no en ArXiv)")
                continue
            
            print(f"\n   📄 Obteniendo: {paper['title']}")
            
            entry = self.fetch_arxiv_by_id(paper['arxiv_id'])
            
            if entry:
                paper_id = entry.id.text
                title = entry.title.text.strip().replace('\n', ' ')
                summary = entry.summary.text.strip().replace('\n', ' ')
                pdf_link = entry.find('link', title='pdf')
                pdf_url = pdf_link['href'] if pdf_link else None
                
                if self.url_exists(paper_id):
                    print(f"      💤 Ya existe: {title[:40]}")
                    continue
                
                print(f"      ✅ Encontrado: {title[:50]}...")
                
                doc = {
                    "source": "ArXiv - Foundational Papers",
                    "title": title,
                    "url": paper_id,
                    "pdf_url": pdf_url,
                    "content_markdown": f"## Abstract\n\n{summary}",
                    "tags": ["foundational", "classic", "research-paper"],
                    "curated_category": "foundational_paper",
                    "needs_pdf_processing": True
                }
                self.save_knowledge(doc)
                time.sleep(2)
            else:
                print(f"      ❌ No encontrado con ID {paper['arxiv_id']}")
        
        # 2. Buscar papers recientes sobre LLM Ops
        if include_recent_llm:
            print(f"\n   🔥 Papers Recientes sobre LLM Ops:")
            # ✅ Para papers recientes SÍ usamos keywords
            api_url = "http://export.arxiv.org/api/query?search_query=all:LLM+operations+OR+large+language+model+deployment&start=0&max_results=5&sortBy=submittedDate&sortOrder=descending"
            
            try:
                response = requests.get(api_url, timeout=15)
                soup = BeautifulSoup(response.text, 'xml')
                entries = soup.find_all('entry')
                
                for entry in entries:
                    paper_id = entry.id.text
                    title = entry.title.text.strip().replace('\n', ' ')
                    summary = entry.summary.text.strip().replace('\n', ' ')
                    pdf_link = entry.find('link', title='pdf')
                    pdf_url = pdf_link['href'] if pdf_link else None
                    
                    if self.url_exists(paper_id):
                        continue
                    
                    print(f"      ✅ Paper reciente: {title[:50]}...")
                    
                    doc = {
                        "source": "ArXiv - Recent LLM Ops",
                        "title": title,
                        "url": paper_id,
                        "pdf_url": pdf_url,
                        "content_markdown": f"## Abstract\n\n{summary}",
                        "tags": ["llm", "operations", "recent", "research-paper"],
                        "curated_category": "recent_llm_paper",
                        "needs_pdf_processing": True
                    }
                    self.save_knowledge(doc)
                    time.sleep(2)
                    
            except Exception as e:
                print(f"   🔥 Error buscando papers recientes: {e}")


if __name__ == "__main__":
    spider = ArxivFoundationalSpider()
    spider.run(include_recent_llm=True)
