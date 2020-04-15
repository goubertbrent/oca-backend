import { Location } from '@angular/common';
import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { AlertController } from '@ionic/angular';
import { Actions, Effect, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { of } from 'rxjs';
import { catchError, filter, map, switchMap, tap, withLatestFrom } from 'rxjs/operators';
import { AppState } from '../reducers';
import { RogerthatService } from '../rogerthat/rogerthat.service';
import { ErrorService } from '../shared/error.service';
import {
  AppointmentsList,
  AppointmentUpdateStatus,
  AvailableDays,
  AvailableTimes,
  BookGovAppointmentExtendedDetailsResponse,
  BookGovAppointmentResponse,
  DeleteAppointmentUpdateStatus,
  DeleteGovAppointmentResponse,
  GetRequiredClientFieldsResponse,
  JccLocation,
  Product,
  ProductDetails,
} from './appointments';
import {
  AddProductAction,
  AddToCalendarAction,
  AddToCalendarCompleteAction,
  CancelAppointmentAction,
  CancelAppointmentFailedAction,
  CancelAppointmentSuccessAction,
  CreateAppointmentAction,
  CreateAppointmentCompleteAction,
  CreateAppointmentFailedAction,
  CreateExtendedAppointmentAction,
  DeleteProductAction,
  GetAppointmentsAction,
  GetAppointmentsFailedAction,
  GetAppointmentsSuccessAction,
  GetAvailableDaysAction,
  GetAvailableDaysFailedAction,
  GetAvailableDaysSuccessAction,
  GetAvailableTimesAction,
  GetAvailableTimesFailedAction,
  GetAvailableTimesSuccessAction,
  GetLocationsForProductAction,
  GetLocationsForProductFailedAction,
  GetLocationsForProductSuccessAction,
  GetProductDetailsAction,
  GetProductDetailsFailedAction,
  GetProductDetailsSuccessAction,
  GetProductsAction,
  GetProductsByProductsAction,
  GetProductsByProductsFailedAction,
  GetProductsByProductsSuccessAction,
  GetProductsFailedAction,
  GetProductsSuccessAction,
  GetRequiredFieldsAction,
  GetRequiredFieldsCompleteAction,
  GetRequiredFieldsFailedAction,
  JccAppointmentsActions,
  JccAppointmentsActionTypes,
} from './jcc-appointments-actions';
import { getLocations, getProductDetails, getSelectedProductsIds } from './jcc-appointments.state';
import { fixProductDetails, fixProductsDetailsMapping } from './util';

const enum ApiCalls {
  GET_APPOINTMENTS = 'jcc.get_appointments',
  ADD_TO_CALENDAR = 'jcc.add_to_calendar',
  EnableSecureAppointmentLinks = 'EnableSecureAppointmentLinks',
  GetAppIdBySecureLink = 'GetAppIdBySecureLink',
  GetAppointmentFieldSettings = 'GetAppointmentFieldSettings',
  GetAppointmentFields = 'GetAppointmentFields',
  GetAppointmentQRCodeText = 'GetAppointmentQRCodeText',
  GetDayPartPeriods = 'GetDayPartPeriods',
  GetLanguages = 'GetLanguages',
  GetRequiredClientFieldsExtended = 'GetRequiredClientFieldsExtended',
  GetRequiredClientFields = 'GetRequiredClientFields',
  GetSecureLinkIdByAppId = 'GetSecureLinkIdByAppId',
  MidofficeRequest = 'MidofficeRequest',
  RequestAddAppointment = 'RequestAddAppointment',
  RequestRemoveAppointment = 'RequestRemoveAppointment',
  RequestUpdateAppointment = 'RequestUpdateAppointment',
  SendAppointmentEmail = 'SendAppointmentEmail',
  SetGovCaseIDToAppointmentID = 'SetGovCaseIDToAppointmentID',
  bookGovAppointmentExtendedDetails = 'bookGovAppointmentExtendedDetails',
  bookGovAppointment = 'bookGovAppointment',
  deleteGovAppointment = 'deleteGovAppointment',
  getGovAppointmentDetails = 'getGovAppointmentDetails',
  getGovAppointmentDuration = 'getGovAppointmentDuration',
  getGovAppointmentExtendedDetails = 'getGovAppointmentExtendedDetails',
  getGovAppointmentTimeUnit = 'getGovAppointmentTimeUnit',
  getGovAppointmentsBSN = 'getGovAppointmentsBSN',
  getGovAppointmentsByClientID = 'getGovAppointmentsByClientID',
  getGovAppointmentsCase = 'getGovAppointmentsCase',
  getGovAppointments = 'getGovAppointments',
  getGovAvailableDays = 'getGovAvailableDays',
  getGovAvailableProductsByProduct = 'getGovAvailableProductsByProduct',
  getGovAvailableProducts = 'getGovAvailableProducts',
  getGovAvailableTimesPerDay = 'getGovAvailableTimesPerDay',
  getGovLatestPlanDate = 'getGovLatestPlanDate',
  getGovLocationDetails = 'getGovLocationDetails',
  getGovLocationsForProduct = 'getGovLocationsForProduct',
  getGovLocations = 'getGovLocations',
  getGovProductDetails = 'getGovProductDetails',
  updateGovAppointmentExtendedDetails = 'updateGovAppointmentExtendedDetails',
  updateGovAppointment = 'updateGovAppointment',
  updateGovAppointmentWithFieldsExtendedDetails = 'updateGovAppointmentWithFieldsExtendedDetails',
  updateGovAppointmentWithFields = 'updateGovAppointmentWithFields',
}

@Injectable()
export class JccAppointmentsEffects {
  @Effect() getAppointments$ = this.actions$.pipe(
    ofType<GetAppointmentsAction>(JccAppointmentsActionTypes.GET_APPOINTMENTS),
    switchMap(action => this.rogerthatService.apiCall<AppointmentsList>(ApiCalls.GET_APPOINTMENTS).pipe(
      map(result => new GetAppointmentsSuccessAction({ ...result, products: fixProductsDetailsMapping(result.products) })),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new GetAppointmentsFailedAction(err));
      })),
    ));

  @Effect() deleteAppointment$ = this.actions$.pipe(
    ofType<CancelAppointmentAction>(JccAppointmentsActionTypes.CANCEL_APPOINTMENT),
    switchMap(action => this.rogerthatService.apiCall<DeleteGovAppointmentResponse>(ApiCalls.deleteGovAppointment, action.payload).pipe(
      map(result => {
        if (result === DeleteAppointmentUpdateStatus.SUCCESS) {
          return new CancelAppointmentSuccessAction({ appointmentID: action.payload.appID });
        } else {
          const err = this.deleteStatusToError(result);
          this.errorService.showErrorDialog(action, err);
          return new CancelAppointmentFailedAction(err);
        }
      }),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new CancelAppointmentFailedAction(err));
      })),
    ));

  @Effect() getAllProductDetails$ = this.actions$.pipe(
    ofType<GetProductsAction>(JccAppointmentsActionTypes.GET_PRODUCTS),
    switchMap(action => this.rogerthatService.apiCall<Product[]>(ApiCalls.getGovAvailableProducts).pipe(
      map(result => new GetProductsSuccessAction(result)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new GetProductsFailedAction(err));
      })),
    ));

  @Effect() getAvailableProductsByProduct$ = this.actions$.pipe(
    ofType<GetProductsByProductsAction>(JccAppointmentsActionTypes.GET_PRODUCTS_BY_PRODUCTS),
    switchMap(action => this.rogerthatService.apiCall<Product[]>(ApiCalls.getGovAvailableProductsByProduct, action.payload).pipe(
      map(result => new GetProductsByProductsSuccessAction(result)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new GetProductsByProductsFailedAction(err));
      })),
    ));

  @Effect() addOrDeleteProductSideEffect$ = this.actions$.pipe(
    ofType<AddProductAction | DeleteProductAction>(JccAppointmentsActionTypes.ADD_PRODUCT, JccAppointmentsActionTypes.DELETE_PRODUCT),
    withLatestFrom(
      this.store.pipe(select(getSelectedProductsIds)),
    ),
    // Wait for result of GetLocationsForProductAction as we need the locations
    switchMap(([, productIds]) => this.store.pipe(
      select(getLocations),
      filter(result => result.length > 0),
      map(locations => new GetProductsByProductsAction({
        ProductNr: productIds.join(','),
        LocatieID: locations.map(loc => loc.locationID).join(','),
      })),
    )));

  @Effect({ dispatch: false }) addOrDeleteProductSecondSideEffect$ = this.actions$.pipe(
    ofType<AddProductAction | DeleteProductAction>(JccAppointmentsActionTypes.ADD_PRODUCT, JccAppointmentsActionTypes.DELETE_PRODUCT),
    withLatestFrom(this.store.pipe(select(getSelectedProductsIds)), this.store.pipe(select(getLocations))),
    map(([, productIds, locations]) => {
      // Not needed in case there's only one location as the same location will be returned again
      if (locations.length !== 1 && productIds.length > 0) {
        this.store.dispatch(new GetLocationsForProductAction({ productID: productIds.join(',') }));
      }
    }),
  );

  @Effect({ dispatch: false }) getProductDetails$ = this.actions$.pipe(
    ofType<GetProductDetailsAction>(JccAppointmentsActionTypes.GET_PRODUCT_DETAILS),
    withLatestFrom(this.store.pipe(select(getProductDetails))),
    switchMap(([action, productDetails]) => {
        const productId = action.payload.productID;
        if (!(productId in productDetails)) {
          return this.rogerthatService.apiCall<ProductDetails>(ApiCalls.getGovProductDetails, action.payload).pipe(
            map(result => this.store.dispatch(new GetProductDetailsSuccessAction({ productId, product: fixProductDetails(result) }))),
            catchError(err => {
              this.errorService.showErrorDialog(action, err);
              this.store.dispatch(new GetProductDetailsFailedAction(err));
              return of();
            }));
        }
        return of();
      },
    ));

  @Effect() getLocationsForProducts$ = this.actions$.pipe(
    ofType<GetLocationsForProductAction>(JccAppointmentsActionTypes.GET_LOCATIONS_FOR_PRODUCTS),
    switchMap(action => this.rogerthatService.apiCall<JccLocation[]>(ApiCalls.getGovLocationsForProduct, action.payload).pipe(
      map(result => new GetLocationsForProductSuccessAction(result)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new GetLocationsForProductFailedAction(err));
      })),
    ));

  @Effect() getAvailableDays$ = this.actions$.pipe(
    ofType<GetAvailableDaysAction>(JccAppointmentsActionTypes.GET_AVAILABLE_DAYS),
    switchMap(action => this.rogerthatService.apiCall<AvailableDays>(ApiCalls.getGovAvailableDays, action.payload).pipe(
      map(result => new GetAvailableDaysSuccessAction(result)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new GetAvailableDaysFailedAction(err));
      })),
    ));

  @Effect() getAvailableTimes$ = this.actions$.pipe(
    ofType<GetAvailableTimesAction>(JccAppointmentsActionTypes.GET_TIMES_FOR_DAY),
    switchMap(action => this.rogerthatService.apiCall<AvailableTimes>(ApiCalls.getGovAvailableTimesPerDay, action.payload).pipe(
      map(result => new GetAvailableTimesSuccessAction(result)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new GetAvailableTimesFailedAction(err));
      })),
    ));

  @Effect() getRequiredFields$ = this.actions$.pipe(
    ofType<GetRequiredFieldsAction>(JccAppointmentsActionTypes.GET_REQUIRED_FIELDS),
    switchMap(action => this.rogerthatService.apiCall<GetRequiredClientFieldsResponse>(ApiCalls.GetRequiredClientFields, action.payload).pipe(
      map(result => new GetRequiredFieldsCompleteAction(result)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new GetRequiredFieldsFailedAction(err));
      })),
    ));

  @Effect() createAppointment$ = this.actions$.pipe(
    ofType<CreateAppointmentAction | CreateExtendedAppointmentAction>(JccAppointmentsActionTypes.CREATE_APPOINTMENT,
      JccAppointmentsActionTypes.CREATE_EXTENDED_APPOINTMENT),
    switchMap(action => {
        // tslint:disable-next-line:max-line-length
        const method = action instanceof CreateExtendedAppointmentAction ? ApiCalls.bookGovAppointmentExtendedDetails : ApiCalls.bookGovAppointment;
        // tslint:disable-next-line:max-line-length
        return this.rogerthatService.apiCall<BookGovAppointmentResponse | BookGovAppointmentExtendedDetailsResponse>(method, action.payload).pipe(
          map(result => {
            if (result.updateStatus === AppointmentUpdateStatus.SUCCESS) {
              return new CreateAppointmentCompleteAction(result);
            } else {
              const err = this.appointmentStatusToError(result.updateStatus);
              this.errorService.showErrorDialog(action, err);
              return new CreateAppointmentFailedAction(err);
            }
          }),
          catchError(err => {
            this.errorService.showErrorDialog(action, err);
            return of(new CreateAppointmentFailedAction(err));
          }));
      },
    ));

  @Effect() addToCalendar$ = this.actions$.pipe(
    ofType<AddToCalendarAction>(JccAppointmentsActionTypes.ADD_TO_CALENDAR),
    switchMap(action => this.rogerthatService.apiCall<{ message: string }>(ApiCalls.ADD_TO_CALENDAR, action.payload).pipe(
      map(result => new AddToCalendarCompleteAction(result)),
      tap(result => this.showDialog(result.payload.message)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new AddToCalendarCompleteAction(err));
      })),
    ));

  @Effect() afterCreateAppointment$ = this.actions$.pipe(
    ofType<CreateAppointmentCompleteAction>(JccAppointmentsActionTypes.CREATE_APPOINTMENT_SUCCESS),
    map(() => new GetAppointmentsAction()),
  );

  constructor(private actions$: Actions<JccAppointmentsActions>,
              private store: Store<AppState>,
              private alertController: AlertController,
              private translate: TranslateService,
              private router: Router,
              private location: Location,
              private rogerthatService: RogerthatService,
              private errorService: ErrorService) {
  }

  private async showDialog(message: string) {
    const dialog = await this.alertController.create({
      message, buttons: [
        { text: this.translate.instant('app.oca.close') },
      ],
    });
    await dialog.present();
  }

  private deleteStatusToError(status: Exclude<DeleteAppointmentUpdateStatus, DeleteAppointmentUpdateStatus.SUCCESS>): string {
    const mapping = {
      [ DeleteAppointmentUpdateStatus.UNKNOWN_ERROR ]: 'app.oca.unknown_error',
      [ DeleteAppointmentUpdateStatus.APPOINTMENT_NOT_FOUND_OR_EXPIRED ]: 'app.oca.appointment_not_found',
    };
    const key = mapping[ status ] || 'app.oca.unknown_error';
    return this.translate.instant(key);
  }

  private appointmentStatusToError(appointmentStatus: Exclude<AppointmentUpdateStatus, AppointmentUpdateStatus.SUCCESS>): string {
    const mapping = {
      [ AppointmentUpdateStatus.UNKNOWN_ERROR ]: 'app.oca.unknown_error',
      [ AppointmentUpdateStatus.START_DATE_IN_PAST ]: 'app.oca.jcc_errors.1',
      [ AppointmentUpdateStatus.LOCATION_NOT_FOUND ]: 'app.oca.jcc_errors.3',
      [ AppointmentUpdateStatus.NO_CLIENT_NAME_SUPPLIED ]: 'app.oca.jcc_errors.4',
      [ AppointmentUpdateStatus.NO_PLANNER_OBJECT_AVAILABLE ]: 'app.oca.jcc_errors.5',
      [ AppointmentUpdateStatus.PLANNER_OBJECT_OVERLAPS ]: 'app.oca.jcc_errors.6',
      [ AppointmentUpdateStatus.INVALID_PRODUCT_NUMBERS ]: 'app.oca.jcc_errors.7',
      [ AppointmentUpdateStatus.MISSING_CLIENT_FIELDS ]: 'app.oca.jcc_errors.12',
      [ AppointmentUpdateStatus.CLIENT_ID_NOT_FOUND ]: 'app.oca.jcc_errors.13',
      [ AppointmentUpdateStatus.INVALID_FIELD ]: 'app.oca.jcc_errors.14',
      [ AppointmentUpdateStatus.NATIONALITY_AND_OTHER_NATIONALITY_CANNOT_BE_COMBINED ]: 'app.oca.jcc_errors.15',
    };
    const key = mapping[ appointmentStatus ] || 'app.oca.unknown_error';
    return this.translate.instant(key);
  }
}
