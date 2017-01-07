from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def coins_required(f):
    """
    Restrict access from users who have no coins.

    :return: Function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.coins == 0:
            flash("Sorry, you're out of coins. You should buy more.",
                  'warning')
            return redirect(url_for('billing.purchase_coins'))

        return f(*args, **kwargs)

    return decorated_function
