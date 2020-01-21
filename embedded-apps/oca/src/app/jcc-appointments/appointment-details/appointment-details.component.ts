import { ChangeDetectionStrategy, Component, Input, ViewEncapsulation } from '@angular/core';
import {
  AppointmentDetailsType,
  AppointmentExtendedDetails,
  FORM_FIELDS,
  JccLocation,
  LocationDetails,
  SelectedProduct,
} from '../appointments';

@Component({
  selector: 'app-jcc-appointment-details',
  templateUrl: './appointment-details.component.html',
  styleUrls: ['./appointment-details.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class AppointmentDetailsComponent {
  @Input() appointment: AppointmentDetailsType | AppointmentExtendedDetails;
  @Input() selectedProducts: SelectedProduct[];
  @Input() location: JccLocation | LocationDetails | null;
  clientFields = FORM_FIELDS;
}
