import { FormComponentType } from '../interfaces/enums';

export enum FormIntegrationProvider {
  EMAIL = 'email',
  GREEN_VALLEY = 'green_valley',
  TOPDESK = 'topdesk',
}

// tslint:disable-next-line:no-empty-interface
export interface GVIntegrationConfig {
}

// tslint:disable-next-line:no-empty-interface
export interface EmailIntegrationConfig {
}

// tslint:disable-next-line:no-empty-interface
export interface TOPDeskIntegrationConfig {
}

export interface BaseIntegrationConfiguration {
  enabled: boolean;
  can_edit: boolean;
}

export interface IntegrationConfigurationGV extends BaseIntegrationConfiguration {
  provider: FormIntegrationProvider.GREEN_VALLEY;
  configuration: GVIntegrationConfig;
}

export interface IntegrationConfigurationEmail extends BaseIntegrationConfiguration {
  provider: FormIntegrationProvider.EMAIL;
  configuration: EmailIntegrationConfig;
}

export interface IntegrationConfigurationTOPDesk extends BaseIntegrationConfiguration {
  provider: FormIntegrationProvider.TOPDESK;
  configuration: TOPDeskIntegrationConfig;
}

export type FormIntegrationConfiguration = IntegrationConfigurationGV | IntegrationConfigurationEmail | IntegrationConfigurationTOPDesk;

export enum GvFieldType {
  FIELD = 'field',
  CONST = 'const',
  FLEX = 'flex',
  LOCATION = 'location',
  ATTACHMENT = 'attachment',
  PERSON = 'person',
  CONSENT = 'consent',
}

export interface GVMappingField {
  type: GvFieldType.FIELD;
  id: string;
  field: string;
  value: string | null;
}

export interface GVMappingConst {
  type: GvFieldType.CONST;
  field: string;
  value: string;
  display_value: string | null;
}

export interface GVMappingFlex {
  type: GvFieldType.FLEX;
  id: string;
  field_def_id: string;
}

export interface GVMappingLocation {
  type: GvFieldType.LOCATION;
  id: string;
  coordinates: string;
  address: string;
  location_type: string;
  location_type_value: string;
}

export interface GVMappingAttachment {
  type: GvFieldType.ATTACHMENT;
  id: string;
  name: string;
  field_def_id: string;
}

export interface GVMappingPerson {
  type: GvFieldType.PERSON;
  id: string;
  field: string;
  sub_field: string;
}

export interface GVMappingConsent {
  type: GvFieldType.CONSENT;
  id: string;
  value_id: string;
}

export type GVComponentMapping =
  GVMappingField
  | GVMappingConst
  | GVMappingFlex
  | GVMappingLocation
  | GVMappingAttachment
  | GVMappingPerson
  | GVMappingConsent;

export interface GVSectionMapping {
  id: string;
  components: GVComponentMapping[];
}

export interface BaseIntegration {
  provider: FormIntegrationProvider;
  enabled: boolean;
  visible: boolean;
}

export interface GVIntegrationFormConfig {
  type_id: string | null;
  mapping: GVSectionMapping[];
}

export interface EmailComponentMapping {
  section_id: string;
  component_id: string;
  component_value: string;
  group_id: number;
}

export interface EmailGroup {
  id: number;
  name: string;
  emails: string[];
}

export interface EmailIntegrationFormConfig {
  email_groups: EmailGroup[];
  default_group: number | null;
  mapping: EmailComponentMapping[];
}

export enum TOPDeskPropertyName {
  BRIEF_DESCRIPTION = 'briefDescription',
  REQUEST = 'request',
  CALL_TYPE = 'callType',
  CATEGORY = 'category',
  SUBCATEGORY = 'subcategory',
  BRANCH = 'branch',
  ENTRY_TYPE = 'entryType',
  LOCATION = 'location',
  OPERATOR = 'operator',
  OPERATOR_GROUP = 'operatorGroup',
  OPTIONAL_FIELDS_1 = 'optionalFields1',
  OPTIONAL_FIELDS_2 = 'optionalFields2',
}

export const TOPDeskOptionalFields = [
  'text1',
  'text2',
  'text3',
  'text4',
  'text5',
  'number1',
  'number2',
  'number3',
  'number4',
  'number5',
  'date1',
  'date2',
  'date3',
  'date4',
  'date5',
  'boolean1',
  'boolean2',
  'boolean3',
  'boolean4',
  'boolean5',
  'memo1',
  'memo2',
  'memo3',
  'memo4',
  'memo5',
] as const;

export type TOPDeskOptionalField = typeof TOPDeskOptionalFields[number];

export interface TOPDeskBaseComponentMapping {
  /**
   * Component id
   */
  id: string;
}

export interface TOPDeskCategoryMapping extends TOPDeskBaseComponentMapping {
  type: TOPDeskPropertyName.CATEGORY;
  categories: {
    /**
     * key: component id, value: topdesk category id
     */
    [ key: string ]: string;
  };
}

export interface TOPDeskSubCategoryMapping extends TOPDeskBaseComponentMapping {
  type: TOPDeskPropertyName.SUBCATEGORY;
  subcategories: {
    /**
     * key: component id, value: topdesk sub category id
     */
    [ key: string ]: string;
  };
}

export interface TOPDeskBriefDescriptionMapping extends TOPDeskBaseComponentMapping {
  type: TOPDeskPropertyName.BRIEF_DESCRIPTION;
}

export const enum OptionalFieldLocationFormat {
  LATITUDE,
  LONGITUDE,
  LATITUDE_LONGITUDE,
}

export interface OptionalFieldsOptions {
  type: FormComponentType.LOCATION;
  format: OptionalFieldLocationFormat;
}

export interface TOPDeskOptionalFieldsMapping extends TOPDeskBaseComponentMapping {
  field: TOPDeskOptionalField;
  options: OptionalFieldsOptions;
}

export interface TOPDeskOptionalField1Mapping extends TOPDeskOptionalFieldsMapping {
  type: TOPDeskPropertyName.OPTIONAL_FIELDS_1;
}

export interface TOPDeskOptionalField2Mapping extends TOPDeskOptionalFieldsMapping {
  type: TOPDeskPropertyName.OPTIONAL_FIELDS_2;
}

export type TOPDeskComponentMapping =
  TOPDeskCategoryMapping
  | TOPDeskSubCategoryMapping
  | TOPDeskBriefDescriptionMapping
  | TOPDeskOptionalField1Mapping
  | TOPDeskOptionalField2Mapping;

export type TOPDeskSupportedMappingTypes = TOPDeskComponentMapping['type'];

export interface TOPDeskSectionMapping {
  id: string;
  components: TOPDeskComponentMapping[];
}

export interface TOPDeskIntegrationFormConfig {
  mapping: TOPDeskSectionMapping[];
}

export interface FormIntegrationGreenValley extends BaseIntegration {
  provider: FormIntegrationProvider.GREEN_VALLEY;
  configuration: GVIntegrationFormConfig;
}

export interface FormIntegrationEmail extends BaseIntegration {
  provider: FormIntegrationProvider.EMAIL;
  configuration: EmailIntegrationFormConfig;
}

export interface FormIntegrationTOPDesk extends BaseIntegration {
  provider: FormIntegrationProvider.TOPDESK;
  configuration: TOPDeskIntegrationFormConfig;
}

export type FormIntegration = FormIntegrationGreenValley | FormIntegrationEmail | FormIntegrationTOPDesk;

export interface TOPDeskCategory {
  id: string;
  name: string;
}

export interface TOPDeskSubCategory extends TOPDeskCategory {
  subcategories: TOPDeskCategory[];
}
