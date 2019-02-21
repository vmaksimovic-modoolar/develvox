odoo.define(
    'account_reconciliation_remove_same_type_constraint.ReconciliationClientAction',
    function (require) {

    "use strict";

    var ReconciliationClientAction = require('account.ReconciliationClientAction');

    ReconciliationClientAction.StatementAction.include({
        /**
         * @override
         *
         * @param {Object} params
         * @param {Object} params.context
         *
         */
        init: function (parent, params) {
            this._super.apply(this, arguments);

            var allow = this.getSession().companyAllowDifferentAccountTypeReconciliation;
            this.model.setAllowDifferentAccountTypeReconciliation(allow);
        },
    });

});
