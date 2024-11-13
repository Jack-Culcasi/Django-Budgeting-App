from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from .models import UserPreferences, Payday, MonthlyExpenses, Category, Transaction, FixedCosts, Broker, Investment, Bank, Pension, NetWorth

class ModelTestCase(TestCase):

    def setUp(self):
        # Create a user for the tests
        self.user = User.objects.create_user(username='testuser', password='testpassword')

        # Create user preferences for currency
        self.user_preferences = UserPreferences.objects.create(user=self.user, currency_symbol='€')

        # Create a payday for the user
        self.payday_date = timezone.now()
        self.payday = Payday.objects.create(user=self.user, payday_date=self.payday_date, amount=1500, note="November payday")

        # Create monthly expenses for the user
        self.start_date = timezone.now()
        self.end_date = timezone.now() + timezone.timedelta(days=30)
        self.monthly_expenses = MonthlyExpenses.objects.create(
            payday=self.payday,
            start_date=self.start_date,
            end_date=self.end_date,
            utilities=200,
            groceries=300,
            misc=50,
            amount=550,
            note="November monthly expenses"
        )

        # Create categories for the user
        self.category1 = Category.objects.create(
            user=self.user,
            monthly_expenses=self.monthly_expenses,
            name='Utilities',
            amount=200,
            note="Utilities expenses"
        )
        self.category2 = Category.objects.create(
            user=self.user,
            monthly_expenses=self.monthly_expenses,
            name='Groceries',
            amount=300,
            note="Groceries expenses"
        )

        # Create a transaction for the user
        self.transaction1 = Transaction.objects.create(
            user=self.user,
            category=self.category1,
            monthly_expenses=self.monthly_expenses,
            amount=150,
            note="Electricity bill"
        )

        # Create fixed costs for the user
        self.fixed_cost1 = FixedCosts.objects.create(
            user=self.user,
            monthly_expenses=self.monthly_expenses,
            name='Rent',
            amount=1000,
            note="Monthly rent"
        )

        # Create a broker for the user
        self.broker = Broker.objects.create(
            user=self.user,
            name='Investment Broker',
            amount=10000,
            note="Investment account"
        )

        # Create an investment for the user
        self.investment = Investment.objects.create(
            broker=self.broker,
            name='Stocks',
            amount=5000,
            note="Stock investment"
        )

        # Create a bank account for the user
        self.bank = Bank.objects.create(
            user=self.user,
            name='Checking Account',
            amount=3000,
            note="Primary checking account"
        )

        # Create a pension for the user
        self.pension = Pension.objects.create(
            user=self.user,
            name='Pension Fund',
            amount=2000,
            note="Retirement savings"
        )

        # Create a net worth entry for the user
        self.net_worth = NetWorth.objects.create(
            user=self.user,
            payday=self.payday,
            date=timezone.now(),
            total_savings=2500,
            total_investments=5000,
            total_pension=2000,
            net_worth=9500,
            note="Net worth at payday"
        )

    def test_user_preferences(self):
        """Test that user preferences are correctly set up."""
        self.assertEqual(self.user_preferences.currency_symbol, '€')

    def test_payday(self):
        """Test payday for user."""
        self.assertEqual(self.payday.amount, 1500)

    def test_monthly_expenses(self):
        """Test monthly expenses for user."""
        self.assertEqual(self.monthly_expenses.utilities, 200)

    def test_category(self):
        """Test category creation and association with monthly expenses."""
        self.assertEqual(self.category1.name, 'Utilities')
        self.assertEqual(self.category1.monthly_expenses, self.monthly_expenses)

    def test_transaction(self):
        """Test transaction creation and association with category."""
        self.assertEqual(self.transaction1.amount, 150)
        self.assertEqual(self.transaction1.category, self.category1)

    def test_fixed_costs(self):
        """Test fixed costs for user."""
        self.assertEqual(self.fixed_cost1.name, 'Rent')

    def test_broker(self):
        """Test broker creation."""
        self.assertEqual(self.broker.name, 'Investment Broker')

    def test_investment(self):
        """Test investment creation and association with broker."""
        self.assertEqual(self.investment.name, 'Stocks')
        self.assertEqual(self.investment.broker, self.broker)

    def test_bank(self):
        """Test bank account creation."""
        self.assertEqual(self.bank.name, 'Checking Account')

    def test_pension(self):
        """Test pension account creation."""
        self.assertEqual(self.pension.name, 'Pension Fund')

    def test_net_worth(self):
        """Test net worth creation and calculation."""
        self.assertEqual(self.net_worth.net_worth, 9500)

    def test_add_transaction_with_existing_category(self):
        """Test adding a transaction with an existing category"""
        self.client.login(username='testuser', password='testpassword')
        
        # Prepare data for the POST request
        data = {
            'amount': '100.00',
            'monthly_expense_id': self.monthly_expenses.id,
            'categories': [str(self.category.id)],  # ID of the existing category
            'note': 'Grocery shopping',
        }

        # Send POST request
        response = self.client.post(reverse('add_transaction'), data)
        
        # Check that the transaction was created
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, 'utf8'),
            {
                'success': True,
                'amount': '100.00',
                'symbol': '€',  # The currency symbol from user preferences
                'category_name': 'Groceries',
                'transaction_id': str(Transaction.objects.last().id),  # Last created transaction
            }
        )

        # Check if the transaction is actually created in the database
        transaction = Transaction.objects.last()
        self.assertEqual(transaction.amount, 100.00)
        self.assertEqual(transaction.category, self.category)
        self.assertEqual(transaction.note, 'Grocery shopping')

    def test_add_transaction_with_new_category(self):
        """Test adding a transaction with a new category"""
        self.client.login(username='testuser', password='testpassword')
        
        # Prepare data for the POST request (new category)
        data = {
            'amount': '50.00',
            'monthly_expense_id': self.monthly_expenses.id,
            'categories': ['New Category'],  # A new category not in the database
            'note': 'New category for test',
        }

        # Send POST request
        response = self.client.post(reverse('add_transaction'), data)
        
        # Check that the transaction was created
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, 'utf8'),
            {
                'success': True,
                'amount': '50.00',
                'symbol': '€',  # The currency symbol from user preferences
                'category_name': 'New Category',
                'transaction_id': str(Transaction.objects.last().id),  # Last created transaction
            }
        )

        # Check if the transaction is actually created in the database
        transaction = Transaction.objects.last()
        self.assertEqual(transaction.amount, 50.00)
        self.assertEqual(transaction.category.name, 'New Category')
        self.assertEqual(transaction.note, 'New category for test')


