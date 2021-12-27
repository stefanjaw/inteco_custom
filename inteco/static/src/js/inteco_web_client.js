// Change the page title e.g. Customers - Inteco
odoo.define('inteco.AbstractWebClient', function(require) {
    'use strict';

    var WebClient = require('web.AbstractWebClient');

    WebClient.include({
        init: function() {
            this._super.apply(this, arguments);
            this.set('title_part', {"zopenerp": "Inteco"});
        },
    });
});
