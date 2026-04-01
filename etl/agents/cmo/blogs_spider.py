"""
CMO Spiders - Marketing Blogs
==============================
Spiders para blogs de marketing con filtrado por keywords de alto valor.
Solo guarda contenido sobre growth engineering, consumer psychology, y data-driven marketing.
"""

import os
import sys
import time
import feedparser
from bs4 import BeautifulSoup

# Importar clase base
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core.base_spider import BaseTechSpider


class CuratedMarketingBlogSpider(BaseTechSpider):
    """
    Clase base para blogs de marketing con filtrado por keywords.
    Solo guarda artículos que contengan conceptos de alto valor.
    """
    
    # Keywords que indican contenido de alta calidad
    HIGH_VALUE_KEYWORDS = [
        # Growth Engineering
        'growth loops', 'growth hacking', 'viral', 'virality', 'network effects',
        'retention', 'activation', 'conversion', 'funnel', 'pirate metrics',
        'product-market fit', 'pmf', 'cohort analysis',
        
        # Consumer Psychology
        'behavioral', 'psychology', 'cognitive bias', 'persuasion', 'influence',
        'system 1', 'system 2', 'heuristics', 'mental availability',
        
        # Strategy & Frameworks
        'positioning', 'category design', 'messaging', 'narrative',
        'brand equity', 'differentiation', 'segmentation',
        
        # Data & Analytics
        'attribution', 'ltv', 'cac', 'unit economics', 'cohort',
        'experimentation', 'a/b test', 'causal inference'
    ]
    
    # Anti-patrones para excluir
    BLOCKED_KEYWORDS = [
        'top 10', 'top 5', 'best tools', 'for beginners',
        'get rich quick', 'secret', 'hack your way',
        'influencer tips', 'motivational', 'mindset'
    ]
    
    def matches_keywords(self, title, summary=""):
        """Verifica si el título o resumen contiene keywords de alto valor."""
        combined_text = (title + " " + summary).lower()
        
        # Bloquear contenido superficial
        if any(blocked in combined_text for blocked in self.BLOCKED_KEYWORDS):
            return False
        
        # Requerir al menos una keyword de calidad
        return any(keyword in combined_text for keyword in self.HIGH_VALUE_KEYWORDS)


class ReforgeSpider(CuratedMarketingBlogSpider):
    """Spider para Reforge Blog - Growth Loops y Product Strategy."""
    
    def run(self, limit=10):
        print(f"\n🔄 [{self.__class__.__name__}] Reforge Blog (Growth Loops)...")
        feed_url = "https://www.reforge.com/blog/feed"
        
        try:
            feed = feedparser.parse(feed_url, agent=self.headers['User-Agent'])
            
            if len(feed.entries) == 0:
                print(f"   ⚠️ Feed vacío o bloqueado. Intentando scraping directo...")
                # TODO: Implementar fallback con BeautifulSoup
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
                if markdown and len(markdown) > 500:
                    filepath = self.save_raw_html(entry.link, entry.title, agent_subdir="cmo/blogs", prefix="Reforge_")
                    
                    doc = {
                        "source": "Reforge Blog",
                        "title": entry.title,
                        "url": entry.link,
                        "file_path": filepath,
                        "content_markdown": markdown,
                        "tags": ["growth", "product-strategy", "retention", "reforge"],
                        "published_date": entry.get('published', ''),
                        "curated_category": "marketing_blog",
                        "marketing_funnel_stage": self._detect_funnel_stage(markdown)
                    }
                    self.save_knowledge(doc)
                    count += 1
                    time.sleep(2)
                    
        except Exception as e:
            print(f"   🔥 Error en Reforge: {e}")
    
    def _detect_funnel_stage(self, content):
        """Detecta la etapa del funnel basándose en keywords."""
        content_lower = content.lower()
        if 'retention' in content_lower or 'churn' in content_lower:
            return 'retention'
        elif 'activation' in content_lower or 'onboarding' in content_lower:
            return 'activation'
        elif 'acquisition' in content_lower or 'awareness' in content_lower:
            return 'acquisition'
        elif 'revenue' in content_lower or 'monetization' in content_lower:
            return 'revenue'
        else:
            return 'general'


