import { DateFormat, FileType, FormComponentType, KeyboardType } from './enums';
import { FormSectionValue, MergedFormResponse } from './form-values';
import { FormIntegration } from '../integrations/integrations';
import { FormValidator } from './validators';

// TODO: most of these can be replaced by types from @oca/web-shared, but the minor differences might make that difficult.

export interface ParagraphComponent {
  type: FormComponentType.PARAGRAPH;
  title?: string | null;
  description?: string | null;
}

export interface BaseInputComponent {
  id: string;
  title: string;
  description: string | null;
  validators: FormValidator[];
  sensitive: boolean;
}

export interface TextInputComponent extends BaseInputComponent {
  type: FormComponentType.TEXT_INPUT;
  placeholder: string | null;
  multiline: boolean;
  keyboard_type: KeyboardType;
  validators: FormValidator[];
}

export enum NextActionType {
  NEXT = 'next',
  SECTION = 'section',
  SUBMIT = 'submit',
  URL = 'url',
}

export interface NextActionDefault {
  type: NextActionType.NEXT;
}

export interface NextActionSection {
  type: NextActionType.SECTION;
  section: string;
}

export interface NextActionSubmit {
  type: NextActionType.SUBMIT;
}

export interface NextActionURL {
  type: NextActionType.URL;
  url: string;
}

export type NextAction = NextActionDefault | NextActionSection | NextActionSubmit | NextActionURL;

export interface UINextAction {
  action: NextAction;
  label: string;
}

export interface Value {
  value: string;
  label: string;
  image_url?: string | null;
  next_action?: NextAction | null;
}

export interface SingleSelectComponent extends BaseInputComponent {
  type: FormComponentType.SINGLE_SELECT;
  choices: Value[];
}

export interface MultiSelectComponent extends BaseInputComponent {
  type: FormComponentType.MULTI_SELECT;
  choices: Value[];
}

export interface DatetimeComponent extends BaseInputComponent {
  type: FormComponentType.DATETIME;
  format: DateFormat;
}

export interface LocationComponent extends BaseInputComponent {
  type: FormComponentType.LOCATION;
}

export interface FileComponent extends BaseInputComponent {
  type: FormComponentType.FILE;
  file_types: FileType[];
}

export type InputComponents =
  TextInputComponent
  | SingleSelectComponent
  | MultiSelectComponent
  | DatetimeComponent
  | LocationComponent
  | FileComponent;

export type FormComponent = ParagraphComponent | InputComponents;

export interface SectionBranding {
  logo_url: string;
  avatar_url: string | null;
}

export interface SubmissionSection {
  title: string;
  description?: string | null;
  components: FormComponent[];
  branding: SectionBranding | null;
  next_button_caption?: string | null;
}

export interface FormSection extends SubmissionSection {
  id: string;
  next_action: NextAction | null;
}

export interface CreateDynamicForm {
  title: string;
  sections: FormSection[];
  submission_section: SubmissionSection | null;
  max_submissions: number;
}


export interface DynamicForm extends CreateDynamicForm {
  id: number;
  version: number;
}

export interface FormStatisticsNumber {
  [ key: string ]: number;
}

export type FormStatisticsFileArray = [ string, string, string ][];
export type FormStatisticsLocationArray = [ number, number ][];
export type FormStatisticsValue = FormStatisticsNumber | FormStatisticsFileArray | FormStatisticsLocationArray;

export function isFormStatisticsNumber(value: FormStatisticsValue): value is FormStatisticsNumber {
  return !Array.isArray(value);
}

export function isFormStatisticsLocationArray(value: FormStatisticsValue): value is FormStatisticsLocationArray {
  return Array.isArray(value) && value.length > 0 && value[ 0 ].length === 2;
}

export interface FormStatistics {
  submissions: number;
  statistics: {
    [ key: string ]: {
      [ key: string ]: FormStatisticsValue;
    };
  };
}

export enum ComponentStatsType {
  VALUES,
  CHOICES,
  FILES,
  LOCATIONS,
  DATES,
  TIMES,
}

export interface ValueComponentStatistics {
  type: ComponentStatsType.VALUES;
  value: ValueAmount[];
}

export interface ValueAmount {
  value: string;
  amount: number;
}

export interface ChoicesComponentStatistics {
  type: ComponentStatsType.CHOICES;
  value: ValueAmount[];
}

export interface FilesComponentStatistics {
  type: ComponentStatsType.FILES;
  value: {
    url: string;
    icon: string;
    fileName: string;
  }[];
}

export interface LocationsComponentStatistics {
  type: ComponentStatsType.LOCATIONS;
  value: {
    lat: number;
    lng: number;
  }[];
}

export interface DatesComponentStatistics {
  type: ComponentStatsType.DATES;
  value: {
    value: Date | null;
    amount: number;
  }[];
  format: string;
}

export interface TimesComponentStatistics {
  type: ComponentStatsType.TIMES;
  value: {
    value: Date | null;
    amount: number;
  }[];
  format: string;
}

export type ComponentStatisticsValues = null
  | ValueComponentStatistics
  | ChoicesComponentStatistics
  | FilesComponentStatistics
  | LocationsComponentStatistics
  | DatesComponentStatistics
  | TimesComponentStatistics;

export interface ComponentStatistics {
  id: string;
  title: string;
  hasResponses: boolean;
  sensitive: boolean;
  values: ComponentStatisticsValues;
}

export interface SectionStatistics {
  title: string;
  id: string;
  number: number;
  components: ComponentStatistics[];
}

export interface FormStatisticsView {
  submissions: number;
  sections: SectionStatistics [];
}

export interface FormTombola {
  winner_message: string;
  winner_count: number;
}

export const enum CompletedFormStepType {
  CONTENT = 'content',
  TEST = 'test',
  SETTINGS = 'settings',
  ACTION = 'action',
  LAUNCH = 'launch',
  INTEGRATIONS = 'integrations',
}

export const COMPLETED_STEP_MAPPING = [
  CompletedFormStepType.CONTENT,
  CompletedFormStepType.TEST,
  CompletedFormStepType.SETTINGS,
  CompletedFormStepType.ACTION,
  CompletedFormStepType.LAUNCH,
  CompletedFormStepType.INTEGRATIONS,
];

export interface CompletedFormStep {
  step_id: CompletedFormStepType;
}

export interface FormSettings {
  id: number;
  title: string;
  visible: boolean;
  visible_until: string | Date | null;
  finished: boolean;
  tombola: FormTombola | null;
  steps: CompletedFormStep[];
  integrations: FormIntegration[];
}

export interface OcaForm<T = DynamicForm> {
  form: T;
  settings: FormSettings;
}

export interface SaveForm {
  data: OcaForm;
  silent?: boolean;
}

export function isInputComponent(component: FormComponent): component is InputComponents {
  return component.type !== FormComponentType.PARAGRAPH;
}

export interface LoadResponses {
  formId: number;
  cursor?: string;
  page_size: number;
}

export interface ExternalReference {
  id: string;
  url: string;
}

export interface FormResponse {
  id: number;
  sections: FormSectionValue[];
  submitted_date: string;
  external_reference?: string;
  version: number;
}

export interface SingleFormResponse {
  cursor: string | null;
  result: MergedFormResponse;
  previous: number | null;
  next: number | null;
  more: boolean;
}


export interface FormResponses {
  cursor: string | null;
  results: FormResponse[];
  more: boolean;
}

export interface DownloadResponses {
  url: string;
}
