import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { ControlContainer, NgForm } from '@angular/forms';
import { MatSelectChange } from '@angular/material/select';
import { TranslateService } from '@ngx-translate/core';
import { EASYMDE_OPTIONS } from '../../../../environments/config';
import {
  ComponentTypeItem,
  COMPONENT_TYPES,
  DATE_FORMATS,
  FILE_TYPES,
  GOTO_SECTION_OPTION,
  KEYBOARD_TYPES,
  OptionsMenuOption,
  SENSITIVE_INFORMATION_OPTION,
  SHOW_DESCRIPTION_OPTION,
  VALIDATION_OPTION,
} from '../../interfaces/consts';
import { DateFormat, FormComponentType, KeyboardType, OptionType } from '../../interfaces/enums';
import { FormComponent, isInputComponent, SingleSelectComponent, UINextAction } from '../../interfaces/forms';
import { FormValidator, FormValidatorType, ValidatorType } from '../../interfaces/validators';

@Component({
  selector: 'oca-form-field',
  templateUrl: './form-field.component.html',
  styleUrls: [ './form-field.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  viewProviders: [ { provide: ControlContainer, useExisting: NgForm } ],
})
export class FormFieldComponent {
  @Input() set value(value: FormComponent) {
    this.setComponent(value, false);
  }

  set component(value: FormComponent) {
    if (value !== this._component) {
      this.setComponent(value, true);
      this.changed();
    }
  }

  get component() {
    return this._component;
  }

  @Input() nextActions: UINextAction[];
  @Input() name: string;
  @Input() formId: number;
  @Output() removeComponent = new EventEmitter<FormComponent>();
  @Output() componentChange = new EventEmitter<FormComponent>();
  EASYMDE_OPTIONS = EASYMDE_OPTIONS;
  FormComponentType = FormComponentType;
  COMPONENT_TYPES = COMPONENT_TYPES;
  KEYBOARD_TYPES = KEYBOARD_TYPES;
  DATE_FORMATS = DATE_FORMATS;
  FILE_TYPES = FILE_TYPES;
  optionsMenuItems: OptionsMenuOption[] = [];
  showDescription = false;
  isRequired = false;
  showRequired = false;
  showValidators = false;
  showNextActions = false;
  validatorTypes: ValidatorType[] = [];
  componentType: ComponentTypeItem = COMPONENT_TYPES[ 0 ];

  private _component: FormComponent;

  constructor(private _translate: TranslateService) {
  }

  changed() {
    this.componentChange.emit(this._component);
  }

  titleChanged(title: string) {
    this.component = { ...this.component, title };
  }

  componentTypeChanged(event: MatSelectChange) {
    const value = event.value as ComponentTypeItem;
    const type = value.value as FormComponentType;
    // @ts-ignore
    this.component = { ...this.component, type };
  }

  init() {
    if (isInputComponent(this._component)) {
      this.isRequired = this._component.validators.some(v => v.type === FormValidatorType.REQUIRED);
      this.showRequired = true;
      this.showValidators = this._component.validators.some(v => v.type !== FormValidatorType.REQUIRED);
    } else {
      this.showValidators = false;
      this.showRequired = false;
    }
    this.setValidatorTypes();
    this.prepareOptionsMenu();
  }

  menuOptionClicked(option: OptionsMenuOption) {
    switch (option.id) {
      case OptionType.SHOW_DESCRIPTION:
        if (option.checked) {
          this.component = { ...this.component, description: null };
        }
        this.showDescription = !option.checked;
        break;
      case OptionType.ENABLE_VALIDATION:
        if (option.checked) {
          if (isInputComponent(this.component)) {
            this.component = {
              ...this.component,
              validators: this.component.validators.filter(v => v.type === FormValidatorType.REQUIRED),
            };
          }
        }
        this.showValidators = !option.checked;
        break;
      case OptionType.GOTO_SECTION_BASED_ON_ANSWER:
        if (option.checked) {
          const comp = this.component as SingleSelectComponent;
          comp.choices = comp.choices.map(c => ({ ...c, next_action: null }));
        }
        this.showNextActions = !option.checked;
        break;
      case OptionType.SENSITIVE_INFORMATION:
        if (isInputComponent(this.component)) {
          this.component = { ...this.component, sensitive: !this.component.sensitive };
        }
    }
    option.checked = !option.checked;
  }

  setRequired() {
    if (this.isRequired) {
      this.addValidator({ type: FormValidatorType.REQUIRED });
    } else {
      this.removeValidator(FormValidatorType.REQUIRED);
    }
  }

  keyboardTypeChanged() {
    this.setValidatorTypes();
    this.changed();
  }

  private setComponent(value: FormComponent, manualChange: boolean) {
    const previousType = this._component?.type;
    this._component = value;
    this.showDescription = this._shouldShowDescription(this._component);
    if (value && (previousType !== value.type)) {
      this.componentType = COMPONENT_TYPES.find(c => c.value === this._component.type) as ComponentTypeItem;
      this.onComponentChange(this._component.type, manualChange);
      this.init();
    }
  }

  private addValidator(validator: FormValidator) {
    if (isInputComponent(this.component)) {
      this.component = { ...this.component, validators: [ ...this.component.validators, validator ] };
    }
  }

  private removeValidator(type: FormValidatorType) {
    if (isInputComponent(this.component)) {
      this.component = { ...this.component, validators: this.component.validators.filter(v => v.type !== type) };
    }
  }

  private prepareOptionsMenu() {
    this.optionsMenuItems = [ { ...SHOW_DESCRIPTION_OPTION, checked: this.showDescription } ];
    if (this.component.type !== FormComponentType.PARAGRAPH) {
      this.optionsMenuItems.push({ ...SENSITIVE_INFORMATION_OPTION, checked: this.component.sensitive });
      if (this.component.type === FormComponentType.SINGLE_SELECT) {
        this.optionsMenuItems.push({ ...GOTO_SECTION_OPTION, checked: this.component.choices.some(c => c.next_action != null) });
      } else if (this.component.type !== FormComponentType.LOCATION) {
        this.optionsMenuItems.push({
          ...VALIDATION_OPTION,
          checked: this.component.validators.filter(v => v.type !== FormValidatorType.REQUIRED).length !== 0,
        });
      }
    }
  }

  private onComponentChange(type: FormComponentType, clearValidators: boolean) {
    let comp = { ...this.component };
    comp.type = type;
    this.showDescription = this._shouldShowDescription(comp);
    if (isInputComponent(comp)) {
      if (!comp.id) {
        comp.id = comp.title as string;
      }
      if (clearValidators) {
        if (comp.validators) {
          // Remove all validators except required
          comp.validators = comp.validators.filter(v => v.type === FormValidatorType.REQUIRED);
        } else {
          comp.validators = [];
        }
      }
      switch (comp.type) {
        case FormComponentType.TEXT_INPUT:
          if (!comp.keyboard_type) {
            comp = { ...comp, keyboard_type: KeyboardType.DEFAULT };
          }
          break;
        case FormComponentType.SINGLE_SELECT:
        case FormComponentType.MULTI_SELECT:
          if (!comp.choices) {
            const value = this._translate.instant('oca.option_x', { number: 1 });
            comp = { ...comp, choices: [ { value, label: value, next_action: null } ] };
          }
          if (comp.type === FormComponentType.SINGLE_SELECT) {
            this.showNextActions = comp.choices.some(c => c.next_action != null);
          }
          break;
        case FormComponentType.DATETIME:
          if (!comp.format) {
            comp = { ...comp, format: DateFormat.DATE };
          }
          break;
      }
    }
    this._component = comp;
  }

  private setValidatorTypes() {
    let validatorTypes: ValidatorType[] = [];
    switch (this.component.type) {
      case FormComponentType.TEXT_INPUT:
        if ([ KeyboardType.NUMBER, KeyboardType.DECIMAL ].includes(this.component.keyboard_type)) {
          validatorTypes = [ ...validatorTypes,
            { type: FormValidatorType.MIN, label: 'oca.Minimum', value: 1 },
            { type: FormValidatorType.MAX, label: 'oca.Maximum', value: 100 },
          ];
        } else {
          validatorTypes = [ ...validatorTypes,
            { type: FormValidatorType.MINLENGTH, label: 'oca.minimum_length', value: 2 },
            { type: FormValidatorType.MAXLENGTH, label: 'oca.maximum_length', value: 200 },
          ];
        }
        break;
      case FormComponentType.MULTI_SELECT:
        validatorTypes = [ ...validatorTypes,
          { type: FormValidatorType.MIN, label: 'oca.select_at_least', value: 2 },
          { type: FormValidatorType.MAX, label: 'oca.select_at_most', value: 2 },
        ];
        break;
      case FormComponentType.DATETIME:
        validatorTypes = [ ...validatorTypes,
          { type: FormValidatorType.MINDATE, label: 'oca.minimum_date', value: new Date(), value_label: 'oca.Date'},
          { type: FormValidatorType.MAXDATE, label: 'oca.maximum_date', value: new Date(), value_label: 'oca.Date'},
        ];
        break;
      case FormComponentType.FILE:
        validatorTypes = [ ...validatorTypes,
          { type: FormValidatorType.MAX, label: 'oca.maximum_file_size', value: 10_485_760, value_label: 'oca.file_size_in_b' },
        ];
        break;
    }
    this.validatorTypes = validatorTypes;
  }

  private _shouldShowDescription(component: FormComponent | null): boolean {
    return component ? component.type === FormComponentType.PARAGRAPH || !!component.description : false;
  }
}
