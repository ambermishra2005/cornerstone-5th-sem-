# Implementation of an Intelligent Personal Finance Management and Expense Prediction System

A complete full-stack Python application implementing an intelligent personal finance tracking, budget management, visual analytics, personalized recommendations, and machine learning expense prediction system using **Multiple Linear Regression (Ordinary Least Squares - OLS)**.

---

## 📑 Project Overview & Milestones

This application is built in strict adherence to the project specification and milestones:

* **Milestone 1 – Identification & Requirement Analysis**: Identifies core challenges in tracking personal expenses, spending leakages, and forecasting future cash outflows.
* **Milestone 2 – System Design & Planning**: Modular architecture comprising User Management, Income & Expense Management, Auto-Categorization, Budget Management, Data Analysis, Regression Engine, and Financial Reporting.
* **Milestone 3 – Implementation & Development**: Full-stack Python application with SQLite database, RESTful API endpoints, Machine Learning pipeline, and a modern responsive dashboard.
* **Milestone 4 – Testing & Validation**: Automated test suite (`test_app.py`) evaluating unit and integration endpoints, with regression validation using **MAE, MSE, RMSE, and $R^2$ Score**.
* **Milestone 5 – Documentation & Deployment**: Comprehensive technical documentation, architecture flowcharts, mathematical explanations, and deployment instructions.

---

## 🔄 System Architecture & Flowchart

The system implements the complete workflow from the project specification:

```
                                 [ Start ]
                                     │
                        [ Open Application / Website ]
                                     │
                           [ Have an Account? ]
                             /               \
                       (No) /                 \ (Yes)
                           v                   v
                [ User Registration ]     [ User Login ]
                • Name                    • Email / Username
                • Email                   • Password
                • Password                     │
                           \                  /
                            v                v
                       [ Dashboard (All Features) ]
                         │       │       │       │       │
       ┌─────────────────┼───────┼───────┼───────┼───────┴─────────────────┐
       ▼                 ▼       ▼       ▼       ▼                         ▼
[ Income & Expenses ]  [ Categorization ]  [ Budgeting ]   [ Data Analysis ]  [ ML Prediction ]  [ Recommendations ]
• Add Income/Expense   • Auto Keyword      • Set Budget    • Cash Flow Trends • Preprocess Data  • Save More
• Edit Record          • Manual Select     • Track Spent   • Category Donut   • Train Regression • Cut Discretionary
• Delete Record        • Store in DB       • Balance Check • Daily Trajectory • Predict Future   • 50/30/20 Principle
• CSV Import / Export                      • ML Recommend  • Payment Modes    • Model Metrics    • Investment Tips
       └─────────────────┬───────┬───────┬───────┬─────────────────────────┘
                         │       │       │       │
                         v       v       v       v
                   [ Financial Reports & Summary ]
                   • Income vs Expenses Comparison
                   • Category-wise Spending Breakdown
                   • Monthly / Yearly Variance Table
                   • Financial Health Score (0-100)
                                 │
                            [ Logout ]
                                 │
                              [ End ]
```

---

## 📊 Study of Dataset & Data Preprocessing

The machine learning model is trained on historical personal finance data (`personal_finance_expense_dataset_1000_rows.csv`).

### Dataset Attributes

| Attribute | Description | Example |
| :--- | :--- | :--- |
| `Date` | Date on which the transaction occurred | `2026-08-15` |
| `Category` | Type of expenditure (Food, Transport, Bills, Shopping, Entertainment, etc.) | `Food` |
| `Amount` | Money spent in the transaction (₹) | `450` |
| `Payment_Mode` | Method used for payment (UPI, Credit Card, Debit Card, Net Banking, Cash) | `UPI` |
| `Income` | Income received during the period (₹) | `30000` |
| `Savings` | Amount saved during the period (₹) | `7000` |
| `Previous_Month_Expense`| Total expenditure incurred in previous month (₹) | `19664` |
| `Monthly_Expense` | **Target Variable**: Total continuous expense for the month (₹) | `23000` |

### Preprocessing Pipeline

1. **Deduplication**: Removes duplicate transaction records.
2. **Missing Value Imputation**: Median strategy for numerical columns, Mode strategy for categorical columns.
3. **Feature Engineering**: Extracts temporal features (`Month`, `Day`, `DayOfWeek`) from transaction dates.
4. **Categorical Encoding**: One-Hot Encoding for `Category` and `Payment_Mode` variables.
5. **Outlier Detection & Capping**: Interquartile Range (IQR) capping ($[Q_1 - 1.5 \times \text{IQR},\, Q_3 + 1.5 \times \text{IQR}]$) to handle extreme spending deviations.
6. **Train/Test Split**: 80% Training dataset, 20% Testing dataset with reproducible random seed (`random_state=42`).

---

## 📐 Machine Learning Model: Multiple Linear Regression

### Mathematical Concept

Multiple Linear Regression models the linear relationship between a dependent target variable ($Y$) and two or more independent variables ($X_1, X_2, \dots, X_n$):

$$Y = \beta_0 + \beta_1 X_1 + \beta_2 X_2 + \dots + \beta_n X_n + \varepsilon$$

