"""
Flask Full-Stack Application for Intelligent Personal Finance Management & Expense Prediction System
Backend REST API + Web Dashboard Serving
"""

import os
import csv
import io
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session, make_response, send_from_directory

from backend.database import (
    get_connection, init_db, register_user, login_user, get_user_by_id, get_user_by_email,
    add_transaction, get_transactions, get_transaction_by_id, update_transaction, delete_transaction,
    set_budget, get_budgets, get_budget_status,
    save_prediction, get_prediction_history, seed_demo_data
)
from backend.ml_engine import ml_engine
from backend.categorizer import auto_categorize, get_all_categories, get_income_categories
from backend.recommendations import generate_personalized_recommendations

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(
    __name__,
    template_folder=TEMPLATES_DIR,
    static_folder=STATIC_DIR
)
app.secret_key = 'super_secure_personal_finance_ml_key_2026'

# Ensure database tables exist
init_db()

# Auto-seed a demo user for instantaneous one-click testing
DEMO_EMAIL = "demo@finance.ai"
demo_user = get_user_by_email(DEMO_EMAIL)
if not demo_user:
    demo_user = register_user("Abhay Sharma", DEMO_EMAIL, "demo123", 45000.0)
if demo_user:
    seed_demo_data(demo_user['id'])

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response

def get_current_user_id():
    """Returns logged-in user id or auto-initializes a fresh zero-balance user for new visitors."""
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
        if user:
            return user['id']

    # New visitor starts fresh with zero records
    fresh_user = register_user("New User", f"user_{os.urandom(4).hex()}@finance.ai", "pass123", 0.0)
    if fresh_user:
        session['user_id'] = fresh_user['id']
        session.permanent = True
        return fresh_user['id']

    user = get_user_by_email(DEMO_EMAIL)
    return user['id'] if user else 1

# ----------------- Frontend Route -----------------

@app.route('/')
def index():
    return render_template('index.html')

# ----------------- Health & Info -----------------

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'system': 'Intelligent Personal Finance Management & Expense Prediction System',
        'ml_model': 'Multiple Linear Regression (OLS)',
        'ml_trained': ml_engine.is_trained,
        'timestamp': datetime.now().isoformat()
    })

# ----------------- Auth Endpoints -----------------

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '').strip()
    raw_name = (data.get('name') or '').strip()

    if not email:
        return jsonify({'error': 'Please enter a valid email address.'}), 400
    if not password or len(password) < 4:
        return jsonify({'error': 'Password must be at least 4 characters long.'}), 400

    # Auto-derive friendly name if blank
    if raw_name:
        name = raw_name
    else:
        name = email.split('@')[0].replace('.', ' ').replace('_', ' ').title()

    income_raw = data.get('monthly_income')
    try:
        monthly_income = float(income_raw) if income_raw is not None and income_raw != '' else 0.0
    except (ValueError, TypeError):
        monthly_income = 0.0

    # Check for existing email
    existing = get_user_by_email(email)
    if existing:
        return jsonify({'error': f'An account with email "{email}" already exists. Please sign in instead.'}), 409

    user = register_user(name, email, password, monthly_income)
    if not user:
        return jsonify({'error': 'Could not create user account. Please try another email.'}), 500

    session['user_id'] = user['id']
    session.permanent = True
    user_dict = dict(user)
    user_dict['is_default'] = False
    return jsonify({
        'success': True,
        'user': user_dict,
        'message': f'Account created for {name}! Starting with zero baseline.'
    })

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '').strip()

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    user = login_user(email, password)
    if not user:
        existing = get_user_by_email(email)
        if not existing:
            return jsonify({'error': f'No account found with email "{email}". Please click "Register" to create one.'}), 404
        return jsonify({'error': 'Incorrect password. Please try again.'}), 401

    session['user_id'] = user['id']
    session.permanent = True
    user_dict = dict(user)
    user_dict['is_default'] = (user['email'] == DEMO_EMAIL)
    return jsonify({'success': True, 'user': user_dict})

@app.route('/api/auth/demo-login', methods=['POST'])
def api_demo_login():
    user = get_user_by_email(DEMO_EMAIL)
    if not user:
        user = register_user("Abhay Sharma", DEMO_EMAIL, "demo123", 45000.0)
    session['user_id'] = user['id']
    user_dict = dict(user)
    user_dict['is_default'] = True
    return jsonify({'success': True, 'user': user_dict})

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    session.pop('user_id', None)
    return jsonify({'success': True, 'message': 'Logged out successfully.'})

