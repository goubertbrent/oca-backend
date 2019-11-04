import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
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
    firstName: rogerthat.user.name,
    lastName: null,
    email: rogerthat.user.account,
    phone: null,
  };

  selectedService: QMaticService;

  constructor(private translate: TranslateService) {
  }

  onServiceSelected(value: string) {
    this.selectedService = this.services.find(s => s.publicId === value) as QMaticService;
    this.serviceSelected.emit(value);
  }

  confirm() {
    this.confirmAppointment.emit({
      title: this.selectedService.name,
      notes: this.translate.instant('app.oca.via_app', {appName: rogerthat.system.appName}),
      customer: this.customer,
    });
  }
}
