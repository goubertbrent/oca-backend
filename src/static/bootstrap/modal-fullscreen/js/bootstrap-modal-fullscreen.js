(function (factory) {
	'use strict';
	if (typeof define === 'function' && define.amd) {
		// Register as an anonymous AMD module:
		define([
			'jquery',
			'bootstrap'
		], factory);
	} else {
		// Browser globals:
		factory(
			window.jQuery
		);
	}
}(function ($) {
	'use strict';

	$.extend($.fn.modal.Constructor.prototype, {
		fit: function () {
			if (this.$element.hasClass('modal-fullscreen')) {
				var
					modalHeight = this.$element.find('.modal-body:first').height()
					, viewportHeight = $(window).height()
				;

				var maxheight = viewportHeight - this.$element.find('.modal-header:first').height() - this.$element.find('.modal-footer:first').height() - 80;
				
				this.$element.find('.modal-body')['css']({
					'max-height': maxheight + 'px'
				});
			}
		}
	});

	var _backdrop = $.fn.modal.Constructor.prototype.backdrop;
	$.fn.modal.Constructor.prototype.backdrop = function () {
		var
			that = this
			, oldCallback = arguments[0]
			, newCallback = function () {
				oldCallback();
				that.fit();
			}
		;

		arguments[0] = newCallback;

		return _backdrop.apply(this, arguments);
	};

	$(window).on('resize', function () {
		$('.modal-fullscreen').modal('fit');
	});
}));
