"""
Personalized Financial Recommendations Engine
Generates tailored, actionable advice as defined in the project flowchart:
1. Save More
2. Reduce Unnecessary Spending
3. Budget Suggestions (50/30/20 Rule & ML Budgeting)
4. Investment Tips
"""

from typing import List, Dict, Any

def generate_personalized_recommendations(user_income: float, transactions: List[Dict[str, Any]], budget_status: Dict[str, Any], ml_prediction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes historical spending behavior and produces actionable recommendations.
    Handles fresh zero-data accounts gracefully.
    """
    income_txs = [t for t in transactions if t['type'] == 'income']
    total_income = sum(t['amount'] for t in income_txs)
    if total_income == 0 and user_income > 0:
        total_income = user_income

    expenses = [t for t in transactions if t['type'] == 'expense']
    total_expense = sum(t['amount'] for t in expenses)
    net_savings = max(0.0, total_income - total_expense)
    savings_rate = round((net_savings / total_income * 100), 1) if total_income > 0 else 0.0

    # Fresh new account with zero data
    if len(transactions) == 0 and total_income == 0:
        return {
            'financial_health_score': 100,
            'is_new_account': True,
            'save_more': {
                'status': 'New Account',
                'badge_color': 'indigo',
                'headline': 'Welcome! Your Account Starts at Zero',
                'detail': 'No transaction records found. Add your income and expenses manually using the "+ Add Record" button to start receiving ML predictions and budget tracking.',
                'actionable_step': 'Add your monthly income (e.g., Salary) to activate your financial dashboard.'
            },
            'unnecessary_spending': {
                'discretionary_total': 0.0,
                'discretionary_percentage': 0.0,
                'top_spenders': [],
                'headline': 'Zero Discretionary Expenses Logged',
                'suggestions': [
                    'Track each daily expense manually to let the system identify unnecessary spending patterns.',
                    'Use auto-categorization by typing merchants like "Uber", "Starbucks", or "Amazon".'
                ]
            },
            'budget_suggestions': {
                'rule': '50/30/20 Principle',
                'needs': {'actual': 0.0, 'target': 0.0, 'percent': 0.0, 'status': 'Pending Data'},
                'wants': {'actual': 0.0, 'target': 0.0, 'percent': 0.0, 'status': 'Pending Data'},
                'savings': {'actual': 0.0, 'target': 0.0, 'percent': 0.0, 'status': 'Pending Data'},
                'ml_budget_recommendation': 'Enter your income to see personalized 50/30/20 allocations and ML predictions.'
            },
            'investment_tips': {
                'emergency_fund_target': 0.0,
                'headline': 'Start Your Wealth Building Journey',
                'tips': [
                    {
                        'title': 'Track Every Rupee',
                        'description': 'Recording your initial manual transactions builds the baseline dataset for future expense predictions.'
                    },
                    {
                        'title': 'Build a Safety Net',
                        'description': 'Aim to save 20% of your incoming paycheck into an emergency fund before taking investment risks.'
                    }
                ]
            },
            'summary_metrics': {
                'total_income': 0.0,
                'total_expense': 0.0,
                'net_savings': 0.0,
                'savings_rate': 0.0
            }
        }

    # Categorize spending by category
    cat_spending = {}
    for t in expenses:
        cat = t.get('category', 'Other')
        cat_spending[cat] = cat_spending.get(cat, 0.0) + t['amount']

    # 1. Save More Strategy
    save_more = {}
    if savings_rate >= 30:
        save_more = {
            'status': 'Excellent',
            'badge_color': 'emerald',
            'headline': f'Outstanding Savings Rate of {savings_rate}%!',
            'detail': f'You saved \u20b9{net_savings:,.0f} this month, exceeding the 20% baseline financial goal. Consider moving surplus funds into long-term compounding instruments.',
            'actionable_step': 'Automate transfer of 15% of your surplus into an index fund on your paycheck date.'
        }
    elif savings_rate >= 20:
        save_more = {
            'status': 'Healthy',
            'badge_color': 'blue',
            'headline': f'Solid Savings Rate of {savings_rate}%',
            'detail': f'You are saving \u20b9{net_savings:,.0f} per month. Pushing this to 25% would add an extra \u20b9{(total_income * 0.05):,.0f} every month to your emergency reserves.',
            'actionable_step': 'Identify 1 non-essential subscription to cancel this week.'
        }
    elif savings_rate > 5:
        save_more = {
            'status': 'Moderate Warning',
            'badge_color': 'amber',
            'headline': f'Low Savings Rate: {savings_rate}%',
            'detail': f'Your monthly savings of \u20b9{net_savings:,.0f} is below the 20% benchmark. High fixed or impulse costs leave limited buffer for emergencies.',
            'actionable_step': 'Aim to save 5% more next month by reducing discretionary dining and shopping.'
        }
    else:
        save_more = {
            'status': 'Critical Alert',
            'badge_color': 'rose',
            'headline': 'Expenses Approaching or Exceeding Income!',
            'detail': f'You spent \u20b9{total_expense:,.0f} against an income of \u20b9{total_income:,.0f}. Net savings is nearly zero.',
            'actionable_step': 'Implement an immediate temporary spending freeze on non-essential purchases.'
        }

    # 2. Reduce Unnecessary Spending (Discretionary Audit)
    discretionary_cats = ['Entertainment', 'Shopping', 'Other']
    discretionary_spend = sum(cat_spending.get(c, 0.0) for c in discretionary_cats)
    discretionary_ratio = round((discretionary_spend / total_expense * 100), 1) if total_expense > 0 else 0.0

    top_discretionary = sorted(
        [(c, cat_spending.get(c, 0.0)) for c in discretionary_cats if cat_spending.get(c, 0.0) > 0],
        key=lambda x: x[1],
        reverse=True
    )

    unnecessary_spending = {
        'discretionary_total': discretionary_spend,
        'discretionary_percentage': discretionary_ratio,
        'top_spenders': [{'category': c, 'amount': amt} for c, amt in top_discretionary],
        'headline': f'{discretionary_ratio}% of your expenses are in discretionary categories',
        'suggestions': [
            f'Cutting 20% of your {top_discretionary[0][0]} spending would instantly save \u20b9{(top_discretionary[0][1] * 0.2):,.0f} each month.' if top_discretionary else 'Maintain your low discretionary spending.',
            'Switch to weekly dining meal plans to limit impulse food orders.',
            'Institute a 48-hour rule for any online shopping item over \u20b91,500.'
        ]
    }

    # 3. Budget Suggestions (50/30/20 Framework & ML Predictions)
    needs_cats = ['Bills', 'Food', 'Healthcare', 'Transport', 'Education']
    needs_spend = sum(cat_spending.get(c, 0.0) for c in needs_cats)
    wants_spend = discretionary_spend

    target_needs = round(total_income * 0.50, 0)
    target_wants = round(total_income * 0.30, 0)
    target_savings = round(total_income * 0.20, 0)

    predicted_next = ml_prediction.get('predicted_expense', total_expense)

    budget_suggestions = {
        'rule': '50/30/20 Principle',
        'needs': {
            'actual': needs_spend,
            'target': target_needs,
            'percent': round((needs_spend / total_income * 100), 1) if total_income > 0 else 0.0,
            'status': 'Within Limit' if needs_spend <= target_needs else 'Exceeds 50% Guideline'
        },
        'wants': {
            'actual': wants_spend,
            'target': target_wants,
            'percent': round((wants_spend / total_income * 100), 1) if total_income > 0 else 0.0,
            'status': 'Within Limit' if wants_spend <= target_wants else 'Exceeds 30% Guideline'
        },
        'savings': {
            'actual': net_savings,
            'target': target_savings,
            'percent': savings_rate,
            'status': 'Target Met' if net_savings >= target_savings else 'Short of 20% Target'
        },
        'ml_budget_recommendation': f'ML Engine forecasts your upcoming monthly expenses at \u20b9{predicted_next:,.0f}. Setting a monthly budget limit of \u20b9{(predicted_next * 1.05):,.0f} provides a healthy 5% safety margin.'
    }

    # 4. Investment Tips
    emergency_target = total_expense * 4.0 # 4 months emergency fund
    investment_tips = {
        'emergency_fund_target': emergency_target,
        'headline': 'Personalized Wealth Building Road Map',
        'tips': [
            {
                'title': 'Build a 3-6 Month Emergency Fund',
                'description': f'Maintain at least \u20b9{emergency_target:,.0f} in high-yield liquid savings or sweep-in fixed deposits before taking on market risk.'
            },
            {
                'title': 'Automate Index Fund SIPs',
                'description': f'With your monthly surplus of \u20b9{net_savings:,.0f}, setting up an auto-SIP of \u20b9{(net_savings * 0.6):,.0f} in a broad market index fund (e.g. Nifty 50 or S&P 500) can compound significantly.'
            },
            {
                'title': 'Debt & Interest Optimization',
                'description': 'Always pay off high-interest credit card balances in full each billing cycle to prevent 36-42% APR interest leakage.'
            }
        ]
    }

    # 5. Financial Health Score (0 to 100)
    score = 0
    # Savings rate contributes up to 40 points
    score += min(40, int(savings_rate * 1.33))
    # Needs within 50% gives 25 points
    if needs_spend <= target_needs:
        score += 25
    else:
        score += max(5, int(25 - (needs_spend - target_needs) / total_income * 50))
    # Wants within 30% gives 20 points
    if wants_spend <= target_wants:
        score += 20
    else:
        score += max(5, int(20 - (wants_spend - target_wants) / total_income * 50))
    # Budget adherence gives up to 15 points
    if budget_status.get('total_spent', 0) <= budget_status.get('total_budget', 999999):
        score += 15
    else:
        score += 5

    health_score = max(10, min(100, score))

    return {
        'financial_health_score': health_score,
        'save_more': save_more,
        'unnecessary_spending': unnecessary_spending,
        'budget_suggestions': budget_suggestions,
        'investment_tips': investment_tips,
        'summary_metrics': {
            'total_income': total_income,
            'total_expense': total_expense,
            'net_savings': net_savings,
            'savings_rate': savings_rate
        }
    }

