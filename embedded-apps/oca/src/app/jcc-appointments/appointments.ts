export interface Product {
  productMaxCountForEvent: number;
  productCode: string | null;
  productId: string;
  productDesc: string;
}

export interface ProductDetails {
  description: string;
  appDuration: number;
  requisites: string[] | string;
  maxCountForEvent: number;
}

export interface BasicClientDetails {
  clientID?: string;
  clientLastName: string;
  clientSex?: string;
  clientDateOfBirth: string;
  clientInitials?: string;
  clientAddress?: string;
  clientPostalCode?: string;
  clientCity?: string;
  clientCountry?: string;
  clientTel?: string;
  clientMail?: string;
  clientLanguage?: string;
}

export interface ClientDetails extends BasicClientDetails {
  clientFirstName?: string;
  clientLastNamePrefix?: string;
  clientBirthdayCompleteness?: 'Complete' | null;
  clientStreetName?: string;
  clientHouseNumber?: string;
  clientHouseNumberSuffix?: string;
  clientMobile?: string;
  clientNationality?: string;
  clientCustomNationality?: string;
}

export interface AppointmentDetailsType {
  productID?: string;
  clientID?: string;
  clientLastName: string;
  clientSex?: string;
  clientDateOfBirth: string;
  clientInitials?: string;
  clientAddress?: string;
  clientPostalCode?: string;
  clientCity?: string;
  clientCountry?: string;
  clientTel?: string;
  clientMail?: string;
  locationID?: string;
  appStartTime: string;
  appEndTime: string;
  appointmentDesc?: string;
  caseID?: string;
  isClientVerified: boolean;
  clientLanguage?: string;
}

export const APPOINTMENT_DETAILS_FIELDS = [
  'productID',
  'clientID',
  'clientLastName',
  'clientSex',
  'clientDateOfBirth',
  'clientInitials',
  'clientAddress',
  'clientPostalCode',
  'clientCity',
  'clientCountry',
  'clientTel',
  'clientMail',
  'locationID',
  'appStartTime',
  'appEndTime',
  'appointmentDesc',
  'caseID',
  'isClientVerified',
  'clientLanguage',
];

export interface AppointmentExtendedDetails extends ClientDetails {
  appointmentID?: string;
  productID?: string;
  productDescription?: string;
  locationID?: string;
  locationDescription?: string;
  appStartTime: string;
  appEndTime: string;
  appointmentDescription?: string;
  caseID?: string;
  isClientVerified: boolean;
}

export interface JccLocation {
  locationID: string;
  locationDesc: string;
  locationOpeningHours?: {
    day: number;
    fromTime1: string;
    tillTime1: string;
    fromTime2: string;
    tillTime2: string;
    fromTime3: string;
    tillTime3: string;
  }[];
}

export interface LocationDetails {
  locationDesc: string;
  address: string;
  postalcode: string;
  city: string;
  telephone: string;
}

export const enum AppointmentUpdateStatus {
  UNKNOWN_ERROR = -1,
  SUCCESS = 0,
  START_DATE_IN_PAST = 1,
  LOCATION_NOT_FOUND = 3,
  NO_CLIENT_NAME_SUPPLIED = 4,
  NO_PLANNER_OBJECT_AVAILABLE = 5,
  PLANNER_OBJECT_OVERLAPS = 6,
  INVALID_PRODUCT_NUMBERS = 7,
  MISSING_CLIENT_FIELDS = 12,
  CLIENT_ID_NOT_FOUND = 13,
  INVALID_FIELD = 14,
  NATIONALITY_AND_OTHER_NATIONALITY_CANNOT_BE_COMBINED = 15,

}

export interface CustomField {
  name: string;
  value: string;
}

export interface BookGovAppointmentExtendedDetailsRequest {
  appDetail: AppointmentExtendedDetails;
  fields?: CustomField[];
}

export interface BookGovAppointmentRequest {
  appDetail: AppointmentDetailsType;
  fields?: CustomField[];
}

export interface BookGovAppointmentResponse {
  updateStatus: AppointmentUpdateStatus;
  appID: string;
}

export type BookGovAppointmentExtendedDetailsResponse = BookGovAppointmentResponse;

