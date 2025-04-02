# Django Budgeting App

A detailed and user-friendly budgeting application built with Django, designed to help users track their finances efficiently. This README provides an overview of the app's functionalities, structured by the main pages available in the web app.

The website is avaliable at [this link](https://brokenomics.eu.pythonanywhere.com/login/?next=/home/), here there's a [demo video](assets/brokenomics_demo.mp4).

---

## **Features**
- **User Authentication**: Secure login/logout system.
- **Payday Tracking**: Manage your monthly income sources.
- **Expense Management**: Categorize and track daily transactions.
- **Fixed Costs**: Keep track of recurring monthly costs.
- **Investment Tracking**: Monitor savings and investments.
- **Net Worth Calculation**: Analyze financial growth over time.
- **Statistics & Insights**: Visualise financial trends with detailed graphs.
- **CSV & Excel Import**: Upload and process financial data efficiently.

---

## **Pages & Functionalities**

### **Overview** (`/`)
- Provides an overview of net worth diversification.
- Displays trends charts.
- Quick access to net worth history.

### **Payday Page** (`/payday`)
- Users can log their income and monthly expenses.
- The process takes the user through different inputs:
  - Income
  - Variable expenses (either via CSV or manual input)
  - Fixed costs
  - Savings
  - Investments
  - Pensions
 
### **Monthly Expenses Page** (`/paydays`)
- Users can access paydays history.
- When selected, each payday shows:
  - Salary, expenses, monthly net, utilities, groceries, misc.
  - Category and fixed costs breakdown.
  - Monthly transactions with category and description.

### **Categories Page** (`/categories`)
- Users can create and manage spending categories.
- Each category tracks total spending for the month.
- Displays differences compared to previous months.

### **Fixed Costs Page** (`/fixed-costs`)
- Logs recurring expenses (e.g., rent, subscriptions, utilities).
- Helps estimate monthly budget planning.

### **Investments Page** (`/investments`)
- Tracks investments in stocks, real estate, and other assets.
- Calculates percentage changes over time.
- Users can manually add or remove investments.

### **Statistics Page** (`/statistics`)
- Users can choose a timeframe to get the following data:
  - Total income
  - Total expenses
  - Avg monthly spending
  - Savings rate
  - Highest spending month
  - Lowest spending month
  - Category breakdown
  - Fun fact
  - Net worth trend

---

## **Installation**

### **Prerequisites**
- Python 3.10+
- Django
- PostgreSQL or SQLite (default)

### **Steps**
1. Clone the repository:
   ```bash
   git clone https://github.com/Jack-Culcasi/Django-Budgeting-App.git
   cd Django-Budgeting-App
   ```

2. Create a virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows use `env\Scripts\activate`
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Apply migrations:
   ```bash
   python manage.py migrate
   ```

5. Create a superuser (admin):
   ```bash
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```bash
   python manage.py runserver
   ```

Access the app at `http://127.0.0.1:8000/`.

---

## **Running Tests**
Run the test suite to verify everything is working correctly:
```bash
python manage.py test
```

---

## **Contributing**
1. Fork the repository.
2. Create a new branch (`git checkout -b feature-name`).
3. Commit your changes (`git commit -m "Add new feature"`).
4. Push to the branch (`git push origin feature-name`).
5. Open a Pull Request.

---

## **License**
This project is open-source and available under the [MIT License](LICENSE).

