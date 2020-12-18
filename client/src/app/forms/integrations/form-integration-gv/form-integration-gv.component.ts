import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import { FormComponentType } from '../../interfaces/enums';
import { FormSection, InputComponents, Value } from '../../interfaces/forms';
import { GVComponentMapping, GvFieldType, GVIntegrationFormConfig, GVSectionMapping } from '../integrations';

interface ValueLabel {
  value: string;
  label: string;
}

@Component({
  selector: 'oca-form-integration-gv',
  templateUrl: './form-integration-gv.component.html',
  styleUrls: [ './form-integration-gv.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormIntegrationGVComponent implements OnChanges {
  @Input() configuration: GVIntegrationFormConfig;
  @Input() sections: FormSection[];
  @Output() configurationChanged = new EventEmitter<GVIntegrationFormConfig>();

  GvFieldType = GvFieldType;

  componentMapping: {
    [ key: string ]: GVComponentMapping[];
  } = {};

  /**
   * Mapping between field type and possible components, per section
   * For example, For a field of type 'location', the user will only have the option to select 'location' components
   */
  componentChoices: {
    // keys: section ids
    [ key: string ]: {
      [key in Exclude<GvFieldType, GvFieldType.CONST>]: InputComponents[];
    };
  };

  formComponentValues: { [ key: string ]: { [ key: string ]: Value[] } } = {};

  mappingTypes = [
    { type: GvFieldType.FIELD, label: 'oca.field' },
    { type: GvFieldType.FLEX, label: 'oca.custom_field' },
    { type: GvFieldType.CONST, label: 'oca.constant' },
    { type: GvFieldType.ATTACHMENT, label: 'oca.Attachment' },
    { type: GvFieldType.LOCATION, label: 'oca.location' },
    { type: GvFieldType.PERSON, label: 'oca.person' },
    { type: GvFieldType.CONSENT, label: 'oca.user_consent' },
  ];

  fieldOptions: ValueLabel[] = [
    { value: 'subject', label: 'oca.subject' },
    { value: 'description', label: 'oca.description' },
    { value: 'type_id', label: 'oca.case_type' },
  ];

  personOptions: ValueLabel[] = [
    { value: 'contact', label: 'oca.contact' },
    { value: 'address', label: 'oca.address' },
    { value: 'identity_number', label: 'oca.identity_number' },
    { value: 'first_name', label: 'oca.first_name' },
    { value: 'family_name', label: 'oca.family_name' },
    { value: 'gender', label: 'oca.gender' },
    { value: 'date_of_birth', label: 'oca.date_of_birth' },
    { value: 'place_of_birth', label: 'oca.place_of_birth' },
    { value: 'nationality', label: 'oca.nationality' },
  ];

  personSubOptions: { contact: ValueLabel[], address: ValueLabel[] } = {
    contact: [
      { value: 'title', label: 'oca.title' },
      { value: 'nickname', label: 'oca.nickname' },
      { value: 'phone_number', label: 'oca.Phone number' },
      { value: 'mobile_number', label: 'oca.mobile_number' },
      { value: 'email', label: 'oca.Email' },
      { value: 'website', label: 'oca.Website' },
      { value: 'fax', label: 'oca.fax' },
    ],
    address: [
      { value: 'street_name', label: 'oca.street_name' },
      { value: 'house_number', label: 'oca.house_number' },
      { value: 'zip_code', label: 'oca.zip_code' },
      { value: 'city', label: 'oca.city' },
      { value: 'country', label: 'oca.country' },
    ],
  };

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.configuration && this.configuration) {
      for (const section of this.configuration.mapping) {
        this.componentMapping[ section.id ] = section.components;
      }
    }
    if (this.configuration && this.sections) {
      this.componentChoices = {};
      for (const section of this.sections) {
        this.formComponentValues[ section.id ] = {};
        const choices: { [key in Exclude<GvFieldType, GvFieldType.CONST>]: InputComponents[] } = {
          [ GvFieldType.LOCATION ]: [],
          [ GvFieldType.PERSON ]: [],
          [ GvFieldType.ATTACHMENT ]: [],
          [ GvFieldType.FLEX ]: [],
          [ GvFieldType.FIELD ]: [],
          [ GvFieldType.CONSENT ]: [],
        };
        for (const component of section.components) {
          switch (component.type) {
            case FormComponentType.PARAGRAPH:
              break;
            case FormComponentType.TEXT_INPUT:
            case FormComponentType.SINGLE_SELECT:
              choices[ GvFieldType.FIELD ].push(component);
              choices[ GvFieldType.FLEX ].push(component);
              choices[ GvFieldType.PERSON ].push(component);
              choices[ GvFieldType.CONSENT ].push(component);
              break;
            case FormComponentType.MULTI_SELECT:
              choices[ GvFieldType.FIELD ].push(component);
              choices[ GvFieldType.FLEX ].push(component);
              choices[ GvFieldType.CONSENT ].push(component);
              break;
            case FormComponentType.DATETIME:
              break;
            case FormComponentType.LOCATION:
              choices[ GvFieldType.LOCATION ].push(component);
              break;
            case FormComponentType.FILE:
              choices[ GvFieldType.ATTACHMENT ].push(component);
              break;
            default:
              throw Error(`Unhandled component ${component}`);
          }
          if (component.type === FormComponentType.SINGLE_SELECT || component.type === FormComponentType.MULTI_SELECT) {
            this.formComponentValues[ section.id ][ component.id ] = component.choices;
          }
        }
        this.componentChoices[ section.id ] = choices;
      }
    }
  }

  addMapping(section: FormSection) {
    if (!(section.id in this.componentMapping)) {
      this.componentMapping[ section.id ] = [];
    }
    this.componentMapping[ section.id ].push({
      type: GvFieldType.CONST,
      field: '',
      value: '',
      display_value: null,
    });
    this.markChanged();
  }

  removeMapping(section: FormSection, mapping: GVComponentMapping) {
    this.componentMapping[ section.id ] = this.componentMapping[ section.id ].filter(m => m !== mapping);
    this.markChanged();
  }

  markChanged() {
    const mapping: GVSectionMapping[] = Object.keys(this.componentMapping).map(sectionId => ({
      id: sectionId,
      components: this.componentMapping[ sectionId ],
    }));
    const updatedConfig: GVIntegrationFormConfig = { ...this.configuration, mapping };
    this.configurationChanged.emit(updatedConfig);
  }

  trackValueLabel(index: number, v: ValueLabel) {
    return v.value;
  }

  trackSections(index: number, section: FormSection) {
    return section.id;
  }

  trackComponentChoices(index: number, component: InputComponents) {
    return component.id;
  }
}
