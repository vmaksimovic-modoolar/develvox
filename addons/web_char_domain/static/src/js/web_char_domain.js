// Copyright 2017-2018 Modoolar <info@modoolar.com>
// License LGPLv3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
"use strict";
odoo.define('web_char_domain.patch', function (require) {

    let pyeval = require('web.pyeval')

    let eval_original = pyeval.eval;
    var py = window.py;

    function wrap(value) {
        if (value === null) { return py.None; }

        switch (typeof value) {
            case 'undefined': throw new Error("No conversion for undefined");
            case 'boolean': return py.bool.fromJSON(value);
            case 'number': return py.float.fromJSON(value);
            case 'string': return py.str.fromJSON(value);
        }

        switch(value.constructor) {
            case Object: return wrapping_dict.fromJSON(value);
            case Array: return wrapping_list.fromJSON(value);
        }

        throw new Error("ValueError: unable to wrap " + value);
    }

    var wrapping_dict = py.type('wrapping_dict', null, {
        __init__: function () {
            this._store = {};
        },
        __getitem__: function (key) {
            var k = key.toJSON();
            if (!(k in this._store)) {
                throw new Error("KeyError: '" + k + "'");
            }
            return wrap(this._store[k]);
        },
        __getattr__: function (key) {
            return this.__getitem__(py.str.fromJSON(key));
        },
        __len__: function () {
            return Object.keys(this._store).length;
        },
        __nonzero__: function () {
            return py.PY_size(this) > 0 ? py.True : py.False;
        },
        get: function () {
            var args = py.PY_parseArgs(arguments, ['k', ['d', py.None]]);

            if (!(args.k.toJSON() in this._store)) { return args.d; }
            return this.__getitem__(args.k);
        },
        fromJSON: function (d) {
            var instance = py.PY_call(wrapping_dict);
            instance._store = d;
            return instance;
        },
        toJSON: function () {
            return this._store;
        },
    });

    var wrapping_list = py.type('wrapping_list', null, {
        __init__: function () {
            this._store = [];
        },
        __getitem__: function (index) {
            return wrap(this._store[index.toJSON()]);
        },
        __len__: function () {
            return this._store.length;
        },
        __nonzero__: function () {
            return py.PY_size(this) > 0 ? py.True : py.False;
        },
        fromJSON: function (ar) {
            var instance = py.PY_call(wrapping_list);
            instance._store = ar;
            return instance;
        },
        toJSON: function () {
            return this._store;
        },
    });

    function wrap_context(context) {
        for (var k in context) {
            if (!context.hasOwnProperty(k)) { continue; }
            var val = context[k];

            if (val === null) { continue; }
            if (val.constructor === Array) {
                context[k] = wrapping_list.fromJSON(val);
            } else if (val.constructor === Object
                       && !py.PY_isInstance(val, py.object)) {
                context[k] = wrapping_dict.fromJSON(val);
            }
        }
        return context;
    }

    function my_pyeval(type, object, context) {

        if (type === 'domain' || type === 'domains'){
            if (type === 'domain')
                object = [object];
            return eval_domains(object, context);
        } else {
            return eval_original(type, object, context);
        }
    };

    function get_normalized_domain(domain_array) {
        var expected = 1; // Holds the number of expected domain expressions
        _.each(domain_array, function (item) {
            if (item === "&" || item === "|") {
                expected++;
            } else if (item !== "!") {
                expected--;
            }
        });
        var new_explicit_ands = _.times(-expected, _.constant("&"));
        return new_explicit_ands.concat(domain_array);
    }

    function eval_domains(domains, evaluation_context) {
        evaluation_context = _.extend(pyeval.context(), evaluation_context || {});
        var result_domain = [];
        // Normalize only if the first domain is the array ["|"] or ["!"]
        var need_normalization = (
            domains &&
            domains.length > 0 &&
            domains[0].length === 1 &&
            (domains[0][0] === "|" || domains[0][0] === "!")
        );
        _(domains).each(function (domain) {
            if (_.isString(domain)) {
                // wrap raw strings in domain
                domain = { __ref: 'domain', __debug: domain };
            }
            var domain_array_to_combine;
            switch(domain.__ref) {
            case 'domain':
                evaluation_context.context = evaluation_context;
                domain_array_to_combine = py.eval(domain.__debug, wrap_context(evaluation_context));
                if (_.isString(domain_array_to_combine)){
                    domain_array_to_combine = pyeval.py_eval(domain_array_to_combine);
                }
                break;
            default:
                domain_array_to_combine = domain;
            }
            if (need_normalization) {
                domain_array_to_combine = get_normalized_domain(domain_array_to_combine);
            }
            result_domain.push.apply(result_domain, domain_array_to_combine);
        });
        return result_domain;
    }

    pyeval.eval = my_pyeval;
});
