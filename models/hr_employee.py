from odoo import api, fields, models, _, exceptions
from odoo.exceptions import ValidationError


class HrBonus(models.Model):
    _name = "hr.bonus"
    _description = "Bonus Request"
    _inherit = "mail.thread"

    name = fields.Char(string='Name', required=True, store=True, readonly=True, compute='_generate_name')
    description = fields.Char(string="Description", required=True,
                              help="Description for the bonus request", tracking=True)
    employee_id = fields.Many2one('hr.employee', required=True, string="Employee Ref", help="Employee", tracking=True)
    date = fields.Date(string="Date", required=True,
                       help="Date in which the additional work happened", tracking=True)
    num_hours = fields.Float(string="Number of hours", required=True,
                             help="Number of hours for bonus", tracking=True)
    rate = fields.Float(string="Rate", readonly=True, compute='_compute_rate', store=True,
                        help="Hourly rate for the employee based on the current running contract", tracking=True)
    amount = fields.Float(string="Amount", required=True, readonly=True, compute='_compute_bonus_amount', store=True,
                          help="Computed amount for the bonus request", tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval', 'Pending'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
    ], string="State", default='draft', copy=False, readonly=True, tracking=True)
    active = fields.Boolean(String="Active", default=True, tracking=True)

    @api.onchange('date', 'employee_id')
    def _generate_name(self):
        for rec in self:
            if rec.employee_id.name and rec.date:
                rec.name = (str(rec.sudo().employee_id.name)
                            + " - " + str(rec.date))
            else:
                rec.name = "New Request"

    @api.onchange('num_hours', 'employee_id')
    def _compute_rate(self):
        for doc in self:
            if doc.sudo().employee_id:
                contract = [contract for contract in doc.sudo().employee_id.contract_ids if contract.state == "open"]
            else:
                if doc.sudo().env.user.employee_id:
                    doc.employee_id = doc.sudo().env.user.employee_id
                contract = [contract for contract in doc.sudo().env.user.employee_id.contract_ids if contract.state == "open"]
            if len(contract) != 1:
                raise ValidationError("There is a multiple or no active contracts for the employee")
            doc.rate = contract[0].gross_salary/30/8

    @api.onchange('num_hours')
    @api.depends('rate')
    def _compute_bonus_amount(self):
        for doc in self:
            doc.amount = doc.num_hours * doc.rate * 1.5

    def action_submit(self):
        self.state = "waiting_approval"
        if self.employee_id.leave_manager_id.partner_id:
            followers = [self.employee_id.leave_manager_id.partner_id.id]
            self.message_subscribe(followers, None)
            self.message_post(subject="Bonus Request"
                              , body="Hello "+self.employee_id.leave_manager_id.name+" please accept my request."
                              , partner_ids=followers)

    def action_approve(self):
        if self.env.user.has_group('hr_holidays.group_hr_holidays_manager'):
            self.state = "approve"
        else:
            raise ValidationError("Only HR manager can approve, reject or reset a request.")

    def action_refuse(self):
        if self.env.user.has_group('hr_holidays.group_hr_holidays_manager'):
            self.state = "refuse"
        else:
            raise ValidationError("Only HR manager can approve, reject or reset a request.")

    def action_reset(self):
        if self.env.user.has_group('hr_holidays.group_hr_holidays_manager'):
            self.state = "draft"
        else:
            raise ValidationError("Only HR manager can approve, reject or reset a request.")


class InheritHREmployee(models.Model):
    _inherit = "hr.employee"

    line_ids = fields.One2many('hr.bonus', 'employee_id', string='Bonus Requests')


class InheritHRContract(models.Model):
    _inherit = "hr.contract"

    gross_salary = fields.Monetary('Gross Salary', tracking=True)


class BonusPayslipLine(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = super(BonusPayslipLine, self).get_inputs(contracts, date_from, date_to)
        bonus = self.env['hr.bonus'].search([('employee_id', '=', contracts.employee_id.id),
                                             ('date', '<=', date_to),
                                             ('date', '>=', date_from),
                                             ('state', '=', 'approve')])
        total = 0
        for rec in bonus:
            total += rec.amount
        bonus_total = {
            'name': 'Bonus',
            'code': "Bonus",
            'amount': total,
            'contract_id': contracts.id,
        }
        res.append(bonus_total)
        return res
