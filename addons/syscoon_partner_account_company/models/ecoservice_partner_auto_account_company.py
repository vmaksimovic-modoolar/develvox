#See LICENSE file for full copyright and licensing details.


from odoo import models, fields, api, _


class ecoservice_partner_auto_account_company(models.Model):
    _name = 'ecoservice.partner.auto.account.company'
    _description = 'Configuration rules for automatic account generation'


    def _constraint_sequence(self):
        for config in self:
            receivable_company = config.receivable_sequence_id.company_id and config.receivable_sequence_id.company_id.id or 0
            payable_company = config.payable_sequence_id.company_id and config.payable_sequence_id.company_id.id or 0
            config_company = config.company_id and config.company_id.id or 0
            if (receivable_company != payable_company) or (receivable_company != config_company):
                return False
        return True

    @api.depends('company_id',)
    @api.multi
    def _compute_name(self):
        self.name = self.company_id.name

    name = fields.Char('Name', compute='_compute_name')
    company_id = fields.Many2one('res.company', 'Company', required=True)
    receivable_sequence_id = fields.Many2one('ir.sequence', 'Receivable Sequence', required=True, domain=[('code', '=', 'partner.auto.receivable')])
    payable_sequence_id = fields.Many2one('ir.sequence', 'Payable Sequence', required=True, domain=[('code', '=', 'partner.auto.payable')])
    receivable_template_id = fields.Many2one('account.account', 'Receivable account Template', required=True)
    payable_template_id = fields.Many2one('account.account', 'Payable account Template', required=True, domain=[('type', '=', 'payable')])
    add_number_to_partner_ref = fields.Boolean('Add Account Number to Partner Ref')

    _sql_constraints = [
        ('code_company_uniq', 'unique (company_id)', _('The configuration must be unique per company !')),
        ('code_payable_uniq', 'unique (payable_sequence_id)', _('The Payable Sequence account must be unique per configuration')),
        ('code_receivable_uniq', 'unique (receivable_sequence_id)', _('The Receivable Sequence account must be unique per configuration'))
    ]
    _constraints = [
        (_constraint_sequence, _('The companys in the Sequences are not the same as the configured Company'), []),
    ]

    @api.multi
    def get_accounts(self, partner_id, ctx={}):
        partner_name = partner_id.name
        config_ids = self.search([('company_id', '=', self.env.user.company_id.id)])
        account_obj = self.env['account.account']
        receivable_account_id = False
        payable_account_id = False
        for config in config_ids:
            if 'type' in ctx and ctx['type'] == 'receivable' or 'type' not in ctx:
                receivable_field_ids = self.env['ir.model.fields'].search([('model', '=', 'res.partner'), ('name', '=', 'property_account_receivable_id')])
                if len(receivable_field_ids) == 1:
                    property_ids = self.env['ir.property'].search([('company_id', '=', config.company_id.id),
                                                                   ('res_id', '=', 'res.partner,%s' % (partner_id)),
                                                                   ('name', '=', 'property_account_receivable_id'),
                                                                   ('fields_id', '=', receivable_field_ids.id)])
                    receivable_code = config.receivable_sequence_id.next_by_id()
                    receiveable_tax_ids = []
                    for ids in config.payable_template_id.tax_ids:
                        receiveable_tax_ids.append(ids.id)
                    receivable_account_values = {
                        'name': partner_name,
                        'currency_id': config.receivable_template_id.currency_id and config.receivable_template_id.currency_id.id or False,
                        'code': receivable_code,
                        'user_type_id': config.receivable_template_id.user_type_id.id,
                        'reconcile': config.receivable_template_id.reconcile,
                        'tax_ids': [(6, 0, receiveable_tax_ids)],
                        'company_id': config.company_id.id,
                        'tag_ids': [(6, 0, config.receivable_template_id.tag_ids.ids)],
                    }
                    receivable_account_id = account_obj.create(receivable_account_values)
                    receivable_property_value = {
                                        'name': 'property_account_receivable_id',
                                        'value_reference': 'account.account,%s' % (receivable_account_id.id),
                                        'res_id': 'res.partner,%s' % (partner_id.id),
                                        'company_id': config.company_id.id,
                                        'fields_id': receivable_field_ids.id,
                                        'type': 'many2one',
                    }
                    if len(property_ids) == 0:
                        self.env['ir.property'].create(receivable_property_value)
                    else:
                        self.env['ir.property'].write(receivable_property_value)
            if 'type' in ctx and ctx['type'] == 'payable' or 'type' not in ctx:
                payable_field_ids = self.env['ir.model.fields'].search([('model', '=', 'res.partner'),('name', '=', 'property_account_payable_id')])
                if len(payable_field_ids) == 1:
                    payable_code = config.payable_sequence_id.next_by_id()
                    payable_tax_ids = []
                    for ids in config.payable_template_id.tax_ids:
                        payable_tax_ids.append(ids.id)
                    payable_account_values = {
                        'name': partner_name,
                        'currency_id': config.payable_template_id.currency_id and config.payable_template_id.currency_id.id or False,
                        'code': payable_code,
                        'user_type_id': config.payable_template_id.user_type_id.id,
                        'reconcile': config.payable_template_id.reconcile,
                        'tax_ids': [(6, 0, payable_tax_ids)],
                        'company_id': config.company_id.id,
                        'tag_ids': [(6, 0, config.payable_template_id.tag_ids.ids)],
                    }
                    payable_account_id = account_obj.create(payable_account_values)
                    payable_property_value = {
                                        'name': 'property_account_payable_id',
                                        'value_reference': 'account.account,%s' % (payable_account_id.id),
                                        'res_id': 'res.partner,%s' % (partner_id.id),
                                        'company_id': config.company_id.id,
                                        'fields_id': payable_field_ids.id,
                                        'type': 'many2one',
                    }
                    property_ids = self.env['ir.property'].search([('company_id', '=', config.company_id.id),
                                                                   ('res_id', '=', 'res.partner,%s' % (partner_id.id)),
                                                                   ('name', '=', 'property_account_payable_id'),
                                                                   ('fields_id', '=', payable_field_ids.id)])
                    if len(property_ids) == 0:
                        self.env['ir.property'].create(payable_property_value)
                    else:
                        self.env['ir.property'].write(payable_property_value)
        return receivable_account_id, payable_account_id


class eco_partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create_accounts(self, ids, context={}):
        auto_account = self.env['ecoservice.partner.auto.account.company']
        partners = self.browse(ids)
        ctx = context
        for partner in partners:
            receiveable, payable = auto_account.get_accounts(partners, ctx)
            config_id = auto_account.search([('company_id', '=', self.env.user.company_id.id)])
            if config_id.add_number_to_partner_ref and receiveable and partner.customer:
                partner.write({
                    'customer_number': receiveable.code,
                    'ref': receiveable.code,
                })
            if config_id.add_number_to_partner_ref and payable and partner.supplier:
                partner.write({
                    'supplier_number': payable.code,
                })
        return receiveable and receiveable.id or False, payable and payable.id or False


class AccountAccount(models.Model):
    _inherit = 'account.account'

    _sql_constraints = [
        ('code_company_user_type_uniq', 'unique (code,company_id,user_type_id)',
         'The code and the user_type of the account must be unique per company !'),
        ('code_company_uniq', 'Check(1=1)', 'The code of the account must be unique per company !')
    ]
