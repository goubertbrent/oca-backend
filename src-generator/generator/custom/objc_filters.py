# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# @@license_version:1.6@@

from mcfw.consts import MISSING

STRING_TYPE = 'string'
BOOL_TYPE = 'bool'
LONG_TYPE = 'long'
FLOAT_TYPE = 'float'
TO_TYPE = 'to'
STRING_LIST_TYPE = 'list_of_string'
BOOL_LIST_TYPE = 'list_of_bool'
LONG_LIST_TYPE = 'list_of_long'
FLOAT_LIST_TYPE = 'list_of_float'
TO_LIST_TYPE = 'list_of_to'

# Mapping of single simple type to type enum
OBJC_SINGLE_TYPE_MAPPING = {
    'unicode':  STRING_TYPE,
    'bool':     BOOL_TYPE,
    'float':    FLOAT_TYPE,
    'long':     LONG_TYPE,
    'int':      LONG_TYPE,
}

# Mapping of list simple type to type enum
OBJC_LIST_TYPE_MAPPING = {
    'unicode': STRING_LIST_TYPE,
    'bool':    BOOL_LIST_TYPE,
    'float':   FLOAT_LIST_TYPE,
    'long':    LONG_LIST_TYPE,
    'int':     LONG_LIST_TYPE,
}

# Mapping of type enum to properly aligned ivar/property code string
OBJC_ALIGNED_REPRESENTATION_MAPPING = {
    STRING_TYPE:      'NSString *',
    BOOL_TYPE:        'BOOL      ',
    FLOAT_TYPE:       'MCTFloat  ',
    LONG_TYPE:        'MCTlong   ',
    STRING_LIST_TYPE: 'NSArray<NSNumber *> *',
    BOOL_LIST_TYPE:   'NSArray<NSNumber *> *',
    FLOAT_LIST_TYPE:  'NSArray<NSNumber *> *',
    LONG_LIST_TYPE:   'NSArray<NSNumber *> *',
}


# Mapping of type enum to non-aligned code string
# TO_TYPE is missing from this list
OBJC_REPRESENTATION_MAPPING = {
    STRING_TYPE:      'NSString *',
    BOOL_TYPE:        'BOOL ',
    FLOAT_TYPE:       'MCTFloat ',
    LONG_TYPE:        'MCTlong ',
    STRING_LIST_TYPE: 'NSArray<NSString *> *',
    BOOL_LIST_TYPE:   'NSArray<NSNumber *> *',
    FLOAT_LIST_TYPE:  'NSArray<NSNumber *> *',
    LONG_LIST_TYPE:   'NSArray<NSNumber *> *',
}


# Render attributes for objC @property declaration, based on AttrDefinition
def objc_attr_property_attribute(attrdef):
    cleantype = objc_attr_internal_type(attrdef)
    if cleantype == STRING_TYPE:
        return '(nonatomic, copy)  '
    if cleantype in [BOOL_TYPE, LONG_TYPE, FLOAT_TYPE]:
        return '(nonatomic)        '
    return '(nonatomic, strong)'


# Map an AttrDefinition to an enumerated type (see *_TYPE constants in this module)
def objc_attr_internal_type(attrdef):
    if objc_attr_is_list_type(attrdef):
        return OBJC_LIST_TYPE_MAPPING.get(attrdef.type, TO_LIST_TYPE)
    return objc_internal_type(attrdef.type)


def objc_internal_type(type_str):
    return OBJC_SINGLE_TYPE_MAPPING.get(type_str, TO_TYPE)


# Check whether an AttrDefinition refers to a collection
def objc_attr_is_list_type(attrdef):
    return attrdef.collection_type == list.__name__


# Render objC classname for a transfer object
def objc_to_classname(attrdef):
    return attrdef and 'MCT_' + attrdef.type.replace('.', '_')


# Render objC classname for an API package
def objc_package_classname(package):
    return package and 'MCT_' + package.replace('.', '_')


