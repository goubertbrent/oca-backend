import { ChangeDetectionStrategy, ChangeDetectorRef, Component, EventEmitter, Input, Output } from '@angular/core';
import { FormGroup, NgForm } from '@angular/forms';
import { TranslateService } from '@ngx-translate/core';
import { CreateAppointment, QMaticBranch, QMaticCustomer, QMaticService } from '../../../appointments';

@Component({
  selector: 'app-create-appointment',
  templateUrl: './create-appointment.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreateAppointmentComponent {
  @Input() services: QMaticService[];
  @Input() branches: QMaticBranch[];
  @Input() dates: { value: string, date: Date }[];
  @Input() times: string[];
  @Input() showLocation: boolean;
  @Input() showDates: boolean;
  @Input() showTimes: boolean;
  @Input() showLoading: boolean;

  @Output() serviceSelected = new EventEmitter<string>();
  @Output() branchSelected = new EventEmitter<string>();
  @Output() dateSelected = new EventEmitter<string>();
  @Output() timeSelected = new EventEmitter<string>();
  @Output() confirmAppointment = new EventEmitter<Omit<CreateAppointment, 'reservation_id'>>();

  customer: Partial<QMaticCustomer> = {
    firstName: (rogerthat.user as any).first_name || rogerthat.user.name.split(' ')[ 0 ],
    lastName: this.getLastName(),
    email: rogerthat.user.account,
    phone: null,
  };

  selectedService: QMaticService;

  constructor(private translate: TranslateService,
              private changeDetectorRef: ChangeDetectorRef) {
  }

  onServiceSelected(value: string) {
    this.selectedService = this.services.find(s => s.publicId === value) as QMaticService;
    this.serviceSelected.emit(value);
  }

  confirm(form: NgForm) {
    if (!form.form.valid) {
      this.markFormGroupTouched(form.form);
      return;
    }
    this.confirmAppointment.emit({
      title: this.selectedService.name,
      notes: this.translate.instant('app.oca.via_app', { appName: rogerthat.system.appName }),
      customer: this.customer,
    });
  }

  private markFormGroupTouched(formGroup: FormGroup) {
    for (const control of Object.values(formGroup.controls)) {
      // setValue ensures the pristine/touched status of the ionic element is updated
      control.setValue(control.value);
      control.markAsTouched();
      control.markAsDirty();
    }
  }

  private getLastName() {
    const split = rogerthat.user.name.split(' ');
    split.shift();
    return (rogerthat.user as any).last_name || split.join(' ');
  }
}
