import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnDestroy, Output, ViewChild } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { MatDatepicker } from '@angular/material/datepicker';
import { IonSelect } from '@ionic/angular';
import { TranslateService } from '@ngx-translate/core';
import { markFormGroupTouched } from '@oca/shared';
import { IFormBuilder, IFormGroup } from '@rxweb/types';
import { IonicSelectableComponent } from 'ionic-selectable';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { getDateString, QMaticBranch, QMaticCustomer, QMaticService } from '../../../appointments';

export interface NewAppointmentForm {
  service: QMaticService | null;
  branch: string | null;
  date: Date | null;
  time: string | null;
  title: string;
  notes: string;
  customer: Partial<QMaticCustomer>;
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

  @Output() serviceSelected = new EventEmitter<string>();
  @Output() branchSelected = new EventEmitter<{ service: string; branch: string }>();
  @Output() dateSelected = new EventEmitter<{ service: string; branch: string; date: string; }>();
  @Output() confirmAppointment = new EventEmitter<NewAppointmentForm>();

  formGroup: IFormGroup<NewAppointmentForm>;

  showValidationError = false;
  private destroyed$ = new Subject();
  private autoOpened = {
    services: false,
    datePicker: false,
    timePicker: false,
  };
  private _services: QMaticService[] = [];
  private _branches: QMaticBranch[] = [];
  private _dates: Date[] = [];
  private _times: string[] = [];

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
        email: fb.control(rogerthat.user.account, Validators.required),
        phone: fb.control(null, Validators.required),
      }),
    });
    this.formGroup.controls.service.valueChanges.pipe(takeUntil(this.destroyed$)).subscribe(v => {
      if (v) {
        this.formGroup.patchValue({ title: v.name, branch: null, date: null, time: null }, { emitEvent: false });
        this.serviceSelected.emit(v.publicId);
      }
    });
    this.formGroup.controls.branch.valueChanges.pipe(takeUntil(this.destroyed$)).subscribe(v => {
      if (v) {
        this.formGroup.patchValue({ date: null, time: null }, { emitEvent: false });
        this.branchSelected.emit({ service: this.formGroup.controls.service.value!.publicId, branch: v });
      }
    });
    this.formGroup.controls.date.valueChanges.pipe(takeUntil(this.destroyed$)).subscribe(v => {
      if (v) {
        this.formGroup.patchValue({ time: null }, { emitEvent: false });
        this.dateSelected.emit({
          service: this.formGroup.controls.service.value!.publicId!,
          branch: this.formGroup.controls.branch.value!,
          date: getDateString(v),
        });
      }
    });
  }

  get times() {
    return this._times;
  }

  @Input() set times(value: string[]) {
    this._times = value;
    if (value?.length > 0 && !this.autoOpened.timePicker) {
      this.autoOpened.timePicker = true;
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
    if (value?.length > 0 && !this.autoOpened.datePicker) {
      this.autoOpened.datePicker = true;
      this.autoOpened.timePicker = false;
      this.datePicker.open();
    }
  }

  get services() {
    return this._services;
  }

  @Input() set services(value: QMaticService[]) {
    this._services = value;
    if (!this.autoOpened.services) {
      this.autoOpened.services = true;
      this.serviceSelect.open();
    }
  }

  get branches() {
    return this._branches;
  }

  @Input() set branches(value: QMaticBranch[]) {
    this._branches = value;
    if (value?.length > 0) {
      this.autoOpened.timePicker = false;
      this.autoOpened.datePicker = false;
      // Automatically select first value if there's only one value, otherwise open the selector
      if (value.length === 1) {
        this.formGroup.controls.branch.setValue(value[ 0 ].publicId);
      } else {
        this.branchSelect.open();
      }
    }
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
