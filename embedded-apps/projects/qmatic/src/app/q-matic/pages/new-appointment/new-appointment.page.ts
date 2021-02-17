import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, ViewEncapsulation } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable, Subject } from 'rxjs';
import { filter, take, takeUntil } from 'rxjs/operators';
import { QMState } from '../../../reducers';
import { getDateString, QMaticBranch, QmaticClientSettings, QMaticParsedService } from '../../appointments';
import {
  GetBranchesAction,
  GetDatesAction,
  GetServicesAction,
  GetSettingsAction,
  GetTimesAction,
  ReserveDateAction,
} from '../../q-matic-actions';
import { getBranches, getClientSettings, getDates, getServices, getTimes, isLoadingNewAppointmentInfo } from '../../q-matic.state';
import { NewAppointmentForm } from './create-appointment/create-appointment.component';

@Component({
  templateUrl: 'new-appointment.page.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class NewAppointmentPage implements OnInit, OnDestroy {
  services$: Observable<QMaticParsedService[]>;
  branches$: Observable<QMaticBranch[]>;
  dates$: Observable<Date[]>;
  times$: Observable<string[]>;
  isLoading$: Observable<boolean>;
  settings$: Observable<QmaticClientSettings>;

  private destroyed$ = new Subject();
  private settings: QmaticClientSettings;

  constructor(private store: Store<QMState>) {
  }

  ngOnInit(): void {
    this.services$ = this.store.pipe(select(getServices));
    this.branches$ = this.store.pipe(select(getBranches));
    this.dates$ = this.store.pipe(select(getDates));
    this.times$ = this.store.pipe(select(getTimes));
    this.settings$ = this.store.pipe(select(getClientSettings), filter(s => s !== null)) as Observable<QmaticClientSettings>;
    this.isLoading$ = this.store.pipe(select(isLoadingNewAppointmentInfo));
    this.store.dispatch(new GetSettingsAction());
    this.settings$.pipe(take(1), takeUntil(this.destroyed$)).subscribe(settings => {
      this.settings = settings;
      if (settings!.first_step_location) {
        this.store.dispatch(new GetBranchesAction({}));
      } else {
        this.store.dispatch(new GetServicesAction({}));
      }
    });
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  serviceChanged(form: NewAppointmentForm) {
    if (this.settings.first_step_location) {
      this.store.dispatch(new GetDatesAction({ service_id: form.service!.publicId, branch_id: form.branch! }));
    } else {
      this.store.dispatch(new GetBranchesAction({ service_id: form.service!.publicId }));
    }
  }

  branchChanged({ service, branch }: NewAppointmentForm) {
    if (this.settings.first_step_location) {
      this.store.dispatch(new GetServicesAction({ branch_id: branch! }));
    } else {
      this.store.dispatch(new GetDatesAction({ service_id: service!.publicId, branch_id: branch! }));
    }
  }

  dateChanged({ service, branch, date }: NewAppointmentForm) {
    this.store.dispatch(new GetTimesAction({
      service_id: service!.publicId,
      branch_id: branch!,
      date: getDateString(date!),
    }));
  }

  confirmAppointment(data: NewAppointmentForm) {
    this.store.dispatch(new ReserveDateAction({
      service_id: data.service!.publicId,
      branch_id: data.branch!,
      date: getDateString(data.date!),
      time: data.time!,
      title: data.title,
      notes: data.notes,
      customer: data.customer,
    }));
  }
}
