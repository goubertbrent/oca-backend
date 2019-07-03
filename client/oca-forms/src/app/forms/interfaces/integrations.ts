export enum FormIntegrationProvider {
  GREEN_VALLEY = 'green_valley',
}

export interface GVIntegrationConfig {
  username: string;
  password: string;
  base_url: string;
}

export interface IntegrationConfigurationGV {
  provider: FormIntegrationProvider.GREEN_VALLEY;
  enabled: boolean;
  configuration: GVIntegrationConfig;
}

export type FormIntegrationConfiguration = IntegrationConfigurationGV;

export enum GvFieldType {
  FIELD = 'field',
  CONST = 'const',
  FLEX = 'flex',
  LOCATION = 'location',
  ATTACHMENT = 'attachment',
  PERSON = 'person',
}

export interface GVMappingField {
  type: GvFieldType.FIELD;
  id: string;
  field: string;
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

export type GVComponentMapping =
  GVMappingField
  | GVMappingConst
  | GVMappingFlex
  | GVMappingLocation
  | GVMappingAttachment
  | GVMappingPerson;

export interface GVSectionMapping {
  id: string;
  components: GVComponentMapping[];
}

export interface BaseIntegration {
  provider: FormIntegrationProvider;
  enabled: boolean;
}

export interface GVIntegrationFormConfig {
  type_id: string | null;
  mapping: GVSectionMapping[];
}

export interface FormIntegrationGreenValley extends BaseIntegration {
  provider: FormIntegrationProvider.GREEN_VALLEY;
  configuration: GVIntegrationFormConfig;
}

export type FormIntegration = FormIntegrationGreenValley;
