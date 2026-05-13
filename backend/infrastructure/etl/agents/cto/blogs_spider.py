"""
CTO Spiders - Engineering Blogs
================================
Spiders para blogs de ingeniería con filtrado por keywords de alto valor.
"""

import os
import sys
import time
import feedparser
from bs4 import BeautifulSoup

# Importar clase base
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core.base_spider import BaseTechSpider


class CuratedBlogSpider(BaseTechSpider):
    """
    Clase base para blogs de ingeniería con filtrado por keywords.
    Solo guarda artículos que contengan palabras clave de alto valor.
    """
    
    # Keywords que indican contenido de alta calidad
    HIGH_VALUE_KEYWORDS = [
        'migration', 'scaling', 'scale', 'post-mortem', 'postmortem',
        'incident', 'outage', 'architecture', 'refactoring', 'performance',
        'distributed', 'infrastructure', 'microservices', 'database'
    ]
    
    def matches_keywords(self, title, summary=""):
        """Verifica si el título o resumen contiene keywords de alto valor."""
        combined_text = (title + " " + summary).lower()
        return any(keyword in combined_text for keyword in self.HIGH_VALUE_KEYWORDS)


class NetflixEngineeringSpider(CuratedBlogSpider):
    """Spider para Netflix Tech Blog - Solo artículos sobre microservicios y escalabilidad."""
    
    def run(self, limit=10):
        print(f"\n📺 [{self.__class__.__name__}] Netflix Tech Blog (Top Microservices)...")
        feed_url = "https://netflixtechblog.com/feed"
        
        try:
            # ✅ CRÍTICO: Usar headers realistas para evitar truncación de Medium
            feed = feedparser.parse(feed_url, agent=self.headers['User-Agent'])
            
            if len(feed.entries) == 0:
                print(f"   ⚠️ Feed vacío o bloqueado. Intentando feed alternativo...")
                # Intentar con feed de Medium directo
                feed_url_alt = "https://medium.com/feed/netflix-techblog"
                feed = feedparser.parse(feed_url_alt, agent=self.headers['User-Agent'])
                
                if len(feed.entries) == 0:
                    print(f"   ❌ Ambos feeds vacíos. Medium puede estar bloqueando.")
                    return
            
            print(f"   📄 Encontrados {len(feed.entries)} artículos en el feed")
            count = 0
            
            for entry in feed.entries:
                if count >= limit:
                    break
                
                if not self.matches_keywords(entry.title, entry.get('summary', '')):
                    continue
                
                if self.url_exists(entry.link):
                    print(f"   💤 Ya existe: {entry.title[:40]}")
                    continue
                
                print(f"   📄 Artículo curado: {entry.title[:50]}...")
                
                markdown = self.extract_content(entry.link)
                if markdown and len(markdown) > 800:
                    filepath = self.save_raw_html(entry.link, entry.title, agent_subdir="cto/blogs", prefix="Netflix_")
                    
                    doc = {
                        "source": "Netflix Tech Blog",
                        "title": entry.title,
                        "url": entry.link,
                        "file_path": filepath,
                        "content_markdown": markdown,
                        "tags": ["architecture", "streaming", "microservices", "netflix"],
                        "published_date": entry.get('published', ''),
                        "curated_category": "engineering_blog"
                    }
                    self.save_knowledge(doc)
                    count += 1
                    time.sleep(2)
                    
        except Exception as e:
            print(f"   🔥 Error en Netflix: {e}")


class UberEngineeringSpider(CuratedBlogSpider):
    """Spider para Uber Engineering - Enfocado en migraciones de bases de datos."""
    
    def run(self, limit=5):
        print(f"\n🚗 [{self.__class__.__name__}] Uber Engineering (DB Migrations)...")
        feed_url = "https://eng.uber.com/feed/"
        
        try:
            # ✅ Usar headers realistas
            feed = feedparser.parse(feed_url, agent=self.headers['User-Agent'])
            count = 0
            
            for entry in feed.entries:
                if count >= limit:
                    break
                
                # Filtrado más estricto para Uber
                combined = (entry.title + " " + entry.get('summary', '')).lower()
                if not ('migration' in combined or 'database' in combined or 'postgres' in combined or 'mysql' in combined):
                    continue
                
                if self.url_exists(entry.link):
                    print(f"   💤 Ya existe: {entry.title[:40]}")
                    continue
                
                print(f"   📄 Artículo curado: {entry.title[:50]}...")
                
                markdown = self.extract_content(entry.link)
                if markdown and len(markdown) > 800:
                    filepath = self.save_raw_html(entry.link, entry.title, agent_subdir="cto/blogs", prefix="Uber_")
                    
                    doc = {
                        "source": "Uber Engineering",
                        "title": entry.title,
                        "url": entry.link,
                        "file_path": filepath,
                        "content_markdown": markdown,
                        "tags": ["distributed-systems", "database", "migration", "uber"],
                        "published_date": entry.get('published', ''),
                        "curated_category": "engineering_blog"
                    }
                    self.save_knowledge(doc)
                    count += 1
                    time.sleep(2)
                    
        except Exception as e:
            print(f"   🔥 Error en Uber: {e}")


class DiscordEngineeringSpider(CuratedBlogSpider):
    """Spider para Discord Engineering - Artículos sobre escalabilidad de Elixir y ScyllaDB."""
    
    def run(self, limit=10):
        print(f"\n💬 [{self.__class__.__name__}] Discord Engineering Blog...")
        blog_url = "https://discord.com/category/engineering"
        
        try:
            response = self.headers
            from bs4 import BeautifulSoup
            import requests
            
            response = requests.get(blog_url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.text, "html.parser")
            
            articles = soup.select("article a[href*='/blog/']")
            
            count = 0
            for link in articles:
                if count >= limit:
                    break
                
                article_url = link.get('href', '')
                if not article_url.startswith('http'):
                    article_url = 'https://discord.com' + article_url
                
                title = link.get_text().strip()
                
                if not self.matches_keywords(title):
                    continue
                
                if self.url_exists(article_url):
                    print(f"   💤 Ya existe: {title[:40]}")
                    continue
                
                print(f"   📄 Artículo curado: {title[:50]}...")
                
                markdown = self.extract_content(article_url)
                if markdown and len(markdown) > 800:
                    filepath = self.save_raw_html(article_url, title, agent_subdir="cto/blogs", prefix="Discord_")
                    
                    doc = {
                        "source": "Discord Engineering",
                        "title": title,
                        "url": article_url,
                        "file_path": filepath,
                        "content_markdown": markdown,
                        "tags": ["elixir", "scylladb", "scaling", "discord"],
                        "curated_category": "engineering_blog"
                    }
                    self.save_knowledge(doc)
                    count += 1
                    time.sleep(3)
                    
        except Exception as e:
            print(f"   🔥 Error en Discord: {e}")


if __name__ == "__main__":
    # Ejemplo de uso
    netflix_spider = NetflixEngineeringSpider()
    netflix_spider.run(limit=5)
    
    uber_spider = UberEngineeringSpider()
    uber_spider.run(limit=3)
    
    discord_spider = DiscordEngineeringSpider()
    discord_spider.run(limit=5)
