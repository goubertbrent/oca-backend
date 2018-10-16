/*
 * Copyright 2018 Mobicage NV
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * @@license_version:1.3@@
 */


var logoUrl = '/static/images/shop/osa_white_' + LANGUAGE + '_64.jpg';
if (LOGO_LANGUAGES.indexOf(LANGUAGE) === -1) {
    logoUrl = '/static/images/shop/osa_white_en_64.jpg';
}

function CreditcardManagerService() {

}

/** @typedef {{brand: string, exp_month: string, exp_year: string, last4: string}} CreditCard */

CreditcardManagerService.prototype = {
    /**
     * Asks the user to add a credit card.
     * Success in case a card was added, error when it failed.
     * No callbacks when canceled.
     * @return {Promise<CreditCard>}
     */
    addCreditcard: function () {
        return new Promise(function (resolve, reject) {
            sln.showProcessing(T('loading-dot-dot-dot'));
            var promises = [Requests.getCreditcardInfo(), Requests.getContacts()];
            Promise.all(promises).then(function (results) {
                sln.hideProcessing();
                var creditCard = results[0];
                var contacts = results[1];

                var html = $.tmpl(templates.billing_manage_credit_card, {
                    header: T('manage-credit-card'),
                    cancelBtn: T('Close'),
                    T: T,
                    creditCard: creditCard,
                    contacts: contacts,
                });
                var manageCreditCardModal = sln.createModal(html);
                manageCreditCardModal.show();

                $('#link_credit_card', manageCreditCardModal).click(doLinkCreditCard);

                function doLinkCreditCard() {
                    var contactId = $('#link_credit_card_contact', manageCreditCardModal).val();
                    var filteredContacts = contacts.filter(function (contact) {
                        return contact.id === contactId;
                    });
                    var contactEmail = filteredContacts.length > 0 ? filteredContacts[0].email : service_user_email;
                    var stripeHandler = StripeCheckout.configure({
                        key: STRIPE_PUBLIC_KEY,
                        image: logoUrl,
                        token: function (token) {
                            sln.showProcessing(T('saving-dot-dot-dot'));
                            var data = {
                                stripe_token: token.id,
                                stripe_token_created: token.created,
                                contact_id: contactId ? parseInt(contactId) : null
                            };
                            Requests.saveCreditcard(data, {showError: false})
                                .then(function (newCreditCard) {
                                    resolve(newCreditCard);
                                })
                                .catch(function (err) {
                                    sln.alert(T('error-occured-credit-card-linking'));
                                    reject(err);
                                })
                                .finally(function () {
                                    sln.hideProcessing();
                                    manageCreditCardModal.modal('hide');
                                });
                        }
                    });
                    // TODO description is not correct anymore
                    stripeHandler.open({
                        name: T('our-city-app'),
                        description: T('our-city-app-subscription'),
                        currency: 'eur',
                        panelLabel: CommonTranslations.SUBSCRIBE,
                        email: contactEmail,
                        allowRememberMe: false
                    });
                }
            });
        });
    }
};

var CreditcardManager = new CreditcardManagerService();
