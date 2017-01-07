from flask import url_for

from lib.tests import ViewTestMixin, assert_status_with_message
from snakeeyes.blueprints.user.models import User


class TestDashboard(ViewTestMixin):
    def test_dashboard_page(self):
        self.login()
        response = self.client.get(url_for('admin.dashboard'))

        assert bytes('User'.encode('utf-8')) in response.data


class TestUsers(ViewTestMixin):
    def test_index_page(self):
        """ Index renders successfully. """
        self.login()
        response = self.client.get(url_for('admin.users'))

        assert response.status_code == 200

    def test_edit_page(self):
        """ Edit page renders successfully. """
        self.login()
        response = self.client.get(url_for('admin.users_edit', id=1))

        assert_status_with_message(200, response, 'admin@local.host')

    def test_edit_resource(self):
        """ Edit this resource successfully. """
        params = {
            'role': 'admin',
            'username': 'foo',
            'active': True
        }

        self.login()
        response = self.client.post(url_for('admin.users_edit', id=1),
                                    data=params, follow_redirects=True)

        assert_status_with_message(200, response,
                                   'User has been saved successfully.')

    def test_bulk_delete_nothing(self):
        """ Last admin account should not get deleted. """
        old_count = User.query.count()
        params = {
            'bulk_ids': [1],
            'scope': 'all_selected_items'
        }

        self.login()
        response = self.client.post(url_for('admin.users_bulk_delete'),
                                    data=params, follow_redirects=True)

        assert_status_with_message(200, response,
                                   '0 user(s) were scheduled to be deleted.')

        new_count = User.query.count()
        assert old_count == new_count

    def test_cancel_subscription(self, subscriptions, mock_stripe):
        """ User subscription gets cancelled. """
        user = User.find_by_identity('subscriber@local.host')
        params = {
            'id': user.id
        }

        self.login()
        response = self.client.post(url_for('admin.users_cancel_subscription'),
                                    data=params, follow_redirects=True)

        assert_status_with_message(200, response,
                                   'Subscription has been cancelled for Subby')
        assert user.cancelled_subscription_on is not None


class TestCoupon(ViewTestMixin):
    def test_index_page(self):
        """ Index renders successfully. """
        self.login()
        response = self.client.get(url_for('admin.coupons'))

        assert response.status_code == 200

    def test_new_page(self, coupons):
        """ New page renders successfully. """
        self.login()
        response = self.client.get(url_for('admin.coupons_new'))

        assert response.status_code == 200

    def test_new_resource(self, mock_stripe):
        """ Edit this resource successfully. """
        params = {
            'code': '1337',
            'duration': 'repeating',
            'percent_off': 5,
            'amount_off': None,
            'currency': 'usd',
            'redeem_by': None,
            'max_redemptions': 10,
            'duration_in_months': 5,
        }

        self.login()
        response = self.client.post(url_for('admin.coupons_new'),
                                    data=params, follow_redirects=True)

        assert_status_with_message(200, response,
                                   'Coupon has been created successfully.')

    def test_bulk_delete(self, coupons, mock_stripe):
        """ Resource gets bulk deleted. """
        params = {
            'bulk_ids': [1, 2, 3],
            'scope': 'all_selected_items'
        }

        self.login()
        response = self.client.post(url_for('admin.coupons_bulk_delete'),
                                    data=params, follow_redirects=True)

        assert_status_with_message(200, response,
                                   '{0} coupons(s)'
                                   ' were scheduled to be deleted.'.format(3))


class TestInvoices(ViewTestMixin):
    def test_index_page(self):
        """ Index renders successfully. """
        self.login()
        response = self.client.get(url_for('admin.invoices'))

        assert response.status_code == 200
