import { DatePipe, Location } from '@angular/common';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnDestroy, OnInit, ViewChild, ViewEncapsulation } from '@angular/core';
import { AlertController } from '@ionic/angular';
import { AlertOptions } from '@ionic/core';
import { Actions, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable, Subject } from 'rxjs';
import { first, map, takeUntil, tap } from 'rxjs/operators';
import { AppState } from '../../../reducers';
import {
  APPOINTMENT_DETAILS_FIELDS,
  AppointmentDetailsType,
  AppointmentExtendedDetails,
  ClientDetails,
  JccLocation,
  Locations,
  Product,
  ProductDetails,
  SelectedProduct,
  SelectedProductsMapping,
} from '../../appointments';
import {
  AddProductAction,
  CreateAppointmentAction,
  CreateAppointmentCompleteAction,
  CreateExtendedAppointmentAction,
  DeleteProductAction,
  GetAvailableDaysAction,
  GetAvailableTimesAction,
  GetProductDetailsAction,
  GetProductDetailsSuccessAction,
  GetProductsAction,
  GetRequiredFieldsAction,
  JccAppointmentsActionTypes,
  UpdateProductAction,
} from '../../jcc-appointments-actions';
import {
  getAvailableDays,
  getAvailableTimes,
  getLocations,
  getRequiredFields,
  getSelectableProducts,
  getSelectedProducts,
  getSelectedProductsIds,
  getSelectedProductsList,
  isProductsLoading,
} from '../../jcc-appointments.state';
import { JccContactDetailsComponent } from './jcc-contact-details/jcc-contact-details.component';
import { JccLocationTimeComponent } from './jcc-location-time/jcc-location-time.component';


enum Step {
  PRODUCTS,
  LOCATION_DATE,
  CONTACT_INFO,
  CONFIRM,
}

