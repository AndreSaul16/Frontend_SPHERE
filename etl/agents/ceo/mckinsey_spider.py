"""
CEO Spider - McKinsey Insights
===============================
Spider para McKinsey Featured Insights - Estrategia empresarial.
"""

import os
import sys
import time
import requests
from bs4 import BeautifulSoup

# Importar clase base
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core.base_spider import BaseTechSpider


class McKinseySpider(BaseTechSpider):
    """
    Spider para McKinsey Featured Insights - Estrategia empresarial.
    """
    
    def __init__(self):
        super().__init__(agent_name="CEO")  # Este es para el agente CEO
    
    def run(self, limit=5):
        print(f"\n🤵 [{self.__class__.__name__}] Revisando McKinsey Insights...")
        url = "https://www.mckinsey.com/featured-insights"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Selector específico de McKinsey (puede cambiar)
            articles = soup.select(".item-title-link")
            
            count = 0
            for link in articles:
                if count >= limit: 
                    break
                
                title = link.get_text().strip()
                article_url = link.get('href', '')
                
                # Corregir URLs relativas
                if not article_url.startswith("http"):
                    article_url = "https://www.mckinsey.com" + article_url
                
                if self.url_exists(article_url):
                    print(f"   💤 Ya existe: {title[:40]}")
                    continue
                
                print(f"   📄 Procesando: {title[:50]}...")
                
                time.sleep(3)  # McKinsey puede ser estricto
                markdown = self.extract_content(article_url)
                
                if markdown and len(markdown) > 1000:
                    filepath = self.save_raw_html(article_url, title, agent_subdir="ceo", prefix="McKinsey_")
                    
                    doc = {
                        "source": "McKinsey",
                        "title": title,
                        "url": article_url,
                        "file_path": filepath,
                        "content_markdown": markdown,
                        "tags": ["strategy", "business", "consulting"]
                    }
                    self.save_knowledge(doc)
                    count += 1
                    
        except Exception as e:
            print(f"   🔥 Error en McKinsey: {e}")


if __name__ == "__main__":
    spider = McKinseySpider()
    spider.run(limit=5)
