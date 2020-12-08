import { DateFormat, FileType, FormComponentType, KeyboardType, OptionType } from './enums';

export interface SelectValue {
  value: string;
  label: string;
}

export const KEYBOARD_TYPES: SelectValue[] = [
  { value: KeyboardType.DEFAULT, label: 'oca.default' },
  { value: KeyboardType.AUTO_CAPITALIZED, label: 'oca.auto_capitalized' },
  { value: KeyboardType.EMAIL, label: 'oca.Email' },
  { value: KeyboardType.URL, label: 'oca.Url' },
  { value: KeyboardType.PHONE, label: 'oca.Phone number' },
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

export const COMPONENT_ICONS: { [key in FormComponentType]: string } = {
  [ FormComponentType.PARAGRAPH ]: 'text_fields',
  [ FormComponentType.TEXT_INPUT ]: 'subject',
  [ FormComponentType.SINGLE_SELECT ]: 'radio_button_unchecked',
  [ FormComponentType.MULTI_SELECT ]: 'check_box',
  [ FormComponentType.DATETIME ]: 'calendar_today',
  [ FormComponentType.FILE ]: 'cloud_upload',
  [ FormComponentType.LOCATION ]: 'my_location',
};

export const COMPONENT_TYPES: ComponentTypeItem[] = [
  { value: FormComponentType.PARAGRAPH, label: 'oca.title_and_description', icon: COMPONENT_ICONS[ FormComponentType.PARAGRAPH ] },
  { value: FormComponentType.TEXT_INPUT, label: 'oca.text_input', icon: COMPONENT_ICONS[ FormComponentType.TEXT_INPUT ] },
  { value: FormComponentType.SINGLE_SELECT, label: 'oca.multiple_choice', icon: COMPONENT_ICONS[ FormComponentType.SINGLE_SELECT ] },
  { value: FormComponentType.MULTI_SELECT, label: 'oca.checkboxes', icon: COMPONENT_ICONS[ FormComponentType.MULTI_SELECT ] },
  { value: FormComponentType.DATETIME, label: 'oca.Date', icon: COMPONENT_ICONS[ FormComponentType.DATETIME ] },
  { value: FormComponentType.FILE, label: 'oca.file_upload', icon: COMPONENT_ICONS[ FormComponentType.FILE ] },
  { value: FormComponentType.LOCATION, label: 'oca.location', icon: COMPONENT_ICONS[ FormComponentType.LOCATION ] },
];

export const DATE_FORMATS: SelectValue[] = [
  { value: DateFormat.DATE, label: 'oca.Date' },
  { value: DateFormat.DATETIME, label: 'oca.datetime' },
  { value: DateFormat.TIME, label: 'oca.Time' },
];

export const FILE_TYPES: SelectValue[] = [
  { value: FileType.DOCUMENT, label: 'oca.document' },
  { value: FileType.PDF, label: 'oca.PDF' },
  { value: FileType.IMAGE, label: 'oca.image' },
  { value: FileType.VIDEO, label: 'oca.video' },
  { value: FileType.AUDIO, label: 'oca.audio' },
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

export const SENSITIVE_INFORMATION_OPTION: OptionsMenuOption = {
  id: OptionType.SENSITIVE_INFORMATION,
  label: 'oca.contains_sensitive_information',
  checked: false,
};
