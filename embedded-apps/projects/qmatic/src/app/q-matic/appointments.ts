export enum QMaticRequiredField {
  EMAIL = 'email',
  PHONE_NUMBER = 'phone-number'
}

export interface QmaticClientSettings {
  required_fields: QMaticRequiredField[];
}

export interface ListAppointments {
  meta: ListResultMeta;
  notifications: any[];
  appointmentList: Appointment[];
}

export interface ListResultMeta {
  arguments: { [ key: string ]: string };
  end: string;
  fields: string;
  limit: null;
  offset: number | null;
  start: string;
  totalResults: number;
}

export interface QMaticCustomServiceData {
  cancelEnabled?: boolean;
  infoText?: string;
  notesFieldEnabled?: boolean;
  rescheduleEnabled?: boolean;
  emails?: string;
  servicenametranslations?: unknown[];
  hisId?: string;
}

export interface QMaticService {
  active: boolean;
  additionalCustomerDuration: number;
  created: number;
  /**
   * possibly contains json
   * @see QMaticCustomServiceData
   */
  custom: string | null;
  duration: number;
  name: string;
  publicEnabled: boolean;
  publicId: string;
  updated: number;
}

export interface ListServices {
  meta: ListResultMeta;
  notifications: any[];
  serviceList: QMaticService[];
}

export interface QMaticBranch {
  addressCity: string;
  addressCountry: string;
  addressLine1: string;
  addressLine2: string;
  addressState: string | null;
  addressZip: string | null;
  branchPrefix: string | null;
  created: number;
  custom: string | null;
  email: string | null;
  fullTimeZone: string;
  latitude: number | null;
  longitude: number | null;
  name: string;
  phone: string | null;
  publicId: string;
  timeZone: string;
  updated: number;
}

export interface ListBranches {
  meta: ListResultMeta;
  notifications: any[];
  branchList: QMaticBranch[];
}

export interface ListDates {
  meta: ListResultMeta;
  notifications: any[];
  /**
   * ISO date string 2019-10-10T00:00:00
   */
  dates: string[];
}

export interface ListTimes {
  meta: ListResultMeta;
  notifications: any[];
  /**
   * HH:MM
   */
  times: string[];
}

export enum AppointmentStatus {
  RESERVED = 10,
  BOOKED = 20,
  NEVER_ARRIVED = 54,
}

export interface QMaticCustomer {
  addressCity: string | null;
  addressCountry: string | null;
  addressLine1: string | null;
  addressLine2: string | null;
  addressState: string | null;
  addressZip: string | null;
  consentIdentifier: string | null;
  consentTimestamp: number | null;
  created: number;
  custom: string | null;
  dateOfBirth: string | null;
  dateOfBirthWithoutTime: string | null;
  deletionTimestamp: string; // 2019-11-09T14:47:44.935+0000
  email: string | null;
  externalId: string;
  firstName: string | null;
  identificationNumber: string | null;
  lastInteractionTimestamp: string; // 2019-10-10T14:47:44.935+0000
  lastName: string | null;
  name: string | null;
  phone: string | null;
  publicId: string;
  retentionPolicy: string;
  updated: string | null;
}

export interface Appointment<DateType = string> {
  allDay: boolean;
  blocking: boolean;
  branch: QMaticBranch;
  created: number;
  custom: string | null;
  customSlotLength: null;
  customers: QMaticCustomer[];
  end: DateType; // 2019-10-10T14:55:00.000+0000
  notes: string | null;
  numberOfCustomers: number;
  publicId: string;
  resource: { custom: string | null, name: string; };
  services: QMaticService[];
  start: DateType; // 2019-10-10T14:55:00.000+0000
  status: AppointmentStatus;
  title: string;
  updated: number;
}

export interface CreateAppointment {
  reservation_id: string;
  title: string;
  customer: Partial<QMaticCustomer>;
  notes: string | null;
}

export function getDateString(date: Date): string {
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const day = date.getDate().toString().padStart(2, '0');
  return `${date.getFullYear()}-${month}-${day}`;
}
