import { ChangeDetectionStrategy, Component, OnInit, ViewEncapsulation } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { QMState } from '../../../reducers';
import { QMaticBranch, QMaticService } from '../../appointments';
import { GetBranchesAction, GetDatesAction, GetServicesAction, GetTimesAction, ReserveDateAction } from '../../q-matic-actions';
import { getBranches, getDates, getServices, getTimes, isLoadingNewAppointmentInfo } from '../../q-matic.state';
import { NewAppointmentForm } from './create-appointment/create-appointment.component';

@Component({
  templateUrl: 'new-appointment.page.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class NewAppointmentPage implements OnInit {
  services$: Observable<QMaticService[]>;
  branches$: Observable<QMaticBranch[]>;
  dates$: Observable<{ value: string; date: Date }[]>;
  times$: Observable<string[]>;
  isLoading$: Observable<boolean>;

  constructor(private store: Store<QMState>) {
  }

  ngOnInit(): void {
    this.services$ = this.store.pipe(select(getServices));
    this.branches$ = this.store.pipe(select(getBranches));
    this.dates$ = this.store.pipe(select(getDates));
    this.times$ = this.store.pipe(select(getTimes));
    this.isLoading$ = this.store.pipe(select(isLoadingNewAppointmentInfo));
    this.store.dispatch(new GetServicesAction());
  }

  serviceChanged(service: string) {
    this.store.dispatch(new GetBranchesAction({ service_id: service }));
  }

  branchChanged({ service, branch }: { service: string; branch: string }) {
    this.store.dispatch(new GetDatesAction({ service_id: service, branch_id: branch }));
  }

  dateChanged({ service, branch, date }: { service: string; branch: string; date: string }) {
    this.store.dispatch(new GetTimesAction({
      service_id: service,
      branch_id: branch!,
      date,
    }));
  }

  confirmAppointment(data: NewAppointmentForm) {
    this.store.dispatch(new ReserveDateAction({
      service_id: data.service!.publicId,
      branch_id: data.branch!,
      date: data.date!,
      time: data.time!,
      title: data.title,
      notes: data.notes,
      customer: data.customer,
    }));
  }
}
