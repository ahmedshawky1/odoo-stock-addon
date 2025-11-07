# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class LoginImage(models.Model):
    _name = 'login.image'
    _description = 'Login Background Images'
    _rec_name = 'name'

    image = fields.Binary(string="Image", required=True)
    name = fields.Char(string="Name", required=True)
