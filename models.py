# pylint: disable=line-too-long
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import importlib
import json
import sys
import traceback

import markdown
import six

from deepdiff import DeepDiff

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.safestring import mark_safe

from passive_data_kit.models import DataGeneratorDefinition, DataPoint

def update_definition_primitive(definition, value, path): # pylint: disable=too-many-branches
    if path.endswith('[]'):
        clean_path = path[:-2]

        existing_list = definition.get(clean_path, {}).get('observed', [])

        if (value in existing_list) is False:
            if isinstance(value, (float, int, six.string_types)):
                existing_list.append(value)
            else:
                existing_list.append('Unknown type: %s' % value)

            definition[clean_path]['observed'] = existing_list

        return

    if isinstance(value, float) and ('real' in definition[path]['types']) is False:
        definition[path]['types'].append('real')
    elif isinstance(value, int) and ('integer' in definition[path]['types']) is False:
        definition[path]['types'].append('integer')
    if isinstance(value, six.string_types) and ('string' in definition[path]['types']) is False:
        definition[path]['types'].append('string')

    if isinstance(value, (int, float)) and (('real' in definition[path]['types']) or ('integer' in definition[path]['types'])):
        if ('range' in definition[path]) is False:
            definition[path]['range'] = [value, value]
        else:
            if value < definition[path]['range'][0]:
                definition[path]['range'][0] = value

            if value > definition[path]['range'][1]:
                definition[path]['range'][1] = value

    if isinstance(value, six.string_types) and ('string' in definition[path]['types']):
        if ('observed' in definition[path]) is False:
            definition[path]['observed'] = []

        if ('is_freetext' in definition[path]) and definition[path]['is_freetext']:
            pass # Freetext - no need to enumerate values
        else:
            if (value in definition[path]['observed']) is False:
                definition[path]['observed'].append(value)


def update_definition(definition, element, prefix=None): # pylint: disable=too-many-branches
    for key in element:
        value = element[key]

        path = key

        if prefix is not None:
            path = prefix + key

        if (path in definition) is False:
            definition[path] = {}

        existing_def = definition[path]

        if ('types' in existing_def) is False:
            existing_def['types'] = []

        if ('pdk_variable_name' in existing_def) is False:
            existing_def['pdk_variable_name'] = 'Unknown (TODO)'

        if ('pdk_variable_description' in existing_def) is False:
            existing_def['pdk_variable_description'] = 'Unknown (TODO)'

        if isinstance(value, dict):
            if ('object' in existing_def['types']) is False:
                existing_def['types'].append('object')

            update_definition(definition, value, prefix=(path + '.')) # pylint: disable=superfluous-parens
        elif isinstance(value, list):
            if ('list' in existing_def['types']) is False:
                existing_def['types'].append('list')

            for item in value:
                if isinstance(item, (float, int, six.string_types)):
                    update_definition_primitive(definition, item, path + '[]')
                elif isinstance(item, dict):
                    update_definition(definition, item, prefix=(path + '[].')) # pylint: disable=superfluous-parens
                elif isinstance(item, list):
                    print('LIST WITHIN LIST[{}]: {} ({})'.format(path, item, type(item)))
                else:
                    print('UKNKOWN IN LIST[{}]: {} ({})'.format(path, item, type(item)))

        elif isinstance(value, (float, int, six.string_types)):
            update_definition_primitive(definition, value, path)
        else:
            print('UNKNOWN ITEM[{}]: {}'.format(path, value))


