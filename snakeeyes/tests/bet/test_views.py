from time import sleep

from flask import url_for, json

from lib.tests import ViewTestMixin, assert_status_with_message


class TestBetting(ViewTestMixin):
    def test_betting_page(self):
        """ Betting page renders successfully. """
        self.login()

        response = self.client.get(url_for('bet.place_bet'))
        assert response.status_code == 200

    def test_betting_history_details(self):
        """ Betting history should render successfully. """
        self.login()
        response = self.client.get(url_for('bet.history'))

        assert_status_with_message(200, response,
                                   'Betting history')

    def test_bet_create(self):
        """ Bet create works. """
        self.login()

        guess = 5
        wagered = 10

        params = {
          'guess': guess,
          'wagered': wagered
        }

        response = self.client.post(url_for('bet.place_bet'),
                                    data=params, follow_redirects=True)

        data = json.loads(response.data)['data']

        assert 'guess' in data
        assert 'die_1' in data
        assert 'die_2' in data
        assert 'roll' in data
        assert 'wagered' in data
        assert 'payout' in data
        assert 'net' in data
        assert 'is_winner' in data

    def test_bet_create_fails_due_to_not_enough_coins(self):
        """ Bet create fails due to not enough coins. """
        self.login()

        guess = 5
        wagered = 100000

        params = {
          'guess': guess,
          'wagered': wagered
        }

        response = self.client.post(url_for('bet.place_bet'),
                                    data=params, follow_redirects=True)

        data = json.loads(response.data)

        assert 'You cannot wager more than your total coins.' in data['error']

    def test_bet_create_fails_due_to_not_betting_enough(self):
        """ Bet create fails due to not betting enough. """
        # Avoid getting rate limited
        sleep(1)

        self.login()

        guess = 5
        wagered = 0

        params = {
          'guess': guess,
          'wagered': wagered
        }

        response = self.client.post(url_for('bet.place_bet'),
                                    data=params, follow_redirects=True)

        data = json.loads(response.data)

        assert 'You need to wager at least 1 coin.' in data['error']