@Component({
  templateUrl: 'jcc-new-appointment-page.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class JccNewAppointmentPage implements OnInit, OnDestroy {
  @ViewChild(JccLocationTimeComponent, { static: true }) locationTimeComponent: JccLocationTimeComponent;
  @ViewChild(JccContactDetailsComponent, { static: true }) contactDetailsComponent: JccContactDetailsComponent;
  appointment: AppointmentExtendedDetails | AppointmentDetailsType = {
    // required properties
    clientDateOfBirth: '',
    appStartTime: '',
    appEndTime: '', // required but ignored by server (according to the docs)
    isClientVerified: false,
    clientLastName: '',
  };
  expandedPanels = [true, false, false, false];
  disabledSteps = [false, true, true, true];
  selectableProducts$: Observable<Product[]>;
  selectedProducts$: Observable<SelectedProduct[]>;
  productCounts$: Observable<SelectedProductsMapping>;
  productsLoading$: Observable<boolean>;
  locations$: Observable<Locations>;
  availableDays$: Observable<string[]>;
  availableTimes$: Observable<string[]>;
  requiredFields$: Observable<string[]>;
  Step = Step;
  useExtendedDetails = false;
  selectedLocation: JccLocation | null = null;
  private selectedProductIds$: Observable<string[]>;
  private destroyed$ = new Subject();

  constructor(private store: Store<AppState>,
              private actions: Actions,
              private changeDetectionRef: ChangeDetectorRef,
              private translate: TranslateService,
              private alertController: AlertController,
              private location: Location,
              private datePipe: DatePipe) {
  }

  ngOnInit(): void {
    this.selectedProducts$ = this.store.pipe(select(getSelectedProductsList));
    this.selectableProducts$ = this.store.pipe(select(getSelectableProducts));
    this.productCounts$ = this.store.pipe(select(getSelectedProducts));
    this.locations$ = this.store.pipe(select(getLocations), tap(locations => {
      // Default to first location
      if (locations.length > 0 && this.appointment.locationID === null) {
        this.appointment.locationID = locations[ 0 ].locationID;
      }
    }));
    this.productsLoading$ = this.store.pipe(select(isProductsLoading));
    this.availableDays$ = this.store.pipe(select(getAvailableDays));
    this.availableTimes$ = this.store.pipe(select(getAvailableTimes));
    this.requiredFields$ = this.store.pipe(select(getRequiredFields));
    this.requiredFields$.pipe(takeUntil(this.destroyed$), map(fields => {
      for (const field of fields) {
        if (!APPOINTMENT_DETAILS_FIELDS.includes(field)) {
          return true;
        }
      }
      return false;
    })).subscribe(result => this.useExtendedDetails = result);
    this.store.dispatch(new GetProductsAction());

    this.selectedProductIds$ = this.store.pipe(select(getSelectedProductsIds), takeUntil(this.destroyed$));
    this.selectedProductIds$.subscribe(productIds => {
      this.appointment = { ...this.appointment, productID: productIds.join(',') };
    });

    // Show annoying popup when details of an item are fetched for the first time
    this.actions.pipe(
      takeUntil(this.destroyed$),
      ofType<GetProductDetailsSuccessAction>(JccAppointmentsActionTypes.GET_PRODUCT_DETAILS_COMPLETE)).subscribe(action => {
      if (action.payload.product.requisites) {
        this.showProductRequisites(action.payload.product);
      }
    });

    // Navigate to appointments overview when appointment is booked
    this.actions.pipe(
      takeUntil(this.destroyed$),
      ofType<CreateAppointmentCompleteAction>(JccAppointmentsActionTypes.CREATE_APPOINTMENT_SUCCESS),
    ).subscribe(() => {
      this.location.back();
    });
  }

  ngOnDestroy(): void {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  addProduct(product: Product) {
    this.store.dispatch(new GetProductDetailsAction({ productID: product.productId }));
    this.store.dispatch(new AddProductAction({ product }));
  }

  updateProduct(event: { productId: string; amount: number }) {
    this.store.dispatch(new UpdateProductAction(event));
  }

  deleteProduct(event: { productId: string }) {
    this.store.dispatch(new DeleteProductAction(event));
  }

  /**
   * Disables steps positioned after the currently opened step
   */
  stepOpened(step: Step) {
    for (let i = 0; i < this.expandedPanels.length; i++) {
      this.expandedPanels[ i ] = false;
    }
    this.expandedPanels[ step ] = true;
    for (let i = 0; i < this.disabledSteps.length; i++) {
      this.disabledSteps[ i ] = i > step;
    }
    this.changeDetectionRef.markForCheck();
  }

  onLocationPicked(locationID: string) {
    this.locations$.pipe(first()).subscribe(locations => {
      this.selectedLocation = locations.find(l => l.locationID === locationID) || null;
      this.appointment = { ...this.appointment, locationID };
    });
    this.selectedProductIds$.pipe(first()).subscribe(productIds => {
      const now = new Date();
      // the api only allows 7 weeks in the future, else no results are returned
      const sevenWeeksFromNow = new Date();
      sevenWeeksFromNow.setDate(sevenWeeksFromNow.getDate() + 49);
      this.store.dispatch(new GetAvailableDaysAction({
        appDuration: 0,
        productID: productIds.join(','),
        locationID,
        startDate: this.getDateString(now),
        endDate: this.getDateString(sevenWeeksFromNow),
      }));
    });
  }

  onDayPicked(date: string) {
    this.selectedProductIds$.pipe(first()).subscribe(productIds => {
      if (productIds.length > 0) {
        this.store.dispatch(new GetAvailableTimesAction({
          productID: productIds.join(','),
          locationID: this.locationTimeComponent.selectedLocation as string,
          date: this.getDateString(new Date(date)),
          appDuration: 0,
        }));
      }
    });
  }

  onTimePicked(date: string) {
    const appStartTime = new Date(date + 'Z').toISOString().split('.')[ 0 ];  // remove .000Z at the end
    this.appointment = { ...this.appointment, appStartTime, appEndTime: appStartTime };
  }

  showStep2() {
    this.selectedProductIds$.pipe(first()).subscribe(productIds => {
      if (productIds.length === 0) {
        this.showDialog({
          message: this.translate.instant('app.oca.please_select_activity'),
        });
      } else {
        this.store.dispatch(new GetRequiredFieldsAction({ productID: productIds.join(',') }));
        this.setCurrentStep(Step.LOCATION_DATE);
      }
    });
  }

  showStep3() {
    if (this.locationTimeComponent.isValid()) {
      this.setCurrentStep(Step.CONTACT_INFO);
    } else {
      this.showDialog({ message: this.translate.instant('app.oca.please_select_a_location_date_and_time') });
    }
  }

  showStep4() {
    if (this.contactDetailsComponent.isValid()) {
      this.setCurrentStep(Step.CONFIRM);
    } else {
      this.showDialog({ message: this.translate.instant('app.oca.please_fill_in_required_fields') });
    }
  }

  confirmAppointment() {
    if (this.useExtendedDetails) {
      this.store.dispatch(new CreateExtendedAppointmentAction({ appDetail: this.appointment }));
    } else {
      const appDetail: Partial<AppointmentDetailsType> = {};
      for (const [key, value] of Object.entries(this.appointment)) {
        if (APPOINTMENT_DETAILS_FIELDS.includes(key)) {
          (appDetail as any)[ key ] = value;
        }
      }
      this.store.dispatch(new CreateAppointmentAction({ appDetail: appDetail as AppointmentDetailsType }));
    }
  }

  setCurrentStep(step: Step) {
    this.stepOpened(step);
  }

  async showProductRequisites(productDetails: ProductDetails) {
    return this.showDialog({
      header: productDetails.description,
      message: `${this.translate.instant('app.oca.what_do_you_need')}
${productDetails.requisites}`,
    });
  }

  async showDialog(options: AlertOptions) {
    const alert = await this.alertController.create({
      header: this.translate.instant('app.oca.error'),
      buttons: [{
        text: this.translate.instant('app.oca.ok'),
        role: 'cancel',
      }],
      ...options,
    });
    await alert.present();
  }

  updateClientDetails(details: Partial<ClientDetails>) {
    this.appointment = { ...this.appointment, ...details };
  }

  private getDateString(date: Date): string {
    return this.datePipe.transform(date, 'yyyy-MM-dd') as string;
  }
}
