import datetime

from sqlalchemy import or_

from lib.util_sqlalchemy import ResourceMixin
from snakeeyes.extensions import db
from snakeeyes.blueprints.billing.models.credit_card import CreditCard
from snakeeyes.blueprints.billing.models.coupon import Coupon
from snakeeyes.blueprints.billing.gateways.stripecom import (
    Customer as PaymentCustomer,
    Charge as PaymentCharge,
    Invoice as PaymentInvoice
)


class Invoice(ResourceMixin, db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)

    # Relationships.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id',
                                                  onupdate='CASCADE',
                                                  ondelete='CASCADE'),
                        index=True, nullable=False)

    # Invoice details.
    plan = db.Column(db.String(128), index=True)
    receipt_number = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    period_start_on = db.Column(db.Date)
    period_end_on = db.Column(db.Date)
    currency = db.Column(db.String(8))
    tax = db.Column(db.Integer())
    tax_percent = db.Column(db.Float())
    total = db.Column(db.Integer())

    # De-normalize the card details so we can render a user's history properly
    # even if they have no active subscription or changed cards at some point.
    brand = db.Column(db.String(32))
    last4 = db.Column(db.Integer)
    exp_date = db.Column(db.Date, index=True)

    def __init__(self, **kwargs):
        # Call Flask-SQLAlchemy's constructor.
        super(Invoice, self).__init__(**kwargs)

    @classmethod
    def search(cls, query):
        """
        Search a resource by 1 or more fields.

        :param query: Search query
        :type query: str
        :return: SQLAlchemy filter
        """
        from snakeeyes.blueprints.user.models import User

        if not query:
            return ''

        search_query = '%{0}%'.format(query)
        search_chain = (User.email.ilike(search_query),
                        User.username.ilike(search_query))

        return or_(*search_chain)

    @classmethod
    def parse_from_event(cls, payload):
        """
        Parse and return the invoice information that will get saved locally.

        :return: dict
        """
        data = payload['data']['object']
        plan_info = data['lines']['data'][0]['plan']

        period_start_on = datetime.datetime.utcfromtimestamp(
            data['lines']['data'][0]['period']['start']).date()
        period_end_on = datetime.datetime.utcfromtimestamp(
            data['lines']['data'][0]['period']['end']).date()

        invoice = {
            'payment_id': data['customer'],
            'plan': plan_info['name'],
            'receipt_number': data['receipt_number'],
            'description': plan_info['statement_descriptor'],
            'period_start_on': period_start_on,
            'period_end_on': period_end_on,
            'currency': data['currency'],
            'tax': data['tax'],
            'tax_percent': data['tax_percent'],
            'total': data['total']
        }

        return invoice

    @classmethod
    def parse_from_api(cls, payload):
        """
        Parse and return the invoice information we are interested in.

        :return: dict
        """
        plan_info = payload['lines']['data'][0]['plan']
        date = datetime.datetime.utcfromtimestamp(payload['date'])

        invoice = {
            'plan': plan_info['name'],
            'description': plan_info['statement_descriptor'],
            'next_bill_on': date,
            'amount_due': payload['amount_due'],
            'interval': plan_info['interval']
        }

        return invoice

    @classmethod
    def prepare_and_save(cls, parsed_event):
        """
        Potentially save the invoice after argument the event fields.

        :param parsed_event: Event params to be saved
        :type parsed_event: dict
        :return: User instance
        """
        # Avoid circular imports.
        from snakeeyes.blueprints.user.models import User

        # Only save the invoice if the user is valid at this point.
        id = parsed_event.get('payment_id')
        user = User.query.filter((User.payment_id == id)).first()

        if user and user.credit_card:
            parsed_event['user_id'] = user.id
            parsed_event['brand'] = user.credit_card.brand
            parsed_event['last4'] = user.credit_card.last4
            parsed_event['exp_date'] = user.credit_card.exp_date

            del parsed_event['payment_id']

            invoice = Invoice(**parsed_event)
            invoice.save()

        return user

    @classmethod
    def upcoming(cls, customer_id):
        """
        Return the upcoming invoice item.

        :param customer_id: Stripe customer id
        :type customer_id: int
        :return: Stripe invoice object
        """
        invoice = PaymentInvoice.upcoming(customer_id)

        return Invoice.parse_from_api(invoice)

    def create(self, user=None, currency=None, amount=None, coins=None,
               coupon=None, token=None):
        """
        Create an invoice item.

        :param user: User to apply the subscription to
        :type user: User instance
        :param amount: Stripe currency
        :type amount: str
        :param amount: Amount in cents
        :type amount: int
        :param coins: Amount of coins
        :type coins: int
        :param coupon: Coupon code to apply
        :type coupon: str
        :param token: Token returned by JavaScript
        :type token: str
        :return: bool
        """
        if token is None:
            return False

        customer = PaymentCustomer.create(token=token, email=user.email)

        if coupon:
            self.coupon = coupon.upper()
            coupon = Coupon.query.filter(Coupon.code == self.coupon).first()
            amount = coupon.apply_discount_to(amount)

        charge = PaymentCharge.create(customer.id, currency, amount)

        # Redeem the coupon.
        if coupon:
            coupon.redeem()

        # Add the coins to the user.
        user.coins += coins

        # Create the invoice item.
        period_on = datetime.datetime.utcfromtimestamp(charge.get('created'))
        card_params = CreditCard.extract_card_params(customer)

        self.user_id = user.id
        self.plan = '&mdash;'
        self.receipt_number = charge.get('receipt_number')
        self.description = charge.get('statement_descriptor')
        self.period_start_on = period_on
        self.period_end_on = period_on
        self.currency = charge.get('currency')
        self.tax = None
        self.tax_percent = None
        self.total = charge.get('amount')
        self.brand = card_params.get('brand')
        self.last4 = card_params.get('last4')
        self.exp_date = card_params.get('exp_date')

        db.session.add(user)
        db.session.add(self)
        db.session.commit()

        return True
