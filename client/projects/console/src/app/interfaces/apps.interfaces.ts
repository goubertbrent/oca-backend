export interface AppSearchResult {
  title: string;
  app_id: string;
}

export interface AppSearchParameters {
  query?: string;
}

export interface AppDetailPayload {
  appId: string;
}

export interface CreateBuildPayload {
  type: BuildType;
  release: boolean;
  debug: boolean;
  generate_screenshots: boolean;
  track: string;
  submit_for_review: boolean;
  branch: string | null;
}

export interface BulkUpdatePayload {
  types: BuildType[];
  release: boolean;
  generate_screenshots: boolean;
  app_ids: string[];
  metadata: AppMetaData[];
}

export interface FileUploadPayload {
  file: string;
}

export interface App {
  app_id: string;
  backend_server: string;
  git_status: GitStatus;
  iphone_store_id: number;
  id: number;
  playstore_category: string;
  appstore_category: string;
  main_language: string;
  other_languages: string[] | string;
  title: string;
  playstore_name: string;
  appstore_name: string;
  app_type: number;
  playstore_track: string;
  main_service: string;
  facebook_registration: boolean;
  contact: number;
  ios_developer_account: number | null;
  android_developer_account: number;
  review_notes: number;
  chat_payments_enabled: boolean;
}

export interface CreateAppPayload {
  app_id: string;
  app_type: number;
  contact: number | null;
  country: string;
  main_language: string;
  official_id: number | null;
  title: string;
  dashboard_email_address: string;
  ios_developer_account: number | null;
  android_developer_account: number | null;
  review_notes: number | null;
}

export interface PatchAppPayload {
  title: string;
  app_type: number;
  playstore_track: string;
  main_service: string;
  secure: boolean;
  facebook_registration: boolean;
  facebook_app_id: number;
  facebook_app_secret: string;
  chat_payments_enabled: boolean;
}

export interface PatchAppCompletePayload {
  app: App;
  rogerthat_app: RogerthatApp;
}

export interface AppMetaData {
  language: string;
  release_notes: string;
  short_description: string;
  description: string;
  description_google_play: string;
  keywords: string;
  support_url: string;
  privacy_policy_url: string;
  terms_of_service_url: string;
  subtitle: string;
}

export const enum BuildStatus {
  CREATED = 1,
  RUNNING = 2,
  SUCCESS = 3,
  FAILURE = 4,
  ABORTED = 5
}

export const BUILD_STATUS_STRINGS = {
  [ BuildStatus.CREATED ]: 'rcc.build_status_created',
  [ BuildStatus.RUNNING ]: 'rcc.build_status_running',
  [ BuildStatus.SUCCESS ]: 'rcc.build_status_success',
  [ BuildStatus.FAILURE ]: 'rcc.build_status_failure',
  [ BuildStatus.ABORTED ]: 'rcc.build_status_aborted',
};

export const enum BuildType {
  ANDROID = 1,
  IOS = 2
}

export const BUILD_TYPE_STRINGS = {
  [ BuildType.ANDROID ]: 'rcc.platform_android',
  [ BuildType.IOS ]: 'rcc.platform_ios',
};

export class TrackTypes {
  static PRODUCTION = 'production';
  static BETA = 'beta';
  static ALPHA = 'alpha';

  static TYPES = [ TrackTypes.PRODUCTION, TrackTypes.BETA, TrackTypes.ALPHA ];
}

export class Build {
  id: number;
  timestamp: string; // ISO 8601 date string
  updated_on: string; // ISO 8601 date string
  type: number;
  status: BuildStatus;
  submit_status: BuildStatus | null;
  build_number: number;
  debug: boolean;
  download_url: string;
  binsha: string;
  track: string;
  version_major: number;
  version_minor: number;
  submit_for_review: boolean;
}

export const enum AppServiceFilter {
  COUNTRY,
  COMMUNITIES,
}

export interface RogerthatApp {
  admin_services: string[];
  android_app_id: string;
  beta: boolean;
  contact_email_address: string;
  core_branding_hash: string;
  country: string;
  creation_time: number;
  dashboard_email_address: string;
  demo: boolean;
  facebook_app_id: number;
  facebook_app_secret: string;
  id: string;
  ios_app_id: string;
  is_default: boolean;
  main_service: string;
  mdp_client_id: string;
  mdp_client_secret: string;
  name: string;
  owncloud_admin_password: string;
  owncloud_admin_username: string;
  owncloud_base_uri: string;
  secure: boolean;
  type: number;
  user_regex: string;
  community_ids: number[];
  service_filter_type: AppServiceFilter;
  default_app_name_mapping: string | null;
}

