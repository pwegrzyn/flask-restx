# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from flask import current_app

from .. import fields

RE_URL = re.compile(r'<(?:[^:<>]+:)?([^<>]+)>')
RE_PARAMS = re.compile(r'<((?:[^:<>]+:)?[^<>]+)>')


def extract_path(path):
    '''
    Transform a Flask/Werkzeug URL pattern in a Swagger one.
    '''
    return RE_URL.sub(r'{\1}', path)


TYPES_MAPPING = {
    'int': 'integer',
    'float': 'number',
    'string': 'string',
    None: 'string',
}


def extract_path_params(path):
    '''
    Extract Flask-style parameters from an URL pattern as Swagger ones.
    '''
    params = []
    for match in RE_PARAMS.findall(path):
        descriptor, name = match.split(':') if ':' in match else (None, match)
        param = {
            'name': name,
            'paramType': 'path',
            'required': True
        }

        if descriptor in TYPES_MAPPING:
            param['type'] = TYPES_MAPPING[descriptor]
        elif descriptor in current_app.url_map.converters:
            param['type'] = 'string'
        else:
            raise ValueError('Unsupported type converter')
        params.append(param)
    return params


FIELDS = {
    fields.String: {'type': 'string'},
    fields.Integer: {'type': 'integer'},
    fields.Boolean: {'type': 'boolean'},
    fields.Float: {'type': 'number'},
    fields.Arbitrary: {'type': 'number'},
    fields.DateTime: {'type': 'string', 'format': 'date-time'},
}

LOCATIONS = {
    'args': 'query',
    'form': 'form',
    'headers': 'header',
}


def field_to_property(field):
    '''Convert a restful.Field into a Swagger property declaration'''
    if field not in FIELDS:
        return {'type': 'string'}
    return FIELDS[field]


def parser_to_params(parser):
    '''Extract Swagger parameters from a RequestParser'''
    params = {}
    for arg in parser.args:
        if arg.location == 'cookie':
            continue
        param = {'paramType': LOCATIONS.get(arg.location, 'query')}
        _handle_arg_type(arg, param)
        if arg.required:
            param['required'] = True
        if arg.help:
            param['description'] = arg.help
        if arg.action == 'append':
            param['allowMultiple'] = True
        params[arg.name] = param
    return params


def _handle_arg_type(arg, param):
    if arg.type is int:
        param['type'] = 'integer'
    elif arg.type is str:
        param['type'] = 'string'
    else:
        param['type'] = 'string'