export interface GetRequiredClientFieldsRequest {
  productID: string;
}

export interface DeleteGovAppointmentRequest {
  appID: string;
}

export const enum DeleteAppointmentUpdateStatus {
  SUCCESS = 0,
  UNKNOWN_ERROR = 1,
  APPOINTMENT_NOT_FOUND_OR_EXPIRED,
}

export type DeleteGovAppointmentResponse = DeleteAppointmentUpdateStatus;

export type GetRequiredClientFieldsResponse = (keyof AppointmentExtendedDetails)[];

export type Locations = JccLocation[];
export type AvailableDays = string[];  // Format: 2019-11-27
export type AvailableTimes = string[];  // Format: 2019-11-27T08:30:00

/** internal types */
export interface AppointmentsList {
  appointments: Required<AppointmentExtendedDetails>[];
  products: {
    [ key: string ]: ProductDetails;
  };
  locations: {
    [ key: string ]: LocationDetails;
  };
}

export interface AppointmentListItem {
  appointment: Required<AppointmentExtendedDetails>;
  location: LocationDetails;
  products: SelectedProduct[];
}

export interface SelectedProduct {
  id: string;
  productDetails: ProductDetails;
  amount: number;
}

export interface SelectedProductsMapping {
  [ key: string ]: number;
}

export interface BaseFormField {
  Name: keyof AppointmentExtendedDetails;
  Description: string | null;
  InputTitle: string | null;
  IsRequired: boolean;
  IsVisible: boolean;
  AutoCompleteAttribute: string | null;
}

export interface FormFieldInput extends BaseFormField {
  DataType: 'text' | 'tel' | 'email' | 'number' | 'textarea' | 'date';
}

export interface FormFieldSelect extends BaseFormField {
  DataType: 'select';
  Choices: { value: string; label: string }[];
}

export type JccFormField = FormFieldInput | FormFieldSelect;

