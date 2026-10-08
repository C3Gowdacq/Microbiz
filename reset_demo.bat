@echo off
echo ==============================================================
echo   Restoring MicroBizAI Showcase Database to Baseline State...
echo ==============================================================
python reset_demo.py
echo ==============================================================
echo   Reset Complete! All 80 products, 25 customers, 350+ sales,
echo   16 expenses, 8 POs, and 20 AI recommendations restored.
echo ==============================================================
pause