class DataPointType(models.Model):
    generator = models.CharField(max_length=1024, unique=True)
    name = models.CharField(max_length=1024, null=True, blank=True)
    category = models.CharField(max_length=1024, null=True, blank=True)

    enabled = models.BooleanField(default=True)

    description = models.TextField(max_length=67108864, default='{}')

    definition = models.TextField(max_length=67108864, default='{}')

    first_seen = models.DateTimeField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    def markdown(self):
        return mark_safe(markdown.markdown(self.description)) # nosec

    def get_absolute_url(self):
        return reverse('pdk_codebook_page', args=[self.generator])

    def update_definition(self, sample=0, override_existing=False): # pylint: disable=unused-argument, too-many-locals, too-many-branches, too-many-statements
        definition = json.loads(self.definition)

        data_generator = DataGeneratorDefinition.definition_for_identifier(self.generator)

        point_query = DataPoint.objects.filter(generator_definition=data_generator).order_by('created')

        if sample > 0:
            point_query = point_query[:sample]

        min_date = None
        max_date = None

        point_count = point_query.count()

        point_index = 0

        while point_index < point_count:
            for point in point_query[point_index:(point_index + 250)]:
                point_def = point.fetch_properties()

                if 'passive-data-metadata' in point_def and 'generator-id' in point_def['passive-data-metadata']:
                    update_definition(definition, point_def)

                    if min_date is None or point.created < min_date:
                        min_date = point.created

                    if max_date is None or point.created > min_date:
                        max_date = point.created
                else:
                    print('[Error] Point pk=' + str(point.pk) + ' missing basic PDK metadata.')

            point_index += 250

        original_definition = json.loads(self.definition)

        for app in settings.INSTALLED_APPS:
            try:
                pdk_api = importlib.import_module(app + '.pdk_api')

                if 'passive-data-metadata.generator-id' in definition:
                    pdk_api.update_data_type_definition(definition, override_existing=override_existing)
                else:
                    print('[Error] Definition missing basic PDK metadata: ' + json.dumps(definition, indent=2))
            except ImportError:
                pass
            except AttributeError:
                pass
            except TypeError:
                print('Error updating data type (%s):' % app)

                traceback.print_exc()
            except: #pylint: disable=bare-except
                traceback.print_exc()

        for app in settings.INSTALLED_APPS:
            try:
                pdk_api = importlib.import_module(app + '.pdk_api')

                if 'passive-data-metadata.generator-id' in definition:
                    name = pdk_api.data_type_name(definition)

                    if name is not None:
                        self.name = name
            except ImportError:
                pass
            except AttributeError:
                pass
            except TypeError:
                print('Error updating data type (%s):' % app)

                traceback.print_exc()
            except: #pylint: disable=bare-except
                traceback.print_exc()

        for app in settings.INSTALLED_APPS:
            try:
                pdk_api = importlib.import_module(app + '.pdk_api')

                if 'passive-data-metadata.generator-id' in definition:
                    category = pdk_api.data_type_category_for_identifier(definition['passive-data-metadata.generator-id'])

                    if category is not None:
                        self.category = category
            except ImportError:
                pass
            except AttributeError:
                pass
            except TypeError:
                print('Error updating data type (%s):' % app)

                traceback.print_exc()
            except: #pylint: disable=bare-except
                traceback.print_exc()

        if 'pdk_description' in definition:
            self.description = definition.get('pdk_description', '')

            del definition['pdk_description']

        diff = DeepDiff(original_definition, definition)

        # print(self.generator + ': ' + json.dumps(definition, indent=2))

        to_delete = []

        python_version = sys.version_info[0]

        if 'type_changes' in diff:
            for key in diff['type_changes']:
                if python_version >= 3:
                    if diff['type_changes'][key]['new_type'] == str and diff['type_changes'][key]['old_type'] == unicode: # pylint: disable=undefined-variable
                        to_delete.append(key)
                    elif diff['type_changes'][key]['new_type'] == unicode and diff['type_changes'][key]['old_type'] == str: # pylint: disable=undefined-variable
                        to_delete.append(key)

        for key in to_delete:
            del diff['type_changes'][key]

        # print(diff)

        self.definition = json.dumps(definition, indent=2)

        if min_date is None:
            pass
        elif self.first_seen is None:
            self.first_seen = min_date
        elif min_date < self.first_seen:
            self.first_seen = min_date

        if max_date is None:
            pass
        elif self.last_seen is None:
            self.last_seen = max_date
        elif max_date < self.last_seen:
            self.last_seen = max_date

        self.save()

    def ordered_variables(self):
        definition = json.loads(self.definition)

        ordered_variables = []
        unordered_variables = []

        for key in definition:
            variable = definition[key]

            variable['pdk_codebook_json'] = json.dumps(variable, indent=2)

            variable['pdk_codebook_key'] = key

            if 'order' in variable:
                ordered_variables.append(variable)
            else:
                unordered_variables.append(variable)

        ordered_variables.sort(key=lambda variable: variable['order'])

        unordered_variables.sort(key=lambda variable: variable['pdk_variable_name'])

        ordered_variables.extend(unordered_variables)

        return ordered_variables

    def variable_groups(self):
        definition = json.loads(self.definition)

        group_names = []

        groups = {
            'Other Variables': []
        }

        for key in definition:
            variable = definition[key]

            variable['pdk_codebook_json'] = json.dumps(variable, indent=2)

            variable['pdk_codebook_key'] = key

            if 'pdk_codebook_group' in variable:
                if (variable['pdk_codebook_group'] in groups) is False:
                    groups[variable['pdk_codebook_group']] = []
                    group_names.append(variable['pdk_codebook_group'])

                groups[variable['pdk_codebook_group']].append(variable)
            else:
                groups['Other Variables'].append(variable)

        group_names.sort()

        group_names.append('Other Variables')

        sorted_list = []

        for name in group_names:
            if groups[name]:
                groups[name].sort(key=lambda variable: variable.get('pdk_codebook_order', sys.maxsize))

                sorted_list.append((name, groups[name]))

        return sorted_list
