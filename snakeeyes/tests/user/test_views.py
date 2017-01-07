from flask import url_for

from lib.tests import assert_status_with_message, ViewTestMixin
from snakeeyes.blueprints.user.models import User


class TestLogin(ViewTestMixin):
    def test_login_page(self):
        """ Login page renders successfully. """
        response = self.client.get(url_for('user.login'))
        assert response.status_code == 200

    def test_login(self):
        """ Login successfully. """
        response = self.login()
        assert response.status_code == 200

    def test_login_activity(self, users):
        """ Login successfully and update the activity stats. """
        user = User.find_by_identity('admin@local.host')
        old_sign_in_count = user.sign_in_count

        response = self.login()

        new_sign_in_count = user.sign_in_count

        assert response.status_code == 200
        assert (old_sign_in_count + 1) == new_sign_in_count

    def test_login_disable(self):
        """ Login failure due to account being disabled. """
        response = self.login(identity='disabled@local.host')

        assert_status_with_message(200, response,
                                   'This account has been disabled.')

    def test_login_fail(self):
        """ Login failure due to invalid login credentials. """
        response = self.login(identity='foo@bar.com')
        assert_status_with_message(200, response,
                                   'Identity or password is incorrect.')

    def test_logout(self):
        """ Logout successfully. """
        self.login()

        response = self.logout()
        assert_status_with_message(200, response, 'You have been logged out.')


class TestPasswordReset(ViewTestMixin):
    def test_begin_password_reset_page(self):
        """ Begin password reset renders successfully. """
        response = self.client.get(url_for('user.begin_password_reset'))
        assert response.status_code == 200

    def test_password_reset_page(self):
        """ Password reset renders successfully. """
        response = self.client.get(url_for('user.password_reset'))
        assert response.status_code == 200

    def test_begin_password_reset_as_logged_in(self):
        """ Begin password reset should redirect to settings. """
        self.login()
        response = self.client.get(url_for('user.begin_password_reset'),
                                   follow_redirects=False)

        assert response.status_code == 302

    def test_password_reset_as_logged_in(self):
        """ Password reset should redirect to settings. """
        self.login()
        response = self.client.get(url_for('user.password_reset'),
                                   follow_redirects=False)

        assert response.status_code == 302

    def test_begin_password_reset_fail(self):
        """ Begin reset failure due to using a non-existent account. """
        user = {'identity': 'foo@invalid.com'}
        response = self.client.post(url_for('user.begin_password_reset'),
                                    data=user, follow_redirects=True)

        assert_status_with_message(200, response, 'Unable to locate account.')

    def test_begin_password_reset(self):
        """ Begin password reset successfully. """
        user = {'identity': 'admin@local.host'}
        response = self.client.post(url_for('user.begin_password_reset'),
                                    data=user, follow_redirects=True)

        assert_status_with_message(200, response,
                                   'An email has been sent to {0}.'.format(
                                     'admin@local.host'))

    def test_password_reset(self, users, token):
        """ Reset successful. """
        reset = {'password': 'newpassword', 'reset_token': token}
        response = self.client.post(url_for('user.password_reset'), data=reset,
                                    follow_redirects=True)

        assert_status_with_message(200, response,
                                   'Your password has been reset.')

        admin = User.find_by_identity('admin@local.host')
        assert admin.password != 'newpassword'

    def test_password_reset_empty_token(self):
        """ Reset failure due to empty reset token. """
        reset = {'password': 'newpassword'}
        response = self.client.post(url_for('user.password_reset'), data=reset,
                                    follow_redirects=True)

        assert_status_with_message(200, response,
                                   'Your reset token has expired or was '
                                   'tampered with.')

    def test_password_reset_invalid_token(self):
        """ Reset failure due to tampered reset token. """
        reset = {'password': 'newpassword', 'token': '123'}
        response = self.client.post(url_for('user.password_reset'), data=reset,
                                    follow_redirects=True)

        assert_status_with_message(200, response,
                                   'Your reset token has expired or was '
                                   'tampered with.')


