import { Action } from '@ngrx/store';
import {
  Appointment,
  CreateAppointment,
  ListAppointments,
  ListBranches,
  ListDates,
  ListServices,
  ListTimes,
  QMaticCustomer,
} from './appointments';

export const enum QMaticActionTypes {
  GET_APPOINTMENTS = '[q-matic] Get appointments',
  GET_APPOINTMENTS_SUCCESS = '[q-matic] Get appointments complete',
  GET_APPOINTMENTS_FAILED = '[q-matic] Get appointments failed',
  GET_SERVICES = '[q-matic] Get services',
  GET_SERVICES_SUCCESS = '[q-matic] Get services complete',
  GET_SERVICES_FAILED = '[q-matic] Get services failed',
  GET_BRANCHES = '[q-matic] Get branches',
  GET_BRANCHES_SUCCESS = '[q-matic] Get branches complete',
  GET_BRANCHES_FAILED = '[q-matic] Get branches failed',
  GET_DATES = '[q-matic] Get dates',
  GET_DATES_SUCCESS = '[q-matic] Get dates complete',
  GET_DATES_FAILED = '[q-matic] Get dates failed',
  GET_TIMES = '[q-matic] Get times',
  GET_TIMES_SUCCESS = '[q-matic] Get times complete',
  GET_TIMES_FAILED = '[q-matic] Get times failed',
  RESERVE_DATE = '[q-matic] Reserve date',
  RESERVE_DATE_SUCCESS = '[q-matic] Reserve date complete',
  RESERVE_DATE_FAILED = '[q-matic] Reserve date failed',
  CONFIRM_APPOINTMENT = '[q-matic] Confirm appointment',
  CONFIRM_APPOINTMENT_SUCCESS = '[q-matic] Confirm appointment complete',
  CONFIRM_APPOINTMENT_FAILED = '[q-matic] Confirm appointment failed',
  CANCEL_APPOINTMENT = '[q-matic] Cancel appointment',
  CANCEL_APPOINTMENT_SUCCESS = '[q-matic] Cancel appointment complete',
  CANCEL_APPOINTMENT_FAILED = '[q-matic] Cancel appointment failed',
  CREATE_ICAL = '[q-matic] Create iCal file',
  CREATE_ICAL_SUCCESS = '[q-matic] Create iCal file complete',
  CREATE_ICAL_FAILED = '[q-matic] Create iCal file failed',
}

export class GetAppointmentsAction implements Action {
  readonly type = QMaticActionTypes.GET_APPOINTMENTS;

}

export class GetAppointmentsSuccessAction implements Action {
  readonly type = QMaticActionTypes.GET_APPOINTMENTS_SUCCESS;

  constructor(public payload: ListAppointments) {
  }
}

export class GetAppointmentsFailedAction implements Action {
  readonly type = QMaticActionTypes.GET_APPOINTMENTS_FAILED;

  constructor(public error: string) {
  }
}

export class GetServicesAction implements Action {
  readonly type = QMaticActionTypes.GET_SERVICES;
}

export class GetServicesSuccessAction implements Action {
  readonly type = QMaticActionTypes.GET_SERVICES_SUCCESS;

  constructor(public payload: ListServices) {
  }
}

export class GetServicesFailedAction implements Action {
  readonly type = QMaticActionTypes.GET_SERVICES_FAILED;

  constructor(public error: string) {
  }
}

export class GetBranchesAction implements Action {
  readonly type = QMaticActionTypes.GET_BRANCHES;

  constructor(public payload: { service_id: string; }) {
  }
}

export class GetBranchesSuccessAction implements Action {
  readonly type = QMaticActionTypes.GET_BRANCHES_SUCCESS;

  constructor(public payload: ListBranches) {
  }
}

export class GetBranchesFailedAction implements Action {
  readonly type = QMaticActionTypes.GET_BRANCHES_FAILED;

  constructor(public error: string) {
  }
}

export class GetDatesAction implements Action {
  readonly type = QMaticActionTypes.GET_DATES;

  constructor(public payload: { service_id: string; branch_id: string; }) {
  }
}

export class GetDatesSuccessAction implements Action {
  readonly type = QMaticActionTypes.GET_DATES_SUCCESS;

