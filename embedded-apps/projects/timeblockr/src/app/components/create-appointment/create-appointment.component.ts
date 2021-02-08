import { StepperSelectionEvent } from '@angular/cdk/stepper';
import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnChanges, OnDestroy, OnInit, Output, ViewChild } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, ValidatorFn, Validators } from '@angular/forms';
import { MatDatepicker } from '@angular/material/datepicker';
import { IonSelect } from '@ionic/angular';
import { TranslateService } from '@ngx-translate/core';
import { markFormGroupTouched, NgChanges } from '@oca/shared';
import { IFormBuilder, IFormGroup } from '@rxweb/types';
import { IonicSelectableComponent } from 'ionic-selectable';
import { Subject } from 'rxjs';
import { take, takeUntil } from 'rxjs/operators';
import {
  CreateTimeblockrAppointment,
  TimeblockrClientDateSlot,
  TimeblockrDynamicField,
  TimeblockrLocation,
  TimeblockrProduct,
} from '../../timeblockr';

interface DynFieldsValue {
  [ key: string ]: string;
}

interface CreateAppointmentForm {
  // Only allow one product for now
  // TODO multiple products
  product: TimeblockrProduct | null;
  location: TimeblockrLocation | null;
  date: Date | null;
  time: string | null;
  dynamicFields: DynFieldsValue;
}

export interface BaseDynamicField {
  field: TimeblockrDynamicField;
}

export const enum InputType {
  text = 'text',
  tel = 'tel',
  email = 'email',
}

export interface DynamicTextField extends BaseDynamicField {
  type: 'input';
  inputType: InputType;
}

export interface DynamicSelectField extends BaseDynamicField {
  type: 'select';
}

export type DynamicField = DynamicTextField | DynamicSelectField;

const INPUT_TYPES = {
  PhoneInt: InputType.tel,
  Email: InputType.email,
  None: InputType.text,
};

const enum Step {
  PRODUCTS = 0,
  LOCATION_DATE_TIME,
  DATA,
  CONFIRM,
}

