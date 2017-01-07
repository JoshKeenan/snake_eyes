import datetime

import pytz

from snakeeyes.blueprints.bet.models.dice import roll
from snakeeyes.blueprints.bet.models.coin import add_subscription_coins
from snakeeyes.blueprints.bet.models.bet import Bet
from snakeeyes.blueprints.billing.models.subscription import Subscription


class TestDice(object):
    def test_dice_roll(self):
        """ Dice rolls should be in bounds. """
        assert isinstance(roll(), int)

        for i in range(1, 100):
            assert roll() >= 1 and roll() <= 6


class TestCoin(object):
    def test_add_coins_to_subscription_upgrade(self):
        """ Add coins to a subscription upgrade. """
        coins = 100

        current_plan = Subscription.get_plan_by_id('bronze')
        new_plan = Subscription.get_plan_by_id('gold')

        coins = add_subscription_coins(coins, current_plan, new_plan, None)

        assert coins == 590

    def test_no_coin_change_for_subscription_downgrade(self):
        """ Same coins for a subscription downgrade. """
        coins = 100

        current_plan = Subscription.get_plan_by_id('gold')
        new_plan = Subscription.get_plan_by_id('bronze')

        coins = add_subscription_coins(coins, current_plan, new_plan, None)

        assert coins == 100

    def test_no_coin_change_for_same_subscription(self):
        """ Same coins for the same subscription. """
        coins = 100

        current_plan = Subscription.get_plan_by_id('gold')
        new_plan = Subscription.get_plan_by_id('gold')

        may_29_2015 = datetime.datetime(2015, 5, 29, 0, 0, 0)
        may_29_2015 = pytz.utc.localize(may_29_2015)

        coins = add_subscription_coins(coins, current_plan, new_plan,
                                       may_29_2015)

        assert coins == 100


class TestBet(object):
    def test_is_winner(self):
        """ Is winner is correct. """
        assert Bet.is_winner(5, 5)

    def test_is_winner_is_incorrect(self):
        """ Is winner is incorrect. """
        assert not Bet.is_winner(3, 5)

    def test_determine_payout_as_winner(self):
        """ Calculate payout as winner is correct. """
        assert 9.0 == Bet.determine_payout(9.0, True)

    def test_determine_payout_as_loser(self):
        """ Calculate payout as loser is correct. """
        assert 1.0 == Bet.determine_payout(9.0, False)

    def test_calculate_net_as_winner(self):
        """ Calculate net as winner is correct. """
        assert 45 == Bet.calculate_net(5, 9.0, True)

    def test_calculate_net_as_loser(self):
        """ Calculate net as loser is correct. """
        assert -5 == Bet.calculate_net(5, 9.0, False)
