from snakeeyes.blueprints.billing.models.coupon import Coupon


class TestCoupon(object):
    def test_apply_amount_off_discount(self, coupons):
        """ Amount is discounted by a fixed amount. """
        amount = 100
        coupon = Coupon.query.first()
        new_amount = coupon.apply_discount_to(amount)

        assert new_amount == 99

    def test_apply_percent_off_discount(self, coupons):
        """ Amount is discounted by a percent. """
        amount = 100
        coupon = Coupon.query.all()[2]
        coupon.percent_off = 33

        new_amount = coupon.apply_discount_to(amount)

        assert new_amount == 67
