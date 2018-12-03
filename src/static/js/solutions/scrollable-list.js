function ScrollableList(container, options) {
    this.container = container;

    this.options = options || {};
    this.options.itemClass = this.options.itemClass || 'item';

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
        var lastItem = this.container.find('.' + this.options.itemClass).last();
        if(sln.isOnScreen(lastItem) && this.hasMore && !this.isLoading) {
            this.load();
        }
    },

    load: function() {
    },

    render: function() {
    },

    reload: function() {
    },
}