class AndrewChenSpider(CuratedMarketingBlogSpider):
    """Spider para Andrew Chen (a16z) - Network Effects y Virality."""
    
    def run(self, limit=10):
        print(f"\n📈 [{self.__class__.__name__}] Andrew Chen Blog (a16z)...")
        feed_url = "https://andrewchen.substack.com/feed"
        
        try:
            feed = feedparser.parse(feed_url, agent=self.headers['User-Agent'])
            print(f"   📄 Encontrados {len(feed.entries)} artículos en el feed")
            count = 0
            
            for entry in feed.entries:
                if count >= limit:
                    break
                
                # Filtrado más estricto para Andrew Chen
                combined = (entry.title + " " + entry.get('summary', '')).lower()
                if not ('network effect' in combined or 'viral' in combined or 
                        'growth' in combined or 'marketplace' in combined or
                        'retention' in combined):
                    continue
                
                if self.url_exists(entry.link):
                    print(f"   💤 Ya existe: {entry.title[:40]}")
                    continue
                
                print(f"   📄 Artículo curado: {entry.title[:50]}...")
                
                markdown = self.extract_content(entry.link)
                if markdown and len(markdown) > 500:
                    filepath = self.save_raw_html(entry.link, entry.title, agent_subdir="cmo/blogs", prefix="AndrewChen_")
                    
                    doc = {
                        "source": "Andrew Chen (a16z)",
                        "title": entry.title,
                        "url": entry.link,
                        "file_path": filepath,
                        "content_markdown": markdown,
                        "tags": ["network-effects", "virality", "growth", "a16z"],
                        "published_date": entry.get('published', ''),
                        "curated_category": "marketing_blog"
                    }
                    self.save_knowledge(doc)
                    count += 1
                    time.sleep(2)
                    
        except Exception as e:
            print(f"   🔥 Error en Andrew Chen: {e}")


class MozBlogSpider(CuratedMarketingBlogSpider):
    """Spider para Moz Blog - SEO técnico y data-driven."""
    
    def run(self, limit=8):
        print(f"\n🔍 [{self.__class__.__name__}] Moz Blog (Technical SEO)...")
        feed_url = "https://moz.com/blog/feed"
        
        try:
            feed = feedparser.parse(feed_url, agent=self.headers['User-Agent'])
            print(f"   📄 Encontrados {len(feed.entries)} artículos en el feed")
            count = 0
            
            for entry in feed.entries:
                if count >= limit:
                    break
                
                # Solo artículos técnicos de SEO
                combined = (entry.title + " " + entry.get('summary', '')).lower()
                if not ('algorithm' in combined or 'ranking' in combined or 
                        'technical' in combined or 'data' in combined or
                        'search intent' in combined or 'crawl' in combined):
                    continue
                
                if self.url_exists(entry.link):
                    print(f"   💤 Ya existe: {entry.title[:40]}")
                    continue
                
                print(f"   📄 Artículo curado: {entry.title[:50]}...")
                
                markdown = self.extract_content(entry.link)
                if markdown and len(markdown) > 500:
                    filepath = self.save_raw_html(entry.link, entry.title, agent_subdir="cmo/blogs", prefix="Moz_")
                    
                    doc = {
                        "source": "Moz Blog",
                        "title": entry.title,
                        "url": entry.link,
                        "file_path": filepath,
                        "content_markdown": markdown,
                        "tags": ["seo", "search", "technical-seo", "data-driven"],
                        "published_date": entry.get('published', ''),
                        "curated_category": "marketing_blog"
                    }
                    self.save_knowledge(doc)
                    count += 1
                    time.sleep(2)
                    
        except Exception as e:
            print(f"   🔥 Error en Moz: {e}")


