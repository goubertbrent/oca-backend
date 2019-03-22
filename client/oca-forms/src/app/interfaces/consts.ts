import { DateFormat, FormComponentType, KeyboardType, OptionType } from './enums';

export interface SelectValue {
  value: string;
  label: string;
}

export const KEYBOARD_TYPES: SelectValue[] = [
  { value: KeyboardType.DEFAULT, label: 'oca.default' },
  { value: KeyboardType.AUTO_CAPITALIZED, label: 'oca.auto_capitalized' },
  { value: KeyboardType.EMAIL, label: 'oca.email' },
  { value: KeyboardType.URL, label: 'oca.url' },
  { value: KeyboardType.PHONE, label: 'oca.phone_number' },
  { value: KeyboardType.NUMBER, label: 'oca.number' },
  { value: KeyboardType.DECIMAL, label: 'oca.decimal' },
  { value: KeyboardType.PASSWORD, label: 'oca.password' },
  { value: KeyboardType.NUMBER_PASSWORD, label: 'oca.number_password' },
];

export interface ComponentTypeItem {
  value: FormComponentType;
  label: string;
  icon: string;
}

export const COMPONENT_TYPES: ComponentTypeItem[] = [
  { value: FormComponentType.PARAGRAPH, label: 'oca.title_and_description', icon: 'text_fields' },
  { value: FormComponentType.TEXT_INPUT, label: 'oca.text_input', icon: 'subject' },
  { value: FormComponentType.SINGLE_SELECT, label: 'oca.multiple_choice', icon: 'radio_button_unchecked' },
  { value: FormComponentType.MULTI_SELECT, label: 'oca.checkboxes', icon: 'check_box' },
  // { value: FormComponentType.DATETIME, label: 'oca.date', icon: 'calendar_today' },
  // { value: FormComponentType.FILE, label: 'oca.file_upload', icon: 'cloud_upload' },
  // { value: FormComponentType.LOCATION, label: 'oca.location', icon: 'my_location' },
];

export const DATE_FORMATS: SelectValue[] = [
  { value: DateFormat.DATE, label: 'oca.date' },
  { value: DateFormat.DATETIME, label: 'oca.datetime' },
  { value: DateFormat.TIME, label: 'oca.time' },
];

export interface OptionsMenuOption {
  id: OptionType;
  label: string;
  checked: boolean;
}

export const SHOW_DESCRIPTION_OPTION: OptionsMenuOption = {
  id: OptionType.SHOW_DESCRIPTION,
  label: 'oca.description',
  checked: false,
};
export const VALIDATION_OPTION: OptionsMenuOption = {
  id: OptionType.ENABLE_VALIDATION,
  label: 'oca.response_validation',
  checked: false,
};
export const GOTO_SECTION_OPTION: OptionsMenuOption = {
  id: OptionType.GOTO_SECTION_BASED_ON_ANSWER,
  label: 'oca.go_to_section_based_on_answer',
  checked: false,
};

export const DELETE_ALL_RESPONSES_OPTION: OptionsMenuOption = {
  id: OptionType.DELETE_ALL_RESPONSES,
  label: 'oca.delete_all_responses',
  checked: false,
};
