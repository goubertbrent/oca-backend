/**
 * Created by lucas on 3/5/16.
 */
(function () {
    'use strict';
    angular.module('toolbar')
        .factory('ToolbarActionsFactory', [ToolbarActionsFactory]);

    function ToolbarActionsFactory () {
        var actions = [];

        function getActions () {
            return actions;
        }

        /**
         * Set toolbar actions. These can be buttons or switches.
         * Each object can have these properties:
         ** type (req): 'button' or 'switch'
         ** text(req): Text of the button or switch
         ** icon: (button only) Icon of the button
         ** value: (switch only) Initial value of the switch
         ** changed: (switch only): function to call when the value changes
         * @param actionsArray
         */
        function setActions (actionsArray) {
            actions = actionsArray;
        }

        function clearActions () {
            // Should be called each time a state change happens.
            actions = [];
        }

        return {
            setActions: setActions,
            clearActions: clearActions,
            getActions: getActions
        };
    }
})();