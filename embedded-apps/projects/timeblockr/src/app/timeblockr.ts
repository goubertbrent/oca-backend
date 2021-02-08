export interface TimeblockrBaseModel {
  Options: {};
  Id: number;
  Guid: string;
  Reference: string | null;
  Name: string;
  /**
   * Contains html
   */
  InfoText: string;
  Description: string;
  ShortDescription: string;
}

export interface TimeblockrProduct extends TimeblockrBaseModel {
  Duration: number;
  DurationMultipleUnits: number | null;
  DescriptionHeader: string;
  ShortDescriptionHeader: string;
  PrerequisitesHeader: string;
  Prerequisites: string;
  /**
   * e.g. 'Aantal personen '
   */
  UnitsToBookText: string;
  MaxUnitsToBook: number;
  DefaultUnitsToBook: number;
  ProductgroupGuid: string | null;
  Productgroup: null;
  SortIndex: number;
  CapacityType: 'Linear' | 'Parallel';
  CreateSeparateBookings: boolean;
  PreparationTime: number;
  FinalizingTime: number;
  WaitingTimeStart: number;
  WaitingTimeDuration: number;
}

export interface TimeblockrAppointment {

}

export interface TimeblockrLocation extends TimeblockrBaseModel {
  Street: string;
  StreetNumber: string;
  StreetNumberAddition: string | null;
  PostalCode: string;
  City: string;
  /**
   * 2 letter code
   */
  Country: string;
  MailAddress: string | null;
  PhoneNumber: string | null;
  Website: string | null;
  Coordinates: null;
  CoverageArea: null;
  Distance: number;
  IsResourceItemOptionalToChoose: boolean;
  SortIndex: number;
  Counters: string;
}

// unused: original data that gets converted on server to TimeblockrDateSlot
export interface TimeblockrTimeslots {
  PeriodOptions: {
    // ISO date (without hour)
    Date: string;
    /**
     * contains number, probably amount of slots that are free on that day
     */
    Value: string;
    // absolutely no clue what the point of this is
    Type: 'Week';
  }[];
  SlotOptions: {
    Date: string;
    Location: {
      Guid: string;
      Reference: string | null;
      Name: string;
      DirectUrl: string;
    };
    /**
     * Day name in english e.g. 'Friday'
     */
    DayOfWeek: string;
    Duration: number;
    Price: null;
    VATPrice: null;
    VATAmount: null;
    VATRate: number;
    Group: null;
    ResourceItem: null;
    ResourceItems: string[] | null;
    SectionGroup: string;
    ParallelCapacity: null
    ParallelBookedCapacity: null;
  }[];
  Type: 'List';
  /**
   * ISO date
   */
  BookInAdvance: string;
  /**
   * ISO date
   */
  BookInFuture: string;
  /**
   * 'Monday, Tuesday, Wednesday, Thursday, Friday'
   */
  CalendarOpenDays: string;
  CalendarMinOpeningTime: string;
  CalendarMaxOpeningTime: string;
  CalendarDateBegin: string;
  CalendarDateEnd: string;
  ProductUnits: {
    ProductGuid: string;
    ProductReference: string | null;
    Units: number;
    Duration: number;
    DurationDefault: number;
    Product: {
      Guid: string;
      Reference: string | null;
      Name: string;
      DirectUrl: string;
    };
    ProductInstanceDuration: null;
    ProductInstanceDurationMultipleUnits: null;
    ProductInstanceReference: null;
    OriginalDuration: null;
    PreparationTime: null;
    FinalizingTime: null;
  }[];
}

export interface TimeblockrClientDateSlot {
  date: Date;
  value: string;
}

export interface TimeblockrDateSlot {
  date: string;
}

export interface TimeblockrOptionValue {
  Value: string;
  Text: string;
  Price: null;
  VATAmount: null;
  VATPrice: null;
}

export interface TimeblockrDynamicField {
  DynamicFieldSourceType: 'UserProfileField';
  // Generated key e.g. UserProfileField_3060
  Key: string;
  // 'INITIALS', 'MAILADDRESS', 'FIRSTNAME', ...
  Code: string;
  Group: null;
  // Field name to be shown to user, e.g. 'First name'
  Name: string;
  // Empty string or for example 'False:Nee;True:JA'.
  // Probably deprecated, as OptionValuesList contains the same but properly structured.
  OptionValues: string;
  OptionValuesList: TimeblockrOptionValue[];
  // If OptIn, OptionValuesList will not be empty -> show as select or radio buttons
  ControlType: 'Text' | 'OptIn';
  SortId: number;
  ValidationType: 'None' | 'Email' | 'PhoneInt';
  // Regex
  ValidationExpression: string;
  MaxLength: number | null;
  IsRequired: boolean;
  InternalType: 'System' | 'SystemOptional' | 'Custom';
  RenderBasedOnUnitsToBook: false;
  Infotext: '';
  UnitNumber: null;
  Attribute: null;
  RegexValidationMessage: string | null;
}

export interface SelectedProduct {
  id: string;
  amount: number;
}

export interface CreateTimeblockrAppointment {

}
