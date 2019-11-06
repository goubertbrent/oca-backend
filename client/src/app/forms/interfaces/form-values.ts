import { FormComponentType } from './enums';
import { ExternalReference, Value } from './forms';

export interface FieldComponentValue {
  id: string;
}

export interface TextInputComponentValue extends FieldComponentValue {
  type: FormComponentType.TEXT_INPUT;
  value: string;
}

export interface SingleSelectComponentValue extends FieldComponentValue {
  type: FormComponentType.SINGLE_SELECT;
  value: string;
}

export interface MultiSelectComponentValue extends FieldComponentValue {
  type: FormComponentType.MULTI_SELECT;
  values: string[];
}

export interface DatetimeValue {
  day: number;
  month: number;
  year: number;
  hour: number;
  minute: number;
}

export interface DatetimeComponentValue extends FieldComponentValue, DatetimeValue {
  type: FormComponentType.DATETIME;
}

export interface FileComponentValue extends FieldComponentValue {
  type: FormComponentType.FILE;
  value: string;
  name: string;
  file_type: string;
}

export interface PostalAddress {
  country: string | null;
  locality: string | null;
  region: string | null;
  post_office_box_number: string | null;
  postal_code: string | null;
  street_address: string | null;
  address_lines: string[];
}

export interface LocationComponentValue extends FieldComponentValue {
  type: FormComponentType.LOCATION;
  latitude: number;
  longitude: number;
  address: PostalAddress | null;
}


export type FormComponentValue =
  TextInputComponentValue
  | SingleSelectComponentValue
  | MultiSelectComponentValue
  | DatetimeComponentValue
  | FileComponentValue
  | LocationComponentValue;

export interface FormSectionValue {
  id: string;
  components: FormComponentValue[];
}

export interface SingleSelectResponse {
  type: FormComponentType.SINGLE_SELECT;
  value: string;
  choices: Value[];
}

export interface SelectedValue extends Value {
  selected: boolean;
}

export interface MultiSelectResponse {
  type: FormComponentType.MULTI_SELECT;
  choices: SelectedValue[];
}

export interface DatetimeResponse {
  type: FormComponentType.DATETIME;
  date: Date;
  format: string;
}

export interface FileResponse extends FileComponentValue {
  icon: string;
}

export type ComponentResponse =
  TextInputComponentValue
  | SingleSelectResponse
  | MultiSelectResponse
  | DatetimeResponse
  | LocationComponentValue
  | FileResponse;

export interface ResponseFormComponent {
  id: string;
  title: string;
  response: ComponentResponse;
}

export interface ResponseFormSectionValue {
  id: string;
  title: string;
  number: number;
  components: ResponseFormComponent[];
}

export interface MergedFormResponse {
  formId: number;
  submissionId: number;
  sections: ResponseFormSectionValue[];
  submitted_date: string;
  external_reference?: string;
}
