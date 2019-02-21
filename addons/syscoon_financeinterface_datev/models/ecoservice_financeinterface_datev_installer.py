#See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo import SUPERUSER_ID
import socket
import fcntl
import struct

class ecoservice_financeinterface_datev_installer(models.TransientModel):
    """ Installer for the Datev interface
    """
    _name = 'ecoservice.financeinterface.datev.installer'
    _inherit = 'res.config.installer'

    name = fields.Char('Name', size=64)
    migrate_datev = fields.Boolean('Migrate', help="If you select this, all account moves from invoices will be migrated.")

    def get_ip_address(self, ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15])
        )[20:24])

    @api.multi
    def send_notification_mail(self):
        ''' Send install notification mail to info@syscoon.com
        '''
        user_data = self.env['res.users'].search_read(SUPERUSER_ID, ['name', 'email', 'phone', 'company_id'])
        ip_address = self.get_ip_address('eth0')
        body = """Datev Installation!\n
        User:      %s
        E-Mail:    %s
        Tel.:      %s
        IP:        %s
        """ % (user_data['name'] or '', user_data['email'] or '', user_data['phone'] or '', ip_address or '')
        body = body.replace("\n", "<br/>")
        mail_dict = {
                    'type': 'email',
                    'body': body,
                    'attachment_ids': [],
                    'parent_id': False,
                    'model': False,
                    'res_id': False,
                    'partner_ids': [],
                    'subject': "Datev-Interface installiert bei " + user_data['company_id'][1],
                    'subtype_id': 1,
        }
        mail_message_id = self.env['mail.message'].create(mail_dict)
        mail_dict['mail_message_id'] = mail_message_id
        mail_dict['email_to'] = 'info@syscoon.com'
        mail_dict['body_html'] = body
        mail_id = self.env['mail.mail'].create(mail_dict)
        self.env['mail.mail'].send([mail_id])
        return

    @api.multi
    def execute(self):
        """ Migrate moves and send an mail
        """
        self.send_notification_mail()
        #obj = self.pool.get("ecoservice.financeinterface.datev.installer").browse(cr, uid, uid, context=context)
        #if obj.migrate_datev:
        #    self.pool.get("ecofi").migrate_datev(cr, uid, context=context)

