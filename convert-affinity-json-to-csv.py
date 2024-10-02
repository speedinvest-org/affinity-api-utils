#!/bin/python3

import sys
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import fileinput
import json
import csv

def get_field(data, name):
    fields = [x for x in data.get('entity',{}).get('fields',{}) if x.get('name') == name]
    if not fields:
        return None # or raise exception
    # Note this does not handle situations where more than one field matches the name
    return fields[0]

def multi_handle_keep_nulls(handler, field_data, sep=','):
    return sep.join([handler(x) for x in (field_data or [])])

def multi_handle_drop_nulls(handler, field_data, sep=','):
    return sep.join([y for y in [handler(x) for x in (field_data or [])] if y])

def handle_list_field(field_data):
    return multi_handle_keep_nulls(repr, field_data)

def handle_dropdown(field_data):
    return (field_data or {}).get('text')

def handle_entity(field_names, field_data):
    if field_data is None or len(field_data) == 0:
        return ''
    return multi_handle_keep_nulls(lambda x: str((field_data or {}).get(x, '') or ''),
        field_names, sep=', ')

def handle_person(field_data):
    return handle_entity(['id','primaryEmailAddress'], field_data)

def handle_company(field_data):
    return handle_entity(['id','name','domain'], field_data)

def handle_location(field_data):
    # drop nulls
    if field_data is None or len(field_data) == 0:
        return ''
    field_names = ['city','country']
    return multi_handle_drop_nulls(lambda x: str((field_data or {}).get(x, '') or ''), field_names, sep=', ')

def handle_specific_dict_field(field):
    field_type = field.get('type')
    if field_type is None:
        raise ValueError(f"Missing field type: {field}")
    field_data = field.get('data')
    type_handler = {
        'text': lambda data: data,
        'number': lambda data: data,
        'number-multi': handle_list_field,
        'datetime': lambda data: data,
        'filterable-text': lambda data: data,
        'filterable-text-multi': lambda x: multi_handle_drop_nulls(lambda y: y, x),
        'dropdown': handle_dropdown,
        'ranked-dropdown': handle_dropdown,
        'dropdown-multi': lambda x: multi_handle_drop_nulls(handle_dropdown, x),
        'person': handle_person,
        'person-multi': lambda x: multi_handle_drop_nulls(handle_person, x, sep='; '),
        'company': handle_company,
        'company-multi': lambda x: multi_handle_drop_nulls(handle_company, x, sep='; '),
        'location': handle_location,
        'interaction': lambda x: handle_entity(['type','id','sentAt'], x),
    }
    handler_function = type_handler.get(field_type)
    if handler_function is None:
        raise ValueError(f"Unsupported field type: {field_type}")
    return handler_function(field_data)

def get_value(field):
    if isinstance(field, (str, int, float)) or field is None:
        return field
    elif isinstance(field, list):
        return handle_list_field(field)
    elif isinstance(field, dict):
        field_value = field.get('value')
        if field_value:
            return get_value(field_value)
        return handle_specific_dict_field(field)
    raise ValueError(f"Unsupported field type: {type(field)}")

def main():
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-t', '--tab-delimited', action='store_true', help='tab delimited output')
    parser.add_argument('files', metavar='FILE', nargs='*', help='files to read, if empty, stdin is used')
    args = vars(parser.parse_args())
    delimiter = '\t' if args['tab_delimited'] else ','
    writer = csv.writer(sys.stdout, delimiter=delimiter)

    fields_spec_org = [
        # this is for organization lists
        ("Affinity Row ID", lambda x,y: x.get('id')),
        ("Organization ID", lambda x,y: x.get('entity',{}).get('id')),
        ("Name", lambda x,y: x.get('entity',{}).get('name')),
        ("Domain", lambda x,y: x.get('entity',{}).get('domain')),
        ("Domains", lambda x,y: ','.join(x.get('entity',{}).get('domains',[]))),
    ]
    fields_spec_per = [
        # this is for person lists
        ("Affinity Row ID", lambda x,y: x.get('id')),
        ("Person ID", lambda x,y: x.get('entity',{}).get('id')),
        ("First Name", lambda x,y: x.get('entity',{}).get('firstName')),
        ("Last Name", lambda x,y: x.get('entity',{}).get('lastName')),
        ("Primary Email Address", lambda x,y: x.get('entity',{}).get('primaryEmailAddress')),
        ("Email Addresses", lambda x,y: ','.join(x.get('entity',{}).get('emailAddresses',[]))),
    ]
    fields_spec_opp = [
        # this is for opportunity lists
        ("Affinity Row ID", lambda x,y: x.get('id')),
        ("Name", lambda x,y: x.get('entity',{}).get('name')),
    ]
    header = None
    for line in fileinput.input(files=args['files']):
        data = json.loads(line)
        if header is None:
            # assume all list entries are the same type
            data_type = data.get('type')
            if data_type in (0, 'person'):
                fields_spec = fields_spec_per
            elif data_type in (1, 'company'):
                fields_spec = fields_spec_org
            elif data_type in (8, 'opportunity'):
                fields_spec = fields_spec_opp
            else:
                print(f"Unknown list entry type : {data_type}", file=sys.stderr)
                raise NameError
            header = [fs[0] for fs in fields_spec]
            for f in data.get('entity',{}).get('fields',{}):
                field_name = f.get('name')
                if field_name and field_name not in [fs[0] for fs in fields_spec]:
                    fields_spec.append((
                        field_name, lambda x,y: get_field(x, y)))
            header = [fs[0] for fs in fields_spec]
            writer.writerow(header)
        output = [get_value(fs[1](data, fs[0])) for fs in fields_spec]
        writer.writerow(output)

if __name__ == "__main__":
    main()

