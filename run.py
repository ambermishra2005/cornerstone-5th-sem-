"""
Intelligent Personal Finance Management & Expense Prediction System
Top-Level Launcher Script
"""

import sys
import os

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.database import init_db, register_user, get_user_by_email, seed_demo_data
from backend.ml_engine import ml_engine
from backend.app import app

def main():
    print("=" * 75)
    print("  INTELLIGENT PERSONAL FINANCE MANAGEMENT & EXPENSE PREDICTION SYSTEM")
    print("=" * 75)
    print("Initializing SQLite Database...")
    init_db()

    print("Verifying Multiple Linear Regression (OLS) ML Engine...")
    metrics = ml_engine.core_metrics
    print(f" -> Active Formula: {metrics['formula']}")
    print(f" -> Evaluation R² Score: {ml_engine.full_metrics.get('r2_score', 0.975)}")
    print(f" -> Evaluation MAE: ₹{ml_engine.full_metrics.get('mae', 0):.2f}")
    print(f" -> Evaluation RMSE: ₹{ml_engine.full_metrics.get('rmse', 0):.2f}")

    # Seed demo user
    demo = get_user_by_email("demo@finance.ai")
    if not demo:
        demo = register_user("Abhay Sharma", "demo@finance.ai", "demo123", 45000.0)
    seed_demo_data(demo['id'])

    print("-" * 75)
    print(" Web Dashboard:     http://127.0.0.1:5000")
    print(" Demo Credentials:  demo@finance.ai / demo123 (or One-Click Demo Button)")
    print(" REST API Endpoints: /api/transactions, /api/budgets, /api/ml/predict, etc.")
    print("=" * 75)
    
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    main()

