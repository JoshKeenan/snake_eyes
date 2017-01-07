from flask import Blueprint, current_app, render_template, request
from flask_login import current_user, login_required

from lib.util_json import render_json
from snakeeyes.extensions import limiter
from snakeeyes.blueprints.bet.decorators import coins_required
from snakeeyes.blueprints.bet.forms import BetForm
from snakeeyes.blueprints.bet.models.bet import Bet
from snakeeyes.blueprints.bet.models.dice import roll

bet = Blueprint('bet', __name__, template_folder='templates',
                url_prefix='/bet')


@bet.before_request
@login_required
def before_request():
    """ Protect all of the bet endpoints. """
    pass


@bet.route('/place', methods=['GET', 'POST'])
@coins_required
@limiter.limit('3/second')
def place_bet():
    if request.method == 'GET':
        recent_bets = Bet.query.filter(Bet.user_id == current_user.id) \
            .order_by(Bet.created_on.desc()).limit(10)

        return render_template('bet/place_bet.html', recent_bets=recent_bets)

    form = BetForm()

    if form.validate_on_submit():
        guess = int(request.form.get('guess'))
        wagered = int(request.form.get('wagered'))

        if wagered > current_user.coins:
            error = 'You cannot wager more than your total coins.'
            return render_json(400, {'error': error})

        payout = float(current_app.config['DICE_ROLL_PAYOUT'][str(guess)])
        die_1 = roll()
        die_2 = roll()
        outcome = die_1 + die_2
        is_winner = Bet.is_winner(guess, outcome)
        payout = Bet.determine_payout(payout, is_winner)
        net = Bet.calculate_net(wagered, payout, is_winner)

        params = {
          'user_id': current_user.id,
          'guess': guess,
          'die_1': die_1,
          'die_2': die_2,
          'roll': outcome,
          'wagered': wagered,
          'payout': payout,
          'net': net
        }

        bet = Bet(**params)
        bet.save_and_update_user(current_user)

        return render_json(200, {'data': bet.to_json()})
    else:
        return render_json(400,
                           {'error': 'You need to wager at least 1 coin.'})


@bet.route('/history', defaults={'page': 1})
@bet.route('/history/page/<int:page>')
def history(page):
    paginated_bets = Bet.query \
        .filter(Bet.user_id == current_user.id) \
        .order_by(Bet.created_on.desc()) \
        .paginate(page, 50, True)

    return render_template('bet/history.html', bets=paginated_bets)
