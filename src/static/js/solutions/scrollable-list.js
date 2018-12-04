function ScrollableList(container, options) {
    this.container = container;

    this.options = options || {};
    this.options.itemClass = this.options.itemClass || 'item';
    this.indicator = this.options.indicator;

    this.reset();
    $(window).scroll(this.validateLoadMore.bind(this));
}

ScrollableList.prototype = {
    reset: function() {
        this.cursor = null;
        this.isLoading = false;
        this.hasMore = true;
    },

    validateLoadMore: function() {
        if (!this.hasMore) {
            return;
        }
        var lastItem = this.container.find('.' + this.options.itemClass).last();
        if(sln.isOnScreen(lastItem) && !this.isLoading) {
            this.load();
        }
    },

    onLoaded: function(data) {
        // data is a paginated result
        this.cursor = data.cursor;
        this.hasMore = data.more;
        this.isLoading = false;
        this.render(data.results);
    },

    load: function() {

    },

    render: function() {
    },

    reload: function() {
    },
}