// InputTitle is currently not used
export const FORM_FIELDS: JccFormField[] = [
//   {
//   Name: 'clientBirthdayCompleteness',
//   Description: null,
//   InputTitle: null,
//   IsRequired: false,
//   IsVisible: false,
//   DataType: 'text',
//   AutoCompleteAttribute: null,
// },
  {
    Name: 'clientSex',
    Description: 'app.oca.gender',
    InputTitle: 'Selecteer je gewenste aanhef',
    IsRequired: false,
    IsVisible: true,
    DataType: 'select',
    Choices: [{ value: 'M', label: 'app.oca.male' }, { value: 'F', label: 'app.oca.female' }],
    AutoCompleteAttribute: 'sex',
  }, {
    Name: 'clientFirstName',
    Description: 'app.oca.first_name',
    InputTitle: 'Vul hier je voornaam of initialen in',
    IsRequired: false,
    IsVisible: false,
    DataType: 'text',
    AutoCompleteAttribute: 'given-name',
  }, {
    Name: 'clientInitials',
    Description: 'app.oca.first_name',
    InputTitle: 'Voer hier uw initialen in',
    IsRequired: false,
    IsVisible: false,
    DataType: 'text',
    AutoCompleteAttribute: 'off',
  }, {
    Name: 'clientLastNamePrefix',
    Description: 'Tussenvoegsel',
    InputTitle: 'Voer hier uw tussenvoegsel in',
    IsRequired: false,
    IsVisible: false,
    DataType: 'text',
    AutoCompleteAttribute: 'off',
  }, {
    Name: 'clientLastName',
    Description: 'app.oca.last_name',
    InputTitle: 'Vul hier je achternaam in',
    IsRequired: true,
    IsVisible: true,
    DataType: 'text',
    AutoCompleteAttribute: 'family-name',
  }, {
    Name: 'clientAddress',
    Description: 'app.oca.address',
    InputTitle: 'Vul hier je straat en huisnummer in',
    IsRequired: false,
    IsVisible: false,
    DataType: 'text',
    AutoCompleteAttribute: 'street-address',
  }, {
    Name: 'clientID',
    Description: 'app.oca.national_insurance_number',
    InputTitle: 'Vul hier je BSN (Burgerservicenummer) in',
    IsRequired: false,
    IsVisible: false,
    DataType: 'text',
    AutoCompleteAttribute: 'off',
  }, {
    Name: 'clientLanguage',
    Description: 'app.oca.language',
    InputTitle: 'Kies hier uw gewenste taal',
    IsRequired: false,
    IsVisible: false,
    DataType: 'text',
    AutoCompleteAttribute: 'language',
  }, {
    Name: 'clientNationality',
    Description: 'app.oca.nationality',
    InputTitle: 'Kies hier uw nationaliteit',
    IsRequired: false,
    IsVisible: false,
    DataType: 'select',
    Choices: [
      { value: 'NL', label: 'app.oca.dutch' },
      { value: 'BE', label: 'app.oca.belgian' },
      { value: 'FR', label: 'app.oca.french' },
      { value: 'DE', label: 'app.oca.german' },
      { value: '', label: 'app.oca.other' }],
    AutoCompleteAttribute: 'off',
  }, {
    Name: 'clientCustomNationality',
    Description: 'app.oca.other_nationality',
    InputTitle: 'Vul hier uw nationaliteit in als deze niet voorkomt bij het veld nationaliteit.',
    IsRequired: false,
    IsVisible: false,
    DataType: 'text',
    AutoCompleteAttribute: 'off',
  }, {
    Name: 'clientDateOfBirth',
    Description: 'app.oca.birth_date',
    InputTitle: 'Vul hier je geboortedatum in',
    IsRequired: false,
    IsVisible: true,
    DataType: 'date',
    AutoCompleteAttribute: 'bday',
  }, {
    Name: 'clientMail',
    Description: 'app.oca.email',
    InputTitle: 'Vul hier je e-mailadres in. Je e-mailadres wordt gebruikt ter bevestiging van je afspraak.',
    IsRequired: true,
    IsVisible: true,
    DataType: 'email',
    AutoCompleteAttribute: 'email',
  }, {
    Name: 'clientTel',
    Description: 'app.oca.phone',
    InputTitle: 'Voer hier uw telefoonnumer in',
    IsRequired: false,
    IsVisible: false,
    DataType: 'tel',
    AutoCompleteAttribute: 'tel-national',
  }, {
    Name: 'clientMobile',
    Description: 'Tapp.oca.mobile_phone',
    InputTitle: 'Voer hier uw mobiele telefoonnummer in',
    IsRequired: false,
    IsVisible: false,
    DataType: 'tel',
    AutoCompleteAttribute: 'tel-national',
  }, {
    Name: 'clientStreetName',
    Description: 'app.oca.street_name',
    InputTitle: 'Vul hier uw straatnaam in',
    IsRequired: false,
    IsVisible: false,
    DataType: 'text',
    AutoCompleteAttribute: 'address-line1',
  }, {
    Name: 'clientHouseNumber',
    Description: 'app.oca.house_number',
    InputTitle: 'Vul hier uw huisnummer (zonder toevoeging) in',
    IsRequired: false,
    IsVisible: false,
    DataType: 'number',
    AutoCompleteAttribute: 'address-line2',
  }, {
    Name: 'clientHouseNumberSuffix',
    Description: 'app.oca.house_number_suffix',
    InputTitle: 'Vul hier uw huisnummer toevoeging in',
    IsRequired: false,
    IsVisible: false,
    DataType: 'text',
    AutoCompleteAttribute: 'address-line3',
  }, {
    Name: 'clientPostalCode',
    Description: 'app.oca.zip_code',
    InputTitle: 'Vul hier je postcode in',
    IsRequired: false,
    IsVisible: false,
    DataType: 'text',
    AutoCompleteAttribute: 'postal-code',
  }, {
    Name: 'clientCity',
    Description: 'app.oca.place',
    InputTitle: 'Vul hier je woonplaats in',
    IsRequired: false,
    IsVisible: false,
    DataType: 'text',
    AutoCompleteAttribute: 'address-level2',
  }, {
    Name: 'appointmentDescription',
    Description: 'app.oca.remarks',
    InputTitle: 'Vul hier aanvullende opmerkingen op je afspraak in',
    IsRequired: false,
    IsVisible: true,
    DataType: 'textarea',
    AutoCompleteAttribute: 'off',
  }];
