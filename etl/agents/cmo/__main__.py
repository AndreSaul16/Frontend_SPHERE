"""
CMO Agent - Main Entry Point
=============================
Punto de entrada para ejecutar el pipeline CMO.
"""

from . import run_cmo_pipeline
import argparse

if __name__ == "__main__":
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
