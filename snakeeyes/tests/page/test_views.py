from flask import url_for

from lib.tests import ViewTestMixin, assert_status_with_message


class TestPage(ViewTestMixin):
    def test_home_page(self):
        """ Home page should respond with a success 200. """
        response = self.client.get(url_for('page.home'))
        assert response.status_code == 200

    def test_terms_page(self):
        """ Terms page should respond with a success 200. """
        response = self.client.get(url_for('page.terms'))
        assert response.status_code == 200

    def test_privacy_page(self):
        """ Privacy page should respond with a success 200. """
        response = self.client.get(url_for('page.privacy'))
        assert response.status_code == 200

    def test_404_page(self):
        """ 404 errors should show the custom 404 page. """
        response = self.client.get('/nochancethispagewilleverexistintheapp')

        assert_status_with_message(404, response, 'Error 404')
