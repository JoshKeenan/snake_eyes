from flask import Blueprint, request
from stripe.error import InvalidRequestError

from lib.util_json import render_json
from snakeeyes.extensions import csrf
from snakeeyes.blueprints.billing.models.invoice import Invoice
from snakeeyes.blueprints.billing.models.subscription import Subscription
from snakeeyes.blueprints.billing.gateways.stripecom import \
    Event as PaymentEvent

stripe_webhook = Blueprint('stripe_webhook', __name__,
                           url_prefix='/stripe_webhook')


@stripe_webhook.route('/event', methods=['POST'])
@csrf.exempt
def event():
    if not request.json:
        return render_json(406, {'error': 'Mime-type is not application/json'})

    if request.json.get('id') is None:
        return render_json(406, {'error': 'Invalid Stripe event'})

    try:
        safe_event = PaymentEvent.retrieve(request.json.get('id'))
        parsed_event = Invoice.parse_from_event(safe_event)

        user = Invoice.prepare_and_save(parsed_event)

        if parsed_event.get('total') > 0:
            plan = Subscription.get_plan_by_id(user.subscription.plan)
            user.add_coins(plan)
    except InvalidRequestError as e:
        # We could not parse the event.
        return render_json(422, {'error': str(e)})
    except Exception as e:
        # Return a 200 because something is really wrong and we want Stripe to
        # stop trying to fulfill this webhook request.
        return render_json(200, {'error': str(e)})

    return render_json(200, {'success': True})
