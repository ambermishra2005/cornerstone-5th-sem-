"""
Expense Auto-Categorization Engine
Provides intelligent keyword-matching and rule-based classification
with fallback to manual categorization.
"""

import re

CATEGORY_KEYWORDS = {
    'Food': [
        'food', 'grocery', 'groceries', 'supermarket', 'dining', 'restaurant',
        'cafe', 'coffee', 'starbucks', 'mcdonalds', 'kfc', 'burger', 'pizza',
        'subway', 'swiggy', 'zomato', 'ubereats', 'doordash', 'bistro', 'bakery',
        'lunch', 'dinner', 'breakfast', 'snack', 'vegetable', 'fruit', 'meat'
    ],
    'Transport': [
        'transport', 'uber', 'lyft', 'ola', 'taxi', 'cab', 'metro', 'subway',
        'train', 'railway', 'bus', 'flight', 'airline', 'fuel', 'petrol', 'diesel',
        'gas', 'gasoline', 'shell', 'parking', 'toll', 'fastag', 'auto', 'commute'
    ],
    'Bills': [
        'bill', 'bills', 'electricity', 'water', 'internet', 'wifi', 'broadband',
        'phone', 'mobile', 'recharge', 'airtel', 'jio', 'verizon', 'rent', 'society',
        'maintenance', 'gas bill', 'cylinder', 'lpg', 'property tax', 'utility'
    ],
    'Entertainment': [
        'entertainment', 'movie', 'cinema', 'theatre', 'theater', 'netflix',
        'spotify', 'disney', 'hulu', 'prime video', 'youtube', 'steam', 'game',
        'gaming', 'playstation', 'xbox', 'concert', 'event', 'party', 'club', 'pub'
    ],
    'Shopping': [
        'shopping', 'amazon', 'flipkart', 'walmart', 'target', 'ebay', 'myntra',
        'clothes', 'clothing', 'apparel', 'shoes', 'footwear', 'electronics',
        'mall', 'store', 'gadget', 'laptop', 'phone', 'furniture', 'home decor'
    ],
    'Healthcare': [
        'healthcare', 'doctor', 'hospital', 'clinic', 'dentist', 'dental',
        'medical', 'medicine', 'pharmacy', 'chemist', 'apollo', 'lab', 'blood test',
        'surgery', 'prescription', 'health', 'fitness', 'gym', 'vitamins'
    ],
    'Education': [
        'education', 'college', 'school', 'university', 'tuition', 'course',
        'coursera', 'udemy', 'edx', 'book', 'books', 'stationery', 'exam',
        'certification', 'training', 'fee', 'fees'
    ],
    'Salary': [
        'salary', 'paycheck', 'payroll', 'wages', 'stipend', 'bonus', 'compensation'
    ],
    'Freelance': [
        'freelance', 'client', 'consulting', 'contract', 'upwork', 'fiverr',
        'project fee', 'retainer', 'gig'
    ],
    'Investment': [
        'dividend', 'interest', 'stock', 'mutual fund', 'sip', 'shares',
        'crypto', 'trading', 'profit', 'capital gain'
    ]
}

def auto_categorize(text: str, default_category: str = 'Other') -> str:
    """
    Classifies a transaction description into a standard financial category.
    Returns matched category or default_category.
    """
    if not text or not isinstance(text, str):
        return default_category

    cleaned = text.lower().strip()
    words = re.findall(r'\b\w+\b', cleaned)

    # 1. Exact or partial word match
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in cleaned or kw in words:
                return category

    return default_category

def get_all_categories():
    """Return standard expense categories."""
    return [
        'Food',
        'Transport',
        'Bills',
        'Shopping',
        'Entertainment',
        'Healthcare',
        'Education',
        'Other'
    ]

def get_income_categories():
    """Return standard income categories."""
    return [
        'Salary',
        'Freelance',
        'Investment',
        'Business',
        'Gift',
        'Other'
    ]

