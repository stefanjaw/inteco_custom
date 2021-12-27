from io import BytesIO
from datetime import date, datetime

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

import pandas as pd


class ReportFinancial(object):

    def __init__(self, obj, data):
        self.obj = obj
        self.data = data

    @staticmethod
    def get_filename():
        return 'Reporte_Notas_Anexos.xlsx'

    def get_content(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        ws = workbook.add_worksheet('Report de Venta')

        style0 = workbook.add_format({
            'valign': 'vcenter',
            'size': 10,
            'bold': True,
            'border': 7
        })
        style1 = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'size': 10,
            'bold': True,
            'border': 7
        })
        style2 = workbook.add_format({
            'valign': 'vcenter',
            'size': 10,
            'font_name': 'Arial',
            'bold': True
        })
        style3 = workbook.add_format({
            'valign': 'vcenter',
            'size': 10,
            'font_name': 'Arial'
        })
        content_number_format_bold = workbook.add_format({
            'size': 10,
            'num_format': '#,##0.00',
            'bold': True
        })
        content_number_format = workbook.add_format({
            'size': 10,
            'num_format': '#,##0.00',
        })
        content_date_format = workbook.add_format({
            'align': 'right',
            'size': 10,
            'num_format': 'dd/mm/yy',
        })

        c = 0
        i = c + 3

        ws.write(0, 0, 'Notas y Anexos de los Estados Financieros', style0)
        ws.write(c + 1, 0, 'De {} a {}'.format(
            date.strftime(self.obj.date_start, '%d/%m/%Y'),
            date.strftime(self.obj.date_end, '%d/%m/%Y')
        ), style0)
        ws.write(c + 2, 0, 'Total General:', style0)

        ws.set_column('A:A', 12)
        ws.set_column('B:B', 10)
        ws.set_column('C:C', 14)
        ws.set_column('D:D', 20)
        ws.set_column('E:E', 17)
        ws.set_column('F:F', 17)
        ws.set_column('G:G', 12)
        ws.set_column('H:H', 12)
        ws.set_column('I:I', 20)
        ws.set_column('J:J', 16)
        ws.set_column('K:K', 5)
        ws.set_column('L:L', 16)
        ws.set_column('M:M', 5.86)
        ws.set_column('N:N', 12)
        ws.set_column('O:O', 12)
        ws.set_column('P:P', 12)
        ws.set_column('Q:Q', 16)
        ws.set_column('R:R', 16)
        ws.set_column('S:S', 16)
        ws.set_column('T:T', 16)
        ws.set_column('U:U', 16)
        ws.set_column('V:V', 16)

        ws.write(i, 0, 'Fecha', style1)
        ws.write(i, 1, 'Cuenta', style1)
        ws.write(i, 2, 'Nro. de Doc.', style1)
        ws.write(i, 3, 'Socio', style1)
        ws.write(i, 4, 'N° de Asiento', style1)
        ws.write(i, 5, 'Referencia', style1)
        ws.write(i, 6, 'F. Vencimiento', style1)
        ws.write(i, 7, 'F. Esperada', style1)
        ws.write(i, 8, 'Etiqueta', style1)
        ws.write(i, 9, 'Saldo pendiente', style1)
        ws.write(i, 10, 'Divisa', style1)
        ws.write(i, 11, 'Importe divisa', style1)
        ws.write(i, 12, 'Pagado', style1)
        ws.write(i, 13, 'F. Pago', style1)
        ws.write(i, 14, 'F. Next Action', style1)
        ws.write(i, 15, 'Nota Interna', style1)

        if self.obj.seniority_report:
            ws.write(i, 16, 'No vencido', style1)
            ws.write(i, 17, '1 - 30', style1)
            ws.write(i, 18, '31 - 60', style1)
            ws.write(i, 19, '61 - 90', style1)
            ws.write(i, 20, '91 - 120', style1)
            ws.write(i, 21, 'Older', style1)

        i += 1

        sum_general_balance = 0
        sum_general_currency = 0

        if not self.obj.seniority_report:
            for k in self.data.keys():
                if self.data[k]:
                    head_i = i
                    sum_balance = 0
                    sum_currency = 0
                    ws.write(head_i, 0, k, style2)
                    ws.write(head_i, 7, 'Total:', style2)
                    i += 1

                    for line_data in self.data[k]:
                        date_format = datetime.strptime(line_data.get('date'), '%d/%m/%Y').date()
                        date_maturity = date_format if not line_data.get('date_maturity') else line_data.get('date_maturity')
                        amount_currency = line_data.get('balance', 0.00) if not line_data.get('account_currency') else line_data.get('amount_currency', 0.00)

                        ws.write(i, 0, line_data.get('date', ''), content_date_format)
                        ws.write(i, 1, line_data.get('account', ''), style3)
                        ws.write(i, 2, line_data.get('vat', ''), style3)
                        ws.write(i, 3, line_data.get('partner', ''), style3)
                        ws.write(i, 4, line_data.get('move', ''), style3)
                        ws.write(i, 5, line_data.get('ref', ''), style3)
                        ws.write(i, 6, date_maturity, content_date_format)
                        ws.write(i, 7, line_data.get('expected_pay_date', ''), content_date_format)
                        ws.write(i, 8, line_data.get('name', ''), style3)
                        ws.write(i, 9, line_data.get('balance', 0.00), content_number_format)
                        ws.write(i, 10, line_data.get('name_currency', ''), style3)
                        ws.write(i, 11, amount_currency, content_number_format)
                        ws.write(i, 12, line_data.get('reconcile', ''), style3)
                        ws.write(i, 13, line_data.get('date_reconcile', ''), content_date_format)
                        ws.write(i, 14, line_data.get('next_action_date', ''), content_date_format)
                        ws.write(i, 15, line_data.get('internal_note', ''), style3)
                        i += 1
                        sum_balance += line_data.get('balance', 0.00)
                        sum_currency += line_data.get('amount_currency', 0.00)

                    ws.write(i, 8, 'Total de la subpartida {}:'.format(line_data.get('account', '')), style2)
                    ws.write(head_i, 9, sum_balance, content_number_format_bold)
                    ws.write(head_i, 11, sum_currency, content_number_format_bold)
                    ws.write(i, 9, sum_balance, content_number_format_bold)
                    ws.write(i, 11, sum_currency, content_number_format_bold)
                    sum_general_balance += sum_balance
                    sum_general_currency += sum_currency
                    i += 3

            ws.write(c + 2, 9, sum_general_balance, content_number_format)
            ws.write(c + 2, 11, sum_general_currency, content_number_format)


        else:
            data_sorted = []

            for k in self.data.keys():
                if self.data[k]:
                    for line_data in self.data[k]:
                        if not line_data.get('date_maturity'):
                            date_format = datetime.strptime(line_data.get('date'), '%d/%m/%Y').date()
                            date_maturity = {'date_maturity': date_format}
                            line_data.update(date_maturity)
                        if not line_data.get('account_currency'):
                            amount_currency = {'amount_currency': line_data.get('balance', 0.00)}
                            line_data.update(amount_currency)
                        data_sorted.append(line_data)

            if data_sorted:
                df = pd.DataFrame(data_sorted)
                df = df.fillna('')
                df = df.sort_values(["account", "partner", "date_maturity"], ascending=(True, True, False))
                data_sorted = df.to_dict('records')

            sum_balance = 0
            sum_currency = 0

            for line_data in data_sorted:

                date_end = self.obj.date_end
                date_end_format = datetime.strptime(date_end.strftime('%m-%d-%Y'), '%m-%d-%Y').date()
                date_maturity = line_data.get('date_maturity')
                days_rest = (date_end_format - date_maturity).days

                ws.write(i, 0, line_data.get('date', ''), content_date_format)
                ws.write(i, 1, line_data.get('account', ''), style3)
                ws.write(i, 2, line_data.get('vat', ''), style3)
                ws.write(i, 3, line_data.get('partner', ''), style3)
                ws.write(i, 4, line_data.get('move', ''), style3)
                ws.write(i, 5, line_data.get('ref', ''), style3)
                ws.write(i, 6, line_data.get('date_maturity', ''), content_date_format)
                ws.write(i, 7, line_data.get('expected_pay_date', ''), content_date_format)
                ws.write(i, 8, line_data.get('name', ''), style3)
                ws.write(i, 9, line_data.get('balance', 0.00), content_number_format)
                ws.write(i, 10, line_data.get('name_currency', ''), style3)
                ws.write(i, 11, line_data.get('amount_currency', 0.00), content_number_format)
                ws.write(i, 12, line_data.get('reconcile', ''), style3)
                ws.write(i, 13, line_data.get('date_reconcile', ''), content_date_format)
                ws.write(i, 14, line_data.get('next_action_date', ''), content_date_format)
                ws.write(i, 15, line_data.get('internal_note', ''), style3)

                if days_rest < 0:
                    ws.write(i, 16, line_data.get('amount_currency', ''), content_number_format)
                elif days_rest in range(0, 31):
                    ws.write(i, 17, line_data.get('amount_currency', ''), content_number_format)
                elif days_rest in range(31, 61):
                    ws.write(i, 18, line_data.get('amount_currency', ''), content_number_format)
                elif days_rest in range(61, 91):
                    ws.write(i, 19, line_data.get('amount_currency', ''), content_number_format)
                elif days_rest in range(91, 121):
                    ws.write(i, 20, line_data.get('amount_currency', ''), content_number_format)
                elif days_rest >= 121:
                    ws.write(i, 21, line_data.get('amount_currency', ''), content_number_format)

                sum_balance += line_data.get('balance', 0.00)
                sum_currency += line_data.get('amount_currency', 0.00)

                i += 1

            ws.write(c + 2, 9, sum_balance, content_number_format)
            ws.write(c + 2, 11, sum_balance, content_number_format)

        workbook.close()
        output.seek(0)
        return output.read()
