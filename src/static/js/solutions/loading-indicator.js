function LoadingIndicator(container) {
    this.container = container;
    this.container.css('display', 'block');
}

LoadingIndicator.prototype = {
    show: function() {
        this.container.html(TMPL_LOADING_SPINNER);
    },

    hide: function() {
        this.container.empty();
    }
};
