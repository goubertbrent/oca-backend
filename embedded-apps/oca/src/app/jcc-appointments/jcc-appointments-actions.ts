import { Action } from '@ngrx/store';
import {
  AppointmentsList,
  AvailableDays,
  AvailableTimes,
  BookGovAppointmentExtendedDetailsRequest,
  BookGovAppointmentExtendedDetailsResponse,
  BookGovAppointmentRequest,
  BookGovAppointmentResponse,
  DeleteGovAppointmentRequest,
  GetRequiredClientFieldsRequest,
  GetRequiredClientFieldsResponse,
  JccLocation,
  Product,
  ProductDetails,
} from './appointments';
import { fixProducts } from './util';

export const enum JccAppointmentsActionTypes {
  GET_APPOINTMENTS = '[jcc] Get appointments',
  GET_APPOINTMENTS_SUCCESS = '[jcc] Get appointments success',
  GET_APPOINTMENTS_FAILED = '[jcc] Get appointments failed',
  CANCEL_APPOINTMENT = '[jcc] Cancel appointment',
  CANCEL_APPOINTMENT_SUCCESS = '[jcc] Cancel appointment success',
  CANCEL_APPOINTMENT_FAILED = '[jcc] Cancel appointment failed',
  GET_PRODUCTS = '[jcc] Get products',
  GET_PRODUCTS_SUCCESS = '[jcc] Get products success',
  GET_PRODUCTS_FAILED = '[jcc] Get products failed',
  GET_PRODUCTS_BY_PRODUCTS = '[jcc] Get products by products',
  GET_PRODUCTS_BY_PRODUCTS_SUCCESS = '[jcc] Get products by products success',
  GET_PRODUCTS_BY_PRODUCTS_FAILED = '[jcc] Get products by products failed',
  GET_PRODUCT_DETAILS = '[jcc] Get product details',
  GET_PRODUCT_DETAILS_COMPLETE = '[jcc] Get product details success',
  GET_PRODUCT_DETAILS_FAILED = '[jcc] Get product details failed',
  GET_LOCATIONS_FOR_PRODUCTS = '[jcc] Get locations for products',
  GET_LOCATIONS_FOR_PRODUCTS_SUCCESS = '[jcc] Get locations for products success',
  GET_LOCATIONS_FOR_PRODUCTS_FAILED = '[jcc] Get locations for products failed',
  GET_AVAILABLE_DAYS = '[jcc] Get available days',
  GET_AVAILABLE_DAYS_SUCCESS = '[jcc] Get available days success',
  GET_AVAILABLE_DAYS_FAILED = '[jcc] Get available days failed',
  GET_TIMES_FOR_DAY = '[jcc] Get times per day',
  GET_TIMES_FOR_DAY_SUCCESS = '[jcc] Get times per day success',
  GET_TIMES_FOR_DAY_FAILED = '[jcc] Get times per day failed',
  CREATE_APPOINTMENT = '[jcc] Create appointment',
  CREATE_EXTENDED_APPOINTMENT = '[jcc] Create extended appointment',
  CREATE_APPOINTMENT_SUCCESS = '[jcc] Create appointment success',
  CREATE_APPOINTMENT_FAILED = '[jcc] Create appointment failed',
  GET_REQUIRED_FIELDS = '[jcc] Get required fields',
  GET_REQUIRED_FIELDS_SUCCESS = '[jcc] Get required fields success',
  GET_REQUIRED_FIELDS_FAILED = '[jcc] Get required fields failed',
  ADD_PRODUCT = '[jcc] Add product',
  UPDATE_PRODUCT = '[jcc] Update product',
  DELETE_PRODUCT = '[jcc] Delete product',
  ADD_TO_CALENDAR = '[jcc] Add to calendar',
  ADD_TO_CALENDAR_SUCCESS = '[jcc] Add to calendar success',
  ADD_TO_CALENDAR_ERROR = '[jcc] Add to calendar failed',
}

export class GetAppointmentsAction implements Action {
  readonly type = JccAppointmentsActionTypes.GET_APPOINTMENTS;

}

export class GetAppointmentsSuccessAction implements Action {
  readonly type = JccAppointmentsActionTypes.GET_APPOINTMENTS_SUCCESS;

  constructor(public payload: AppointmentsList) {
  }
}

export class GetAppointmentsFailedAction implements Action {
  readonly type = JccAppointmentsActionTypes.GET_APPOINTMENTS_FAILED;