  constructor(public payload: ListDates) {
  }
}

export class GetDatesFailedAction implements Action {
  readonly type = QMaticActionTypes.GET_DATES_FAILED;

  constructor(public error: string) {
  }
}

export class GetTimesAction implements Action {
  readonly type = QMaticActionTypes.GET_TIMES;

  constructor(public payload: { service_id: string; branch_id: string; date: string; }) {
  }
}

export class GetTimesSuccessAction implements Action {
  readonly type = QMaticActionTypes.GET_TIMES_SUCCESS;

  constructor(public payload: ListTimes) {
  }
}

export class GetTimesFailedAction implements Action {
  readonly type = QMaticActionTypes.GET_TIMES_FAILED;

  constructor(public error: string) {
  }
}

export class ReserveDateAction implements Action {
  readonly type = QMaticActionTypes.RESERVE_DATE;

  constructor(public payload: { service_id: string; branch_id: string; date: string; time: string; notes: string | null; customer: Partial<QMaticCustomer>; title: string }) {
  }
}

export class ReserveDateSuccessAction implements Action {
  readonly type = QMaticActionTypes.RESERVE_DATE_SUCCESS;

  constructor(public payload: Appointment) {
  }
}

export class ReserveDateFailedAction implements Action {
  readonly type = QMaticActionTypes.RESERVE_DATE_FAILED;

  constructor(public error: string) {
  }
}

export class ConfirmAppointmentAction implements Action {
  readonly type = QMaticActionTypes.CONFIRM_APPOINTMENT;

  constructor(public payload: CreateAppointment) {
  }
}

export class ConfirmAppointmentSuccessAction implements Action {
  readonly type = QMaticActionTypes.CONFIRM_APPOINTMENT_SUCCESS;

  constructor(public payload: Appointment) {
  }
}

export class ConfirmAppointmentFailedAction implements Action {
  readonly type = QMaticActionTypes.CONFIRM_APPOINTMENT_FAILED;

  constructor(public error: string) {
  }
}

export class CancelAppointmentAction implements Action {
  readonly type = QMaticActionTypes.CANCEL_APPOINTMENT;

  constructor(public payload: { appointment_id: string }) {
  }
}

export class CancelAppointmentSuccessAction implements Action {
  readonly type = QMaticActionTypes.CANCEL_APPOINTMENT_SUCCESS;

  constructor(public payload: { appointment_id: string }) {
  }
}

export class CancelAppointmentFailedAction implements Action {
  readonly type = QMaticActionTypes.CANCEL_APPOINTMENT_FAILED;

  constructor(public error: string) {
  }
}

export class CreateIcalAction implements Action {
  readonly type = QMaticActionTypes.CREATE_ICAL;

  constructor(public payload: { appointment_id: string }) {
  }
}

export class CreateIcalSuccessAction implements Action {
  readonly type = QMaticActionTypes.CREATE_ICAL_SUCCESS;

  constructor(public payload: { message: string }) {
  }
}

export class CreateIcalFailedAction implements Action {
  readonly type = QMaticActionTypes.CREATE_ICAL_FAILED;

  constructor(public error: string) {
  }
}

export type QMaticActions = GetAppointmentsAction
  | GetAppointmentsSuccessAction
  | GetAppointmentsFailedAction
  | GetServicesAction
  | GetServicesSuccessAction
  | GetServicesFailedAction
  | GetBranchesAction
  | GetBranchesSuccessAction
  | GetBranchesFailedAction
  | GetDatesAction
  | GetDatesSuccessAction
  | GetDatesFailedAction
  | GetTimesAction
  | GetTimesSuccessAction
  | GetTimesFailedAction
  | ReserveDateAction
  | ReserveDateSuccessAction
  | ReserveDateFailedAction
  | ConfirmAppointmentAction
  | ConfirmAppointmentSuccessAction
  | ConfirmAppointmentFailedAction
  | CancelAppointmentAction
  | CancelAppointmentSuccessAction
  | CancelAppointmentFailedAction
  | CreateIcalAction
  | CreateIcalSuccessAction
  | CreateIcalFailedAction;

