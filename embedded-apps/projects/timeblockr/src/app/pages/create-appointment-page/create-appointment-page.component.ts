import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import {
  CreateTimeblockrAppointment,
  SelectedProduct,
  TimeblockrClientDateSlot,
  TimeblockrDynamicField,
  TimeblockrLocation,
  TimeblockrProduct,
} from '../../timeblockr';
import {
  createAppointment,
  loadDynamicFields,
  loadLocations,
  loadProducts,
  loadTimeslots,
  loadTimeslotsOnDay,
} from '../../timeblockr.actions';
import {
  getDateSlots,
  getDynamicFields,
  getLocations,
  getProducts,
  getTimeSLots,
  isLoadingNewAppointmentData,
} from '../../timeblockr.state';

@Component({
  selector: 'timeblockr-create-appointment-page',
  templateUrl: './create-appointment-page.component.html',
  styleUrls: ['./create-appointment-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreateAppointmentPageComponent implements OnInit {
  products$: Observable<TimeblockrProduct[]>;
  locations$: Observable<TimeblockrLocation[]>;
  dateslots$: Observable<TimeblockrClientDateSlot[]>;
  timeslots$: Observable<TimeblockrClientDateSlot[]>;
  dynamicFields$: Observable<TimeblockrDynamicField[]>;
  loading$: Observable<boolean>;
  selectedData: { location: string | null; products: SelectedProduct[]; date: string | null; time: string | null; } = {
    location: null,
    products: [],
    date: null,
    time: null,
  };

  constructor(private store: Store) {
  }

  ngOnInit() {
    this.products$ = this.store.pipe(select(getProducts));
    this.locations$ = this.store.pipe(select(getLocations));
    this.dateslots$ = this.store.pipe(select(getDateSlots));
    this.timeslots$ = this.store.pipe(select(getTimeSLots));
    this.dynamicFields$ = this.store.pipe(select(getDynamicFields));
    this.loading$ = this.store.pipe(select(isLoadingNewAppointmentData));
    this.store.dispatch(loadProducts({ data: { selectedProducts: [] } }));
    this.store.dispatch(loadLocations());
  }

  onProductChanged($event: TimeblockrProduct) {
    this.selectedData.products = [{ amount: 1, id: $event.Guid }];
    this.store.dispatch(loadDynamicFields({
      data: {
        selectedProducts: this.selectedData.products,
        locationId: this.selectedData.location!,
      },
    }));
    this.maybeRequestTimeslots();
  }

  onLocationChanged($event: TimeblockrLocation) {
    this.selectedData.location = $event.Guid;
    this.maybeRequestTimeslots();
  }

  onDateChanged($event: string) {
    this.selectedData.date = $event;
    this.store.dispatch(loadTimeslotsOnDay({
      data: {
        locationId: this.selectedData.location!,
        selectedProducts: this.selectedData.products,
        selectedDate: $event,
      },
    }));
  }

  onTimeChanged($event: string) {
    this.selectedData.time = $event;
  }

  doCreateAppointment($event: CreateTimeblockrAppointment) {
    this.store.dispatch(createAppointment({ data: $event }));
  }

  private maybeRequestTimeslots() {
    if (this.selectedData.location && this.selectedData.products.length > 0) {
      this.store.dispatch(loadTimeslots({
        data: {
          locationId: this.selectedData.location,
          selectedProducts: this.selectedData.products,
        },
      }));
    }
  }
}
