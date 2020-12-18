import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  EventEmitter,
  Input,
  OnDestroy,
  Output,
  ViewEncapsulation,
} from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { TranslateService } from '@ngx-translate/core';
import { markFormGroupTouched } from '@oca/shared';
import { IFormBuilder, IFormGroup } from '@rxweb/types';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { QMaticBranch, QMaticCustomer, QMaticService } from '../../../appointments';

export interface NewAppointmentForm {
  service: QMaticService | null;
  branch: string | null;
  date: string | null;
  time: string | null;
  title: string;
  notes: string;
  customer: Partial<QMaticCustomer>;
}

@Component({
  selector: 'qm-create-appointment',
  templateUrl: './create-appointment.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class CreateAppointmentComponent implements OnDestroy {
  @Input() services: QMaticService[];
  @Input() branches: QMaticBranch[];
  @Input() dates: { value: string, date: Date }[];
  @Input() times: string[];
  @Input() showLoading: boolean;

  @Output() serviceSelected = new EventEmitter<string>();
  @Output() branchSelected = new EventEmitter<{ service: string; branch: string }>();
  @Output() dateSelected = new EventEmitter<{ service: string; branch: string; date: string; }>();
  @Output() confirmAppointment = new EventEmitter<NewAppointmentForm>();

  formGroup: IFormGroup<NewAppointmentForm>;

  showValidationError = false;
  private destroyed$ = new Subject();

  constructor(private translate: TranslateService,
              private formBuilder: FormBuilder) {
    const fb = formBuilder as IFormBuilder;
    this.formGroup = fb.group<NewAppointmentForm>({
      service: fb.control(null, Validators.required),
      branch: fb.control(null, Validators.required),
      date: fb.control(null, Validators.required),
      time: fb.control(null, Validators.required),
      title: fb.control(null, Validators.required),
      notes: fb.control(this.translate.instant('app.qm.via_app', { appName: rogerthat.system.appName }), Validators.required),
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
          date: v,
        });
      }
    });
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
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