@app.route('/api/auth/me', methods=['GET'])
def api_me():
    user_id = get_current_user_id()
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found.'}), 404
    user_dict = dict(user)
    user_dict['is_default'] = (user['email'] == DEMO_EMAIL)
    return jsonify({'user': user_dict})

# ----------------- Transactions Endpoints -----------------

@app.route('/api/transactions', methods=['GET'])
def api_get_transactions():
    user_id = get_current_user_id()
    category = request.args.get('category')
    type_ = request.args.get('type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = request.args.get('limit', type=int)

    txs = get_transactions(user_id, start_date=start_date, end_date=end_date, category=category, type_=type_, limit=limit)
    return jsonify({'transactions': txs, 'count': len(txs)})

@app.route('/api/transactions', methods=['POST'])
def api_add_transaction():
    user_id = get_current_user_id()
    data = request.get_json() or {}

    date = data.get('date') or datetime.now().strftime('%Y-%m-%d')
    type_ = data.get('type', 'expense').lower()
    amount = float(data.get('amount', 0))
    payment_mode = data.get('payment_mode', 'UPI')
    description = data.get('description', '').strip()
    category = data.get('category')

    if amount <= 0:
        return jsonify({'error': 'Amount must be greater than zero.'}), 400

    # Auto-categorize if category is missing or set to auto
    if not category or category.lower() == 'auto':
        category = auto_categorize(description, default_category='Food' if type_ == 'expense' else 'Salary')

    tx_id = add_transaction(user_id, date, type_, category, amount, payment_mode, description)
    return jsonify({
        'success': True,
        'transaction': {
            'id': tx_id,
            'user_id': user_id,
            'date': date,
            'type': type_,
            'category': category,
            'amount': amount,
            'payment_mode': payment_mode,
            'description': description
        }
    }), 201

@app.route('/api/transactions/<int:tx_id>', methods=['GET'])
def api_get_single_transaction(tx_id):
    user_id = get_current_user_id()
    tx = get_transaction_by_id(tx_id, user_id)
    if not tx:
        return jsonify({'error': 'Transaction not found.'}), 404
    return jsonify({'transaction': tx})

@app.route('/api/transactions/<int:tx_id>', methods=['PUT'])
def api_update_transaction(tx_id):
    user_id = get_current_user_id()
    data = request.get_json() or {}

    date = data.get('date')
    type_ = data.get('type', 'expense').lower()
    category = data.get('category')
    amount = float(data.get('amount', 0))
    payment_mode = data.get('payment_mode', 'UPI')
    description = data.get('description', '')

    success = update_transaction(tx_id, user_id, date, type_, category, amount, payment_mode, description)
    if not success:
        return jsonify({'error': 'Failed to update transaction.'}), 400
    return jsonify({'success': True, 'message': 'Transaction updated successfully.'})

@app.route('/api/transactions/<int:tx_id>', methods=['DELETE'])
def api_delete_transaction(tx_id):
    user_id = get_current_user_id()
    success = delete_transaction(tx_id, user_id)
    if not success:
        return jsonify({'error': 'Failed to delete transaction.'}), 400
    return jsonify({'success': True, 'message': 'Transaction deleted successfully.'})

@app.route('/api/transactions/auto-categorize', methods=['POST'])
def api_auto_categorize():
    data = request.get_json() or {}
    text = data.get('description', '')
    predicted_category = auto_categorize(text)
    return jsonify({'category': predicted_category})

@app.route('/api/transactions/import-csv', methods=['POST'])
def api_import_csv():
    user_id = get_current_user_id()
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in request.'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400

    imported_count = 0
    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.DictReader(stream)
        for row in reader:
            date = row.get('Date') or row.get('date') or datetime.now().strftime('%Y-%m-%d')
            amount = float(row.get('Amount') or row.get('amount') or 0)
            type_ = (row.get('Type') or row.get('type') or 'expense').lower()
            category = row.get('Category') or row.get('category') or 'Other'
            payment_mode = row.get('Payment_Mode') or row.get('payment_mode') or 'UPI'
            description = row.get('Description') or row.get('Merchant') or row.get('description') or ''

            if amount > 0:
                add_transaction(user_id, date, type_, category, amount, payment_mode, description)
                imported_count += 1

        return jsonify({'success': True, 'imported_count': imported_count})
    except Exception as e:
        return jsonify({'error': f'Failed to parse CSV: {str(e)}'}), 400

@app.route('/api/transactions/export-csv', methods=['GET'])
def api_export_csv():
    user_id = get_current_user_id()
    txs = get_transactions(user_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Date', 'Type', 'Category', 'Amount', 'Payment_Mode', 'Description'])
    for t in txs:
        writer.writerow([t['id'], t['date'], t['type'], t['category'], t['amount'], t['payment_mode'], t['description']])

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=transactions_export.csv'
    response.headers['Content-type'] = 'text/csv'
    return response

# ----------------- Budgets Endpoints -----------------

@app.route('/api/budgets', methods=['GET'])
def api_get_budgets():
    user_id = get_current_user_id()
    month_year = request.args.get('month_year') or datetime.now().strftime('%Y-%m')
    budgets = get_budgets(user_id, month_year)
    return jsonify({'budgets': budgets, 'month_year': month_year})

@app.route('/api/budgets', methods=['POST'])
def api_set_budget():
    user_id = get_current_user_id()
    data = request.get_json() or {}
    category = data.get('category')
    monthly_limit = float(data.get('monthly_limit', 0))
    month_year = data.get('month_year') or datetime.now().strftime('%Y-%m')

    if not category or monthly_limit < 0:
        return jsonify({'error': 'Category and valid monthly limit are required.'}), 400

    set_budget(user_id, category, monthly_limit, month_year)
    return jsonify({'success': True, 'message': 'Budget updated successfully.'})

@app.route('/api/budgets/status', methods=['GET'])
def api_get_budget_status():
    user_id = get_current_user_id()
    month_year = request.args.get('month_year') or datetime.now().strftime('%Y-%m')
    status = get_budget_status(user_id, month_year)
    return jsonify(status)

@app.route('/api/budgets/auto-recommend', methods=['POST'])
def api_auto_recommend_budgets():
    """Auto-calibrates monthly budgets using ML Multiple Linear Regression forecast based on manual data."""
    user_id = get_current_user_id()
    user = get_user_by_id(user_id)
    is_default = (user['email'] == DEMO_EMAIL) if user else False
    txs = get_transactions(user_id)
    
    income_txs = [t for t in txs if t['type'] == 'income']
    total_income = sum(t['amount'] for t in income_txs)
    user_income = total_income if total_income > 0 else (user['monthly_income'] if user else 0.0)

    # Get user's actual entered expenses
    exp_txs = [t for t in txs if t['type'] == 'expense']
    prev_expense = sum(t['amount'] for t in exp_txs)

    # For default account fallback to demo figures if empty
    if is_default and (user_income <= 0 or prev_expense <= 0):
        user_income = 45000.0
        prev_expense = 21000.0

    if not is_default and (user_income <= 0 or prev_expense <= 0):
        return jsonify({
            'success': False,
            'error': 'Please enter both an income and an expense record manually first so the ML engine can calibrate your budget!'
        }), 400

    month_year = datetime.now().strftime('%Y-%m')

    # ML prediction for the upcoming month
    prediction = ml_engine.predict(income=user_income, prev_expense=prev_expense)
    predicted_total = prediction['predicted_expense']

    # Standard realistic category allocation breakdown based on dataset distribution
    allocations = {
        'Bills': 0.35,
        'Food': 0.20,
        'Transport': 0.12,
        'Shopping': 0.12,
        'Entertainment': 0.08,
        'Healthcare': 0.06,
        'Education': 0.04,
        'Other': 0.03
    }

    recommended_budgets = []
    for cat, weight in allocations.items():
        limit = round(predicted_total * weight, -1) # round to nearest 10
        set_budget(user_id, cat, limit, month_year)
        recommended_budgets.append({'category': cat, 'monthly_limit': limit})

    return jsonify({
        'success': True,
        'predicted_monthly_total': predicted_total,
        'recommended_budgets': recommended_budgets,
        'message': 'Category budgets successfully updated based on Multiple Linear Regression predictions!'
    })

# ----------------- Machine Learning (Regression) Endpoints -----------------

@app.route('/api/ml/metrics', methods=['GET'])
def api_ml_metrics():
    summary = ml_engine.get_summary()
    return jsonify(summary)

@app.route('/api/ml/predict', methods=['POST'])
def api_ml_predict():
    user_id = get_current_user_id()
    user = get_user_by_id(user_id)
    is_default = (user['email'] == DEMO_EMAIL) if user else False

    data = request.get_json(silent=True) or {}

    raw_income = data.get('income')
    raw_prev = data.get('previous_month_expense')
    try:
        income = float(raw_income) if raw_income is not None else 0.0
    except (ValueError, TypeError):
        income = 0.0

    try:
        prev_expense = float(raw_prev) if raw_prev is not None else 0.0
    except (ValueError, TypeError):
        prev_expense = 0.0

    category = data.get('category', 'Food')
    payment_mode = data.get('payment_mode', 'UPI')
    amount = float(data.get('amount') or 0.0)
    month = int(data.get('month', datetime.now().month))

    # For default account ONLY: provide default prediction numbers if not provided
    if is_default and (income <= 0 or prev_expense <= 0):
        income = 45000.0
        prev_expense = 21000.0
        if amount <= 0:
            amount = 1500.0

    # For any other account: strictly require both income and expenses
    if not is_default and (income <= 0 or prev_expense <= 0):
        return jsonify({
            'predicted_expense': 0.0,
            'has_data': False,
            'confidence_interval': {'lower': 0.0, 'upper': 0.0},
            'expected_savings': 0.0,
            'expected_savings_rate': 0.0,
            'message': 'Please enter both monthly income and expenses to generate prediction for your account.',
            'inputs': {'income': income, 'previous_month_expense': prev_expense}
        })

    result = ml_engine.predict(
        income=income,
        prev_expense=prev_expense,
        category=category,
        payment_mode=payment_mode,
        amount=amount if amount > 0 else 1500.0,
        month=month
    )

    # Only persist non-zero predictions to DB
    if result.get('has_data', True) and result.get('predicted_expense', 0) > 0:
        save_prediction(
            user_id=user_id,
            predicted_expense=result['predicted_expense'],
            income_input=income,
            prev_expense_input=prev_expense,
            mae=result['metrics']['mae'],
            rmse=result['metrics']['rmse'],
            r2_score=result['metrics']['r2_score']
        )

    return jsonify(result)

@app.route('/api/ml/history', methods=['GET'])
def api_ml_history():
    user_id = get_current_user_id()
    history = get_prediction_history(user_id)
    return jsonify({'history': history})

@app.route('/api/ml/retrain', methods=['POST'])
def api_ml_retrain():
    summary = ml_engine.train()
    return jsonify({
        'success': True,
        'message': 'Multiple Linear Regression model retrained successfully with Ordinary Least Squares (OLS).',
        'metrics': summary
    })

# ----------------- Analytics & Reports Endpoints -----------------

@app.route('/api/analytics/summary', methods=['GET'])
def api_analytics_summary():
    user_id = get_current_user_id()
    txs = get_transactions(user_id)

    total_income = sum(t['amount'] for t in txs if t['type'] == 'income')
    total_expense = sum(t['amount'] for t in txs if t['type'] == 'expense')
    net_savings = max(0.0, total_income - total_expense)
    savings_rate = round((net_savings / total_income * 100), 1) if total_income > 0 else 0.0

    # Category breakdown (expenses only)
    cat_breakdown = {}
    for t in txs:
        if t['type'] == 'expense':
            cat = t['category']
            cat_breakdown[cat] = cat_breakdown.get(cat, 0.0) + t['amount']

    # Payment mode breakdown
    pm_breakdown = {}
    for t in txs:
        if t['type'] == 'expense':
            pm = t['payment_mode']
            pm_breakdown[pm] = pm_breakdown.get(pm, 0.0) + t['amount']

    # Monthly Trends (aggregated by YYYY-MM)
    monthly_data = {}
    for t in txs:
        ym = t['date'][:7] if len(t['date']) >= 7 else '2026-10'
        if ym not in monthly_data:
            monthly_data[ym] = {'month': ym, 'income': 0.0, 'expense': 0.0}
        if t['type'] == 'income':
            monthly_data[ym]['income'] += t['amount']
        else:
            monthly_data[ym]['expense'] += t['amount']

    sorted_months = sorted(list(monthly_data.values()), key=lambda x: x['month'])

    return jsonify({
        'total_income': total_income,
        'total_expense': total_expense,
        'net_savings': net_savings,
        'savings_rate': savings_rate,
        'category_breakdown': cat_breakdown,
        'payment_mode_breakdown': pm_breakdown,
        'monthly_trends': sorted_months,
        'recent_transactions': txs[:8]
    })

@app.route('/api/analytics/reports', methods=['GET'])
def api_analytics_reports():
    user_id = get_current_user_id()
    user = get_user_by_id(user_id)
    is_default = (user['email'] == DEMO_EMAIL) if user else False
    txs = get_transactions(user_id)
    current_my = datetime.now().strftime('%Y-%m')
    budget_status = get_budget_status(user_id, current_my)

    # ML prediction for current context based on user's manual data
    income_txs = [t for t in txs if t['type'] == 'income']
    total_income = sum(t['amount'] for t in income_txs)
    user_income = total_income if total_income > 0 else (user['monthly_income'] if user else 0.0)
    prev_expense = budget_status['total_spent']

    if not is_default and (user_income <= 0 or prev_expense <= 0):
        ml_pred = {
            'predicted_expense': 0.0,
            'has_data': False,
            'confidence_interval': {'lower': 0.0, 'upper': 0.0},
            'expected_savings': 0.0,
            'expected_savings_rate': 0.0,
            'message': 'Awaiting owner income and expenses to generate prediction.'
        }
    else:
        income_to_use = user_income if user_income > 0 else (45000.0 if is_default else 0.0)
        exp_to_use = prev_expense if prev_expense > 0 else (21000.0 if is_default else 0.0)
        ml_pred = ml_engine.predict(income=income_to_use, prev_expense=exp_to_use)

    recs = generate_personalized_recommendations(
        user_income=user_income,
        transactions=txs,
        budget_status=budget_status,
        ml_prediction=ml_pred
    )

    return jsonify({
        'user': user,
        'budget_status': budget_status,
        'recommendations': recs,
        'ml_prediction': ml_pred
    })

@app.route('/api/recommendations', methods=['GET'])
def api_recommendations():
    user_id = get_current_user_id()
    user = get_user_by_id(user_id)
    is_default = (user['email'] == DEMO_EMAIL) if user else False
    txs = get_transactions(user_id)
    current_my = datetime.now().strftime('%Y-%m')
    budget_status = get_budget_status(user_id, current_my)

    income_txs = [t for t in txs if t['type'] == 'income']
    total_income = sum(t['amount'] for t in income_txs)
    user_income = total_income if total_income > 0 else (user['monthly_income'] if user else 0.0)
    prev_expense = budget_status['total_spent']

    if not is_default and (user_income <= 0 or prev_expense <= 0):
        ml_pred = {
            'predicted_expense': 0.0,
            'has_data': False,
            'confidence_interval': {'lower': 0.0, 'upper': 0.0},
            'expected_savings': 0.0,
            'expected_savings_rate': 0.0,
            'message': 'Awaiting owner income and expenses.'
        }
    else:
        income_to_use = user_income if user_income > 0 else (45000.0 if is_default else 0.0)
        exp_to_use = prev_expense if prev_expense > 0 else (21000.0 if is_default else 0.0)
        ml_pred = ml_engine.predict(income=income_to_use, prev_expense=exp_to_use)

    recs = generate_personalized_recommendations(
        user_income=user_income,
        transactions=txs,
        budget_status=budget_status,
        ml_prediction=ml_pred
    )
    return jsonify(recs)

@app.route('/api/demo/reset', methods=['POST'])
def api_demo_reset():
    user_id = get_current_user_id()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transactions WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM budgets WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM predictions WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

    seed_demo_data(user_id)
    return jsonify({'success': True, 'message': 'Demo data reset successfully.'})

# Global error handler
@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Endpoint not found.'}), 404
    return render_template('index.html')

if __name__ == '__main__':
    print("="*70)
    print("Intelligent Personal Finance Management & Expense Prediction System")
    print("Starting Flask Full-Stack Server on http://127.0.0.1:5000 ...")
    print("="*70)
    app.run(host='0.0.0.0', port=5000, debug=True)
