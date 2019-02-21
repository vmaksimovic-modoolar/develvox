# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

from odoo import models


class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'


    def _parse_file_camt(self, root):
        ns = {k or 'ns': v for k, v in root.nsmap.items()}

        def is_full_of_zeros(strg):
            pattern_zero = re.compile('^0+$')
            return bool(pattern_zero.match(strg))

        curr_cache = {c['name']: c['id'] for c in self.env['res.currency'].search_read([], ['id', 'name'])}
        statement_list = []
        unique_import_set = set([])
        currency = account_no = False
        for statement in root[0].findall('ns:Stmt', ns):
            statement_vals = {}
            statement_vals['name'] = statement.xpath('ns:Id/text()', namespaces=ns)[0]

            # Transaction Entries 0..n
            transactions = []
            sequence = 0

            # Currency 0..1
            currency = statement.xpath('ns:Acct/ns:Ccy/text() | ns:Bal/ns:Amt/@Ccy', namespaces=ns)[0]

            for entry in statement.findall('ns:Ntry', ns):
                sequence += 1
                entry_vals = {
                    'sequence': sequence,
                }

                # Amount 1..1
                amount = float(entry.xpath('ns:Amt/text()', namespaces=ns)[0])

                # Credit Or Debit Indicator 1..1
                sign = entry.xpath('ns:CdtDbtInd/text()', namespaces=ns)[0]
                counter_party = 'Dbtr'
                if sign == 'DBIT':
                    amount *= -1
                    counter_party = 'Cdtr'
                entry_vals['amount'] = amount

                # Amount currency
                instruc_amount = entry.xpath('ns:NtryDtls/ns:TxDtls/ns:AmtDtls/ns:InstdAmt/ns:Amt/text()', namespaces=ns)
                instruc_curr = entry.xpath('ns:NtryDtls/ns:TxDtls/ns:AmtDtls/ns:InstdAmt/ns:Amt/@Ccy', namespaces=ns)
                if instruc_amount and instruc_curr and instruc_curr[0] != currency and instruc_curr[0] in curr_cache:
                    amount_currency = sum([float(x) for x in instruc_amount])
                    entry_vals['amount_currency'] = amount_currency if entry_vals['amount'] > 0 else -amount_currency
                    entry_vals['currency_id'] = curr_cache[instruc_curr[0]]

                # Date 0..1
                transaction_date = entry.xpath('ns:ValDt/ns:Dt/text() | ns:BookgDt/ns:Dt/text() | ns:BookgDt/ns:DtTm/text()', namespaces=ns)
                entry_vals['date'] = transaction_date and transaction_date[0] or False

                # Name 0..1
                transaction_name = entry.xpath('.//ns:RmtInf/ns:Ustrd/text()', namespaces=ns)
                transaction_name = transaction_name or entry.xpath('ns:AddtlNtryInf/text()', namespaces=ns)
                partner_name = entry.xpath('.//ns:RltdPties/ns:%s/ns:Nm/text()' % (counter_party,), namespaces=ns)
                ### add for AOK-Verlag
                if partner_name:
                    transaction_name.insert(0, partner_name[0])
                ####
                entry_vals['name'] = ' '.join(transaction_name) if transaction_name else '/'
                entry_vals['partner_name'] = partner_name and partner_name[0] or False
                # Bank Account No
                bank_account_no = entry.xpath(""".//ns:RltdPties/ns:%sAcct/ns:Id/ns:IBAN/text() |
                                                  (.//ns:%sAcct/ns:Id/ns:Othr/ns:Id)[1]/text()
                                                  """ % (counter_party, counter_party), namespaces=ns)
                entry_vals['account_number'] = bank_account_no and bank_account_no[0] or False

                # Reference 0..1
                # Structured communication if available
                ref = entry.xpath('.//ns:RmtInf/ns:Strd/ns:%sRefInf/ns:Ref/text()' % (counter_party,), namespaces=ns)
                if not ref:
                    # Otherwise, any of below given as reference
                    ref = entry.xpath("""ns:AcctSvcrRef/text() | ns:NtryDtls/ns:TxDtls/ns:Refs/ns:TxId/text() |
                                      ns:NtryDtls/ns:TxDtls/ns:Refs/ns:InstrId/text() | ns:NtryDtls/ns:TxDtls/ns:Refs/ns:EndToEndId/text() |
                                      ns:NtryDtls/ns:TxDtls/ns:Refs/ns:MndtId/text() | ns:NtryDtls/ns:TxDtls/ns:Refs/ns:ChqNb/text()
                                      """, namespaces=ns)
                entry_vals['ref'] = ref and ref[0] or False
                unique_import_ref = entry.xpath('ns:AcctSvcrRef/text()', namespaces=ns)
                if unique_import_ref and not is_full_of_zeros(unique_import_ref[0]):
                    entry_ref = entry.xpath('ns:NtryRef/text()', namespaces=ns)
                    if entry_ref:
                        entry_vals['unique_import_id'] = '{}-{}'.format(unique_import_ref[0], entry_ref[0])
                    elif not entry_ref and unique_import_ref[0] not in unique_import_set:
                        entry_vals['unique_import_id'] = unique_import_ref[0]
                    else:
                        entry_vals['unique_import_id'] = '{}-{}'.format(unique_import_ref[0], sequence)
                else:
                    entry_vals['unique_import_id'] = '{}-{}'.format(statement_vals['name'], sequence)

                unique_import_set.add(entry_vals['unique_import_id'])
                transactions.append(entry_vals)
            statement_vals['transactions'] = transactions

            # Start Balance
            # any (OPBD, PRCD, ITBD):
            #   OPBD : Opening Balance
            #   PRCD : Previous Closing Balance
            #   ITBD : Interim Balance (in the case of preceeding pagination)
            start_amount = float(statement.xpath("ns:Bal/ns:Tp/ns:CdOrPrtry[ns:Cd='OPBD' or ns:Cd='PRCD' or ns:Cd='ITBD']/../../ns:Amt/text()",
                                                              namespaces=ns)[0])
            # Credit Or Debit Indicator 1..1
            sign = statement.xpath('ns:Bal/ns:CdtDbtInd/text()', namespaces=ns)[0]
            if sign == 'DBIT':
                start_amount *= -1
            statement_vals['balance_start'] = start_amount
            # Ending Balance
            # Statement Date
            # any 'CLBD', 'CLAV'
            #   CLBD : Closing Balance
            #   CLAV : Closing Available
            end_amount = float(statement.xpath("ns:Bal/ns:Tp/ns:CdOrPrtry[ns:Cd='CLBD' or ns:Cd='CLAV']/../../ns:Amt/text()",
                                                              namespaces=ns)[0])
            sign = statement.xpath(
                "ns:Bal/ns:Tp/ns:CdOrPrtry[ns:Cd='CLBD' or ns:Cd='CLAV']/../../ns:CdtDbtInd/text()", namespaces=ns
            )[0]
            if sign == 'DBIT':
                end_amount *= -1
            statement_vals['balance_end_real'] = end_amount

            statement_vals['date'] = statement.xpath("ns:Bal/ns:Tp/ns:CdOrPrtry[ns:Cd='CLBD' or ns:Cd='CLAV']/../../ns:Dt/ns:Dt/text()",
                                                              namespaces=ns)[0]
            statement_list.append(statement_vals)

            # Account Number    1..1
            # if not IBAN value then... <Othr><Id> would have.
            account_no = statement.xpath('ns:Acct/ns:Id/ns:IBAN/text() | ns:Acct/ns:Id/ns:Othr/ns:Id/text()', namespaces=ns)[0]

        return currency, account_no, statement_list