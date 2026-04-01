"""
CFO Agent - Main Entry Point
=============================
Punto de entrada para ejecutar el pipeline CFO.
"""

from . import run_cfo_pipeline
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='CFO Knowledge Pipeline')
    parser.add_argument('--limit', type=int, default=2, help='Docs por spider (default: 2)')
    parser.add_argument('--quick', action='store_true', help='Modo rápido (1 por spider)')
    
    args = parser.parse_args()
    
    if args.quick:
        run_cfo_pipeline(limit_per_spider=1)
    else:
        run_cfo_pipeline(limit_per_spider=args.limit)
