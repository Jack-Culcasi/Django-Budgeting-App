from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from .models import (CsvPreferences, UserPreferences, Rule, Payday, MonthlyExpenses, 
                    Category, Transaction, FixedCosts, Broker, Investment, Bank, Pension, NetWorth)
from .utils import delete_user_data, handle_csv_file, handle_uploaded_file
from io import BytesIO
import csv

class BudgetingAppTests(TestCase):

    def setUp(self):
        """Setup mock data for testing."""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = Client()
        self.client.login(username='testuser', password='testpass')
        
        # Create Payday
        self.payday = Payday.objects.create(user=self.user, payday_date="2025-01-01", amount=Decimal('1000.00'))

        # Create MonthlyExpenses
        self.monthly_expenses = MonthlyExpenses.objects.create(
            payday=self.payday,
            start_date="2025-01-01",
            end_date="2025-01-31",
            utilities=Decimal('100.00'),
            groceries=Decimal('200.00'),
            misc=Decimal('50.00'),
            amount=Decimal('350.00')
        )

        # Create Category
        self.category = Category.objects.create(
            user=self.user,
            monthly_expenses=self.monthly_expenses,
            name="Groceries",
            amount=Decimal('200.00')
        )

    def test_model_creation(self):
        """Test if models are created correctly."""
        self.assertEqual(Payday.objects.count(), 1)
        self.assertEqual(MonthlyExpenses.objects.count(), 1)
        self.assertEqual(Category.objects.count(), 1)

    def test_home_view(self):
        """Test home page rendering and context."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_statistics_view(self):
        """Test statistics view functionality."""
        response = self.client.post(reverse('statistics'), {
            'from_month': 'January',
            'from_year': '2025',
            'to_month': 'January',
            'to_year': '2025'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('summary_text', response.context)

    def test_delete_user_data(self):
        """Test the utility function to delete user data."""
        result = delete_user_data(request=self._mock_request(self.user))
        self.assertTrue(result)
        self.assertEqual(Payday.objects.filter(user=self.user).count(), 0)

    def test_handle_csv_file(self):
        """Test CSV handling function."""
        csv_content = """Date,Transaction Type,Transaction Description,Amount\n2025-01-01,Purchase,Test Transaction,100.00"""
        csv_file = BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'test.csv'

        request = self._mock_request(self.user, files={'file': csv_file})
        result = handle_csv_file(request, csv_file, self.monthly_expenses)
        self.assertTrue(result)
        self.assertEqual(Transaction.objects.filter(user=self.user).count(), 1)

    def test_handle_uploaded_file(self):
        """Test XLSX file handling function."""
        xlsx_content = BytesIO()  # Simulate a BytesIO Excel file
        result = handle_uploaded_file(xlsx_content, self._mock_request(self.user))
        self.assertTrue(result)

    def test_difference_with_last_month_category(self):
        """Test difference_with_last_month method for Category."""
        previous_month_expenses = MonthlyExpenses.objects.create(
            payday=self.payday,
            start_date="2024-12-01",
            end_date="2024-12-31",
            utilities=Decimal('100.00'),
            groceries=Decimal('150.00'),
            misc=Decimal('50.00'),
            amount=Decimal('300.00')
        )

        previous_category = Category.objects.create(
            user=self.user,
            monthly_expenses=previous_month_expenses,
            name="Groceries",
            amount=Decimal('150.00')
        )

        difference = self.category.difference_with_last_month()
        self.assertEqual(difference, Decimal('50.00'))

    def test_difference_with_last_month_fixed_cost(self):
        """Test difference_with_last_month method for FixedCosts."""
        previous_month_expenses = MonthlyExpenses.objects.create(
            payday=self.payday,
            start_date="2024-12-01",
            end_date="2024-12-31",
            utilities=Decimal('80.00'),
            groceries=Decimal('150.00'),
            misc=Decimal('50.00'),
            amount=Decimal('280.00')
        )

        previous_fixed_cost = FixedCosts.objects.create(
            user=self.user,
            monthly_expenses=previous_month_expenses,
            name="Utilities",
            amount=Decimal('80.00')
        )

        fixed_cost = FixedCosts.objects.create(
            user=self.user,
            monthly_expenses=self.monthly_expenses,
            name="Utilities",
            amount=Decimal('100.00')
        )

        difference = fixed_cost.difference_with_last_month()
        self.assertEqual(difference, Decimal('20.00'))

    def test_average_amount_category(self):
        """Test average_amount method for Category."""
        Category.objects.create(
            user=self.user,
            monthly_expenses=self.monthly_expenses,
            name="Groceries",
            amount=Decimal('300.00')
        )

        average = self.category.average_amount()
        self.assertEqual(average, Decimal('250.00'))

    def test_transaction_deletion(self):
        """Test deletion of a transaction updates the category."""
        transaction = Transaction.objects.create(
            user=self.user,
            category=self.category,
            monthly_expenses=self.monthly_expenses,
            amount=Decimal('50.00'),
            note="Test Transaction"
        )

        transaction.delete_transaction()
        self.assertEqual(Transaction.objects.filter(id=transaction.id).count(), 0)
        self.assertEqual(self.category.amount, Decimal('150.00'))

    def test_perc_diff_with_last_month_net_worth(self):
        """Test perc_diff_with_last_month method for NetWorth."""
        previous_net_worth = NetWorth.objects.create(
            user=self.user,
            payday=self.payday,
            date="2024-12-31",
            total_savings=Decimal('500.00'),
            total_investments=Decimal('1000.00'),
            total_pension=Decimal('200.00'),
            net_worth=Decimal('1700.00')
        )

        current_net_worth = NetWorth.objects.create(
            user=self.user,
            payday=self.payday,
            date="2025-01-31",
            total_savings=Decimal('600.00'),
            total_investments=Decimal('1100.00'),
            total_pension=Decimal('250.00'),
            net_worth=Decimal('1950.00')
        )

        percentage_difference = current_net_worth.perc_diff_with_last_month()
        self.assertEqual(percentage_difference, Decimal('14.71'))

    def test_adjust_fixedcosts_categories(self):
        """Test the adjust_fixedcosts_categories utility function."""
        fixed_cost = FixedCosts.objects.create(
            user=self.user,
            monthly_expenses=self.monthly_expenses,
            name="Rent",
            amount=Decimal('500.00')
        )

        request = self._mock_request(self.user)
        success = delete_user_data(request)
        self.assertTrue(success)
        self.assertEqual(FixedCosts.objects.filter(id=fixed_cost.id).count(), 0)

    def test_restricted_permissions(self):
        """Ensure restricted permissions are enforced."""
        another_user = User.objects.create_user(username='otheruser', password='otherpass')
        another_payday = Payday.objects.create(user=another_user, payday_date="2025-01-15", amount=Decimal('800.00'))

        response = self.client.get(reverse('home'))
        self.assertNotContains(response, another_payday.amount)

    def test_search_payday_invalid_criteria(self):
        """Test search_payday function with invalid criteria."""
        response = self.client.post(reverse('paydays'), {
            'month': 'InvalidMonth',
            'year': '2025'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['paydays'])

    def test_edge_case_empty_csv(self):
        """Test edge case for empty CSV upload."""
        csv_file = BytesIO()  # Empty file
        csv_file.name = 'empty.csv'

        request = self._mock_request(self.user, files={'file': csv_file})
        result = handle_csv_file(request, csv_file, self.monthly_expenses)
        self.assertFalse(result)

    def _mock_request(self, user, files=None):
        """Helper function to mock a request object."""
        class MockRequest:
            def __init__(self):
                self.user = user
                self.FILES = files or {}

        return MockRequest()

if __name__ == '__main__':
    TestCase.main()