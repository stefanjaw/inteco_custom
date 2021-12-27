odoo.define('theme_inteco.website_sale_login', (require) => {
    'use strict';

    require('web.dom_ready');
    const $UserRequired = $('.js_inteco_user_required');
    const Widget = require('web.Widget');
    const ajax = require('web.ajax');
    const {qweb} = require('web.core');

    if(!$UserRequired.length){
        return $.Deferred().reject('No website checkout user required element found.');
    }

    const UserRequired = Widget.extend({
        events: {
            'click a': 'show_view',
            'submit .singup_form': '_submit_handler',
            'change #country_id': '_on_change_country'
        }, _on_change_country(ev){
            const country_id = ev.currentTarget.selectedOptions[0].value;
            if(!country_id){
                return false;
            }
            ajax.post('/inteco/render-province', {country_id}).then((html) => {
                const $ele = $('#province');
                $ele.find('select').remove();
                $ele.append(html);
                $ele.find('select').show();
            });
            ev.preventDefault();
            ev.stopPropagation();
        }, show_view(ev){
            ev.preventDefault();
            this.hide();
            const element = $(ev.currentTarget).data('action');
            this.$(`.${element}`).removeClass('hidden');
        }, hide(){
            this.$('.js_body>div').addClass('hidden');
        }, _submit_handler(ev){
            ev.preventDefault();
            const datas = $(ev.currentTarget).serializeArray(),
                params = {}, $error = this.$('.js_errors');
            for(const data of datas){
                params[data.name] = data.value;
            }
            $error.addClass('hidden');
            ajax.post(ev.currentTarget.action, params).then((res) => {
                const json = JSON.parse(res);
                if(json.success){
                    window.location = '/shop/checkout';
                }else{
                    $error.removeClass('hidden').text(json.error_msg);
                }
            });

        }
    });

    $UserRequired.each(function(){
        new UserRequired().attachTo($(this));
    });

    return UserRequired;
});
