"""
reset_demo.py -- 1-Click Master Presentation Reset Script for MicroBizAI.
Resets the database and restores all 80 products, 25 customers, 350+ sales,
16 expenses, 8 purchase orders, and 20 multi-agent AI recommendations.

Usage:
    python reset_demo.py
"""

import os
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.scripts.expand_abundant_dataset import seed_massive_data

if __name__ == "__main__":
    print("\n[RESET] Resetting MicroBizAI Demo Data to Original Presentation State...\n")
    seed_massive_data()
    print("\n[SUCCESS] MicroBizAI Demo Data successfully restored to Pristine Showcase State!\n")
