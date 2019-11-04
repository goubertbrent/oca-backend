import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { AppState } from '../../../reducers';
import { CreateAppointment, QMaticBranch, QMaticService } from '../../appointments';
import { GetBranchesAction, GetDatesAction, GetServicesAction, GetTimesAction, ReserveDateAction } from '../../q-matic-actions';
import { getBranches, getDates, getServices, getTimes, isLoadingNewAppointmentInfo } from '../../q-matic.state';

@Component({
  templateUrl: 'new-appointment.page.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewAppointmentPage implements OnInit {
  services$: Observable<QMaticService[]>;
  branches$: Observable<QMaticBranch[]>;
  dates$: Observable<{ value: string; date: Date }[]>;
  times$: Observable<string[]>;
  isLoading$: Observable<boolean>;

  selectedService: string | null = null;
  selectedBranch: string | null = null;
  selectedDate: string | null = null;
  selectedTime: string | null = null;

  constructor(private store: Store<AppState>) {
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
    this.selectedService = service;
    this.store.dispatch(new GetBranchesAction({ service_id: this.selectedService }));
    this.selectedBranch = null;
    this.selectedDate = null;
    this.selectedTime = null;
  }

  branchChanged(branch: string) {
    this.selectedBranch = branch;
    this.store.dispatch(new GetDatesAction({ service_id: this.selectedService as string, branch_id: this.selectedBranch }));
    this.selectedDate = null;
    this.selectedTime = null;
  }

  dateChanged(date: string) {
    this.selectedDate = date;
    this.store.dispatch(new GetTimesAction({
      service_id: this.selectedService as string,
      branch_id: this.selectedBranch as string,
      date: this.selectedDate,
    }));
    this.selectedTime = null;
  }

  timeChanged(time: string) {
    this.selectedTime = time;
  }

  confirmAppointment(data: Omit<CreateAppointment, 'reservation_id'>) {
    this.store.dispatch(new ReserveDateAction({
      service_id: this.selectedService as string,
      branch_id: this.selectedBranch as string,
      date: this.selectedDate as string,
      time: this.selectedTime as string,
      title: data.title,
      notes: data.notes,
      customer: data.customer,
    }));
  }
}
