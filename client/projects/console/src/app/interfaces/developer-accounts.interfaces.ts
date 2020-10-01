export interface DeveloperAccount {
  readonly id: number;
  type: 'android' | 'ios';
  name: string;
  account_email: string;
  ios_dev_team: string | null;
  iphone_developer: string | null;
  iphone_distribution: string | null;
  google_credentials_json: string | null;
  readonly copyright?: string;
}

export interface CreateDeveloperAccountPayload {
  type: 'android' | 'ios';
  name: string;
  account_email: string;
  account_password: string | null;
  google_credentials_json: string | null;
  fastlane_session?: string;
}

export interface Contact {
  readonly id?: number;
  first_name: string;
  last_name: string;
  phone_number: string;
  email: string;
  support_email: string;
  address_line_1: string;
  city: string;
  postal_code: string;
  country: string;
}

export interface ReviewNotes {
  readonly id?: number;
  name: string;
  first_name: string;
  last_name: string;
  phone_number: string;
  email_address: string;
  demo_user: string;
  demo_password: string;
  notes: string;
}
