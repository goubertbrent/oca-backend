describe("Constant: constants.ModuleConstants", function () {
    'use strict';
    beforeEach(module("constants"));
    it("should be defined", inject(function (ModuleConstants) {
        expect(typeof ModuleConstants).toBeDefined();
    }));
    it("should not have duplicated sortorders", inject(function (ModuleConstants) {
        var modulesArray = [];
        angular.forEach(ModuleConstants, function (module) {
            if (module.sortOrder) {
                modulesArray.push(module);
            }
        });
        angular.forEach(modulesArray, function (module) {
            var modulesWithSortOrder = modulesArray.filter(function (m) {
                return m.sortOrder === module.sortOrder;
            });
            expect(modulesWithSortOrder.length).toBe(1);
        });
    }));
});