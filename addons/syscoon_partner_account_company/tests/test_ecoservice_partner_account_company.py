# -*- coding: utf-8 -*-
##############################################################################
#    ecoservice_partner_account_company
#    Copyright (c) 2016 ecoservice GbR (<http://www.ecoservice.de>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    This program based on OpenERP.
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
##############################################################################
from openerp.tests.common import TransactionCase


class TestEcoservicePartneraccountcompany(TransactionCase):
    def setUp(self):
        """ setUp ***"""
        super(TestEcoservicePartneraccountcompany, self).setUp()
        cr, uid = self.cr, self.uid
        self.account = self.registry('account.account')
        self.partner = self.registry('res.partner')
        self.auto_account = self.registry('ecoservice.partner.auto.account.company')
        self.sequence = self.registry('ir.sequence')
        self.account_id_recievable = self.registry("ir.model.data").get_object_reference(cr, uid, "account", "a_recv")[1]
        self.account_id_payable = self.registry("ir.model.data").get_object_reference(cr, uid, "account", "a_pay")[1]
        self.company_id = self.registry("ir.model.data").get_object_reference(cr, uid, "base", "main_company")[1]
        self.partner_id = self.registry("ir.model.data").get_object_reference(cr, uid, "base", "res_partner_2")[1]
        self.sequence_payable = self.sequence.create(cr, uid, {'name': 'PAYABLE',
                                                               'prefix': 'PAYABLE'}, context=None)
        self.sequence_receivable = self.sequence.create(cr, uid, {'name': 'RECEIVEABLE',
                                                               'prefix': 'RECEIVEABLE'}, context=None)
        self.auto_account_id = self.auto_account.create(cr, uid, {
                                                                    'company_id': self.company_id,
                                                                    'receivable_sequence_id': self.sequence_receivable,
                                                                    'payable_sequence_id': self.sequence_payable,
                                                                    'receivable_template_id': self.account_id_recievable,
                                                                    'payable_template_id': self.account_id_payable,
                                                    },
                                                context=None)

    def test_00_check_creation(self):
        """ Testing if the paybale and receivable account will be created correct"""
        cr, uid = self.cr, self.uid
        self.partner.create_accounts(cr, uid, [self.partner_id], context={})
        accounts = self.partner.read(cr, uid, self.partner_id, ['property_account_receivable_id','property_account_payable'])
        account_receivable = self.account.read(cr, uid, accounts['property_account_receivable'][0], ['code', 'reconcile','user_type_id','company_id','name'], load='_classic_write')
        checkdict = {'id': account_receivable['id'],
                     'code': 'RECEIVEABLE1',
                     'reconcile': True,
                     'user_type_id': 2,
                     'company_id': 1,
                     #'type': 'receivable',
                     'name': 'Agrolait'}
        self.assertEqual(account_receivable, checkdict, "The receivable account creation failed")
        account_payable = self.account.read(cr, uid, accounts['property_account_payable_id'][0], ['code', 'reconcile','user_type_id','company_id', 'name'], load='_classic_write')
        checkdict = {'id': account_payable['id'],
                     'code': 'PAYABLE1',
                     'reconcile': True,
                     'user_type_id': 3,
                     'company_id': 1,
                     #'type': 'payable',
                     'name': 'Agrolait'}
        self.assertEqual(account_payable, checkdict, "The payable account creation failed")
