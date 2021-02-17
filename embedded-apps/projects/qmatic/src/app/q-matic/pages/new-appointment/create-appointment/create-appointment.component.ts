import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnDestroy, Output, ViewChild } from '@angular/core';
import { AbstractControl, FormBuilder, Validators } from '@angular/forms';
import { MatDatepicker } from '@angular/material/datepicker';
import { IonSelect } from '@ionic/angular';
import { TranslateService } from '@ngx-translate/core';
import { markFormGroupTouched } from '@oca/shared';
import { IFormBuilder, IFormGroup } from '@rxweb/types';
import { IonicSelectableComponent } from 'ionic-selectable';
import { Observable, Subject } from 'rxjs';
import { map, takeUntil } from 'rxjs/operators';
import { QMaticBranch, QmaticClientSettings, QMaticCustomer, QMaticParsedService, QMaticRequiredField } from '../../../appointments';

export interface NewAppointmentForm {
  service: QMaticParsedService | null;
  branch: string | null;
  date: Date | null;
  time: string | null;
  title: string;
  notes: string;
  customer: Partial<QMaticCustomer>;
}

function makeRequired(formControl: AbstractControl) {
  formControl.setValidators(Validators.required);
  formControl.updateValueAndValidity({ emitEvent: false });
}

@Component({
  selector: 'qm-create-appointment',
  templateUrl: './create-appointment.component.html',
  styleUrls: ['./create-appointment.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreateAppointmentComponent implements OnDestroy {
  @ViewChild('serviceSelect', { static: true }) serviceSelect: IonicSelectableComponent;
  @ViewChild('branchSelect', { static: true }) branchSelect: IonSelect;
  @ViewChild('dateInput', { static: true }) dateInput: HTMLInputElement;
  @ViewChild('datePicker', { static: true }) datePicker: MatDatepicker<Date>;
  @ViewChild('timePicker', { static: true }) timePicker: IonSelect;

  @Input() showLoading: boolean;

  @Output() serviceSelected = new EventEmitter<NewAppointmentForm>();
  @Output() branchSelected = new EventEmitter<NewAppointmentForm>();
  @Output() dateSelected = new EventEmitter<NewAppointmentForm>();
  @Output() confirmAppointment = new EventEmitter<NewAppointmentForm>();
  formGroup: IFormGroup<NewAppointmentForm>;
  extraProductInfo$: Observable<string | undefined>;
  showValidationError = false;
  private destroyed$ = new Subject();
  private _services: QMaticParsedService[] = [];
  private _branches: QMaticBranch[] = [];
  private _dates: Date[] = [];
  private _times: string[] = [];
  private _settings: QmaticClientSettings | null = null;

  constructor(private translate: TranslateService,
              private formBuilder: FormBuilder) {
    const fb = formBuilder as IFormBuilder;
    this.formGroup = fb.group<NewAppointmentForm>({
      service: fb.control(null, Validators.required),
      branch: fb.control(null, Validators.required),
      date: fb.control(null, Validators.required),
      time: fb.control(null, Validators.required),
      title: fb.control(null, Validators.required),
      notes: fb.control(''),
      customer: fb.group<Partial<QMaticCustomer>>({
        firstName: fb.control(rogerthat.user.firstName || rogerthat.user.name.split(' ')[ 0 ], Validators.required),
        lastName: fb.control(this.getLastName(), Validators.required),
        email: fb.control(rogerthat.user.account),
        phone: fb.control(null),
      }),
    });
    this.extraProductInfo$ = this.formGroup.controls.service.valueChanges.pipe(
      map(service => this.settings?.show_product_info ? service?.parsedCustom?.infoText : ''),
    );
    this.formGroup.controls.service.valueChanges.pipe(takeUntil(this.destroyed$)).subscribe(v => {
      if (v) {
        this.formGroup.patchValue({ title: v.name, date: null, time: null }, { emitEvent: false });
        if (!this.settings!.first_step_location) {
          this.formGroup.controls.branch.setValue(null, { emitEvent: false });
        }
        this.serviceSelected.emit(this.formGroup.value!);
      }
    });
    this.formGroup.controls.branch.valueChanges.pipe(takeUntil(this.destroyed$)).subscribe(v => {
      if (v) {
        this.formGroup.patchValue({ date: null, time: null }, { emitEvent: false });
        if (this.settings!.first_step_location) {
          this.formGroup.controls.service.setValue(null, { emitEvent: false });
        }
        this.branchSelected.emit(this.formGroup.value!);
      }
    });
    this.formGroup.controls.date.valueChanges.pipe(takeUntil(this.destroyed$)).subscribe(v => {
      if (v) {
        this.formGroup.patchValue({ time: null }, { emitEvent: false });
        this.dateSelected.emit(this.formGroup.value!);
      }
    });
  }

  get settings() {
    return this._settings;
  }

  @Input() set settings(value: QmaticClientSettings | null) {
    this._settings = value;
    if (value) {
      const controls = this.customerForm.controls;
      if (value.required_fields.includes(QMaticRequiredField.PHONE_NUMBER)) {
        makeRequired(controls.phone!);
      }
      if (value.required_fields.includes(QMaticRequiredField.EMAIL)) {
        makeRequired(controls.email!);
      }
    }
  }

  get times() {
    return this._times;
  }

  @Input() set times(value: string[]) {
    this._times = value;
    if (value?.length > 0) {
      // Automatically select first value if there's only one value, otherwise open the selector
      if (value.length === 1) {
        this.formGroup.controls.time.setValue(value[ 0 ]);
      } else {
        this.timePicker.open();
      }
    }
  }

  get dates() {
    return this._dates;
  }

  @Input() set dates(value: Date[]) {
    this._dates = value;
    if (value?.length > 0) {
      this.datePicker.open();
    }
  }

  get services() {
    return this._services;
  }

  @Input() set services(value: QMaticParsedService[]) {
    this._services = value;
    if (value?.length) {
      this.serviceSelect.open();
    }
  }

  get branches() {
    return this._branches;
  }

  @Input() set branches(value: QMaticBranch[]) {
    this._branches = value;
    if (value?.length > 0) {
      // Automatically select first value if there's only one value, otherwise open the selector
      if (value.length === 1) {
        this.formGroup.controls.branch.setValue(value[ 0 ].publicId);
      } else {
        this.branchSelect.open();
      }
    }
  }

  get customerForm() {
    return (this.formGroup.controls.customer as IFormGroup<Partial<QMaticCustomer>>);
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  dateFilter = (date: Date | null): boolean => {
    if (!date) {
      return false;
    }
    const checkTime = date.getTime();
    return this._dates.some(d => d.getTime() === checkTime);
  };

  get shouldHideService() {
    if (this.settings?.first_step_location) {
      return this.formGroup.controls.branch.invalid;
    }
    return false;
  }

  get shouldHideBranch() {
    if (this.settings?.first_step_location) {
      return false;
    }
    return this.formGroup.controls.service.invalid;
  }

  get shouldHideDate() {
    if (this.settings?.first_step_location) {
      return this.formGroup.controls.service.invalid;
    }
    return this.formGroup.controls.branch.invalid;
  }

  confirm() {
    if (this.formGroup.invalid) {
      markFormGroupTouched(this.formGroup);
      this.showValidationError = true;
      return;
    }
    this.showValidationError = false;
    this.confirmAppointment.emit(this.formGroup.value!);
  }

  private getLastName() {
    const split = rogerthat.user.name.split(' ');
    split.shift();
    return rogerthat.user.lastName || split.join(' ');
  }
}
