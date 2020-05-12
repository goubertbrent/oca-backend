# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley Belgium NV
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
# @@license_version:1.7@@

import inspect
import os

import jinja2
import licenses
from class_definition import ClassDefinition, AttrDefinition, PackageDefinition, FunctionDefinition, SubType, key_type
from mcfw.consts import MISSING
from mcfw.properties import simple_types, get_members, object_factory, typed_property
from .custom import filters, csharp_filters, java_filters, objc_filters, ts_filters

JINJA_ENVIRONMENT = jinja2.Environment(
    undefined=jinja2.StrictUndefined,
    extensions=('jinja2.ext.loopcontrols',),
    loader=jinja2.FileSystemLoader([os.path.join(os.path.dirname(__file__), 'templates')]))

for module in (filters, csharp_filters, java_filters, objc_filters, ts_filters):
    for name, func in inspect.getmembers(module, lambda x: inspect.isfunction(x)):
        JINJA_ENVIRONMENT.filters[name] = func

DELIMITER = '*' * 50


def _get_collection_type(type_):
    return isinstance(type_, list) and list.__name__ or None


def _get_type_string(type_):
    real_type = _get_real_type(type_)
    if real_type in simple_types:
        return real_type.__name__
    elif isinstance(real_type, object_factory):
        return '%s.%s' % (real_type.__module__, real_type.__class__.__name__)
    else:
        return '%s.%s' % (real_type.__module__, real_type.__name__)


def _get_real_type(type_):
    if type_ == str:
        raise RuntimeError('str type not allowed (use unicode)')
    if type_ in [(str, unicode), (unicode, str)]:
        raise RuntimeError('str+unicode tuple type found (use unicode)')
    if isinstance(type_, (list, tuple)):
        return type_[0]
    return type_


def _sort_values_by_keys(mapping):
    return [mapping[k] for k in sorted(mapping.keys())]


def populate_class_def_fields(class_def, type_, prop, name):
    type_name = _get_type_string(type_)
    collection = list.__name__ if prop.list else None
    attr_def = AttrDefinition(name=name,
                              type_=type_name,
                              collection_type=collection,
                              doc=prop.doc,
                              default=prop.default,
                              subtype=_get_subtype(class_def, name))
    class_def.fields.append(attr_def)


def _get_subtype(class_def, name):
    typed_prop = getattr(class_def.clazz, name)
    if isinstance(typed_prop, typed_property):
        if isinstance(typed_prop.type, object_factory):
            return SubType(typed_prop.type, _get_type_string(key_type(typed_prop.type)))


def build_class_definition(type_, stash, super_class=None):
    clazz = type(type_) if isinstance(type_, object_factory) else type_
    complex_props, simple_props = get_members(clazz)
    for (_, prop) in complex_props:
        if not isinstance(prop, object_factory):
            process_type(prop.type, stash)
    class_def = ClassDefinition(package=clazz.__module__,
                                name=clazz.__name__,
                                doc=clazz.__doc__,
                                clazz=type_,
                                super_class=super_class)
    for name, prop in (complex_props + simple_props):
        t = type(prop.type) if isinstance(prop.type, object_factory) else prop.type
        populate_class_def_fields(class_def, t, prop, name)
    return class_def


def process_type(type_, stash):
    type_ = _get_real_type(type_)
    if type_ in simple_types or type_ in stash:
        return
    if isinstance(type_, object_factory) and type(type_) == object_factory:
        return
    class_def = build_class_definition(type_, stash)
    if isinstance(type_, object_factory):
        # Ensure the subtypes are generated as well
        for value in type_.subtype_mapping.itervalues():
            stash[_get_type_string(value)] = build_class_definition(value, stash, class_def)
    stash[_get_type_string(type_)] = class_def


def check_function_validity(f, max_argument_count):
    if not hasattr(f, "meta") or "kwarg_types" not in f.meta or "return_type" not in f.meta:
        raise ValueError("Cannot inspect function %s. Meta data is missing" % f)

    if _get_collection_type(f.meta.get('return_type')) == list.__name__:
        raise ValueError('List return type not supported')

    from custom.filters import SIMPLE_TYPES
    if f.meta.get('return_type') in SIMPLE_TYPES:
        raise ValueError("Only TOs are supported as return type")

    if len(f.meta.get("kwarg_types")) > max_argument_count:
        raise ValueError("Only %s argument(s) allowed" % max_argument_count)


def process_function(f, stash, max_argument_count):
    check_function_validity(f, max_argument_count)
    # process return type
    process_type(f.meta["return_type"], stash)
    # process argument types
    for kwarg_type in f.meta["kwarg_types"].itervalues():
        process_type(kwarg_type, stash)


def super_class_has_field(super_class, field):
    for super_field in super_class.fields:
        if super_field.name == field.name:
            return super_field.type == field.type

    if super_class.super_class:
        return super_class_has_field(super_class.super_class, field)

    return False


