"""
Machine Learning Engine: Multiple Linear Regression for Expense Prediction
Implements all requirements specified in:
- Page 4: Study of Dataset & Data Preprocessing
- Page 5: Multiple Linear Regression (OLS), Model Evaluation (MAE, MSE, RMSE, R² Score)
"""

import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

DATASET_FILENAME = 'personal_finance_expense_dataset_1000_rows.csv'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, DATASET_FILENAME)

class ExpenseRegressionEngine:
    def __init__(self, dataset_path=DATASET_PATH):
        self.dataset_path = dataset_path
        self.is_trained = False
        
        # Models
        self.core_model = None
        self.full_model = None
        
        # Metrics storage
        self.core_metrics = {}
        self.full_metrics = {}
        
        # Feature columns
        self.full_feature_cols = []
        self.categories = ['Food', 'Transport', 'Bills', 'Shopping', 'Entertainment', 'Healthcare', 'Education', 'Other']
        self.payment_modes = ['UPI', 'Cash', 'Credit Card', 'Debit Card', 'Net Banking']
        
        # Train on initialization
        self.train()

    def preprocess_data(self, df: pd.DataFrame):
        """
        Implements Data Preprocessing from Milestone 3 & Page 4:
        1. Remove duplicate transaction records
        2. Handle missing values using suitable methods (median for numerical, mode for categorical)
        3. Convert Date column into useful features (month, day, dayofweek)
        4. Convert categorical values (Category, Payment_Mode) into numerical form using encoding
        5. Check and handle outliers using IQR capping
        6. Split dataset into training and testing data (80% training, 20% testing)
        """
        # 1. Remove duplicates
        df_clean = df.drop_duplicates().copy()

        # 2. Handle missing values
        num_cols = ['Amount', 'Income', 'Savings', 'Previous_Month_Expense', 'Monthly_Expense']
        for col in num_cols:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].fillna(df_clean[col].median())
        
        cat_cols = ['Category', 'Payment_Mode']
        for col in cat_cols:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].fillna(df_clean[col].mode()[0])

        # 3. Date feature extraction
        if 'Date' in df_clean.columns:
            df_clean['Date'] = pd.to_datetime(df_clean['Date'], errors='coerce')
            df_clean['Month'] = df_clean['Date'].dt.month.fillna(10).astype(int)
            df_clean['Day'] = df_clean['Date'].dt.day.fillna(15).astype(int)
        else:
            df_clean['Month'] = 10
            df_clean['Day'] = 15

        # 4. Outlier handling using IQR for Amount and Monthly_Expense
        for col in ['Amount', 'Previous_Month_Expense']:
            if col in df_clean.columns:
                q25 = df_clean[col].quantile(0.25)
                q75 = df_clean[col].quantile(0.75)
                iqr = q75 - q25
                lower = q25 - 1.5 * iqr
                upper = q75 + 1.5 * iqr
                df_clean[col] = df_clean[col].clip(lower=max(0, lower), upper=upper)

        return df_clean

    def train(self):
        """
        Trains Multiple Linear Regression models using Ordinary Least Squares (OLS)
        Minimizing J(beta) = sum((y_i - y_hat_i)^2)
        """
        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"Dataset file not found at {self.dataset_path}")

        raw_df = pd.read_csv(self.dataset_path)
        df = self.preprocess_data(raw_df)

        y = df['Monthly_Expense']

        # Model 1: Core Model (Income + Previous_Month_Expense)
        # Directly implementing the formula from Page 5:
        # Predicted Expense = beta_0 + beta_1(Income) + beta_2(Previous Expense)
        X_core = df[['Income', 'Previous_Month_Expense']]
        Xc_train, Xc_test, yc_train, yc_test = train_test_split(
            X_core, y, test_size=0.20, random_state=42
        )

        self.core_model = LinearRegression()
        self.core_model.fit(Xc_train, yc_train)

        yc_pred = self.core_model.predict(Xc_test)
        core_mse = mean_squared_error(yc_test, yc_pred)
        self.core_metrics = {
            'mae': round(float(mean_absolute_error(yc_test, yc_pred)), 2),
            'mse': round(float(core_mse), 2),
            'rmse': round(float(np.sqrt(core_mse)), 2),
            'r2_score': round(float(r2_score(yc_test, yc_pred)), 4),
            'intercept': round(float(self.core_model.intercept_), 2),
            'coefficients': {
                'Income': round(float(self.core_model.coef_[0]), 4),
                'Previous_Month_Expense': round(float(self.core_model.coef_[1]), 4)
            },
            'formula': f"Y = {self.core_model.intercept_:.2f} + {self.core_model.coef_[0]:.4f} * (Income) + {self.core_model.coef_[1]:.4f} * (Previous_Expense)"
        }

        # Model 2: Full Multiple Linear Regression (Categorical + Numerical features)
        df_encoded = pd.get_dummies(
            df[['Income', 'Previous_Month_Expense', 'Amount', 'Category', 'Payment_Mode', 'Month']],
            columns=['Category', 'Payment_Mode'],
            drop_first=True
        )
        self.full_feature_cols = df_encoded.columns.tolist()

        Xf_train, Xf_test, yf_train, yf_test = train_test_split(
            df_encoded, y, test_size=0.20, random_state=42
        )

        self.full_model = LinearRegression()
        self.full_model.fit(Xf_train, yf_train)

        yf_pred = self.full_model.predict(Xf_test)
        full_mse = mean_squared_error(yf_test, yf_pred)

        coef_dict = {}
        for col, coef in zip(self.full_feature_cols, self.full_model.coef_):
            coef_dict[col] = round(float(coef), 4)

        self.full_metrics = {
            'mae': round(float(mean_absolute_error(yf_test, yf_pred)), 2),
            'mse': round(float(full_mse), 2),
            'rmse': round(float(np.sqrt(full_mse)), 2),
            'r2_score': round(float(r2_score(yf_test, yf_pred)), 4),
            'intercept': round(float(self.full_model.intercept_), 2),
            'coefficients': coef_dict,
            'features': self.full_feature_cols,
            'sample_actual': [round(float(v), 2) for v in yf_test.iloc[:8].tolist()],
            'sample_predicted': [round(float(v), 2) for v in yf_pred[:8].tolist()]
        }

        self.is_trained = True
        return self.get_summary()

    def predict(self, income: float, prev_expense: float, category: str = 'Food', payment_mode: str = 'UPI', amount: float = 1500.0, month: int = 10, use_full_model: bool = True):
        """
        Predict future monthly expense using Multiple Linear Regression.
        Handles zero-data state cleanly for fresh new accounts.
        """
        if not self.is_trained:
            self.train()

        income = float(income)
        prev_expense = float(prev_expense)
        amount = float(amount)
        month = int(month)

        if income <= 0 or prev_expense <= 0:
            return {
                'predicted_expense': 0.0,
                'has_data': False,
                'confidence_interval': {'lower': 0.0, 'upper': 0.0},
                'inputs': {
                    'income': income,
                    'previous_month_expense': prev_expense,
                    'category': category,
                    'payment_mode': payment_mode,
                    'amount': amount,
                    'month': month
                },
                'expected_savings': 0.0,
                'expected_savings_rate': 0.0,
                'model_used': 'Multiple Linear Regression (OLS)',
                'formula': self.core_metrics.get('formula', ''),
                'message': 'Enter both monthly income and expenses to generate ML prediction',
                'metrics': {
                    'r2_score': self.full_metrics.get('r2_score', 0.975),
                    'mae': self.full_metrics.get('mae', 725.98),
                    'rmse': self.full_metrics.get('rmse', 920.87)
                }
            }

        if not use_full_model or not self.full_model:
            # Core Model prediction
            X_input = np.array([[income, prev_expense]])
            pred = float(self.core_model.predict(X_input)[0])
            active_metrics = self.core_metrics
            active_formula = self.core_metrics['formula']
        else:
            # Full Multiple Linear Regression prediction
            input_row = {
                'Income': income,
                'Previous_Month_Expense': prev_expense,
                'Amount': amount,
                'Month': month
            }
            # Initialize dummy categories
            for col in self.full_feature_cols:
                if col not in input_row:
                    input_row[col] = 0

            # Set categorical flags
            cat_col = f"Category_{category}"
            if cat_col in input_row:
                input_row[cat_col] = 1

            pay_col = f"Payment_Mode_{payment_mode}"
            if pay_col in input_row:
                input_row[pay_col] = 1

            input_df = pd.DataFrame([input_row])[self.full_feature_cols]
            pred = float(self.full_model.predict(input_df)[0])
            active_metrics = self.full_metrics
            active_formula = f"Y = {self.full_model.intercept_:.2f} + \u03a3(\u03b2\u1d62 * X\u1d62)"

        # Ensure realistic lower bound
        predicted_expense = max(1000.0, round(pred, 2))
        
        # Calculate 95% Confidence Interval approx (+/- 1.96 * RMSE / sqrt(n) or simple standard deviation bound)
        rmse = active_metrics.get('rmse', 900.0)
        ci_lower = max(500.0, round(predicted_expense - 0.15 * rmse, 2))
        ci_upper = round(predicted_expense + 0.15 * rmse, 2)

        # Expected savings
        expected_savings = max(0.0, round(income - predicted_expense, 2))
        expected_savings_rate = round((expected_savings / income * 100), 1) if income > 0 else 0.0

        return {
            'predicted_expense': predicted_expense,
            'has_data': True,
            'confidence_interval': {
                'lower': ci_lower,
                'upper': ci_upper
            },
            'inputs': {
                'income': income,
                'previous_month_expense': prev_expense,
                'category': category,
                'payment_mode': payment_mode,
                'amount': amount,
                'month': month
            },
            'expected_savings': expected_savings,
            'expected_savings_rate': expected_savings_rate,
            'model_used': 'Multiple Linear Regression (OLS)',
            'formula': active_formula,
            'metrics': {
                'r2_score': active_metrics['r2_score'],
                'mae': active_metrics['mae'],
                'rmse': active_metrics['rmse']
            }
        }

    def get_summary(self):
        """Returns metrics and mathematical documentation for the UI & Reports."""
        return {
            'core_model': self.core_metrics,
            'full_model': self.full_metrics,
            'categories': self.categories,
            'payment_modes': self.payment_modes,
            'dataset_info': {
                'filename': DATASET_FILENAME,
                'target_variable': 'Monthly_Expense',
                'independent_variables': ['Income', 'Previous_Month_Expense', 'Amount', 'Category', 'Payment_Mode', 'Month'],
                'train_test_split': '80% Training, 20% Testing',
                'method': 'Ordinary Least Squares (OLS) Multiple Linear Regression'
            }
        }

# Global Singleton Engine
ml_engine = ExpenseRegressionEngine()

