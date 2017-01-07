from collections import OrderedDict

from flask_wtf import Form
from wtforms import (
  SelectField,
  StringField,
  BooleanField,
  IntegerField,
  FloatField,
  DateTimeField
)
from wtforms.validators import (
  DataRequired,
  Length,
  Optional,
  Regexp,
  NumberRange
)
from wtforms_components import Unique

from lib.locale import Currency
from lib.util_wtforms import ModelForm, choices_from_dict
from snakeeyes.blueprints.user.models import db, User
from snakeeyes.blueprints.billing.models.coupon import Coupon


class SearchForm(Form):
    q = StringField('Search terms', [Optional(), Length(1, 256)])


class BulkDeleteForm(Form):
    SCOPE = OrderedDict([
        ('all_selected_items', 'All selected items'),
        ('all_search_results', 'All search results')
    ])

    scope = SelectField('Privileges', [DataRequired()],
                        choices=choices_from_dict(SCOPE, prepend_blank=False))


class UserForm(ModelForm):
    username_message = 'Letters, numbers and underscores only please.'

    coins = IntegerField('Coins', [DataRequired(),
                                   NumberRange(min=1, max=2147483647)])

    username = StringField(validators=[
        Unique(
            User.username,
            get_session=lambda: db.session
        ),
        Optional(),
        Length(1, 16),
        Regexp('^\w+$', message=username_message)
    ])

    role = SelectField('Privileges', [DataRequired()],
                       choices=choices_from_dict(User.ROLE,
                                                 prepend_blank=False))
    active = BooleanField('Yes, allow this user to sign in')


class UserCancelSubscriptionForm(Form):
    pass


class CouponForm(Form):
    percent_off = IntegerField('Percent off (%)', [Optional(),
                                                   NumberRange(min=1,
                                                               max=100)])
    amount_off = FloatField('Amount off ($)', [Optional(),
                                               NumberRange(min=0.01,
                                                           max=21474836.47)])
    code = StringField('Code', [DataRequired(), Length(1, 32)])
    currency = SelectField('Currency', [DataRequired()],
                           choices=choices_from_dict(Currency.TYPES,
                                                     prepend_blank=False))
    duration = SelectField('Duration', [DataRequired()],
                           choices=choices_from_dict(Coupon.DURATION,
                                                     prepend_blank=False))
    duration_in_months = IntegerField('Duration in months', [Optional(),
                                                             NumberRange(
                                                                 min=1,
                                                                 max=12)])
    max_redemptions = IntegerField('Max Redemptions',
                                   [Optional(), NumberRange(min=1,
                                                            max=2147483647)])
    redeem_by = DateTimeField('Redeem by', [Optional()],
                              format='%Y-%m-%d %H:%M:%S')

    def validate(self):
        if not Form.validate(self):
            return False

        result = True
        percent_off = self.percent_off.data
        amount_off = self.amount_off.data

        if percent_off is None and amount_off is None:
            empty_error = 'Pick at least one.'
            self.percent_off.errors.append(empty_error)
            self.amount_off.errors.append(empty_error)
            result = False
        elif percent_off and amount_off:
            both_error = 'Cannot pick both.'
            self.percent_off.errors.append(both_error)
            self.amount_off.errors.append(both_error)
            result = False
        else:
            pass

        return result
