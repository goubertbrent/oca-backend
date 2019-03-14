import { DateFormat, FileType, FormComponentType, KeyboardType } from './enums';
import { FormValidator } from './validators.interfaces';

export interface ParagraphComponent {
  type: FormComponentType.PARAGRAPH;
  title?: string | null;
  description?: string | null;
}

export interface BaseInputComponent {
  id: string;
  title: string | null;
  description: string | null;
  validators: FormValidator[];
}

export interface TextInputComponent extends BaseInputComponent {
  type: FormComponentType.TEXT_INPUT;
  placeholder: string | null;
  multiline: boolean;
  keyboard_type: KeyboardType;
  validators: FormValidator[];
}

export const enum NextActionType {
  NEXT = 'next',
  SECTION = 'section',
  SUBMIT = 'submit',
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

export type NextAction = NextActionDefault | NextActionSection | NextActionSubmit;

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

export interface FormSection {
  id?: string;
  title: string;
  description?: string | null;
  components: FormComponent[];
}

export interface CreateDynamicForm {
  title: string;
  sections: FormSection[];
  submission_section: FormSection | null;
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
  value: FormStatisticsFileArray;
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

export interface ComponentStatistics {
  id: string;
  title: string;
  responses: number;
  values: null
    | ValueComponentStatistics
    | ChoicesComponentStatistics
    | FilesComponentStatistics
    | LocationsComponentStatistics
    | DatesComponentStatistics
    | TimesComponentStatistics;
}

export interface SectionStatistics {
  title: string;
  id: string;
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

export interface FormSettings {
  id: number;
  title: string;
  visible: boolean;
  visible_until: string | Date;
  finished: boolean;
  tombola: FormTombola | null;
}

export interface OcaForm<T = DynamicForm> {
  form: T;
  settings: FormSettings;
}

export function isInputComponent(component: FormComponent): component is InputComponents {
  return component.type !== FormComponentType.PARAGRAPH;
}


export function isCreateForm(component: OcaForm<CreateDynamicForm> | OcaForm<DynamicForm>): component is OcaForm<CreateDynamicForm> {
  return (component as any).form.id === undefined;
}
