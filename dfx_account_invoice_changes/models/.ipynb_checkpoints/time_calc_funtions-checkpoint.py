# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from odoo import models, fields, api


class TimeCalcFuntions(models.Model):
    _name = 'time.calc.funtions'

    def calc_weekend_days(self, init_date, time, mode):
        """
        Este metodo toma una fecha de inicio y una cantidad de horas, va realizando una sumatoria de fines de semana existentes
        de acuerdo a modo escogido, en modo 0 toma en cuenta que time contiene horas de fines de semana, en modo 2 descarta las
        horas de fines de semana y calcula time como horas de dias laborales
        Usa signo si time es negativo hace el calculo en retroceso de dias.
        :param init_date: Fecha de inicio del calculo
        :param time: cantidad de horas a calcular
        :param mode: modo 0 toma las horas incluyendo fines de semana, modo 1 toma horas sin incluir fines de semana
        :return: cantidad de dias de los fines de semana
        """
        if init_date and time:
            count_days = 0
            date = init_date
            sign = 1 if time >= 0 else -1
            sum_delta = 0 if mode == 0 else 2
            sum_days = 1 if mode == 0 else 2
            for day in range(0, timedelta(hours=(sign * time)).days):
                date = date + timedelta(days=sign)
                if date.weekday() in (5, 6):
                    date = date + timedelta(days=(sign * sum_delta))
                    count_days += (sign * sum_days)
            hours = timedelta(hours=time) - timedelta(days=timedelta(hours=time).days)
            if hours != timedelta(hours=0):
                date = date + hours
                if date.weekday() in (5, 6):
                    count_days += (sign * sum_days)
            return count_days
        else:
            return 0

    def cal_bussines_date(self, init_date, time):
        if init_date and time:
            date_prestamp = init_date
            date = fields.Datetime.context_timestamp(self, timestamp=date_prestamp)
            count_days = timedelta(hours=time).days + self.calc_weekend_days(date, time, 1)
            hours = timedelta(hours=time) - timedelta(days=timedelta(hours=time).days)
            return date_prestamp + timedelta(days=count_days) + hours

    def cal_hours_date(self, init_date, end_date):
        if init_date and end_date:
            hours_count = (end_date - init_date).total_seconds() / 3600
            date = fields.Datetime.context_timestamp(self, timestamp=init_date)
            count_days = hours_count - self.calc_weekend_days(date, hours_count, 0) * 24
            return count_days
        else:
            return 0
