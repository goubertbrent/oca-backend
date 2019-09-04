/*
 * Copyright 2019 Green Valley Belgium NV
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
 * @@license_version:1.5@@
 */

// a services list per organization type
function ServicesList(organizationType, container) {
    this.organizationType = organizationType;

    this.cursor = null;
    this.hasMore = true;
    this.isLoading = false;
    this.generatedOn = null;

    this.services = []; // cache
    this.servicesContainer = container;

    document.getElementById('content-container').addEventListener('scroll', this.validateLoadMoreServices.bind(this),
        {passive: true});
}

ServicesList.prototype = {
    showLoadingSpinner: function() {
        $('#services_loading_indicator').html(TMPL_LOADING_SPINNER);
        this.isLoading = true;
    },

    hideLoadingSpinner: function() {
        $('#services_loading_indicator').html('');
        this.isLoading = false;
    },

    getServices: function(callback) {
        // Get more services from the backend
        // in case the cursor is not null, it will fetch the next batch
        // and append it to the cache
        var self = this;
        self.showLoadingSpinner();
        sln.call({
            url: '/common/services/get_all',
            data: {
                organization_type: self.organizationType,
                cursor: self.cursor
            },
            success: function (data) {
                var newServices = [];
                if(self.cursor === data.cursor || !data.services.length) {
                    self.hasMore = false;
                }
                self.cursor = data.cursor;
                self.generatedOn = data.generated_on;
                $.each(data.services, function(i, service) {
                    if(self.services.indexOf(service) === -1) {
                        service.statistics.lastQuestionAnsweredDate = sln.format(new Date(service.statistics.last_unanswered_question_timestamp * 1000));
                        service.hasAgenda = service.modules.indexOf('agenda') !== -1;
                        service.hasQA = service.modules.indexOf('ask_question') !== -1;
                        service.hasBroadcast = service.modules.indexOf('broadcast') !== -1;
                        service.hasStaticContent = service.modules.indexOf('static_content') !== -1;
                        newServices.push(service);
                    }
                });
                // add to cache
                self.services = self.services.concat(newServices);
                self.hideLoadingSpinner();
                callback(newServices);
            }
        });
    },

    renderServices: function (services) {
        // render the given services by appending them to the container
        var self = this;
        if(services.length && self.generatedOn) {
            var formattedDate = sln.format(new Date(self.generatedOn * 1000));
            $('#generated_on').show().text(formattedDate);
        } else {
            $('#generated_on').hide();
        }

        $.each(services, function(i, service) {
            var serviceHtml = $.tmpl(templates['services/service'], {
                service: service,
                t: CommonTranslations,
            });
            self.servicesContainer.append(serviceHtml);
            $('button.delete-service', serviceHtml).click(function () {
                var $this = $(this);
                var serviceEmail = $this.attr('service_email');
                var serviceName = $this.attr('service_name');
                var message = T('confirm_delete_service', {service_name: serviceName});
                sln.confirm(message, function () {
                    self.deleteService(serviceEmail);
                });
            });
            $('.service-icons>div', serviceHtml).each(function () {
                var $this = $(this);
                if ($this.attr('disabled')) {
                    $this.attr('data-original-title', '(' + CommonTranslations.module_disabled + ') ' + $this.attr('data-original-title'));
                }
            }).tooltip();
        });

        self.validateLoadMoreServices();
    },

    clearContainer: function() {
        this.servicesContainer.html('');
    },

    reset: function() {
        this.hasMore = true;
        this.cursor = null;
        this.services = [];
        this.clearContainer();
    },

    loadServices: function(forecReload) {
        // Load the services from the backend
        // if forecReload is set, it will clear the cursor and cache
        // then fetch the services from the start
        if(forecReload) {
            this.reset();
        } else {
            if(!this.hasMore) {
                return;
            }
        }

        this.getServices(this.renderServices.bind(this));
    },

    reloadServices: function() {
        // reload/render the services from cache if available first
        if(!this.hasMore && this.isEmpty()) {
            this.showCreateButton();
            return;
        }

        this.clearContainer();

        if(this.isEmpty()) {
            this.loadServices();
        } else {
            this.renderServices(this.services);
        }
    },

    validateLoadMoreServices: function() {
        var lastService = this.servicesContainer.find('.service').last();
        if(sln.isOnScreen(lastService) && this.hasMore && !this.isLoading) {
            this.loadServices();
        }

        if(!this.hasMore && this.isEmpty()) {
            this.showCreateButton();
        }
    },

    deleteService: function(serviceEmail) {
        var self = this;
        sln.call({
            url: '/common/services/delete',
            method: 'post',
            data: {
                service_email: serviceEmail
            },
            success: function (data) {
                if (data.success) {
                    self.serviceDeleted(serviceEmail);
                } else {
                    sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                }
            }
        });
    },

    serviceDeleted: function(serviceEmail) {
        var self = this;
        self.services = self.services.filter(function (a) {
            return a.service_email !== serviceEmail;
        });

        var serviceRow = $('.service[service_email="' + serviceEmail + '"]');
        serviceRow.hide('slow', function(){
            serviceRow.remove();
            self.reloadServices();
        });
    },

    isEmpty: function() {
        return this.services.length === 0;
    },

    showCreateButton: function() {
        var createServiceButton = $('<p>' + CommonTranslations.no_services_create_here +
            ' <a class="btn btn-success" href="#/services/add"><i class="fa fa-plus"></i> ' +
            CommonTranslations.create_service +
            '</a></p>');
        this.servicesContainer.html(createServiceButton);
    }

};