# Render objC instance name for a CAPI package
def objc_package_instancename(package):
    return package.replace('.', '_') + '_IClientRPC_instance'


OBJC_RESERVED_KEYWORDS = ['atomic', 'auto', 'break', 'bycopy', 'byref', 'case', 'char',
                          'const', 'continue', 'default', 'description', 'do', 'double', 'else', 'enum',
                          'extern', 'float', 'for', 'goto', 'hash', 'id', 'if', 'in', 'inline', 'inout',
                          'int', 'long', 'nil', 'nonatomic', 'oneway', 'out', 'register',
                          'restrict', 'retain', 'return', 'self', 'short', 'signed', 'sizeof',
                          'static', 'struct', 'super', 'switch', 'typedef', 'union', 'unsigned',
                          'void', 'volatile', 'while', 'strong', 'weak', 'friend']


# Cleanup a name to make it objC compliant (e.g. reserved keywords, dots in name)
def objc_cleanup_name(name):
    name = name.rstrip('_')
    if name in OBJC_RESERVED_KEYWORDS:
        name += 'X'
    return name


# Generate property name for a field AttrDefinition
def objc_property_field_name(attrdef):
    return objc_cleanup_name(attrdef.name)


# Generate ivar name for a field AttrDefinition
def objc_ivar_field_name(attrdef):
    return objc_property_field_name(attrdef) + '_'


# generate name for transfer object class definition
def objc_make_to_name(to):
    return to and 'MCT' + '_' + to.package.replace('.', '_') + '_' + to.name


# check whether property must be deallocated in destructor
def objc_field_must_be_deallocated(field):
    return objc_attr_internal_type(field) not in [BOOL_TYPE, LONG_TYPE, FLOAT_TYPE]


# used for tracking TODOs
def objc_error(param):
    raise RuntimeError('ERROR - Not yet implemented ' + unicode(param))


# used for tracking TODOs
def objc_warning(param):
    print 'WARNING - Not yet implemented ' + unicode(param)
    return ''


##########################################################################################
# IVAR / PROPERTY / ARG / RETURN_TYPE TYPES
##########################################################################################


# Generate properly aligned code for field definition (ivar + property)
def objc_code_fieldtype_representation(attrdef):
    return objc_code_type_representation(attrdef, allow_collection=True, align=True)


# Generate code for return type
def objc_code_rtype_representation(attrdef):
    return objc_code_type_representation(attrdef, allow_collection=False, align=False)


# Generate code for argument type
def objc_code_argtype_representation(attrdef):
    return objc_code_type_representation(attrdef, allow_collection=True, align=False)


def objc_code_type_representation(attrdef, allow_collection, align):
    if not allow_collection and attrdef.collection_type:
        raise RuntimeError('Collection not supported')

    internal_type = objc_attr_internal_type(attrdef)
    if internal_type == TO_TYPE:
        return objc_to_classname(attrdef) + ' *'

    if internal_type == TO_LIST_TYPE:
        return 'NSArray<%s%s *> *' % ('__kindof ' if attrdef.subtype else '',
                                      objc_to_classname(attrdef))

    return OBJC_REPRESENTATION_MAPPING[internal_type]


def objc_representation_for_type(type_str):
    return OBJC_REPRESENTATION_MAPPING[objc_internal_type(type_str)]


def objc_default_value(field):
    if field.default == MISSING:
        raise Exception("There is no default value (field: %s)" % field.name)

    if field.default is None:
        return 'nil'
    if field.collection_type:
        return '[NSMutableArray arrayWithCapacity:0]'

    if field.type not in OBJC_SINGLE_TYPE_MAPPING:
        raise Exception("field.type (%s) not in OBJC_SINGLE_TYPE_MAPPING" % field.type)

    if field.type == 'unicode':
        return '@"%s"' % field.default
    if field.type == 'bool':
        return 'YES' if field.default else 'NO'
    return field.default
