
import odoo.tests


@odoo.tests.common.at_install(False)
@odoo.tests.common.post_install(True)
class TestUi(odoo.tests.HttpCase):
    """ Test to cover interaction with the website's user interface """

    def test_01_new_lead(self):
        """ Validates the process of requesting a quotation via the website's
            contact form
        """
        tour = 'inteco_request_quotation_tour'
        self.phantom_js(
            url_path="/",
            code="odoo.__DEBUG__.services['web_tour.tour'].run('%s')" % tour,
            ready="odoo.__DEBUG__.services['web_tour.tour'].tours.%s.ready" % (
                tour))
