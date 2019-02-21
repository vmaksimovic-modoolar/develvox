odoo.define(
    'account_reconciliation_remove_same_type_constraint.ReconciliationModel',
    function (require) {

    "use strict";

    var ReconciliationModel = require('account.ReconciliationModel');

    ReconciliationModel.StatementModel.include({
        /**
         * @override
         *
         * @param {Widget} parent
         * @param {object} options
         */
        init: function (parent, options) {
            this._super.apply(this, arguments);
            // NOTE: ReconciliationClientAction does not allow to override the
            //       options passed to the model constructor.
            this.allowDifferentAccountTypeReconciliation = options && options.allowDifferentAccountTypeReconciliation || false;
        },
        /**
         * change the possibility to reconcile different account types
         * @param {Boolean} allow
         */
        setAllowDifferentAccountTypeReconciliation: function (allow) {
            this.allowDifferentAccountTypeReconciliation = allow;
        },
        /**
         * add a line proposition after checking receivable and payable accounts
         * constraint if the company doesn't allow to reconcile, otherwise
         * reconcile normally
         *
         * @override
         *
         * @param {Object} line
         * @param {Object} prop
         */
        _addProposition: function (line, prop) {
            if (!this.allowDifferentAccountTypeReconciliation) {
                this._super.apply(this, arguments);
            } else {
                line.reconciliation_proposition.push(prop);
                _.each(line.reconciliation_proposition, function (prop) {
                    prop.partial_reconcile = false;
                });
            }
        }
    });

});
