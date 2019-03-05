import { DateFormat, FileType, FormComponentType, KeyboardType, LocationMode } from './enums';
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
  options: LocationMode[];
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

export type FormStatisticsArray = [ string, string, string ];
export type FormStatisticsValue = FormStatisticsNumber | FormStatisticsArray;

export interface FormStatistics {
  submissions: number;
  statistics: {
    [ key: string ]: {
      [ key: string ]: FormStatisticsValue;
    };
  };
}

export interface FormTombola {
  winner_message: string;
  winner_count: number;
}

export interface FormSettings {
  id: number;
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