  constructor(public error: string) {
  }
}

export class CancelAppointmentAction implements Action {
  readonly type = JccAppointmentsActionTypes.CANCEL_APPOINTMENT;

  constructor(public payload: DeleteGovAppointmentRequest) {
  }

}

export class CancelAppointmentSuccessAction implements Action {
  readonly type = JccAppointmentsActionTypes.CANCEL_APPOINTMENT_SUCCESS;

  constructor(public payload: {appointmentID: string}) {
  }
}

export class CancelAppointmentFailedAction implements Action {
  readonly type = JccAppointmentsActionTypes.CANCEL_APPOINTMENT_FAILED;

  constructor(public error: string) {
  }
}

export class GetProductsAction implements Action {
  readonly type = JccAppointmentsActionTypes.GET_PRODUCTS;

}

export class GetProductsSuccessAction implements Action {
  readonly type = JccAppointmentsActionTypes.GET_PRODUCTS_SUCCESS;

  constructor(public payload: Product[]) {
    fixProducts(payload);
  }
}

export class GetProductsFailedAction implements Action {
  readonly type = JccAppointmentsActionTypes.GET_PRODUCTS_FAILED;

  constructor(public error: string) {
  }
}

export class GetProductsByProductsAction implements Action {
  readonly type = JccAppointmentsActionTypes.GET_PRODUCTS_BY_PRODUCTS;

  constructor(public payload: { ProductNr: string; LocatieID: string; }) {
  }
}

export class GetProductsByProductsSuccessAction implements Action {
  readonly type = JccAppointmentsActionTypes.GET_PRODUCTS_BY_PRODUCTS_SUCCESS;

  constructor(public payload: Product[]) {
    fixProducts(payload);
  }
}

export class GetProductsByProductsFailedAction implements Action {
  readonly type = JccAppointmentsActionTypes.GET_PRODUCTS_BY_PRODUCTS_FAILED;

  constructor(public error: string) {
  }
}

export class GetProductDetailsAction implements Action {
  readonly type = JccAppointmentsActionTypes.GET_PRODUCT_DETAILS;

  constructor(public payload: { productID: string }) {
  }
}

export class GetProductDetailsSuccessAction implements Action {
  readonly type = JccAppointmentsActionTypes.GET_PRODUCT_DETAILS_COMPLETE;

  constructor(public payload: { productId: string; product: ProductDetails }) {
  }
}

export class GetProductDetailsFailedAction implements Action {
  readonly type = JccAppointmentsActionTypes.GET_PRODUCT_DETAILS_FAILED;

  constructor(public error: string) {
  }
}

export class AddProductAction implements Action {
  readonly type = JccAppointmentsActionTypes.ADD_PRODUCT;

  constructor(public payload: { product: Product }) {
  }
}

export class UpdateProductAction implements Action {
  readonly type = JccAppointmentsActionTypes.UPDATE_PRODUCT;

  constructor(public payload: { productId: string; amount: number }) {
  }
}

export class DeleteProductAction implements Action {
  readonly type = JccAppointmentsActionTypes.DELETE_PRODUCT;

  constructor(public payload: { productId: string }) {
  }
}

export class GetLocationsForProductAction implements Action {
  readonly type = JccAppointmentsActionTypes.GET_LOCATIONS_FOR_PRODUCTS;

  constructor(public payload: { productID: string; }) {
  }

}

export class GetLocationsForProductSuccessAction implements Action {
  readonly type = JccAppointmentsActionTypes.GET_LOCATIONS_FOR_PRODUCTS_SUCCESS;

  constructor(public payload: JccLocation[]) {
  }
}

export class GetLocationsForProductFailedAction implements Action {
  readonly type = JccAppointmentsActionTypes.GET_LOCATIONS_FOR_PRODUCTS_FAILED;

  constructor(public error: string) {
  }
}

export class GetAvailableDaysAction implements Action {
  readonly type = JccAppointmentsActionTypes.GET_AVAILABLE_DAYS;

  constructor(public payload: { locationID: string; productID: string; startDate: string; endDate: string; appDuration: number; }) {
  }

}

export class GetAvailableDaysSuccessAction implements Action {
  readonly type = JccAppointmentsActionTypes.GET_AVAILABLE_DAYS_SUCCESS;

  constructor(public payload: AvailableDays) {
  }
}

export class GetAvailableDaysFailedAction implements Action {
  readonly type = JccAppointmentsActionTypes.GET_AVAILABLE_DAYS_FAILED;

