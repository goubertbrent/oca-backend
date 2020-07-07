export enum FormIntegrationProvider {
  GREEN_VALLEY = 'green_valley',
  EMAIL = 'email',
}

export interface GVIntegrationConfig {
}

export interface EmailIntegrationConfig {
}

export interface BaseIntegrationConfiguration {
  enabled: boolean;
  visible: boolean;
}

export interface IntegrationConfigurationGV extends BaseIntegrationConfiguration {
  provider: FormIntegrationProvider.GREEN_VALLEY;
  configuration: GVIntegrationConfig;
}

export interface IntegrationConfigurationEmail extends BaseIntegrationConfiguration {
  provider: FormIntegrationProvider.EMAIL;
  configuration: EmailIntegrationConfig;
}

export type FormIntegrationConfiguration = IntegrationConfigurationGV | IntegrationConfigurationEmail;

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

export interface FormIntegrationGreenValley extends BaseIntegration {
  provider: FormIntegrationProvider.GREEN_VALLEY;
  configuration: GVIntegrationFormConfig;
}

export interface FormIntegrationEmail extends BaseIntegration {
  provider: FormIntegrationProvider.EMAIL;
  configuration: EmailIntegrationFormConfig;
}

export type FormIntegration = FormIntegrationGreenValley | FormIntegrationEmail;
