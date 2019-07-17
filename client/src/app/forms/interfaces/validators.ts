import { DatetimeValue } from './form-values';

export enum FormValidatorType {
  REQUIRED = 'required',
  MIN = 'min',
  MAX = 'max',
  MINDATE = 'mindate',
  MAXDATE = 'maxdate',
  MINLENGTH = 'minlength',
  MAXLENGTH = 'maxlength',
  REGEX = 'regex',
}

export interface BaseValidator {
  type: FormValidatorType;
  error_message?: string | null;
}

export interface RequiredValidator extends BaseValidator {
  type: FormValidatorType.REQUIRED;
}

export interface MinValidator extends BaseValidator {
  type: FormValidatorType.MIN;
  value: number;
}

export interface MaxValidator extends BaseValidator {
  type: FormValidatorType.MAX;
  value: number;
}

export interface MinLengthValidator extends BaseValidator {
  type: FormValidatorType.MINLENGTH;
  value: number;
}

export interface MaxLengthValidator extends BaseValidator {
  type: FormValidatorType.MAXLENGTH;
  value: number;
}

export interface MinDateValidator extends BaseValidator, DatetimeValue {
  type: FormValidatorType.MINDATE;
}

export interface MaxDateValidator extends BaseValidator, DatetimeValue {
  type: FormValidatorType.MAXDATE;
}

export type FormValidator =
  RequiredValidator
  | MinValidator
  | MaxValidator
  | MinLengthValidator
  | MaxLengthValidator
  | MinDateValidator
  | MaxDateValidator;

export interface ValidatorType {
  type: Exclude<FormValidatorType, FormValidatorType.REQUIRED>;
  label: string;
  value: number | Date;
  value_label?: string;
}
