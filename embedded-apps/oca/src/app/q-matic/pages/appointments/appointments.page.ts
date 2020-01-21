import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { AlertController } from '@ionic/angular';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { combineLatest, Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { AppState } from '../../../reducers';
import { CallStateType, isStatus, ResultState } from '../../../shared/call-state';
import { Appointment, ListAppointments } from '../../appointments';
import { CancelAppointmentAction, CreateIcalAction, GetAppointmentsAction } from '../../q-matic-actions';
import { getAppointments, getAppointmentsList } from '../../q-matic.state';

@Component({
  templateUrl: 'appointments.page.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppointmentsPage implements OnInit {
  result$: Observable<ResultState<ListAppointments>>;
  appointments$: Observable<{ upcoming: Appointment<Date>[], past: Appointment<Date>[] }>;
  showNoResults$: Observable<boolean>;
  isLoading$: Observable<boolean>;

  constructor(private store: Store<AppState>,
              private translate: TranslateService,
              private datePipe: DatePipe,
              private alertController: AlertController) {
  }

  ngOnInit(): void {
    this.store.dispatch(new GetAppointmentsAction());
    this.result$ = this.store.pipe(select(getAppointments));
    this.appointments$ = this.store.pipe(select(getAppointmentsList));
    this.isLoading$ = this.result$.pipe(isStatus(CallStateType.LOADING));
    this.showNoResults$ = combineLatest([this.result$.pipe(isStatus(CallStateType.SUCCESS)), this.appointments$])
      .pipe(map(([success, appointments]) => success && appointments.upcoming.length === 0));
  }

  async cancelAppointment(appointment: Appointment<Date>) {
    const alert = await this.alertController.create({
      header: this.translate.instant('app.oca.confirm'),
      message: this.translate.instant('app.oca.confirm_delete_appointment', { date: this.datePipe.transform(appointment.start, 'medium') }),
      buttons: [
        {
          text: this.translate.instant('app.oca.no'),
          role: 'cancel',
        },
        {
          text: this.translate.instant('app.oca.yes'),
          handler: () => this.store.dispatch(new CancelAppointmentAction({ appointment_id: appointment.publicId })),
        },
      ],
    });
    await alert.present();
  }

  addToCalendar(appointment: Appointment<Date>) {
    this.store.dispatch(new CreateIcalAction({ appointment_id: appointment.publicId }));
  }
}