def filter_fields_of_subclasses(tos):
    def find_super_class_in_tos(to):
        super_key = '.'.join((to.super_class.package.replace('com.mobicage', 'rogerthat'), to.super_class.name))
        if super_key in tos:
            return to.super_class
        if to.super_class.super_class:
            return find_super_class_in_tos(to.super_class)

    for to in tos.itervalues():
        # for every TO, find it's closest super class
        if to.super_class:
            super_class = find_super_class_in_tos(to)
            if super_class:
                # remove fields that are common between the subclass and super class and remove them
                for field in reversed(to.fields):
                    if super_class_has_field(super_class, field):
                        to.fields.remove(field)


def hierarchy_depth(to):
    c = 0
    while to.super_class:
        c += 1
        to = to.super_class
    return c


def generate_TOs(mapping, client_mapping, max_argument_count):
    tos = {}
    all_funcs = {}
    all_funcs.update(mapping)
    all_funcs.update(client_mapping)
    for f in all_funcs.itervalues():
        process_function(f, tos, max_argument_count)

    # filter fields of subclasses that are present in generated super classes
    filter_fields_of_subclasses(tos)

    # super classes need to be rendered before subclasses
    return sorted(tos.itervalues(), key=lambda to: (hierarchy_depth(to), to.name))


def generate_CAPI_packages(capi_functions, max_argument_count):
    return generate_packages(capi_functions, max_argument_count)


def generate_API_packages(api_functions, max_argument_count):
    return generate_packages(api_functions, max_argument_count)


def generate_packages(functions, max_argument_count):
    # TODO: should refactor and reuse the type analysis code in this method and in build_class_definition
    stash = dict()
    for full_function_name in sorted(functions.keys()):
        f = functions[full_function_name]
        check_function_validity(f, max_argument_count)

        package, short_function_name = full_function_name.rsplit('.', 1)
        if (package not in stash):
            stash[package] = PackageDefinition(package)

        func = FunctionDefinition(short_function_name)

        stash[package].functions.append(func)

        arg_list = f.meta.get('fargs')[0]
        arg_dict = f.meta.get('kwarg_types')

        for arg in arg_list:
            arg_def = AttrDefinition(arg, _get_type_string(arg_dict[arg]), _get_collection_type(arg_dict[arg]))
            func.args.append(arg_def)

        func.rtype = AttrDefinition(type_=_get_type_string(f.meta.get('return_type')))

    return _sort_values_by_keys(stash)


def sort_by_name(to):
    return to.name


def render(tos, api_packages, capi_packages, target):
    license_text = _read_file(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools", "change_license",
                     "gig_apache_license_header.tmpl"))
    path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    tmpl = '%s.tmpl' % target
    license_string = licenses.get_license(license_text, target)
    if target == 'typescript':
        tos = sorted([to for to in tos if not to.is_supertype], key=sort_by_name)
    object_factories = sorted({to.super_class for to in tos if to.super_class}, key=sort_by_name)
    # avoid duplicates
    enums = sorted({to.subtype_enum.name: to.subtype_enum for to in object_factories}.values(), key=sort_by_name)
    context = {'DELIMITER': DELIMITER, "LICENSE": license_string, 'tos': tos, 'CS_API_packages': api_packages,
               'SC_API_packages': capi_packages, 'path': path, 'MISSING': MISSING,
               'object_factories': object_factories,
               'enums': enums}
    if target == 'typescript':
        JINJA_ENVIRONMENT.block_start_string = '@%'
        JINJA_ENVIRONMENT.block_end_string = '%@'
        JINJA_ENVIRONMENT.variable_start_string = '@@'
        JINJA_ENVIRONMENT.variable_end_string = '@@'
    jinja_template = JINJA_ENVIRONMENT.get_template(tmpl)
    gen_content = jinja_template.render(context)
    # _write_file(gen_content, "%s.gen.tmp" % os.path.join(os.path.dirname(__file__), target))
    _process_gen_file(gen_content, path)


def _process_gen_file(gen_content, path):
    current_file = None
    current_content = list()
    for line in gen_content.splitlines():
        if line == DELIMITER:
            if current_file:
                _write_file('\n'.join(current_content), current_file)
                current_file = None
                current_content = list()
        elif not current_file:
            if not line:
                continue
            current_file = os.path.join(path, line)
        else:
            current_content.append(line)


def _write_file(content, file_name):
    path = os.path.dirname(file_name)
    if path and not os.path.exists(path):
        os.makedirs(path)
    f = open(file_name, "w")
    try:
        line_sep = os.linesep
        if content[-1] != line_sep:
            content += line_sep
        f.write(content)
    finally:
        f.close()
    print 'Generated %s' % file_name


def _read_file(file_name):
    if not os.path.exists(file_name):
        raise RuntimeError("File '%s' does not exist" % os.path.abspath(file_name))
    f = open(file_name, "r")
    try:
        return f.read()
    finally:
        f.close()


def generate(target, mapping, client_mapping, max_argument_count=1):
    print 'Generating %s' % target
    render(generate_TOs(mapping, client_mapping, max_argument_count),
           generate_API_packages(mapping, max_argument_count),
           generate_CAPI_packages(client_mapping, max_argument_count),
           target)