class TestSignup(ViewTestMixin):
    def test_signup_page(self):
        """ Signup renders successfully. """
        response = self.client.get(url_for('user.signup'))

        assert response.status_code == 200

    def test_welcome_page(self, users):
        """ Welcome renders successfully. """
        self.login()
        response = self.client.get(url_for('user.welcome'))

        assert response.status_code == 200

    def test_begin_signup_fail_logged_in(self, users):
        """ Signup should redirect to settings. """
        self.login()
        response = self.client.get(url_for('user.signup'),
                                   follow_redirects=False)

        assert response.status_code == 302

    def test_begin_signup_fail(self):
        """ Signup failure due to using an account that exists. """
        user = {'email': 'admin@local.host', 'password': 'password'}
        response = self.client.post(url_for('user.signup'), data=user,
                                    follow_redirects=True)

        assert_status_with_message(200, response, 'Already exists.')

    def test_signup(self, users):
        """ Signup successfully. """
        old_user_count = User.query.count()

        user = {'email': 'new@local.host', 'password': 'password'}
        response = self.client.post(url_for('user.signup'), data=user,
                                    follow_redirects=True)

        assert_status_with_message(200, response,
                                   'Awesome, thanks for signing up!')

        new_user_count = User.query.count()
        assert (old_user_count + 1) == new_user_count

        new_user = User.find_by_identity('new@local.host')
        assert new_user.password != 'password'

    def test_welcome(self, users):
        """ Create username successfully. """
        self.login()

        user = {'username': 'hello'}
        response = self.client.post(url_for('user.welcome'), data=user,
                                    follow_redirects=True)

        assert_status_with_message(200, response,
                                   'Sign up is complete, enjoy our services.')

    def test_welcome_with_existing_username(self, users):
        """ Create username failure due to username already existing. """
        self.login()

        u = User.find_by_identity('admin@local.host')
        u.username = 'hello'
        u.save()

        user = {'username': 'hello'}
        response = self.client.post(url_for('user.welcome'), data=user,
                                    follow_redirects=True)

        assert_status_with_message(200, response,
                                   'You already picked a username.')


class TestSettings(ViewTestMixin):
    def test_settings_page(self):
        """ Settings renders successfully. """
        self.login()
        response = self.client.get(url_for('user.settings'))

        assert response.status_code == 200


class TestUpdateCredentials(ViewTestMixin):
    def test_update_credentials_page(self):
        """ Update credentials renders successfully. """
        self.login()
        response = self.client.get(url_for('user.update_credentials'))

        assert response.status_code == 200

    def test_begin_update_credentials_invalid_current(self):
        """ Update credentials failure due to invalid current password. """
        self.login()

        user = {'current_password': 'nopenope', 'email': 'admin@local.host'}
        response = self.client.post(url_for('user.update_credentials'),
                                    data=user, follow_redirects=True)

        old_user = User.find_by_identity('admin@local.host')
        print(old_user)
        print('----')
        print(response.data)

        assert_status_with_message(200, response, 'Does not match.')

    def test_begin_update_credentials_existing_email(self):
        """ Update credentials failure due to existing account w/ email. """
        self.login()

        user = {
            'current_password': 'password',
            'email': 'disabled@local.host'
        }
        response = self.client.post(url_for('user.update_credentials'),
                                    data=user, follow_redirects=True)

        assert_status_with_message(200, response, 'Already exists.')

    def test_begin_update_credentials_email_change(self):
        """ Update credentials but only the e-mail address. """
        self.login()

        user = {
            'current_password': 'password',
            'email': 'admin2@local.host'
        }
        response = self.client.post(url_for('user.update_credentials'),
                                    data=user, follow_redirects=True)

        assert_status_with_message(200, response,
                                   'Your sign in settings have been updated.')

        old_user = User.find_by_identity('admin@local.host')
        assert old_user is None

        new_user = User.find_by_identity('admin2@local.host')
        assert new_user is not None

    def test_begin_update_credentials_password_change(self, client):
        """ Update credentials but only the password. """
        self.login()

        user = {
            'current_password': 'password',
            'email': 'admin@local.host',
            'password': 'newpassword'
        }

        response = self.client.post(url_for('user.update_credentials'),
                                    data=user, follow_redirects=True)

        assert response.status_code == 200

        self.logout()
        self.login()
        assert response.status_code == 200

    def test_begin_update_credentials_email_password(self):
        """ Update both the email and a new password. """
        self.login()

        user = {
            'current_password': 'password',
            'email': 'admin2@local.host',
            'password': 'newpassword'
        }

        response = self.client.post(url_for('user.update_credentials'),
                                    data=user, follow_redirects=True)

        assert response.status_code == 200


class TestUpdateLocale(ViewTestMixin):
    def test_update_locale_page(self, users):
        """ Update locale renders successfully. """
        self.login()
        response = self.client.get(url_for('user.update_locale'))

        assert response.status_code == 200

    def test_locale(self, users):
        """ Locale works successfully. """
        self.login()

        user = {'locale': 'kl'}
        response = self.client.post(url_for('user.update_locale'), data=user,
                                    follow_redirects=True)

        assert_status_with_message(200, response,
                                   'Your locale settings have been updated.')

    def test_klingon_locale(self, users):
        """ Klingon locale works successfully. """
        user = User.find_by_identity('admin@local.host')
        user.locale = 'kl'
        user.save()

        self.login()

        response = self.client.get(url_for('billing.purchase_coins'))

        # Klingon for "Card".
        assert_status_with_message(200, response, 'Chaw')
