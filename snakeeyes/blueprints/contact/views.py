from flask import (
    Blueprint,
    flash,
    redirect,
    request,
    url_for,
    render_template)
from flask_login import current_user

from snakeeyes.blueprints.contact.forms import ContactForm

contact = Blueprint('contact', __name__, template_folder='templates')


@contact.route('/contact', methods=['GET', 'POST'])
def index():
    # Pre-populate the email field if the user is signed in.
    form = ContactForm(obj=current_user)

    if form.validate_on_submit():
        # This prevents circular imports.
        from snakeeyes.blueprints.contact.tasks import deliver_contact_email

        deliver_contact_email.delay(request.form.get('email'),
                                    request.form.get('message'))

        flash('Thanks, expect a response shortly.', 'success')
        return redirect(url_for('contact.index'))

    return render_template('contact/index.html', form=form)
