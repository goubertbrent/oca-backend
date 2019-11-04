import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { Appointment, AppointmentStatus } from '../appointments';

@Component({
  selector: 'app-appointment-card',
  templateUrl: './appointment-card.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppointmentCardComponent {
  @Input() appointment: Appointment<Date>;
  @Output() cancelClicked = new EventEmitter<Appointment<Date>>();
  @Output() addToCalendarClicked = new EventEmitter<Appointment<Date>>();

  AppointmentStatus = AppointmentStatus;
}
