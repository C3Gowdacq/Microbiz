"""
backend/scripts/seed_guide_demo_data.py

Master Seed & Reset Script for MicroBizAI Academic & Guide Presentation.
Delegates to the expanded abundant dataset seeder with 80+ products, 25 customers, 350+ sales, 16 expenses, and 20 recommendations.

Run anytime:
    python backend/scripts/seed_guide_demo_data.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.scripts.expand_abundant_dataset import seed_massive_data

if __name__ == "__main__":
    seed_massive_data()
