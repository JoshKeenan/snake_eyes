import click

from snakeeyes.app import create_app
from snakeeyes.extensions import db
from snakeeyes.blueprints.billing.gateways.stripecom import Plan as PaymentPlan

# Create an app context for the database connection.
app = create_app()
db.app = app


@click.group()
def cli():
    """ Perform various tasks with Stripe's API. """
    pass


@click.command()
def sync_plans():
    """
    Sync (upsert) STRIPE_PLANS to Stripe.

    :return: None
    """
    if app.config['STRIPE_PLANS'] is None:
        return None

    for _, value in app.config['STRIPE_PLANS'].items():
        plan = PaymentPlan.retrieve(value.get('id'))

        if plan:
            PaymentPlan.update(id=value.get('id'),
                               name=value.get('name'),
                               metadata=value.get('metadata'),
                               statement_descriptor=value.get(
                                   'statement_descriptor'))
        else:
            PaymentPlan.create(**value)

    return None


@click.command()
@click.argument('plan_ids', nargs=-1)
def delete_plans(plan_ids):
    """
    Delete 1 or more plans from Stripe.

    :return: None
    """
    for plan_id in plan_ids:
        PaymentPlan.delete(plan_id)

    return None


@click.command()
def list_plans():
    """
    List all existing plans on Stripe.

    :return: Stripe plans
    """
    click.echo(PaymentPlan.list())


cli.add_command(sync_plans)
cli.add_command(delete_plans)
cli.add_command(list_plans)
