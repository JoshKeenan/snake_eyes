from snakeeyes.extensions import mail
from snakeeyes.blueprints.user.tasks import deliver_password_reset_email
from snakeeyes.blueprints.user.models import User


class TestTasks(object):
    def test_deliver_password_reset_email(self, token):
        """ Deliver a password reset email. """
        with mail.record_messages() as outbox:
            user = User.find_by_identity('admin@local.host')
            deliver_password_reset_email(user.id, token)

            assert len(outbox) == 1
            assert token in outbox[0].body