@Component({
  selector: 'timeblockr-create-appointment',
  templateUrl: './create-appointment.component.html',
  styleUrls: ['./create-appointment.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreateAppointmentComponent implements OnInit, OnChanges, OnDestroy {
  @ViewChild('productSelect', { static: true }) productSelect: IonicSelectableComponent;
  @ViewChild('locationSelect', { static: true }) locationSelect: IonSelect;
  @ViewChild('datePicker', { static: true }) datePicker: MatDatepicker<Date>;
  @ViewChild('timePicker', { static: true }) timePicker: IonSelect;
  @Input() isLoading: boolean;
  @Input() products: TimeblockrProduct[];
  @Input() locations: TimeblockrLocation[];
  @Input() dateSlots: TimeblockrClientDateSlot[];
  @Input() timeSlots: TimeblockrClientDateSlot[];
  @Input() dynamicFields: TimeblockrDynamicField[];
  @Output() productChanged = new EventEmitter<TimeblockrProduct>();
  @Output() locationChanged = new EventEmitter<TimeblockrLocation>();
  @Output() dateChanged = new EventEmitter<string>();
  @Output() timeChanged = new EventEmitter<string>();
  @Output() createAppointment = new EventEmitter<CreateTimeblockrAppointment>();

  templateDynamicFields: DynamicField[] = [];
  formGroup: IFormGroup<CreateAppointmentForm>;
  fb: IFormBuilder;
  stepAnimationDone = new Subject();

  private destroyed$ = new Subject();

  constructor(formBuilder: FormBuilder,
              private translate: TranslateService) {
    const fb = formBuilder as IFormBuilder;
    this.fb = formBuilder;
    this.formGroup = fb.group<CreateAppointmentForm>({
      product: fb.control(null, Validators.required),
      location: fb.control(null, Validators.required),
      date: fb.control(null, Validators.required),
      time: fb.control(null, Validators.required),
      dynamicFields: fb.group({}),
    });
    this.formGroup.controls.product.valueChanges.pipe(takeUntil(this.destroyed$)).subscribe(selectedProduct => {
      if (selectedProduct) {
        this.formGroup.patchValue({ date: null, time: null }, { emitEvent: false });
        this.productChanged.emit(selectedProduct);
      }
    });
    this.formGroup.controls.location.valueChanges.pipe(takeUntil(this.destroyed$)).subscribe(location => {
      if (location) {
        this.formGroup.patchValue({ date: null, time: null }, { emitEvent: false });
        this.locationChanged.emit(location);
      }
    });
    this.formGroup.controls.date.valueChanges.pipe(takeUntil(this.destroyed$)).subscribe(date => {
      if (date) {
        this.formGroup.patchValue({ time: null }, { emitEvent: false });
        const iso = date.toISOString();
        const item = this.dateSlots.find(d => d.date.toISOString() === iso);
        if (item) {
          this.dateChanged.emit(item.value);
        }
      }
    });
    this.formGroup.controls.time.valueChanges.pipe(takeUntil(this.destroyed$)).subscribe(time => {
      if (time) {
        this.timeChanged.emit(time);
      }
    });
  }

  ngOnInit() {
  }

  ngOnChanges(changes: NgChanges<CreateAppointmentComponent>) {
    if (changes.products?.currentValue.length > 0) {
      this.productSelect.open();
    }
    if (changes.locations?.currentValue.length > 0) {
      // Automatically select first value if there's only one value
      if (this.locations.length === 1) {
        this.formGroup.controls.location.setValue(this.locations[ 0 ]);
      }
    }
    if (changes.timeSlots?.currentValue.length > 0) {
      // Automatically select first value if there's only one value, otherwise open the selector
      if (this.timeSlots.length === 1) {
        this.formGroup.controls.time.setValue(this.timeSlots[ 0 ].value);
      } else {
        this.timePicker.open();
      }
    }
    if (changes.dynamicFields?.currentValue.length > 0) {
      this.setDynamicFields();
    }
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  submit() {
    if (this.formGroup.invalid) {
      markFormGroupTouched(this.formGroup);
      return;
    }
    // TODO
    this.createAppointment.emit({});
  }

  dateFilter = (date: Date | null): boolean => {
    if (!date) {
      return false;
    }
    const checkTime = date.getTime();
    return this.dateSlots.some(d => d.date.getTime() === checkTime);
  };

  getErrorMessage(field: DynamicField): string | null {
    const control = (this.formGroup.controls.dynamicFields as FormGroup).controls[ field.field.Key ];
    if (control.touched) {
      if (control.invalid) {
        if (control.hasError('required')) {
          return this.translate.instant('app.timeblockr.this_field_is_required');
        }
        if (control.hasError('email')) {
          return this.translate.instant('app.timeblockr.invalid_email_address');
        }
        if (control.hasError('maxlength')) {
          return this.translate.instant('app.timeblockr.value_too_long');
        }
        if (control.hasError('pattern')) {
          if (field.field.RegexValidationMessage) {
            return field.field.RegexValidationMessage;
          }
          return this.translate.instant('app.timeblockr.invalid_value');
        }
      }
    }
    return null;
  }

  stepChanged($event: StepperSelectionEvent) {
    if ($event.selectedIndex === Step.LOCATION_DATE_TIME) {
      const { location, date } = this.formGroup.value!;
      if (!location) {
        if (this.locations.length > 1) {
          this.locationSelect.open();
        }
      } else if (!date) {
        // If we don't wait the overlay won't be positioned correctly
        this.stepAnimationDone.asObservable().pipe(take(1)).subscribe(() => {
          this.datePicker.open();
        });
      }
    }
  }

  getFieldValue(field: DynamicField): string {
    const controlValue = (this.formGroup.controls.dynamicFields as IFormGroup<DynFieldsValue>).controls[ field.field.Key ].value!;
    if (field.type === 'input') {
      return controlValue;
    }
    return field.field.OptionValuesList.find(o => o.Value === controlValue)?.Text ?? controlValue;
  }

  private setDynamicFields() {
    const fieldsControl = (this.formGroup.controls.dynamicFields as FormGroup);
    const previousValue = fieldsControl.value;
    for (const controlName of Object.keys(fieldsControl.controls)) {
      fieldsControl.removeControl(controlName);
    }
    this.templateDynamicFields = [];
    for (const field of this.dynamicFields) {
      const control = this.getFormControlForField(field);
      fieldsControl.addControl(field.Key, control);
      this.templateDynamicFields.push(this.getTemplateDynamicField(field));
    }
    fieldsControl.patchValue(previousValue);
  }

  private getFormControlForField(field: TimeblockrDynamicField): FormControl {
    const validators: ValidatorFn[] = [];
    if (field.IsRequired) {
      validators.push(Validators.required);
    }
    if (field.MaxLength) {
      validators.push(Validators.maxLength(field.MaxLength));
    }
    if (field.ValidationType === 'Email') {
      validators.push(Validators.email);
    }
    if (field.ValidationExpression) {
      validators.push(Validators.pattern(field.ValidationExpression));
    }
    return new FormControl(null, validators);
  }

  private getTemplateDynamicField(field: TimeblockrDynamicField): DynamicField {
    if (field.OptionValuesList.length > 0) {
      return { type: 'select', field };
    }
    return { type: 'input', field, inputType: INPUT_TYPES[ field.ValidationType ] };
  }
}