class AhrefsBlogSpider(CuratedMarketingBlogSpider):
    """Spider para Ahrefs Blog - Data-driven SEO."""
    
    def run(self, limit=8):
        print(f"\n📊 [{self.__class__.__name__}] Ahrefs Blog (Data-driven SEO)...")
        feed_url = "https://ahrefs.com/blog/feed/"
        
        try:
            feed = feedparser.parse(feed_url, agent=self.headers['User-Agent'])
            print(f"   📄 Encontrados {len(feed.entries)} artículos en el feed")
            count = 0
            
            for entry in feed.entries:
                if count >= limit:
                    break
                
                # Solo artículos con datos y análisis
                combined = (entry.title + " " + entry.get('summary', '')).lower()
                if not ('data' in combined or 'study' in combined or 
                        'research' in combined or 'analysis' in combined or
                        'ranking' in combined):
                    continue
                
                if self.url_exists(entry.link):
                    print(f"   💤 Ya existe: {entry.title[:40]}")
                    continue
                
                print(f"   📄 Artículo curado: {entry.title[:50]}...")
                
                markdown = self.extract_content(entry.link)
                if markdown and len(markdown) > 500:
                    filepath = self.save_raw_html(entry.link, entry.title, agent_subdir="cmo/blogs", prefix="Ahrefs_")
                    
                    doc = {
                        "source": "Ahrefs Blog",
                        "title": entry.title,
                        "url": entry.link,
                        "file_path": filepath,
                        "content_markdown": markdown,
                        "tags": ["seo", "data-analysis", "research", "ahrefs"],
                        "published_date": entry.get('published', ''),
                        "curated_category": "marketing_blog"
                    }
                    self.save_knowledge(doc)
                    count += 1
                    time.sleep(2)
                    
        except Exception as e:
            print(f"   🔥 Error en Ahrefs: {e}")


class KellblogSpider(CuratedMarketingBlogSpider):
    """Spider para Kellblog (Dave Kellogg) - SaaS Metrics."""
    
    def run(self, limit=8):
        print(f"\n💼 [{self.__class__.__name__}] Kellblog (SaaS Metrics)...")
        feed_url = "https://kellblog.com/feed/"
        
        try:
            feed = feedparser.parse(feed_url, agent=self.headers['User-Agent'])
            print(f"   📄 Encontrados {len(feed.entries)} artículos en el feed")
            count = 0
            
            for entry in feed.entries:
                if count >= limit:
                    break
                
                # Solo artículos sobre métricas y estrategia SaaS
                combined = (entry.title + " " + entry.get('summary', '')).lower()
                if not ('metrics' in combined or 'saas' in combined or 
                        'revenue' in combined or 'growth' in combined or
                        'gtm' in combined or 'marketing' in combined):
                    continue
                
                if self.url_exists(entry.link):
                    print(f"   💤 Ya existe: {entry.title[:40]}")
                    continue
                
                print(f"   📄 Artículo curado: {entry.title[:50]}...")
                
                markdown = self.extract_content(entry.link)
                if markdown and len(markdown) > 500:
                    filepath = self.save_raw_html(entry.link, entry.title, agent_subdir="cmo/blogs", prefix="Kellblog_")
                    
                    doc = {
                        "source": "Kellblog (Dave Kellogg)",
                        "title": entry.title,
                        "url": entry.link,
                        "file_path": filepath,
                        "content_markdown": markdown,
                        "tags": ["saas", "metrics", "b2b-marketing", "strategy"],
                        "published_date": entry.get('published', ''),
                        "curated_category": "marketing_blog"
                    }
                    self.save_knowledge(doc)
                    count += 1
                    time.sleep(2)
                    
        except Exception as e:
            print(f"   🔥 Error en Kellblog: {e}")


if __name__ == "__main__":
    # Ejemplo de uso
    print("🚀 Iniciando spiders de Marketing Blogs...\n")
    
    reforge = ReforgeSpider(agent_name="CMO")
    reforge.run(limit=5)
    
    andrew_chen = AndrewChenSpider(agent_name="CMO")
    andrew_chen.run(limit=5)
    
    moz = MozBlogSpider(agent_name="CMO")
    moz.run(limit=5)
    
    ahrefs = AhrefsBlogSpider(agent_name="CMO")
    ahrefs.run(limit=5)
    
    kellblog = KellblogSpider(agent_name="CMO")
    kellblog.run(limit=5)
    
    print("\n✅ Ejecución completada")
