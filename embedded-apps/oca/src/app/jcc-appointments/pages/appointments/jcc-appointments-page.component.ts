import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { AlertController } from '@ionic/angular';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable, Subscription } from 'rxjs';
import { AppState } from '../../../reducers';
import { AppointmentExtendedDetails, AppointmentListItem, SelectedProduct } from '../../appointments';
import { AddToCalendarAction, CancelAppointmentAction, GetAppointmentsAction } from '../../jcc-appointments-actions';
import { getAppointments, hasNoAppointments, isLoadingAppointments } from '../../jcc-appointments.state';

@Component({
  templateUrl: 'jcc-appointments-page.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  styles: [`.summary-item {

  ion-label {
    font-size: 14px;
    font-weight: bold;
  }

  ion-note {
    font-size: 14px;
  }

  }`],
})
export class JccAppointmentsPage implements OnInit, OnDestroy {
  isLoading$: Observable<boolean>;
  appointments$: Observable<AppointmentListItem[]>;
  showNoResults$: Observable<boolean>;
  selectedProducts: { [ key: string ]: SelectedProduct[] } = {};
  private subscription: Subscription;

  constructor(private store: Store<AppState>,
              private translate: TranslateService,
              private datePipe: DatePipe,
              private alertController: AlertController) {
  }

  ngOnInit(): void {
    this.isLoading$ = this.store.pipe(select(isLoadingAppointments));
    this.appointments$ = this.store.pipe(select(getAppointments));
    this.showNoResults$ = this.store.pipe(select(hasNoAppointments));
    this.store.dispatch(new GetAppointmentsAction());
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }

  async cancelAppointment(appointment: Required<AppointmentExtendedDetails>) {
    const alert = await this.alertController.create({
      header: this.translate.instant('app.oca.confirm'),
      message: this.translate.instant('app.oca.confirm_delete_appointment', { date: this.datePipe.transform(appointment.appStartTime) }),
      buttons: [
        {
          text: this.translate.instant('app.oca.no'),
          role: 'cancel',
        },
        {
          text: this.translate.instant('app.oca.yes'),
          handler: () => this.store.dispatch(new CancelAppointmentAction({ appID: appointment.appointmentID })),
        },
      ],
    });
    await alert.present();
  }

  addToCalendar(appointment: Required<AppointmentExtendedDetails>) {
    this.store.dispatch(new AddToCalendarAction({ appointmentID: appointment.appointmentID }));
  }
}