Where:
* $Y$ is the predicted continuous monthly expense.
* $X_1, X_2, \dots, X_n$ are the input financial features (Income, Previous Month Expense, Category, Payment Mode, Amount).
* $\beta_0$ is the intercept term.
* $\beta_1, \dots, \beta_n$ are the estimated regression coefficients.
* $\varepsilon$ is the residual error term.

### Ordinary Least Squares (OLS) Estimation

The model parameters are estimated by minimizing the **Sum of Squared Errors (SSE)**:

$$J(\beta) = \sum_{i=1}^{m} \left( y_i - \hat{y}_i \right)^2$$

### Evaluation Metrics (Milestone 4 Results)

| Metric | Meaning & Formula | System Benchmark Value |
| :--- | :--- | :--- |
| **$R^2$ Score** | Proportion of variance explained by model: $1 - \frac{\sum(y_i - \hat{y}_i)^2}{\sum(y_i - \bar{y})^2}$ | **0.9750 (97.5% accuracy)** |
| **MAE** | Mean Absolute Error: $\frac{1}{m}\sum \|y_i - \hat{y}_i\|$ | **₹725.98** |
| **MSE** | Mean Squared Error: $\frac{1}{m}\sum (y_i - \hat{y}_i)^2$ | **847,994.97** |
| **RMSE** | Root Mean Squared Error: $\sqrt{\text{MSE}}$ | **₹920.87** |

---

## 🚀 Installation & Backend Setup

### 1. Requirements
* Python 3.10+ (tested on Python 3.14)
* Installed packages: `Flask`, `scikit-learn`, `pandas`, `numpy`, `scipy`

### 2. Quickstart (One Command)
Run the application server:
```powershell
python run.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

### 3. Demo Credentials
The application pre-populates a realistic demo profile with 30 transactions, category budgets, and trained ML models:
* **One-Click**: Click the **One-Click Demo Account** button in the header.
* **Or Manual Login**:
  * **Email**: `demo@finance.ai`
  * **Password**: `demo123`

---

## 🧪 Automated Testing & Validation

To execute the Milestone 4 automated test suite:
```powershell
python test_app.py
```
This runs 5 comprehensive test suites covering:
1. `test_ml_model_metrics`: Validates $R^2 > 0.90$, MAE, RMSE, and confidence interval bounds.
2. `test_database_crud`: Verifies user auth, transaction CRUD, and budget tracking.
3. `test_auto_categorization`: Tests keyword-matching across all financial categories.
4. `test_budget_management`: Validates budget calculation and over-budget triggers.
5. `test_flask_api_endpoints`: Verifies all REST API responses and JSON payloads.

---

## 🔌 REST API Documentation

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Backend status & ML training confirmation |
| `POST` | `/api/auth/register` | Register new user account |
| `POST` | `/api/auth/login` | Authenticate user |
| `POST` | `/api/auth/demo-login` | Instant demo login |
| `GET` | `/api/transactions` | Filter & retrieve transaction records |
| `POST` | `/api/transactions` | Add new record (with auto/manual category) |
| `PUT` | `/api/transactions/<id>` | Update existing transaction record |
| `DELETE`| `/api/transactions/<id>` | Delete transaction record |
| `POST` | `/api/transactions/auto-categorize`| Return auto-detected category for description |
| `POST` | `/api/transactions/import-csv` | Bulk import transactions from CSV file |
| `GET` | `/api/transactions/export-csv` | Download transactions as CSV |
| `GET` | `/api/budgets/status` | Current spending vs category budget limits |
| `POST` | `/api/budgets` | Set or update monthly category budget |
| `POST` | `/api/budgets/auto-recommend`| Auto-adjust budgets using ML expense forecast |
| `GET` | `/api/ml/metrics` | Return MAE, MSE, RMSE, $R^2$, and $\beta$ coefficients |
| `POST` | `/api/ml/predict` | Predict future monthly expenditure |
| `POST` | `/api/ml/retrain` | Retrain regression model on dataset |
| `GET` | `/api/analytics/summary` | Cash flow trends & category breakdown |
| `GET` | `/api/recommendations` | Personalized 4-pillar financial recommendations |

---

## 📁 Project Structure

```
cornerstone_project-main/
├── backend/
│   ├── app.py              # Flask application & REST API routes
│   ├── database.py         # SQLite3 database engine & CRUD operations
│   ├── ml_engine.py        # Multiple Linear Regression (OLS) training & predictions
│   ├── categorizer.py      # Keyword auto-categorization engine
│   └── recommendations.py  # 4-pillar financial advisory engine
├── templates/
│   └── index.html          # Responsive single-page dashboard
├── static/
│   ├── css/
│   │   └── styles.css      # Dark glassmorphic theme styling
│   └── js/
│       └── app.js          # Client-side state, API calls & Chart.js controllers
├── personal_finance_expense_dataset_1000_rows.csv # Training dataset
├── sample_expenses.csv     # Sample CSV for bulk import testing
├── run.py                  # Server launcher script
├── test_app.py             # Milestone 4 automated validation suite
└── README.md               # Project documentation & milestone guide
```
