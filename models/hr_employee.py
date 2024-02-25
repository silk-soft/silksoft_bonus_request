from odoo import api, fields, models, _, exceptions
from odoo.exceptions import ValidationError


class HrBonus(models.Model):
    _name = "hr.bonus"

    description = fields.Char(string="Description", required=True,
                              help="Description for the bonus request")
    employee_id = fields.Many2one('hr.employee', string="Employee Ref", help="Employee")
    date = fields.Date(string="Date", required=True,
                       help="Date in which the additional work happened")
    num_hours = fields.Float(string="Number of hours", required=True,
                             help="Number of hours for bonus")
    rate = fields.Float(string="Rate", readonly=True, compute='_compute_rate', store=True,
                        help="Hourly rate for the employee based on the current running contract")
    amount = fields.Float(string="Amount", required=True, readonly=True, compute='_compute_bonus_amount', store=True,
                          help="Computed amount for the bonus request")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval', 'Pending'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
    ], string="State", default='draft', copy=False, readonly=True)

    @api.onchange('num_hours')
    def _compute_rate(self):
        for doc in self:
            contract = [contract for contract in doc.sudo().employee_id.contract_ids if contract.state == "open"]
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

    def action_approve(self):
        self.state = "approve"

    def action_refuse(self):
        self.state = "refuse"

    def action_reset(self):
        self.state = "draft"


class InheritHREmployee(models.Model):
    _inherit = "hr.employee"

    line_ids = fields.One2many('hr.bonus', 'employee_id', string='Bonus Requests')


# todo: add user access
# class InheritHREmployeePublic(models.Model):
#     _inherit = "res.users"
#
#     line_ids = fields.One2many('hr.bonus', 'employee_id', string='Bonus Requests')


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
