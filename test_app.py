"""
Milestone 4: Automated Testing & Validation Suite
Tests Unit, Integration, and ML Model performance (MAE, MSE, RMSE, R² Score)
"""

import unittest
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.app import app
from backend.ml_engine import ml_engine
from backend.database import (
    init_db, register_user, login_user, add_transaction,
    get_transactions, update_transaction, delete_transaction,
    set_budget, get_budget_status, get_user_by_email
)
from backend.categorizer import auto_categorize
from backend.recommendations import generate_personalized_recommendations

class PersonalFinanceSystemTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = app.test_client()

    # 1. Milestone 4: ML Model Evaluation Metrics Test
    def test_ml_model_metrics(self):
        """Verifies Multiple Linear Regression meets Milestone 4 metrics standards."""
        metrics = ml_engine.full_metrics
        self.assertIn('r2_score', metrics)
        self.assertIn('mae', metrics)
        self.assertIn('mse', metrics)
        self.assertIn('rmse', metrics)

        # Check R² Score is high (above 0.90)
        self.assertGreater(metrics['r2_score'], 0.90, "R² Score must exceed 0.90")
        
        # Check RMSE is positive and finite
        self.assertGreater(metrics['rmse'], 0)
        self.assertGreater(metrics['mae'], 0)

        # Check prediction output
        pred = ml_engine.predict(income=45000, prev_expense=22000, category='Food', payment_mode='UPI', amount=1500)
        self.assertIn('predicted_expense', pred)
        self.assertIn('confidence_interval', pred)
        self.assertGreater(pred['predicted_expense'], 0)
        self.assertLess(pred['confidence_interval']['lower'], pred['confidence_interval']['upper'])

    # 2. Database CRUD Test
    def test_database_crud(self):
        """Verifies User, Transaction, and Budget database operations."""
        email = "test_user_qa@finance.ai"
        user = get_user_by_email(email)
        if not user:
            user = register_user("Test User", email, "secret123", 50000)
        self.assertIsNotNone(user)

        # Authentication test
        logged_in = login_user(email, "secret123")
        self.assertIsNotNone(logged_in)
        self.assertEqual(logged_in['email'], email)

        # Add transaction
        tx_id = add_transaction(user['id'], '2026-10-15', 'expense', 'Food', 1250, 'UPI', 'Test Dinner')
        self.assertIsInstance(tx_id, int)

        # Fetch transaction
        txs = get_transactions(user['id'], category='Food')
        self.assertTrue(any(t['id'] == tx_id for t in txs))

        # Update transaction
        updated = update_transaction(tx_id, user['id'], '2026-10-15', 'expense', 'Food', 1400, 'UPI', 'Test Dinner Revised')
        self.assertTrue(updated)

        # Delete transaction
        deleted = delete_transaction(tx_id, user['id'])
        self.assertTrue(deleted)

    # 3. Categorization Engine Test
    def test_auto_categorization(self):
        """Verifies intelligent keyword-matching auto categorizer."""
        self.assertEqual(auto_categorize('Whole foods organic grocery store'), 'Food')
        self.assertEqual(auto_categorize('Uber cab ride to office'), 'Transport')
        self.assertEqual(auto_categorize('Monthly high-speed fiber wifi bill'), 'Bills')
        self.assertEqual(auto_categorize('Netflix 4K UHD streaming plan'), 'Entertainment')
        self.assertEqual(auto_categorize('Amazon prime clothes and electronics'), 'Shopping')
        self.assertEqual(auto_categorize('Apollo pharmacy prescription medicine'), 'Healthcare')
        self.assertEqual(auto_categorize('Udemy complete machine learning masterclass'), 'Education')

    # 4. Budget Status & Calculations Test
    def test_budget_management(self):
        """Verifies monthly budget setting and balance tracking."""
        user = get_user_by_email("demo@finance.ai")
        set_budget(user['id'], 'Bills', 15000, '2026-10')
        status = get_budget_status(user['id'], '2026-10')
        self.assertIn('categories', status)
        self.assertIn('total_budget', status)
        self.assertIn('total_spent', status)

    # 5. REST API Endpoints Integration Test
    def test_flask_api_endpoints(self):
        """Tests Flask HTTP API responses."""
        # Health check
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data['status'], 'healthy')

        # ML Metrics API
        res = self.client.get('/api/ml/metrics')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn('core_model', data)
        self.assertIn('full_model', data)

        # ML Prediction API
        res = self.client.post('/api/ml/predict', json={
            'income': 40000,
            'previous_month_expense': 20000,
            'category': 'Food',
            'payment_mode': 'UPI',
            'amount': 800
        })
        self.assertEqual(res.status_code, 200)
        pred_data = json.loads(res.data)
        self.assertIn('predicted_expense', pred_data)

        # Recommendations API
        res = self.client.get('/api/recommendations')
        self.assertEqual(res.status_code, 200)
        rec_data = json.loads(res.data)
        self.assertIn('save_more', rec_data)
        self.assertIn('unnecessary_spending', rec_data)
        self.assertIn('budget_suggestions', rec_data)
        self.assertIn('investment_tips', rec_data)
        self.assertIn('financial_health_score', rec_data)

    # 6. Test New Account Zero Baseline & Manual Prediction Workflow
    def test_new_account_zero_baseline_and_manual_prediction(self):
        """Verifies that a newly registered account starts strictly at 0, and manual entry drives predictions."""
        fresh_email = f"fresh_user_{os.urandom(4).hex()}@finance.ai"
        
        # 1. Register new user
        reg_res = self.client.post('/api/auth/register', json={
            'name': 'Fresh User',
            'email': fresh_email,
            'password': 'password123',
            'monthly_income': 0
        })
        self.assertEqual(reg_res.status_code, 200)
        reg_data = json.loads(reg_res.data)
        user_id = reg_data['user']['id']

        # 2. Check all data starts strictly at 0
        txs_res = self.client.get('/api/transactions')
        txs_data = json.loads(txs_res.data)
        self.assertEqual(len(txs_data['transactions']), 0, "New account transactions must start at 0")

        summary_res = self.client.get('/api/analytics/summary')
        summary_data = json.loads(summary_res.data)
        self.assertEqual(summary_data['total_income'], 0, "New account income must start at 0")
        self.assertEqual(summary_data['total_expense'], 0, "New account expenses must start at 0")
        self.assertEqual(summary_data['net_savings'], 0, "New account savings must start at 0")

        # Verify prediction is 0 when income and expense are 0
        zero_pred = self.client.post('/api/ml/predict', json={'income': 0, 'previous_month_expense': 0})
        zero_data = json.loads(zero_pred.data)
        self.assertEqual(zero_data['predicted_expense'], 0.0, "Prediction must be 0 when data is 0")
        self.assertFalse(zero_data.get('has_data', True))

        # 3. Enter manual income record
        add_inc = self.client.post('/api/transactions', json={
            'type': 'income',
            'amount': 45000,
            'category': 'Salary',
            'payment_mode': 'Net Banking',
            'description': 'Manual Monthly Salary'
        })
        self.assertEqual(add_inc.status_code, 201)

        # 4. Enter manual expense records
        add_exp1 = self.client.post('/api/transactions', json={
            'type': 'expense',
            'amount': 12000,
            'category': 'Bills',
            'payment_mode': 'UPI',
            'description': 'Apartment Rent'
        })
        self.assertEqual(add_exp1.status_code, 201)

        add_exp2 = self.client.post('/api/transactions', json={
            'type': 'expense',
            'amount': 4500,
            'category': 'Food',
            'payment_mode': 'Credit Card',
            'description': 'Monthly Groceries'
        })
        self.assertEqual(add_exp2.status_code, 201)

        # 5. Verify updated manual totals
        updated_summary = json.loads(self.client.get('/api/analytics/summary').data)
        self.assertEqual(updated_summary['total_income'], 45000)
        self.assertEqual(updated_summary['total_expense'], 16500)
        self.assertEqual(updated_summary['net_savings'], 28500)

        # 6. Predict future expense based on manual entries
        pred_res = self.client.post('/api/ml/predict', json={
            'income': updated_summary['total_income'],
            'previous_month_expense': updated_summary['total_expense'],
            'category': 'Food',
            'payment_mode': 'UPI',
            'amount': 1500
        })
        self.assertEqual(pred_res.status_code, 200)
        pred_data = json.loads(pred_res.data)
        self.assertGreater(pred_data['predicted_expense'], 1000)
        self.assertIn('confidence_interval', pred_data)
        self.assertEqual(pred_data['inputs']['income'], 45000)
        self.assertEqual(pred_data['inputs']['previous_month_expense'], 16500)

    # 7. Test Default Account vs Another Account Prediction Isolation
    def test_default_vs_another_account_prediction_isolation(self):
        """Verifies default prediction numbers exist ONLY for default account, and other accounts require owner income & expenses."""
        # A. Default demo account login
        demo_login = self.client.post('/api/auth/demo-login')
        self.assertEqual(demo_login.status_code, 200)
        demo_user = json.loads(demo_login.data)['user']
        self.assertTrue(demo_user['is_default'])

        # Default account receives prediction numbers even if empty request is sent
        demo_pred = self.client.post('/api/ml/predict', json={'income': 0, 'previous_month_expense': 0})
        demo_pred_data = json.loads(demo_pred.data)
        self.assertGreater(demo_pred_data['predicted_expense'], 0, "Default account must have default prediction numbers")
        self.assertTrue(demo_pred_data.get('has_data', False))

        # B. Register another user account
        other_email = f"other_user_{os.urandom(4).hex()}@finance.ai"
        other_reg = self.client.post('/api/auth/register', json={
            'name': 'Other Owner',
            'email': other_email,
            'password': 'password123',
            'monthly_income': 0
        })
        self.assertEqual(other_reg.status_code, 200)
        other_user = json.loads(other_reg.data)['user']
        self.assertFalse(other_user['is_default'], "Other account must not be default")

        # In another account: 0 income & 0 expense -> Strictly 0 prediction
        p0 = self.client.post('/api/ml/predict', json={'income': 0, 'previous_month_expense': 0})
        d0 = json.loads(p0.data)
        self.assertEqual(d0['predicted_expense'], 0.0)
        self.assertFalse(d0.get('has_data', True))

        # In another account: only income entered -> Strictly 0 prediction
        p_inc = self.client.post('/api/ml/predict', json={'income': 50000, 'previous_month_expense': 0})
        d_inc = json.loads(p_inc.data)
        self.assertEqual(d_inc['predicted_expense'], 0.0, "Prediction must be 0 if only income is provided in other account")
        self.assertFalse(d_inc.get('has_data', True))

        # In another account: only expense entered -> Strictly 0 prediction
        p_exp = self.client.post('/api/ml/predict', json={'income': 0, 'previous_month_expense': 12000})
        d_exp = json.loads(p_exp.data)
        self.assertEqual(d_exp['predicted_expense'], 0.0, "Prediction must be 0 if only expense is provided in other account")
        self.assertFalse(d_exp.get('has_data', True))

        # In another account: owner adds BOTH expenses and income -> Prediction added!
        p_both = self.client.post('/api/ml/predict', json={
            'income': 50000,
            'previous_month_expense': 18000,
            'category': 'Food',
            'payment_mode': 'UPI',
            'amount': 1500
        })
        d_both = json.loads(p_both.data)
        self.assertGreater(d_both['predicted_expense'], 1000, "Prediction must be added when owner has income and expenses")
        self.assertTrue(d_both.get('has_data', False))
        self.assertGreater(d_both['expected_savings'], 0)

if __name__ == '__main__':
    unittest.main()