export const enum AppTypes {
  ROGERTHAT,
  CITY_APP,
  ENTERPRISE,
  OSA_LOYALTY,
  YSAAA
}

export const APP_TYPES = [
  { value: AppTypes.ROGERTHAT, label: 'rcc.app_type_rogerthat' },
  { value: AppTypes.CITY_APP, label: 'rcc.app_type_city_app' },
  { value: AppTypes.ENTERPRISE, label: 'rcc.app_type_enterprise' },
  { value: AppTypes.OSA_LOYALTY, label: 'rcc.app_type_osa_loyalty' },
  { value: AppTypes.YSAAA, label: 'rcc.app_type_ysaaa' },
];

export interface AppAsset {
  app_ids: string[];
  content_type: string;
  is_default: boolean;
  id: string;
  kind: string;
  url: string;
  scale_x: number;
}

export interface EditAppAssetPayload extends AppAsset {
  file: any;
}

export interface AppColors {
  app_tint_color: string;
  primary_color: string;
  homescreen_background: string;
  homescreen_text: string;
}

export interface AppNavigationItemParams {
  /**
   * Only set when the navigation item's `action` is in COLLAPSE_NAVIGATION_ACTIONS
   */
  collapse?: boolean;
  /**
   * Only set when the navigation item's `action` is `open_app`
   */
  android_app_id?: string;
  android_scheme?: string;
  ios_app_id?: string;
  ios_scheme?: string;
}

export interface AppNavigationItem {
  action: string | null;
  action_type: string;
  color: string | null;
  icon: string;
  text: string;
  params: AppNavigationItemParams;
}

export interface AppToolbar {
  items: AppNavigationItem[];
}

export interface AppSidebar {
  color: string;
  footer: boolean;
  footer_alignment: string;
  items: AppNavigationItem[];
  style: string;
  toolbar: AppToolbar;
}

export interface NameValue {
  name: string;
  value: string;
}

export interface Translations {
  [ key: string ]: NameValue[];
}

export interface AppNavigationItemError {
  [ key: string ]: string[];
}

export interface AppToolbarError {
  items: AppNavigationItemError[];
}

export interface AppSidebarError {
  color?: string[];
  footer?: string[];
  footer_alignment?: string[];
  items?: AppNavigationItemError[];
  style: string[];
  toolbar: AppToolbarError;
}

export interface AppImageInfo {
  type: string;
  exists: boolean;
  width: number;
  height: number;
  format: string;
}

export interface UpdateAppImagePayload {
  type: string;
  file: any;
}

export interface GenerateImagesPayload {
  types: string[];
  file: any;
}

export interface SaveChangesPayload {
  comment: string;
}

export const enum GitStatus {
  CLEAN = 1,
  DRAFT = 2,
}

export interface BuildSettings {
  friends_enabled: boolean;
  friends_caption: string;
  app_service_guid: string;
  registration_type: number;
  registration_type_oauth_url: string;
  registration_type_qr_url: string;
  registration_type_oauth_domain: string;
  translations: Translations;
}

export enum RegistrationType {
  DEFAULT = 1,
  OAUTH = 2,
  FULL_OAUTH = 3,
  QR = 4,
}

export const registrationTypes = [ {
  label: 'rcc.default',
  description: 'rcc.registration_default_explanation',
  value: RegistrationType.DEFAULT,
}, {
  label: 'rcc.oauth',
  description: 'rcc.registration_oauth_explanation',
  value: RegistrationType.OAUTH,
}, {
  label: 'rcc.full_oauth',
  description: 'rcc.registration_full_oauth_explanation',
  value: RegistrationType.FULL_OAUTH,
}, {
  label: 'rcc.qr',
  description: 'rcc.registration_qr_explanation',
  value: RegistrationType.QR,
} ];

export const FriendCaptions = [ {
  value: null,
  label: 'rcc.friends',
}, {
  value: 'contacts',
  label: 'rcc.contacts',
}, {
  value: 'colleagues',
  label: 'rcc.colleagues',
} ];

export interface OAuthSettings {
  url: string;
  authorize_path: string;
  token_path: string;
  identity_path: string;
  scopes: string;
  client_id: string;
  secret: string;
  domain: string;
  service_identity_email: string;
  public_key: string | null;
  jwt_audience: string | null;
  jwt_issuer: string | null;
}

export interface AppSettings {
  wifi_only_downloads: boolean;
  background_fetch_timestamps: number[];
  oauth: OAuthSettings;
  birthday_message_enabled: boolean;
  birthday_message: string;
  ios_firebase_project_id: string;
  ios_apns_key_id: string;
}

export interface NavigationAction {
  value: string;
  action_type: string | null;
  label: string;
}

export interface BulkUpdateErrors {
  [ key: string ]: [ string, string[] ];
}