  constructor(public error: string) {
  }
}


export class GetAvailableTimesAction implements Action {
  readonly type = JccAppointmentsActionTypes.GET_TIMES_FOR_DAY;

  constructor(public payload: { locationID: string; productID: string; date: string; appDuration: number }) {
  }

}

export class GetAvailableTimesSuccessAction implements Action {
  readonly type = JccAppointmentsActionTypes.GET_TIMES_FOR_DAY_SUCCESS;

  constructor(public payload: AvailableTimes) {
  }
}

export class GetAvailableTimesFailedAction implements Action {
  readonly type = JccAppointmentsActionTypes.GET_TIMES_FOR_DAY_FAILED;

  constructor(public error: string) {
  }
}

export class CreateAppointmentAction implements Action {
  readonly type = JccAppointmentsActionTypes.CREATE_APPOINTMENT;

  constructor(public payload: BookGovAppointmentRequest) {
  }
}

export class CreateExtendedAppointmentAction implements Action {
  readonly type = JccAppointmentsActionTypes.CREATE_EXTENDED_APPOINTMENT;

  constructor(public payload: BookGovAppointmentExtendedDetailsRequest) {
  }
}

export class CreateAppointmentCompleteAction implements Action {
  readonly type = JccAppointmentsActionTypes.CREATE_APPOINTMENT_SUCCESS;

  constructor(public payload: BookGovAppointmentResponse | BookGovAppointmentExtendedDetailsResponse) {
  }
}

export class CreateAppointmentFailedAction implements Action {
  readonly type = JccAppointmentsActionTypes.CREATE_APPOINTMENT_FAILED;

  constructor(public error: string) {
  }
}

export class GetRequiredFieldsAction implements Action {
  readonly type = JccAppointmentsActionTypes.GET_REQUIRED_FIELDS;

  constructor(public payload: GetRequiredClientFieldsRequest) {
  }
}

export class GetRequiredFieldsCompleteAction implements Action {
  readonly type = JccAppointmentsActionTypes.GET_REQUIRED_FIELDS_SUCCESS;

  constructor(public payload: GetRequiredClientFieldsResponse) {
  }
}

export class GetRequiredFieldsFailedAction implements Action {
  readonly type = JccAppointmentsActionTypes.GET_REQUIRED_FIELDS_FAILED;

  constructor(public error: string) {
  }
}

export class AddToCalendarAction implements Action {
  readonly type = JccAppointmentsActionTypes.ADD_TO_CALENDAR;

  constructor(public payload: { appointmentID: string }) {
  }
}

export class AddToCalendarCompleteAction implements Action {
  readonly type = JccAppointmentsActionTypes.ADD_TO_CALENDAR_SUCCESS;

  constructor(public payload: { message: string }) {
  }
}

export class AddToCalendarFailedAction implements Action {
  readonly type = JccAppointmentsActionTypes.ADD_TO_CALENDAR_ERROR;

  constructor(public error: string) {
  }
}

export type JccAppointmentsActions = GetAppointmentsAction
  | GetAppointmentsSuccessAction
  | GetAppointmentsFailedAction
  | CancelAppointmentAction
  | CancelAppointmentSuccessAction
  | CancelAppointmentFailedAction
  | GetProductsAction
  | GetProductsSuccessAction
  | GetProductsFailedAction
  | GetProductsByProductsAction
  | GetProductsByProductsSuccessAction
  | GetProductsByProductsFailedAction
  | GetProductDetailsAction
  | GetProductDetailsSuccessAction
  | GetProductDetailsFailedAction
  | AddProductAction
  | UpdateProductAction
  | DeleteProductAction
  | GetLocationsForProductAction
  | GetLocationsForProductSuccessAction
  | GetLocationsForProductFailedAction
  | GetAvailableDaysAction
  | GetAvailableDaysSuccessAction
  | GetAvailableDaysFailedAction
  | GetAvailableTimesAction
  | GetAvailableTimesSuccessAction
  | GetAvailableTimesFailedAction
  | CreateAppointmentAction
  | CreateExtendedAppointmentAction
  | CreateAppointmentCompleteAction
  | CreateAppointmentFailedAction
  | GetRequiredFieldsAction
  | GetRequiredFieldsCompleteAction
  | GetRequiredFieldsFailedAction
  | AddToCalendarAction
  | AddToCalendarCompleteAction
  | AddToCalendarFailedAction;



