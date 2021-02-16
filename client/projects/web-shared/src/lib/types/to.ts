// tslint:disable:no-empty-interface
export type FormComponentTO =
  FileComponentTO
  | TextInputComponentTO
  | MultiSelectComponentTO
  | DatetimeComponentTO
  | ParagraphComponentTO
  | LocationComponentTO
  | SingleSelectComponentTO;

export type FormComponentValueTO =
  SingleSelectComponentValueTO
  | TextInputComponentValueTO
  | MultiSelectComponentValueTO
  | DatetimeComponentValueTO
  | LocationComponentValueTO
  | FileComponentValueTO;

export type FormValidatorTO =
  RegexValidatorTO
  | MinLengthValidatorTO
  | MaxDateValidatorTO
  | MinValidatorTO
  | MaxLengthValidatorTO
  | MaxValidatorTO
  | RequiredValidatorTO
  | MinDateValidatorTO;

export type JobOfferActionTO =
  JobOfferOpenActionTO
  | JobOfferChatActionTO;

export type MapActionChipTO =
  SearchSuggestionTO;

export type MapAnnouncementTO =
  TextAnnouncementTO;

export type MapGeometryTO =
  MultiLineStringGeometryTO
  | LineStringGeometryTO
  | PolygonGeometryTO
  | MultiPolygonGeometryTO;

export type MapItemLineTO =
  MapItemLineTextTO;

export type MapListSectionItemTO =
  OpeningHoursListSectionItemTO
  | ToggleListSectionItemTO
  | LinkListSectionItemTO
  | ExpandableListSectionItemTO
  | OpeningHoursSectionItemTO;

export type MapSearchSuggestionTO =
  MapSearchSuggestionItemTO
  | MapSearchSuggestionKeywordTO;

export type MapSectionTO =
  VoteSectionTO
  | NewsItemSectionTO
  | MediaSectionTO
  | GeometrySectionTO
  | TextSectionTO
  | NewsSectionTO
  | ListSectionTO
  | NewsGroupSectionTO;

export type NewFlowMessageTO =
  MessageTO
  | FormMessageTO;

export type NextActionTO =
  NextActionURLTO
  | NextActionSectionTO
  | NextActionSubmitTO
  | NextActionDefaultTO;

export type Step =
  MessageFlowStepTO
  | FormFlowStepTO;


export const enum FormComponentType {
  TEXT_INPUT = 'text_input',
  FILE = 'file',
  MULTI_SELECT = 'multi_select',
  DATETIME = 'datetime',
  PARAGRAPH = 'paragraph',
  LOCATION = 'location',
  SINGLE_SELECT = 'single_select',
}

export const enum FormValidatorType {
  REGEX = 'regex',
  REQUIRED = 'required',
  MIN = 'min',
  MAX = 'max',
  MAXLENGTH = 'maxlength',
  MINLENGTH = 'minlength',
  MAXDATE = 'maxdate',
  MINDATE = 'mindate',
}

export const enum JobOfferActionType {
  OPEN = 0,
  CHAT = 1,
}

export const enum MapActionChipType {
  SEARCH_SUGGESTION = 'search_suggestion',
}

export const enum MapAnnouncementType {
  TEXT = 'text',
}

export const enum MapGeometryType {
  MULTI_POLYGON = 'MultiPolygon',
  POLYGON = 'Polygon',
  LINE_STRING = 'LineString',
  MULTI_LINE_STRING = 'MultiLineString',
}

export const enum MapItemLineType {
  TEXT = 'text',
}

export const enum MapListSectionItemType {
  OPENING_HOURS = 'opening_hours',
  EXPANDABLE = 'expandable',
  DYNAMIC_OPENING_HOURS = 'opening-hours',
  LINK = 'link',
  TOGGLE = 'toggle',
}

export const enum MapSearchSuggestionType {
  ITEM = 'item',
  KEYWORD = 'keyword',
}

export const enum MapSectionType {
  NEWS_GROUP = 'news-group',
  GEOMETRY = 'geometry',
  MEDIA = 'media',
  LIST = 'list',
  NEWS_ITEM = 'news-item',
  TEXT = 'text',
  VOTE = 'vote',
  NEWS = 'news',
}

export const enum MessageType {
  MESSAGE = 'message_step',
  FORM = 'form_step',
}

export const enum NewMessageType {
  FORM_MESSAGE = 2,
  MESSAGE = 1,
}

export const enum NextActionType {
  URL = 'url',
  SECTION = 'section',
  SUBMIT = 'submit',
  NEXT = 'next',
}


export interface AckInvitationByInvitationSecretRequestTO {
  invitor_code: string | null;
  secret: string | null;
}

export interface AckInvitationByInvitationSecretResponseTO {
}

export interface AckMessageRequestTO {
  button_id: string | null;
  custom_reply: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  timestamp: number;
}

export interface AckMessageResponseTO {
  result: number;
}

export interface AddProfileAddressRequestTO {
  geo_location: GeoPointTO | null;
  bus_nr: string | null;
  city: string | null;
  distance: number;
  house_nr: string | null;
  label: string | null;
  street_name: string | null;
  type: number;
  zip_code: string | null;
}

export interface AddProfileAddressResponseTO {
  geo_location: GeoPointTO | null;
  bus_nr: string | null;
  city: string | null;
  distance: number;
  house_nr: string | null;
  label: string | null;
  street_name: string | null;
  type: number;
  uid: string | null;
  zip_code: string | null;
}

export interface AddProfilePhoneNumberRequestTO {
  label: string | null;
  number: string | null;
  type: number;
}

export interface AddProfilePhoneNumberResponseTO {
  label: string | null;
  number: string | null;
  type: number;
  uid: string | null;
}

export interface AdvancedOrderCategory {
  items: AdvancedOrderItem[];
  id: string | null;
  name: string | null;
}

export interface AdvancedOrderFormMessageTO {
  attachments: AttachmentTO[];
  form: AdvancedOrderFormTO | null;
  member: MemberStatusTO | null;
  alert_flags: number;
  branding: string | null;
  context: string | null;
  default_priority: number;
  default_sticky: boolean;
  flags: number;
  key: string | null;
  message: string | null;
  message_type: number;
  parent_key: string | null;
  priority: number;
  sender: string | null;
  threadTimestamp: number;
  thread_avatar_hash: string | null;
  thread_background_color: string | null;
  thread_size: number;
  thread_text_color: string | null;
  timestamp: number;
}

export interface AdvancedOrderFormTO {
  widget: AdvancedOrderTO | null;
  javascript_validation: string | null;
  negative_button: string | null;
  negative_button_ui_flags: number;
  negative_confirmation: string | null;
  positive_button: string | null;
  positive_button_ui_flags: number;
  positive_confirmation: string | null;
  type: string | null;
}

export interface AdvancedOrderItem {
  description: string | null;
  has_price: boolean;
  id: string | null;
  image_url: string | null;
  name: string | null;
  step: number;
  step_unit: string | null;
  step_unit_conversion: number;
  unit: string | null;
  unit_price: number;
  value: number;
}

export interface AdvancedOrderTO {
  categories: AdvancedOrderCategory[];
  currency: string | null;
  leap_time: number;
}

export interface AdvancedOrderWidgetResultTO {
  categories: AdvancedOrderCategory[];
  currency: string | null;
}

export interface AppPaymentProviderTO {
  asset_types: string[];
  background_color: string | null;
  black_white_logo: string | null;
  button_color: string | null;
  currencies: string[];
  description: string | null;
  embedded_app_id: string | null;
  enabled: boolean;
  id: string | null;
  logo_url: string | null;
  name: string | null;
  oauth_authorize_url: string | null;
  text_color: string | null;
  version: number;
}

export interface AttachmentTO {
  thumbnail: Thumbnail | null;
  content_type: string | null;
  download_url: string | null;
  name: string | null;
  size: number;
}

export interface AutoCompleteFormMessageTO {
  attachments: AttachmentTO[];
  form: AutoCompleteFormTO | null;
  member: MemberStatusTO | null;
  alert_flags: number;
  branding: string | null;
  context: string | null;
  default_priority: number;
  default_sticky: boolean;
  flags: number;
  key: string | null;
  message: string | null;
  message_type: number;
  parent_key: string | null;
  priority: number;
  sender: string | null;
  threadTimestamp: number;
  thread_avatar_hash: string | null;
  thread_background_color: string | null;
  thread_size: number;
  thread_text_color: string | null;
  timestamp: number;
}

export interface AutoCompleteFormTO {
  widget: AutoCompleteTO | null;
  javascript_validation: string | null;
  negative_button: string | null;
  negative_button_ui_flags: number;
  negative_confirmation: string | null;
  positive_button: string | null;
  positive_button_ui_flags: number;
  positive_confirmation: string | null;
  type: string | null;
}

export interface AutoCompleteTO {
  choices: string[];
  keyboard_type: string | null;
  max_chars: number;
  place_holder: string | null;
  suggestions: string[];
  value: string | null;
}

export interface BaseMediaTO {
  content: string | null;
  thumbnail_url: string | null;
  type: string | null;
}

export interface BasePaymentMethod {
  amount: number;
  currency: string | null;
  precision: number;
}

export interface BecameFriendsRequestTO {
  friend: FriendRelationTO | null;
  user: string | null;
}

export interface BecameFriendsResponseTO {
}

export interface BreakFriendshipRequestTO {
  friend: string | null;
}

export interface BreakFriendshipResponseTO {
}

export interface BulkSaveJobsRequestTO {
  ids: number[];
  status: number;
}

export interface BulkSaveJobsResponseTO {
  ids: number[];
}

export interface ButtonTO {
  action: string | null;
  caption: string | null;
  color: string | null;
  id: string | null;
  ui_flags: number;
}

export interface CancelPaymentRequestTO {
  transaction_id: string | null;
}

export interface CancelPaymentResponseTO {
  error: ErrorPaymentTO | null;
  success: boolean;
}

export interface ChangeMembersOfConversationRequestTO {
  emails: string[];
  parent_message_key: string | null;
  type: string | null;
}

export interface ChangeMembersOfConversationResponseTO {
  error_string: string | null;
}

export interface ChatMemberStatisticsTO {
  count: number;
  search_enabled: boolean;
  show_members: boolean;
}

export interface ChoiceTO {
  label: string | null;
  value: string | null;
}

export interface ConsentSettingsTO {
  ask_push_notifications: boolean;
  ask_tos: boolean;
}

export interface ConversationDeletedRequestTO {
  parent_message_key: string | null;
}

export interface ConversationDeletedResponseTO {
}

export interface ConversationMemberTO {
  avatar_url: string | null;
  email: string | null;
  name: string | null;
  permission: string | null;
}

export interface CoordsListTO {
  coords: GeoPointTO[];
}

export interface CreateAssetRequestTO {
  currency: string | null;
  iban: string | null;
  provider_id: string | null;
  type: string | null;
}

export interface CreateAssetResponseTO {
  error: ErrorPaymentTO | null;
  result: PaymentProviderAssetTO | null;
  success: boolean;
}

export interface CreateJobChatRequestTO {
  anonymous: boolean;
  job_id: number;
  message: string | null;
}

export interface CreateJobChatResponseTO {
  message_key: string | null;
}

export interface CreateNotificationRequestTO {
}

export interface CreateNotificationResponseTO {
}

export interface CreateTransactionRequestTO {
  params: string | null;
  provider_id: string | null;
}

export interface CreateTransactionResponseTO {
  error: ErrorPaymentTO | null;
  result: CreateTransactionResultTO | null;
  success: boolean;
}

export interface CreateTransactionResultTO {
  params: string | null;
  transaction_id: string | null;
}

export interface DateSelectFormMessageTO {
  attachments: AttachmentTO[];
  form: DateSelectFormTO | null;
  member: MemberStatusTO | null;
  alert_flags: number;
  branding: string | null;
  context: string | null;
  default_priority: number;
  default_sticky: boolean;
  flags: number;
  key: string | null;
  message: string | null;
  message_type: number;
  parent_key: string | null;
  priority: number;
  sender: string | null;
  threadTimestamp: number;
  thread_avatar_hash: string | null;
  thread_background_color: string | null;
  thread_size: number;
  thread_text_color: string | null;
  timestamp: number;
}

export interface DateSelectFormTO {
  widget: DateSelectTO | null;
  javascript_validation: string | null;
  negative_button: string | null;
  negative_button_ui_flags: number;
  negative_confirmation: string | null;
  positive_button: string | null;
  positive_button_ui_flags: number;
  positive_confirmation: string | null;
  type: string | null;
}

export interface DateSelectTO {
  date: number;
  has_date: boolean;
  has_max_date: boolean;
  has_min_date: boolean;
  max_date: number;
  min_date: number;
  minute_interval: number;
  mode: string | null;
  unit: string | null;
}

export interface DatetimeComponentTO {
  validators: FormValidatorTO[];
  description: string | null;
  format: string | null;
  id: string | null;
  sensitive: boolean;
  title: string | null;
  readonly type: FormComponentType.DATETIME;
}

export interface DatetimeComponentValueTO {
  day: number;
  hour: number;
  minute: number;
  month: number;
  year: number;
  id: string | null;
  readonly type: FormComponentType.DATETIME;
}

export interface DeleteConversationRequestTO {
  parent_message_key: string | null;
}

export interface DeleteConversationResponseTO {
}

export interface DeleteGroupRequestTO {
  guid: string | null;
}

export interface DeleteGroupResponseTO {
}

export interface DeleteProfileAddressesRequestTO {
  uids: string[];
}

export interface DeleteProfileAddressesResponseTO {
}

export interface DeleteProfilePhoneNumbersRequestTO {
  uids: string[];
}

export interface DeleteProfilePhoneNumbersResponseTO {
}

export interface DisableNewsRequestTO {
  news_id: number;
}

export interface DisableNewsResponseTO {
}

export interface EditProfileRequestTO {
  access_token: string | null;
  avatar: string | null;
  birthdate: number;
  extra_fields: string | null;
  first_name: string | null;
  gender: number;
  has_birthdate: boolean;
  has_gender: boolean;
  last_name: string | null;
  name: string | null;
}

export interface EditProfileResponseTO {
}

export interface EmbeddedAppTO {
  description: string | null;
  name: string | null;
  serving_url: string | null;
  title: string | null;
  types: string[];
  url_regexes: string[];
  version: number;
}

export interface EndMessageFlowRequestTO {
  message_flow_run_id: string | null;
  parent_message_key: string | null;
  wait_for_followup: boolean;
}

export interface EndMessageFlowResponseTO {
}

export interface ErrorPaymentTO {
  code: string | null;
  data: string | null;
  message: string | null;
}

export interface ErrorTO {
  action: string | null;
  caption: string | null;
  message: string | null;
  title: string | null;
}

export interface ExpandableListSectionItemTO {
  icon: string | null;
  icon_color: string | null;
  title: string | null;
  readonly type: MapListSectionItemType.EXPANDABLE;
}

export interface FacebookRogerthatProfileMatchTO {
  fbId: string | null;
  fbName: string | null;
  fbPicture: string | null;
  rtId: string | null;
}

export interface FileComponentTO {
  validators: FormValidatorTO[];
  description: string | null;
  file_types: string[];
  id: string | null;
  sensitive: boolean;
  title: string | null;
  readonly type: FormComponentType.FILE;
}

export interface FileComponentValueTO {
  file_type: string | null;
  name: string | null;
  value: string | null;
  id: string | null;
  readonly type: FormComponentType.FILE;
}

export interface FindFriendItemTO {
  avatar_url: string | null;
  email: string | null;
  name: string | null;
}

export interface FindFriendRequestTO {
  avatar_size: number;
  cursor: string | null;
  search_string: string | null;
}

export interface FindFriendResponseTO {
  items: FindFriendItemTO[];
  cursor: string | null;
  error_string: string | null;
}

export interface FindRogerthatUsersViaEmailRequestTO {
  email_addresses: string[];
}

export interface FindRogerthatUsersViaEmailResponseTO {
  matched_addresses: string[];
}

export interface FindRogerthatUsersViaFacebookRequestTO {
  access_token: string | null;
}

export interface FindRogerthatUsersViaFacebookResponseTO {
  matches: FacebookRogerthatProfileMatchTO[];
}

export interface FindServiceCategoryTO {
  items: FindServiceItemTO[];
  category: string | null;
  cursor: string | null;
}

export interface FindServiceItemTO {
  avatar: string | null;
  avatar_id: number;
  description: string | null;
  description_branding: string | null;
  detail_text: string | null;
  email: string | null;
  name: string | null;
  qualified_identifier: string | null;
}

export interface FindServiceRequestTO {
  geo_point: GeoPointWithTimestampTO | null;
  avatar_size: number;
  cursor: string | null;
  hashed_tag: string | null;
  organization_type: number;
  search_string: string | null;
}

export interface FindServiceResponseTO {
  matches: FindServiceCategoryTO[];
  error_string: string | null;
}

export interface FloatListWidgetResultTO {
  values: number[];
}

export interface FloatWidgetResultTO {
  value: number;
}

export interface FlowStartedRequestTO {
  message_flow_run_id: string | null;
  service: string | null;
  static_flow_hash: string | null;
  thread_key: string | null;
}

export interface FlowStartedResponseTO {
}

export interface FormFlowStepTO {
  form_result: FormResult | null;
  acknowledged_timestamp: number;
  answer_id: string | null;
  button: string | null;
  display_value: string | null;
  form_type: string | null;
  message: string | null;
  message_flow_id: string | null;
  received_timestamp: number;
  step_id: string | null;
  readonly step_type: MessageType.FORM;
}

export interface FormMessageTO {
  attachments: AttachmentTO[];
  form: FormTO | null;
  member: MemberStatusTO | null;
  alert_flags: number;
  branding: string | null;
  context: string | null;
  default_priority: number;
  default_sticky: boolean;
  flags: number;
  key: string | null;
  message: string | null;
  parent_key: string | null;
  priority: number;
  sender: string | null;
  threadTimestamp: number;
  thread_avatar_hash: string | null;
  thread_background_color: string | null;
  thread_size: number;
  thread_text_color: string | null;
  timestamp: number;
  readonly message_type: NewMessageType.FORM_MESSAGE;
}

export interface FormResult {
  result: WidgetResult | null;
  type: string | null;
}

export interface FormSectionBrandingTO {
  avatar_url: string | null;
  logo_url: string | null;
}

export interface FormSectionTO {
  branding: FormSectionBrandingTO | null;
  components: FormComponentTO[];
  next_action: NextActionTO | null;
  description: string | null;
  id: string | null;
  next_button_caption: string | null;
  title: string | null;
}

export interface FormSectionValueTO {
  components: FormComponentValueTO[];
  id: string | null;
}

export interface FormTO {
  widget: Widget | null;
  javascript_validation: string | null;
  negative_button: string | null;
  negative_button_ui_flags: number;
  negative_confirmation: string | null;
  positive_button: string | null;
  positive_button_ui_flags: number;
  positive_confirmation: string | null;
  type: string | null;
}

export interface FormVersionTO {
  id: number;
  version: number;
}

export interface ForwardLogsRequestTO {
  jid: string | null;
}

export interface ForwardLogsResponseTO {
}

export interface FriendCategoryTO {
  avatar: string | null;
  guid: string | null;
  name: string | null;
}

export interface FriendRelationTO {
  avatarId: number;
  email: string | null;
  name: string | null;
  type: number;
}

export interface FriendSelectFormMessageTO {
  attachments: AttachmentTO[];
  form: FriendSelectFormTO | null;
  member: MemberStatusTO | null;
  alert_flags: number;
  branding: string | null;
  context: string | null;
  default_priority: number;
  default_sticky: boolean;
  flags: number;
  key: string | null;
  message: string | null;
  message_type: number;
  parent_key: string | null;
  priority: number;
  sender: string | null;
  threadTimestamp: number;
  thread_avatar_hash: string | null;
  thread_background_color: string | null;
  thread_size: number;
  thread_text_color: string | null;
  timestamp: number;
}

export interface FriendSelectFormTO {
  widget: FriendSelectTO | null;
  javascript_validation: string | null;
  negative_button: string | null;
  negative_button_ui_flags: number;
  negative_confirmation: string | null;
  positive_button: string | null;
  positive_button_ui_flags: number;
  positive_confirmation: string | null;
  type: string | null;
}

export interface FriendSelectTO {
  multi_select: boolean;
  selection_required: boolean;
}

export interface FriendTO {
  actionMenu: ServiceMenuTO | null;
  appData: string | null;
  avatarHash: string | null;
  avatarId: number;
  callbacks: number;
  category_id: string | null;
  contentBrandingHash: string | null;
  description: string | null;
  descriptionBranding: string | null;
  email: string | null;
  existence: number;
  flags: number;
  generation: number;
  hasUserData: boolean;
  homeBrandingHash: string | null;
  name: string | null;
  organizationType: number;
  pokeDescription: string | null;
  profileData: string | null;
  qualifiedIdentifier: string | null;
  shareLocation: boolean;
  sharesContacts: boolean;
  sharesLocation: boolean;
  type: number;
  userData: string | null;
  versions: number[];
}

export interface GPSLocationFormMessageTO {
  attachments: AttachmentTO[];
  form: GPSLocationFormTO | null;
  member: MemberStatusTO | null;
  alert_flags: number;
  branding: string | null;
  context: string | null;
  default_priority: number;
  default_sticky: boolean;
  flags: number;
  key: string | null;
  message: string | null;
  message_type: number;
  parent_key: string | null;
  priority: number;
  sender: string | null;
  threadTimestamp: number;
  thread_avatar_hash: string | null;
  thread_background_color: string | null;
  thread_size: number;
  thread_text_color: string | null;
  timestamp: number;
}

export interface GPSLocationFormTO {
  widget: GPSLocationTO | null;
  javascript_validation: string | null;
  negative_button: string | null;
  negative_button_ui_flags: number;
  negative_confirmation: string | null;
  positive_button: string | null;
  positive_button_ui_flags: number;
  positive_confirmation: string | null;
  type: string | null;
}

export interface GPSLocationTO {
  gps: boolean;
}

export interface GeoPointTO {
  lat: number;
  lon: number;
}

export interface GeoPointWithTimestampTO {
  accuracy: number;
  latitude: number;
  longitude: number;
  timestamp: number;
}

export interface GeometrySectionTO {
  geometry: MapGeometryTO[];
  description: string | null;
  title: string | null;
  readonly type: MapSectionType.GEOMETRY;
}

export interface GetAppAssetRequestTO {
  kind: string | null;
}

export interface GetAppAssetResponseTO {
  kind: string | null;
  scale_x: number;
  url: string | null;
}

export interface GetAvatarRequestTO {
  avatarId: number;
  size: number;
}

export interface GetAvatarResponseTO {
  avatar: string | null;
}

export interface GetCategoryRequestTO {
  category_id: string | null;
}

export interface GetCategoryResponseTO {
  category: FriendCategoryTO | null;
}

export interface GetConversationAvatarRequestTO {
  avatar_hash: string | null;
  thread_key: string | null;
}

export interface GetConversationAvatarResponseTO {
  avatar: string | null;
}

export interface GetConversationMemberMatchesRequestTO {
  parent_message_key: string | null;
}

export interface GetConversationMemberMatchesResponseTO {
  emails: string[];
}

export interface GetConversationMembersRequestTO {
  cursor: string | null;
  parent_message_key: string | null;
  search_string: string | null;
}

export interface GetConversationMembersResponseTO {
  items: ConversationMemberTO[];
  cursor: string | null;
}

export interface GetConversationRequestTO {
  offset: string | null;
  parent_message_key: string | null;
}

export interface GetConversationResponseTO {
  conversation_sent: boolean;
}

export interface GetConversationStatisticsRequestTO {
  parent_message_key: string | null;
}

export interface GetConversationStatisticsResponseTO {
  members: ChatMemberStatisticsTO | null;
  permission: string | null;
}

export interface GetEmbeddedAppRequestTO {
  name: string | null;
}

export interface GetEmbeddedAppResponseTO {
  description: string | null;
  name: string | null;
  serving_url: string | null;
  title: string | null;
  types: string[];
  url_regexes: string[];
  version: number;
}

export interface GetEmbeddedAppsRequestTO {
  type: string | null;
}

export interface GetEmbeddedAppsResponseTO {
  embedded_apps: EmbeddedAppTO[];
}

export interface GetFormRequestTO {
  id: number;
}

export interface GetFormResponseTO {
  sections: FormSectionTO[];
  submission_section: FormSectionTO | null;
  id: number;
  max_submissions: number;
  title: string | null;
  version: number;
}

export interface GetFriendEmailsRequestTO {
}

export interface GetFriendEmailsResponseTO {
  emails: string[];
  friend_set_version: number;
  generation: number;
}

export interface GetFriendInvitationSecretsRequestTO {
}

export interface GetFriendInvitationSecretsResponseTO {
  secrets: string[];
}

export interface GetFriendRequestTO {
  avatar_size: number;
  email: string | null;
}

export interface GetFriendResponseTO {
  friend: FriendTO | null;
  avatar: string | null;
  generation: number;
}

export interface GetGroupAvatarRequestTO {
  avatar_hash: string | null;
  size: number;
}

export interface GetGroupAvatarResponseTO {
  avatar: string | null;
}

export interface GetGroupsRequestTO {
}

export interface GetGroupsResponseTO {
  groups: GroupTO[];
}

export interface GetIdentityQRCodeRequestTO {
  email: string | null;
  size: string | null;
}

export interface GetIdentityQRCodeResponseTO {
  qrcode: string | null;
  shortUrl: string | null;
}

export interface GetIdentityRequestTO {
}

export interface GetIdentityResponseTO {
  identity: IdentityTO | null;
  shortUrl: string | null;
}

export interface GetJSEmbeddingRequestTO {
}

export interface GetJSEmbeddingResponseTO {
  items: JSEmbeddingItemTO[];
}

export interface GetJobChatInfoRequestTO {
  job_id: number;
}

export interface GetJobChatInfoResponseTO {
  anonymous: JobChatAnonymousTO | null;
  chat_key: string | null;
  default_text: string | null;
  info_text: string | null;
  job_id: number;
}

export interface GetJobsCriteriaRequestTO {
}

export interface GetJobsCriteriaResponseTO {
  contract_types: JobKeyLabelTO[];
  job_domains: JobKeyLabelTO[];
  location: JobCriteriaLocationTO | null;
  notifications: JobCriteriaNotificationsTO | null;
  active: boolean;
  keywords: string[];
}

export interface GetJobsRequestTO {
  activity_type: string | null;
  cursor: string | null;
  ids: number[];
}

export interface GetJobsResponseTO {
  info: JobsInfoTO | null;
  items: JobOfferTO[];
  cursor: string | null;
  has_more: boolean;
  is_profile_active: boolean;
}

export interface GetMapItemDetailsRequestTO {
  ids: string[];
  tag: string | null;
}

export interface GetMapItemDetailsResponseTO {
  items: MapItemDetailsTO[];
}

export interface GetMapItemsRequestTO {
  coords: GeoPointTO | null;
  search: MapSearchTO | null;
  cursor: string | null;
  distance: number;
  filter: string | null;
  tag: string | null;
}

export interface GetMapItemsResponseTO {
  items: MapItemTO[];
  top_sections: MapSectionTO[];
  cursor: string | null;
  distance: number;
}

export interface GetMapRequestTO {
  tag: string | null;
}

export interface GetMapResponseTO {
  action_chips: MapActionChipTO[];
  addresses: ProfileAddressTO[];
  announcement: MapAnnouncementTO | null;
  base_urls: MapBaseUrlsTO | null;
  buttons: MapButtonTO[];
  defaults: MapDefaultsTO | null;
  filters: MapFilterTO[];
  notifications: MapNotificationsTO | null;
  empty_text: string | null;
  functionalities: string[];
  title: string | null;
}

export interface GetMapSearchSuggestionsRequestTO {
  coords: GeoPointTO | null;
  search: MapSearchTO | null;
  distance: number;
  filter: string | null;
  tag: string | null;
}

export interface GetMapSearchSuggestionsResponseTO {
  items: MapSearchSuggestionTO[];
}

export interface GetMenuIconRequestTO {
  coords: number[];
  service: string | null;
  size: number;
}

export interface GetMenuIconResponseTO {
  icon: string | null;
  iconHash: string | null;
}

export interface GetNewsGroupRequestTO {
  group_id: string | null;
}

export interface GetNewsGroupResponseTO {
  group: NewsGroupTO | null;
}

export interface GetNewsGroupServicesRequestTO {
  cursor: string | null;
  group_id: string | null;
  key: string | null;
}

export interface GetNewsGroupServicesResponseTO {
  services: NewsSenderTO[];
  cursor: string | null;
}

export interface GetNewsGroupsRequestTO {
}

export interface GetNewsGroupsResponseTO {
  if_empty: IfEmtpyScreenTO | null;
  rows: NewsGroupRowTO[];
  has_locations: boolean;
}

export interface GetNewsItemDetailsRequestTO {
  id: number;
}

export interface GetNewsItemDetailsResponseTO {
  item: NewsStreamItemTO | null;
}

export interface GetNewsStreamFilterTO {
  group_id: string | null;
  group_type: string | null;
  search_string: string | null;
  service_identity_email: string | null;
}

export interface GetNewsStreamItemsRequestTO {
  filter: GetNewsStreamFilterTO | null;
  cursor: string | null;
  news_ids: number[];
}

export interface GetNewsStreamItemsResponseTO {
  items: NewsStreamItemTO[];
  cursor: string | null;
  group_id: string | null;
}

export interface GetPaymentAssetsRequestTO {
  provider_id: string | null;
}

export interface GetPaymentAssetsResponseTO {
  assets: PaymentProviderAssetTO[];
}

export interface GetPaymentMethodsRequestTO {
  base_method: BasePaymentMethod | null;
  methods: PaymentMethodTO[];
  service: string | null;
  test_mode: boolean;
}

export interface GetPaymentMethodsResponseTO {
  methods: PaymentProviderMethodsTO[];
}

export interface GetPaymentProfileRequestTO {
  provider_id: string | null;
}

export interface GetPaymentProfileResponseTO {
  first_name: string | null;
  last_name: string | null;
}

export interface GetPaymentProvidersRequestTO {
}

export interface GetPaymentProvidersResponseTO {
  payment_providers: AppPaymentProviderTO[];
}

export interface GetPaymentTransactionsRequestTO {
  asset_id: string | null;
  cursor: string | null;
  provider_id: string | null;
  type: string | null;
}

export interface GetPaymentTransactionsResponseTO {
  transactions: PaymentProviderTransactionTO[];
  cursor: string | null;
}

export interface GetPendingPaymentDetailsRequestTO {
  transaction_id: string | null;
}

export interface GetPendingPaymentDetailsResponseTO {
  error: ErrorPaymentTO | null;
  result: PendingPaymentDetailsTO | null;
  success: boolean;
}

export interface GetProfileAddressesRequestTO {
}

export interface GetProfileAddressesResponseTO {
  items: ProfileAddressTO[];
}

export interface GetProfilePhoneNumbersRequestTO {
}

export interface GetProfilePhoneNumbersResponseTO {
  items: ProfilePhoneNumberTO[];
}

export interface GetSavedMapItemsRequestTO {
  cursor: string | null;
  tag: string | null;
}

export interface GetSavedMapItemsResponseTO {
  items: MapItemTO[];
  cursor: string | null;
}

export interface GetServiceActionInfoRequestTO {
  action: string | null;
  allow_cross_app: boolean;
  code: string | null;
}

export interface GetServiceActionInfoResponseTO {
  error: ErrorTO | null;
  actionDescription: string | null;
  app_id: string | null;
  avatar: string | null;
  avatar_id: number;
  description: string | null;
  descriptionBranding: string | null;
  email: string | null;
  name: string | null;
  profileData: string | null;
  qualifiedIdentifier: string | null;
  staticFlow: string | null;
  staticFlowBrandings: string[];
  staticFlowHash: string | null;
  type: number;
}

export interface GetStaticFlowRequestTO {
  coords: number[];
  service: string | null;
  staticFlowHash: string | null;
}

export interface GetStaticFlowResponseTO {
  staticFlow: string | null;
}

export interface GetTargetInfoRequestTO {
  currency: string | null;
  provider_id: string | null;
  target: string | null;
}

export interface GetTargetInfoResponseTO {
  error: ErrorPaymentTO | null;
  result: TargetInfoTO | null;
  success: boolean;
}

export interface GetUserInfoRequestTO {
  allow_cross_app: boolean;
  code: string | null;
}

export interface GetUserInfoResponseTO {
  error: ErrorTO | null;
  app_id: string | null;
  avatar: string | null;
  avatar_id: number;
  description: string | null;
  descriptionBranding: string | null;
  email: string | null;
  name: string | null;
  profileData: string | null;
  qualifiedIdentifier: string | null;
  type: number;
}

export interface GetUserLinkRequestTO {
  link: string | null;
}

export interface GetUserLinkResponseTO {
  link: string | null;
}

export interface GroupTO {
  avatar_hash: string | null;
  guid: string | null;
  members: string[];
  name: string | null;
}

export interface HeartBeatRequestTO {
  SDKVersion: string | null;
  appType: number;
  buildFingerPrint: string | null;
  deviceId: string | null;
  deviceModelName: string | null;
  flushBackLog: boolean;
  localeCountry: string | null;
  localeLanguage: string | null;
  majorVersion: number;
  minorVersion: number;
  netCarrierCode: string | null;
  netCarrierName: string | null;
  netCountry: string | null;
  netCountryCode: string | null;
  networkState: string | null;
  product: string | null;
  simCarrierCode: string | null;
  simCarrierName: string | null;
  simCountry: string | null;
  simCountryCode: string | null;
  timestamp: number;
  timezone: string | null;
  timezoneDeltaGMT: number;
}

export interface HeartBeatResponseTO {
  systemTime: number;
}

export interface IdentityTO {
  avatarId: number;
  birthdate: number;
  communityId: number;
  email: string | null;
  firstName: string | null;
  gender: number;
  hasBirthdate: boolean;
  hasGender: boolean;
  homeScreenId: string | null;
  lastName: string | null;
  name: string | null;
  owncloudPassword: string | null;
  owncloudUri: string | null;
  owncloudUsername: string | null;
  profileData: string | null;
  qualifiedIdentifier: string | null;
}

export interface IdentityUpdateRequestTO {
  identity: IdentityTO | null;
}

export interface IdentityUpdateResponseTO {
}

export interface IfEmtpyScreenTO {
  message: string | null;
  title: string | null;
}

export interface InviteFriendRequestTO {
  allow_cross_app: boolean;
  email: string | null;
  message: string | null;
}

export interface InviteFriendResponseTO {
}

export interface JSEmbeddingItemTO {
  hash: string | null;
  name: string | null;
}

export interface JobChatAnonymousTO {
  default_value: boolean;
  enabled: boolean;
}

export interface JobCriteriaGeoLocationTO {
  latitude: number;
  longitude: number;
}

export interface JobCriteriaLocationTO {
  geo: JobCriteriaGeoLocationTO | null;
  address: string | null;
  distance: number;
}

export interface JobCriteriaNotificationsTO {
  delivery_day: string | null;
  delivery_time: number;
  how_often: string | null;
  timezone: string | null;
}

export interface JobKeyLabelTO {
  enabled: boolean;
  key: string | null;
  label: string | null;
}

export interface JobOfferChatActionTO {
  chat_key: string | null;
  icon: string | null;
  label: string | null;
  readonly type: JobOfferActionType.CHAT;
}

export interface JobOfferContractTO {
  type: string | null;
}

export interface JobOfferEmployerTO {
  name: string | null;
}

export interface JobOfferFunctionTO {
  description: string | null;
  title: string | null;
}

export interface JobOfferLocationTO {
  geo_location: LatLonTO | null;
  city: string | null;
  country_code: string | null;
  postal_code: string | null;
  street: string | null;
  street_number: string | null;
}

export interface JobOfferOpenActionTO {
  action: string | null;
  icon: string | null;
  label: string | null;
  readonly type: JobOfferActionType.OPEN;
}

export interface JobOfferProviderTO {
  image_url: string | null;
}

export interface JobOfferSourceTO {
  avatar_url: string | null;
  id: string | null;
  name: string | null;
  type: string | null;
}

export interface JobOfferTO {
  actions: JobOfferActionTO[];
  contract: JobOfferContractTO | null;
  employer: JobOfferEmployerTO | null;
  function: JobOfferFunctionTO | null;
  location: JobOfferLocationTO | null;
  source: JobOfferSourceTO | null;
  details: string | null;
  job_id: number;
  timestamp: number;
}

export interface JobsInfoTO {
  providers: JobOfferProviderTO[];
  description: string | null;
  title: string | null;
}

export interface JsMessageFlowMemberRunTO {
  steps: Step[];
  flow_params: string | null;
  hashed_tag: string | null;
  message_flow_run_id: string | null;
  parent_message_key: string | null;
  sender: string | null;
  service_action: string | null;
}

export interface LatLonTO {
  lat: number;
  lon: number;
}

export interface LineStringGeometryTO {
  line: CoordsListTO | null;
  color: string | null;
  readonly type: MapGeometryType.LINE_STRING;
}

export interface LinkListSectionItemTO {
  external: boolean;
  request_user_link: boolean;
  style: number;
  url: string | null;
  icon: string | null;
  icon_color: string | null;
  title: string | null;
  readonly type: MapListSectionItemType.LINK;
}

export interface ListSectionTO {
  items: MapListSectionItemTO[];
  style: string | null;
  readonly type: MapSectionType.LIST;
}

export interface ListStreetsRequestTO {
  zip_code: string | null;
}

export interface ListStreetsResponseTO {
  items: string[];
}

export interface ListZipCodesRequestTO {
}

export interface ListZipCodesResponseTO {
  items: ZipCodeTO[];
}

export interface LocationComponentTO {
  validators: FormValidatorTO[];
  description: string | null;
  id: string | null;
  sensitive: boolean;
  title: string | null;
  readonly type: FormComponentType.LOCATION;
}

export interface LocationComponentValueTO {
  address: PostalAddressTO | null;
  latitude: number;
  longitude: number;
  id: string | null;
  readonly type: FormComponentType.LOCATION;
}

export interface LocationWidgetResultTO {
  altitude: number;
  horizontal_accuracy: number;
  latitude: number;
  longitude: number;
  timestamp: number;
  vertical_accuracy: number;
}

export interface LockMessageRequestTO {
  message_key: string | null;
  message_parent_key: string | null;
}

export interface LockMessageResponseTO {
  members: MemberStatusTO[];
}

export interface LogErrorRequestTO {
  description: string | null;
  errorMessage: string | null;
  mobicageVersion: string | null;
  platform: number;
  platformVersion: string | null;
  timestamp: number;
}

export interface LogErrorResponseTO {
}

export interface LogInvitationSecretSentRequestTO {
  phone_number: string | null;
  secret: string | null;
  timestamp: number;
}

export interface LogInvitationSecretSentResponseTO {
}

export interface LongWidgetResultTO {
  value: number;
}

export interface MapBaseUrlsTO {
  icon_pin: string | null;
  icon_transparent: string | null;
}

export interface MapButtonTO {
  action: string | null;
  color: string | null;
  icon: string | null;
  service: string | null;
  text: string | null;
}

export interface MapDefaultsTO {
  coords: GeoPointTO | null;
  distance: number;
  filter: string | null;
  max_distance: number;
}

export interface MapFilterTO {
  key: string | null;
  label: string | null;
}

export interface MapIconTO {
  color: string | null;
  id: string | null;
}

export interface MapItemDetailsTO {
  geometry: MapGeometryTO[];
  sections: MapSectionTO[];
  id: string | null;
}

export interface MapItemLineTextPartTO {
  color: string | null;
  text: string | null;
}

export interface MapItemLineTextTO {
  parts: MapItemLineTextPartTO[];
  readonly type: MapItemLineType.TEXT;
}

export interface MapItemTO {
  coords: GeoPointTO | null;
  icon: MapIconTO | null;
  lines: MapItemLineTO[];
  description: string | null;
  id: string | null;
  title: string | null;
}

export interface MapNotificationsTO {
  enabled: boolean;
}

export interface MapSearchSuggestionItemTO {
  id: string | null;
  text: string | null;
  readonly type: MapSearchSuggestionType.ITEM;
}

export interface MapSearchSuggestionKeywordTO {
  text: string | null;
  readonly type: MapSearchSuggestionType.KEYWORD;
}

export interface MapSearchTO {
  query: string | null;
}

export interface MapVoteOptionTO {
  color: string | null;
  count: number;
  icon: string | null;
  id: string | null;
  selected: boolean;
  title: string | null;
}

export interface MarkMessagesAsReadRequestTO {
  message_keys: string[];
  parent_message_key: string | null;
}

export interface MarkMessagesAsReadResponseTO {
}

export interface MaxDateValidatorTO {
  day: number;
  error_message: string | null;
  hour: number;
  minute: number;
  month: number;
  year: number;
  readonly type: FormValidatorType.MAXDATE;
}

export interface MaxLengthValidatorTO {
  error_message: string | null;
  value: number;
  readonly type: FormValidatorType.MAXLENGTH;
}

export interface MaxValidatorTO {
  error_message: string | null;
  value: number;
  readonly type: FormValidatorType.MAX;
}

export interface MediaSectionTO {
  items: BaseMediaTO[];
  ratio: SizeTO | null;
  readonly type: MapSectionType.MEDIA;
}

export interface MediaTO {
  content: string | null;
  height: number;
  thumbnail_url: string | null;
  type: string | null;
  width: number;
}

export interface MemberStatusTO {
  acked_timestamp: number;
  button_id: string | null;
  custom_reply: string | null;
  member: string | null;
  received_timestamp: number;
  status: number;
}

export interface MemberStatusUpdateRequestTO {
  acked_timestamp: number;
  button_id: string | null;
  custom_reply: string | null;
  flags: number;
  member: string | null;
  message: string | null;
  parent_message: string | null;
  received_timestamp: number;
  status: number;
}

export interface MemberStatusUpdateResponseTO {
}

export interface MessageEmbeddedAppTO {
  context: string | null;
  description: string | null;
  id: string | null;
  image_url: string | null;
  result: string | null;
  title: string | null;
}

export interface MessageFlowErrorRequestTO {
  description: string | null;
  errorMessage: string | null;
  jsCommand: string | null;
  mobicageVersion: string | null;
  platform: number;
  platformVersion: string | null;
  stackTrace: string | null;
  timestamp: number;
}

export interface MessageFlowErrorResponseTO {
}

export interface MessageFlowFinishedRequestTO {
  end_id: string | null;
  message_flow_run_id: string | null;
  parent_message_key: string | null;
}

export interface MessageFlowFinishedResponseTO {
}

export interface MessageFlowMemberResultRequestTO {
  run: JsMessageFlowMemberRunTO | null;
  email_admins: boolean;
  emails: string[];
  end_id: string | null;
  flush_id: string | null;
  message_flow_name: string | null;
  results_email: boolean;
  timestamp: number;
}

export interface MessageFlowMemberResultResponseTO {
}

export interface MessageFlowStepTO {
  acknowledged_timestamp: number;
  answer_id: string | null;
  button: string | null;
  message: string | null;
  message_flow_id: string | null;
  received_timestamp: number;
  step_id: string | null;
  readonly step_type: MessageType.MESSAGE;
}

export interface MessageLockedRequestTO {
  members: MemberStatusTO[];
  dirty_behavior: number;
  message_key: string | null;
  parent_message_key: string | null;
}

export interface MessageLockedResponseTO {
}

export interface MessageTO {
  attachments: AttachmentTO[];
  buttons: ButtonTO[];
  embedded_app: MessageEmbeddedAppTO | null;
  members: MemberStatusTO[];
  alert_flags: number;
  branding: string | null;
  context: string | null;
  default_priority: number;
  default_sticky: boolean;
  dismiss_button_ui_flags: number;
  flags: number;
  key: string | null;
  message: string | null;
  parent_key: string | null;
  priority: number;
  sender: string | null;
  threadTimestamp: number;
  thread_avatar_hash: string | null;
  thread_background_color: string | null;
  thread_size: number;
  thread_text_color: string | null;
  timeout: number;
  timestamp: number;
  readonly message_type: NewMessageType.MESSAGE;
}

export interface MinDateValidatorTO {
  day: number;
  error_message: string | null;
  hour: number;
  minute: number;
  month: number;
  year: number;
  readonly type: FormValidatorType.MINDATE;
}

export interface MinLengthValidatorTO {
  error_message: string | null;
  value: number;
  readonly type: FormValidatorType.MINLENGTH;
}

export interface MinValidatorTO {
  error_message: string | null;
  value: number;
  readonly type: FormValidatorType.MIN;
}

export interface MultiLineStringGeometryTO {
  lines: CoordsListTO[];
  color: string | null;
  readonly type: MapGeometryType.MULTI_LINE_STRING;
}

export interface MultiPolygonGeometryTO {
  polygons: PolygonTO[];
  color: string | null;
  readonly type: MapGeometryType.MULTI_POLYGON;
}

export interface MultiSelectComponentTO {
  choices: ValueTO[];
  validators: FormValidatorTO[];
  description: string | null;
  id: string | null;
  sensitive: boolean;
  title: string | null;
  readonly type: FormComponentType.MULTI_SELECT;
}

export interface MultiSelectComponentValueTO {
  values: string[];
  id: string | null;
  readonly type: FormComponentType.MULTI_SELECT;
}

export interface MultiSelectFormMessageTO {
  attachments: AttachmentTO[];
  form: MultiSelectFormTO | null;
  member: MemberStatusTO | null;
  alert_flags: number;
  branding: string | null;
  context: string | null;
  default_priority: number;
  default_sticky: boolean;
  flags: number;
  key: string | null;
  message: string | null;
  message_type: number;
  parent_key: string | null;
  priority: number;
  sender: string | null;
  threadTimestamp: number;
  thread_avatar_hash: string | null;
  thread_background_color: string | null;
  thread_size: number;
  thread_text_color: string | null;
  timestamp: number;
}

export interface MultiSelectFormTO {
  widget: MultiSelectTO | null;
  javascript_validation: string | null;
  negative_button: string | null;
  negative_button_ui_flags: number;
  negative_confirmation: string | null;
  positive_button: string | null;
  positive_button_ui_flags: number;
  positive_confirmation: string | null;
  type: string | null;
}

export interface MultiSelectTO {
  choices: ChoiceTO[];
  values: string[];
}

export interface MyDigiPassAddress {
  address_1: string | null;
  address_2: string | null;
  city: string | null;
  country: string | null;
  state: string | null;
  zip: string | null;
}

export interface MyDigiPassEidAddress {
  municipality: string | null;
  street_and_number: string | null;
  zip_code: string | null;
}

export interface MyDigiPassEidProfile {
  card_number: string | null;
  chip_number: string | null;
  created_at: string | null;
  date_of_birth: string | null;
  first_name: string | null;
  first_name_3: string | null;
  gender: string | null;
  issuing_municipality: string | null;
  last_name: string | null;
  location_of_birth: string | null;
  nationality: string | null;
  noble_condition: string | null;
  validity_begins_at: string | null;
  validity_ends_at: string | null;
}

export interface MyDigiPassFormMessageTO {
  attachments: AttachmentTO[];
  form: MyDigiPassFormTO | null;
  member: MemberStatusTO | null;
  alert_flags: number;
  branding: string | null;
  context: string | null;
  default_priority: number;
  default_sticky: boolean;
  flags: number;
  key: string | null;
  message: string | null;
  message_type: number;
  parent_key: string | null;
  priority: number;
  sender: string | null;
  threadTimestamp: number;
  thread_avatar_hash: string | null;
  thread_background_color: string | null;
  thread_size: number;
  thread_text_color: string | null;
  timestamp: number;
}

export interface MyDigiPassFormTO {
  widget: MyDigiPassTO | null;
  javascript_validation: string | null;
  negative_button: string | null;
  negative_button_ui_flags: number;
  negative_confirmation: string | null;
  positive_button: string | null;
  positive_button_ui_flags: number;
  positive_confirmation: string | null;
  type: string | null;
}

export interface MyDigiPassProfile {
  born_on: string | null;
  first_name: string | null;
  last_name: string | null;
  preferred_locale: string | null;
  updated_at: string | null;
  uuid: string | null;
}

export interface MyDigiPassTO {
  scope: string | null;
}

export interface MyDigiPassWidgetResultTO {
  address: MyDigiPassAddress | null;
  eid_address: MyDigiPassEidAddress | null;
  eid_profile: MyDigiPassEidProfile | null;
  profile: MyDigiPassProfile | null;
  eid_photo: string | null;
  email: string | null;
  phone: string | null;
}

export interface NewAdvancedOrderFormRequestTO {
  form_message: AdvancedOrderFormMessageTO | null;
}

export interface NewAdvancedOrderFormResponseTO {
  received_timestamp: number;
}

export interface NewAutoCompleteFormRequestTO {
  form_message: AutoCompleteFormMessageTO | null;
}

export interface NewAutoCompleteFormResponseTO {
  received_timestamp: number;
}

export interface NewDateSelectFormRequestTO {
  form_message: DateSelectFormMessageTO | null;
}

export interface NewDateSelectFormResponseTO {
  received_timestamp: number;
}

export interface NewFlowMessageRequestTO {
  form_result: FormResult | null;
  message: NewFlowMessageTO | null;
  message_flow_run_id: string | null;
  step_id: string | null;
}

export interface NewFlowMessageResponseTO {
}

export interface NewFriendSelectFormRequestTO {
  form_message: FriendSelectFormMessageTO | null;
}

export interface NewFriendSelectFormResponseTO {
  received_timestamp: number;
}

export interface NewGPSLocationFormRequestTO {
  form_message: GPSLocationFormMessageTO | null;
}

export interface NewGPSLocationFormResponseTO {
  received_timestamp: number;
}

export interface NewJobsRequestTO {
  activity_types: string[];
  creation_time: number;
}

export interface NewJobsResponseTO {
}

export interface NewMessageRequestTO {
  message: MessageTO | null;
}

export interface NewMessageResponseTO {
  received_timestamp: number;
}

export interface NewMultiSelectFormRequestTO {
  form_message: MultiSelectFormMessageTO | null;
}

export interface NewMultiSelectFormResponseTO {
  received_timestamp: number;
}

export interface NewMyDigiPassFormRequestTO {
  form_message: MyDigiPassFormMessageTO | null;
}

export interface NewMyDigiPassFormResponseTO {
  received_timestamp: number;
}

export interface NewOauthFormRequestTO {
  form_message: OauthFormMessageTO | null;
}

export interface NewOauthFormResponseTO {
  received_timestamp: number;
}

export interface NewOpenIdFormRequestTO {
  form_message: OpenIdFormMessageTO | null;
}

export interface NewOpenIdFormResponseTO {
  received_timestamp: number;
}

export interface NewPayFormRequestTO {
  form_message: PayFormMessageTO | null;
}

export interface NewPayFormResponseTO {
  received_timestamp: number;
}

export interface NewPhotoUploadFormRequestTO {
  form_message: PhotoUploadFormMessageTO | null;
}

export interface NewPhotoUploadFormResponseTO {
  received_timestamp: number;
}

export interface NewRangeSliderFormRequestTO {
  form_message: RangeSliderFormMessageTO | null;
}

export interface NewRangeSliderFormResponseTO {
  received_timestamp: number;
}

export interface NewSignFormRequestTO {
  form_message: SignFormMessageTO | null;
}

export interface NewSignFormResponseTO {
  received_timestamp: number;
}

export interface NewSingleSelectFormRequestTO {
  form_message: SingleSelectFormMessageTO | null;
}

export interface NewSingleSelectFormResponseTO {
  received_timestamp: number;
}

export interface NewSingleSliderFormRequestTO {
  form_message: SingleSliderFormMessageTO | null;
}

export interface NewSingleSliderFormResponseTO {
  received_timestamp: number;
}

export interface NewTextBlockFormRequestTO {
  form_message: TextBlockFormMessageTO | null;
}

export interface NewTextBlockFormResponseTO {
  received_timestamp: number;
}

export interface NewTextLineFormRequestTO {
  form_message: TextLineFormMessageTO | null;
}

export interface NewTextLineFormResponseTO {
  received_timestamp: number;
}

export interface NewsActionButtonTO {
  action: string | null;
  caption: string | null;
  flow_params: string | null;
  id: string | null;
}

export interface NewsGroupLayoutTO {
  background_image_url: string | null;
  badge_count: number;
  promo_image_url: string | null;
  subtitle: string | null;
  title: string | null;
}

export interface NewsGroupRowTO {
  items: NewsGroupTO[];
}

export interface NewsGroupSectionTO {
  filter: GetNewsStreamFilterTO | null;
  items: NewsStreamItemTO[];
  group_id: string | null;
  placeholder_image: string | null;
  readonly type: MapSectionType.NEWS_GROUP;
}

export interface NewsGroupTO {
  if_empty: IfEmtpyScreenTO | null;
  layout: NewsGroupLayoutTO | null;
  services: NewsSenderTO[];
  tabs: NewsGroupTabInfoTO[];
  key: string | null;
  name: string | null;
}

export interface NewsGroupTabInfoTO {
  key: string | null;
  name: string | null;
  notifications: number;
}

export interface NewsItemSectionTO {
  item: NewsStreamItemTO | null;
  group_id: string | null;
  placeholder_image: string | null;
  readonly type: MapSectionType.NEWS_ITEM;
}

export interface NewsSectionTO {
  filter: GetNewsStreamFilterTO | null;
  limit: number;
  placeholder_image: string | null;
  readonly type: MapSectionType.NEWS;
}

export interface NewsSenderTO {
  avatar_id: number;
  avatar_url: string | null;
  email: string | null;
  name: string | null;
}

export interface NewsStreamItemTO {
  buttons: NewsActionButtonTO[];
  media: MediaTO | null;
  sender: NewsSenderTO | null;
  actions: number;
  blocked: boolean;
  disabled: boolean;
  flags: number;
  id: number;
  match_type: number;
  message: string | null;
  notifications: number;
  qr_code_caption: string | null;
  qr_code_content: string | null;
  share_url: string | null;
  timestamp: number;
  title: string | null;
  type: number;
}

export interface NextActionDefaultTO {
  readonly type: NextActionType.NEXT;
}

export interface NextActionSectionTO {
  section: string | null;
  readonly type: NextActionType.SECTION;
}

export interface NextActionSubmitTO {
  readonly type: NextActionType.SUBMIT;
}

export interface NextActionURLTO {
  url: string | null;
  readonly type: NextActionType.URL;
}

export interface OauthFormMessageTO {
  attachments: AttachmentTO[];
  form: OauthFormTO | null;
  member: MemberStatusTO | null;
  alert_flags: number;
  branding: string | null;
  context: string | null;
  default_priority: number;
  default_sticky: boolean;
  flags: number;
  key: string | null;
  message: string | null;
  message_type: number;
  parent_key: string | null;
  priority: number;
  sender: string | null;
  threadTimestamp: number;
  thread_avatar_hash: string | null;
  thread_background_color: string | null;
  thread_size: number;
  thread_text_color: string | null;
  timestamp: number;
}

export interface OauthFormTO {
  widget: OauthTO | null;
  javascript_validation: string | null;
  negative_button: string | null;
  negative_button_ui_flags: number;
  negative_confirmation: string | null;
  positive_button: string | null;
  positive_button_ui_flags: number;
  positive_confirmation: string | null;
  type: string | null;
}

export interface OauthTO {
  caption: string | null;
  success_message: string | null;
  url: string | null;
}

export interface OpenIdAddressTO {
  country: string | null;
  locality: string | null;
  postal_code: string | null;
  street_address: string | null;
}

export interface OpenIdFormMessageTO {
  attachments: AttachmentTO[];
  form: OpenIdFormTO | null;
  member: MemberStatusTO | null;
  alert_flags: number;
  branding: string | null;
  context: string | null;
  default_priority: number;
  default_sticky: boolean;
  flags: number;
  key: string | null;
  message: string | null;
  message_type: number;
  parent_key: string | null;
  priority: number;
  sender: string | null;
  threadTimestamp: number;
  thread_avatar_hash: string | null;
  thread_background_color: string | null;
  thread_size: number;
  thread_text_color: string | null;
  timestamp: number;
}

export interface OpenIdFormTO {
  widget: OpenIdTO | null;
  javascript_validation: string | null;
  negative_button: string | null;
  negative_button_ui_flags: number;
  negative_confirmation: string | null;
  positive_button: string | null;
  positive_button_ui_flags: number;
  positive_confirmation: string | null;
  type: string | null;
}

export interface OpenIdTO {
  provider: string | null;
  scope: string | null;
}

export interface OpenIdWidgetResultTO {
  address: OpenIdAddressTO | null;
  birthdate: string | null;
  email: string | null;
  email_verified: boolean;
  family_name: string | null;
  gender: string | null;
  given_name: string | null;
  locale: string | null;
  name: string | null;
  phone_number: string | null;
  phone_number_verified: boolean;
}

export interface OpeningHourExceptionTO {
  periods: OpeningPeriodTO[];
  description: string | null;
  description_color: string | null;
  end_date: string | null;
  start_date: string | null;
}

export interface OpeningHourTO {
  day: number;
  time: string | null;
}

export interface OpeningHoursListSectionItemTO {
  opening_hours: OpeningInfoTO | null;
  icon: string | null;
  icon_color: string | null;
  title: string | null;
  readonly type: MapListSectionItemType.OPENING_HOURS;
}

export interface OpeningHoursSectionItemTO {
  opening_hours: OpeningHoursTO | null;
  timezone: string | null;
  icon: string | null;
  icon_color: string | null;
  title: string | null;
  readonly type: MapListSectionItemType.DYNAMIC_OPENING_HOURS;
}

export interface OpeningHoursTO {
  exceptional_opening_hours: OpeningHourExceptionTO[];
  periods: OpeningPeriodTO[];
  id: string | null;
  text: string | null;
  title: string | null;
  type: string | null;
}

export interface OpeningInfoTO {
  weekday_text: WeekDayTextTO[];
  description: string | null;
  description_color: string | null;
  name: string | null;
  subtitle: string | null;
  title: string | null;
  title_color: string | null;
}

export interface OpeningPeriodTO {
  close: OpeningHourTO | null;
  open: OpeningHourTO | null;
  description: string | null;
  description_color: string | null;
}

export interface ParagraphComponentTO {
  description: string | null;
  title: string | null;
  readonly type: FormComponentType.PARAGRAPH;
}

export interface PayFormMessageTO {
  attachments: AttachmentTO[];
  form: PayFormTO | null;
  member: MemberStatusTO | null;
  alert_flags: number;
  branding: string | null;
  context: string | null;
  default_priority: number;
  default_sticky: boolean;
  flags: number;
  key: string | null;
  message: string | null;
  message_type: number;
  parent_key: string | null;
  priority: number;
  sender: string | null;
  threadTimestamp: number;
  thread_avatar_hash: string | null;
  thread_background_color: string | null;
  thread_size: number;
  thread_text_color: string | null;
  timestamp: number;
}

export interface PayFormTO {
  widget: PayTO | null;
  javascript_validation: string | null;
  negative_button: string | null;
  negative_button_ui_flags: number;
  negative_confirmation: string | null;
  positive_button: string | null;
  positive_button_ui_flags: number;
  positive_confirmation: string | null;
  type: string | null;
}

export interface PayMethodTO {
  amount: number;
  currency: string | null;
  precision: number;
  target: string | null;
}

export interface PayTO {
  base_method: BasePaymentMethod | null;
  methods: PaymentMethod[];
  auto_submit: boolean;
  embedded_app_id: string | null;
  memo: string | null;
  target: string | null;
  test_mode: boolean;
}

export interface PayWidgetResultTO {
  provider_id: string | null;
  status: string | null;
  transaction_id: string | null;
}

export interface PaymentAssetBalanceTO {
  amount: number;
  description: string | null;
  precision: number;
}

export interface PaymentAssetRequiredActionTO {
  action: string | null;
  data: string | null;
  description: string | null;
}

export interface PaymentMethod {
  amount: number;
  calculate_amount: boolean;
  currency: string | null;
  precision: number;
  provider_id: string | null;
  target: string | null;
}

export interface PaymentMethodTO {
  amount: number;
  calculate_amount: boolean;
  currency: string | null;
  precision: number;
  provider_id: string | null;
  target: string | null;
}

export interface PaymentProviderAssetTO {
  available_balance: PaymentAssetBalanceTO | null;
  required_action: PaymentAssetRequiredActionTO | null;
  total_balance: PaymentAssetBalanceTO | null;
  currency: string | null;
  enabled: boolean;
  has_balance: boolean;
  has_transactions: boolean;
  id: string | null;
  name: string | null;
  provider_id: string | null;
  type: string | null;
  verified: boolean;
}

export interface PaymentProviderMethodsTO {
  embedded_app: EmbeddedAppTO | null;
  methods: PayMethodTO[];
  provider: AppPaymentProviderTO | null;
}

export interface PaymentProviderTransactionTO {
  amount: number;
  currency: string | null;
  from_asset_id: string | null;
  id: string | null;
  memo: string | null;
  name: string | null;
  precision: number;
  timestamp: number;
  to_asset_id: string | null;
  type: string | null;
}

export interface PendingPaymentDetailsTO {
  assets: PaymentProviderAssetTO[];
  provider: AppPaymentProviderTO | null;
  receiver: UserDetailsTO | null;
  receiver_asset: PaymentProviderAssetTO | null;
  amount: number;
  currency: string | null;
  memo: string | null;
  precision: number;
  status: string | null;
  timestamp: number;
  transaction_id: string | null;
}

export interface PendingPaymentTO {
  status: string | null;
  transaction_id: string | null;
}

export interface PhotoUploadFormMessageTO {
  attachments: AttachmentTO[];
  form: PhotoUploadFormTO | null;
  member: MemberStatusTO | null;
  alert_flags: number;
  branding: string | null;
  context: string | null;
  default_priority: number;
  default_sticky: boolean;
  flags: number;
  key: string | null;
  message: string | null;
  message_type: number;
  parent_key: string | null;
  priority: number;
  sender: string | null;
  threadTimestamp: number;
  thread_avatar_hash: string | null;
  thread_background_color: string | null;
  thread_size: number;
  thread_text_color: string | null;
  timestamp: number;
}

export interface PhotoUploadFormTO {
  widget: PhotoUploadTO | null;
  javascript_validation: string | null;
  negative_button: string | null;
  negative_button_ui_flags: number;
  negative_confirmation: string | null;
  positive_button: string | null;
  positive_button_ui_flags: number;
  positive_confirmation: string | null;
  type: string | null;
}

export interface PhotoUploadTO {
  camera: boolean;
  gallery: boolean;
  quality: string | null;
  ratio: string | null;
}

export interface PokeServiceRequestTO {
  context: string | null;
  email: string | null;
  hashed_tag: string | null;
  timestamp: number;
}

export interface PokeServiceResponseTO {
}

export interface PolygonGeometryTO {
  rings: CoordsListTO[];
  color: string | null;
  readonly type: MapGeometryType.POLYGON;
}

export interface PolygonTO {
  rings: CoordsListTO[];
}

export interface PostalAddressTO {
  address_lines: string[];
  country: string | null;
  locality: string | null;
  post_office_box_number: string | null;
  postal_code: string | null;
  region: string | null;
  street_address: string | null;
}

export interface PressMenuIconRequestTO {
  context: string | null;
  coords: number[];
  generation: number;
  hashed_tag: string | null;
  message_flow_run_id: string | null;
  service: string | null;
  static_flow_hash: string | null;
  timestamp: number;
}

export interface PressMenuIconResponseTO {
}

export interface ProfileAddressTO {
  geo_location: GeoPointTO | null;
  bus_nr: string | null;
  city: string | null;
  distance: number;
  house_nr: string | null;
  label: string | null;
  street_name: string | null;
  type: number;
  uid: string | null;
  zip_code: string | null;
}

export interface ProfilePhoneNumberTO {
  label: string | null;
  number: string | null;
  type: number;
  uid: string | null;
}

export interface PublicKeyTO {
  algorithm: string | null;
  index: string | null;
  name: string | null;
  public_key: string | null;
}

export interface PushNotificationSettingsTO {
  enabled: boolean;
}

export interface PutGroupRequestTO {
  avatar: string | null;
  guid: string | null;
  members: string[];
  name: string | null;
}

export interface PutGroupResponseTO {
  avatar_hash: string | null;
}

export interface RangeSliderFormMessageTO {
  attachments: AttachmentTO[];
  form: RangeSliderFormTO | null;
  member: MemberStatusTO | null;
  alert_flags: number;
  branding: string | null;
  context: string | null;
  default_priority: number;
  default_sticky: boolean;
  flags: number;
  key: string | null;
  message: string | null;
  message_type: number;
  parent_key: string | null;
  priority: number;
  sender: string | null;
  threadTimestamp: number;
  thread_avatar_hash: string | null;
  thread_background_color: string | null;
  thread_size: number;
  thread_text_color: string | null;
  timestamp: number;
}

export interface RangeSliderFormTO {
  widget: RangeSliderTO | null;
  javascript_validation: string | null;
  negative_button: string | null;
  negative_button_ui_flags: number;
  negative_confirmation: string | null;
  positive_button: string | null;
  positive_button_ui_flags: number;
  positive_confirmation: string | null;
  type: string | null;
}

export interface RangeSliderTO {
  high_value: number;
  low_value: number;
  max: number;
  min: number;
  precision: number;
  step: number;
  unit: string | null;
}

export interface ReceiveApiCallResultRequestTO {
  error: string | null;
  id: number;
  result: string | null;
}

export interface ReceiveApiCallResultResponseTO {
}

export interface ReceivePaymentRequestTO {
  amount: number;
  asset_id: string | null;
  memo: string | null;
  precision: number;
  provider_id: string | null;
}

export interface ReceivePaymentResponseTO {
  error: ErrorPaymentTO | null;
  result: PendingPaymentTO | null;
  success: boolean;
}

export interface RegexValidatorTO {
  error_message: string | null;
  value: string | null;
  readonly type: FormValidatorType.REGEX;
}

export interface ReportObjectionableContentRequestTO {
  object: string | null;
  reason: string | null;
  type: string | null;
}

export interface ReportObjectionableContentResponseTO {
}

export interface RequiredValidatorTO {
  error_message: string | null;
  readonly type: FormValidatorType.REQUIRED;
}

export interface SaveJobsCriteriaRequestTO {
  criteria: SaveJobsCriteriaTO | null;
  active: boolean;
}

export interface SaveJobsCriteriaResponseTO {
  active: boolean;
  new_profile: boolean;
}

export interface SaveJobsCriteriaTO {
  location: JobCriteriaLocationTO | null;
  notifications: JobCriteriaNotificationsTO | null;
  contract_types: string[];
  job_domains: string[];
  keywords: string[];
}

export interface SaveMapItemVoteRequestTO {
  item_id: string | null;
  option_id: string | null;
  tag: string | null;
  vote_id: string | null;
}

export interface SaveMapItemVoteResponseTO {
  options: MapVoteOptionTO[];
  item_id: string | null;
  vote_id: string | null;
}

export interface SaveMapNotificationsRequestTO {
  notifications: MapNotificationsTO | null;
  tag: string | null;
}

export interface SaveMapNotificationsResponseTO {
  notifications: MapNotificationsTO | null;
  message: string | null;
}

export interface SaveNewsGroupServicesRequestTO {
  action: string | null;
  group_id: string | null;
  key: string | null;
  service: string | null;
}

export interface SaveNewsGroupServicesResponseTO {
}

export interface SaveNewsStatisticsRequestTO {
  news_ids: number[];
  type: string | null;
}

export interface SaveNewsStatisticsResponseTO {
}

export interface SaveSettingsRequest {
  push_notifications: PushNotificationSettingsTO | null;
  callLogging: boolean;
  tracking: boolean;
}

export interface SaveSettingsResponse {
  settings: SettingsTO | null;
}

export interface SearchSuggestionTO {
  icon: string | null;
  title: string | null;
  readonly type: MapActionChipType.SEARCH_SUGGESTION;
}

export interface SendApiCallCallbackResultTO {
  error: string | null;
  result: string | null;
}

export interface SendApiCallRequestTO {
  hashed_tag: string | null;
  id: number;
  method: string | null;
  params: string | null;
  service: string | null;
  synchronous: boolean;
}

export interface SendApiCallResponseTO {
  result: SendApiCallCallbackResultTO | null;
}

export interface SendMessageRequestTO {
  attachments: AttachmentTO[];
  buttons: ButtonTO[];
  embedded_app: MessageEmbeddedAppTO | null;
  flags: number;
  key: string | null;
  members: string[];
  message: string | null;
  parent_key: string | null;
  priority: number;
  sender_reply: string | null;
  timeout: number;
}

export interface SendMessageResponseTO {
  key: string | null;
  timestamp: number;
}

export interface ServiceMenuItemLinkTO {
  external: boolean;
  request_user_link: boolean;
  url: string | null;
}

export interface ServiceMenuItemTO {
  form: FormVersionTO | null;
  link: ServiceMenuItemLinkTO | null;
  action: number;
  coords: number[];
  embeddedApp: string | null;
  fallThrough: boolean;
  hashedTag: string | null;
  iconColor: string | null;
  iconHash: string | null;
  iconName: string | null;
  label: string | null;
  requiresWifi: boolean;
  roles: number[];
  runInBackground: boolean;
  screenBranding: string | null;
  staticFlowHash: string | null;
}

export interface ServiceMenuTO {
  items: ServiceMenuItemTO[];
  aboutLabel: string | null;
  branding: string | null;
  callConfirmation: string | null;
  callLabel: string | null;
  messagesLabel: string | null;
  phoneNumber: string | null;
  share: boolean;
  shareCaption: string | null;
  shareDescription: string | null;
  shareImageUrl: string | null;
  shareLabel: string | null;
  shareLinkUrl: string | null;
  staticFlowBrandings: string[];
}

export interface SetMobilePhoneNumberRequestTO {
  phoneNumber: string | null;
}

export interface SetMobilePhoneNumberResponseTO {
}

export interface SettingsTO {
  consent: ConsentSettingsTO | null;
  backgroundFetchTimestamps: number[];
  geoLocationSamplingIntervalBattery: number;
  geoLocationSamplingIntervalCharging: number;
  geoLocationTracking: boolean;
  geoLocationTrackingDays: number;
  geoLocationTrackingTimeslot: number[];
  operatingVersion: number;
  recordGeoLocationWithPhoneCalls: boolean;
  recordPhoneCalls: boolean;
  recordPhoneCallsDays: number;
  recordPhoneCallsTimeslot: number[];
  useGPSBattery: boolean;
  useGPSCharging: boolean;
  version: number;
  wifiOnlyDownloads: boolean;
  xmppReconnectInterval: number;
}

export interface ShareServiceRequestTO {
  recipient: string | null;
  service_email: string | null;
}

export interface ShareServiceResponseTO {
}

export interface SignFormMessageTO {
  attachments: AttachmentTO[];
  form: SignFormTO | null;
  member: MemberStatusTO | null;
  alert_flags: number;
  branding: string | null;
  context: string | null;
  default_priority: number;
  default_sticky: boolean;
  flags: number;
  key: string | null;
  message: string | null;
  message_type: number;
  parent_key: string | null;
  priority: number;
  sender: string | null;
  threadTimestamp: number;
  thread_avatar_hash: string | null;
  thread_background_color: string | null;
  thread_size: number;
  thread_text_color: string | null;
  timestamp: number;
}

export interface SignFormTO {
  widget: SignTO | null;
  javascript_validation: string | null;
  negative_button: string | null;
  negative_button_ui_flags: number;
  negative_confirmation: string | null;
  positive_button: string | null;
  positive_button_ui_flags: number;
  positive_confirmation: string | null;
  type: string | null;
}

export interface SignTO {
  algorithm: string | null;
  caption: string | null;
  index: string | null;
  key_name: string | null;
  payload: string | null;
}

export interface SignWidgetResultTO {
  public_key: PublicKeyTO | null;
  payload_signature: string | null;
  total_signature: string | null;
}

export interface SingleSelectComponentTO {
  choices: ValueTO[];
  validators: FormValidatorTO[];
  description: string | null;
  id: string | null;
  sensitive: boolean;
  title: string | null;
  readonly type: FormComponentType.SINGLE_SELECT;
}

export interface SingleSelectComponentValueTO {
  value: string | null;
  id: string | null;
  readonly type: FormComponentType.SINGLE_SELECT;
}

export interface SingleSelectFormMessageTO {
  attachments: AttachmentTO[];
  form: SingleSelectFormTO | null;
  member: MemberStatusTO | null;
  alert_flags: number;
  branding: string | null;
  context: string | null;
  default_priority: number;
  default_sticky: boolean;
  flags: number;
  key: string | null;
  message: string | null;
  message_type: number;
  parent_key: string | null;
  priority: number;
  sender: string | null;
  threadTimestamp: number;
  thread_avatar_hash: string | null;
  thread_background_color: string | null;
  thread_size: number;
  thread_text_color: string | null;
  timestamp: number;
}

export interface SingleSelectFormTO {
  widget: SingleSelectTO | null;
  javascript_validation: string | null;
  negative_button: string | null;
  negative_button_ui_flags: number;
  negative_confirmation: string | null;
  positive_button: string | null;
  positive_button_ui_flags: number;
  positive_confirmation: string | null;
  type: string | null;
}

export interface SingleSelectTO {
  choices: ChoiceTO[];
  value: string | null;
}

export interface SingleSliderFormMessageTO {
  attachments: AttachmentTO[];
  form: SingleSliderFormTO | null;
  member: MemberStatusTO | null;
  alert_flags: number;
  branding: string | null;
  context: string | null;
  default_priority: number;
  default_sticky: boolean;
  flags: number;
  key: string | null;
  message: string | null;
  message_type: number;
  parent_key: string | null;
  priority: number;
  sender: string | null;
  threadTimestamp: number;
  thread_avatar_hash: string | null;
  thread_background_color: string | null;
  thread_size: number;
  thread_text_color: string | null;
  timestamp: number;
}

export interface SingleSliderFormTO {
  widget: SingleSliderTO | null;
  javascript_validation: string | null;
  negative_button: string | null;
  negative_button_ui_flags: number;
  negative_confirmation: string | null;
  positive_button: string | null;
  positive_button_ui_flags: number;
  positive_confirmation: string | null;
  type: string | null;
}

export interface SingleSliderTO {
  max: number;
  min: number;
  precision: number;
  step: number;
  unit: string | null;
  value: number;
}

export interface SizeTO {
  height: number;
  width: number;
}

export interface StartChatRequestTO {
  avatar: string | null;
  emails: string[];
  key: string | null;
  topic: string | null;
}

export interface StartChatResponseTO {
  key: string | null;
  timestamp: number;
}

export interface StartFlowRequestTO {
  attachments_to_dwnl: string[];
  brandings_to_dwnl: string[];
  flow_params: string | null;
  message_flow_run_id: string | null;
  parent_message_key: string | null;
  service: string | null;
  static_flow: string | null;
  static_flow_hash: string | null;
}

export interface StartFlowResponseTO {
}

export interface StartServiceActionRequestTO {
  action: string | null;
  context: string | null;
  email: string | null;
  message_flow_run_id: string | null;
  static_flow_hash: string | null;
  timestamp: number;
}

export interface StartServiceActionResponseTO {
}

export interface SubmitAdvancedOrderFormRequestTO {
  result: AdvancedOrderWidgetResultTO | null;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  timestamp: number;
}

export interface SubmitAdvancedOrderFormResponseTO {
  result: number;
}

export interface SubmitAutoCompleteFormRequestTO {
  result: UnicodeWidgetResultTO | null;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  timestamp: number;
}

export interface SubmitAutoCompleteFormResponseTO {
  result: number;
}

export interface SubmitDateSelectFormRequestTO {
  result: LongWidgetResultTO | null;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  timestamp: number;
}

export interface SubmitDateSelectFormResponseTO {
  result: number;
}

export interface SubmitDynamicFormRequestTO {
  sections: FormSectionValueTO[];
  id: number;
  test: boolean;
  version: number;
}

export interface SubmitDynamicFormResponseTO {
  errormsg: string | null;
  success: boolean;
}

export interface SubmitFriendSelectFormRequestTO {
  result: UnicodeListWidgetResultTO | null;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  timestamp: number;
}

export interface SubmitFriendSelectFormResponseTO {
  result: number;
}

export interface SubmitGPSLocationFormRequestTO {
  result: LocationWidgetResultTO | null;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  timestamp: number;
}

export interface SubmitGPSLocationFormResponseTO {
  result: number;
}

export interface SubmitMultiSelectFormRequestTO {
  result: UnicodeListWidgetResultTO | null;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  timestamp: number;
}

export interface SubmitMultiSelectFormResponseTO {
  result: number;
}

export interface SubmitMyDigiPassFormRequestTO {
  result: MyDigiPassWidgetResultTO | null;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  timestamp: number;
}

export interface SubmitMyDigiPassFormResponseTO {
  result: number;
}

export interface SubmitOauthFormRequestTO {
  result: UnicodeWidgetResultTO | null;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  timestamp: number;
}

export interface SubmitOauthFormResponseTO {
  result: number;
}

export interface SubmitOpenIdFormRequestTO {
  result: OpenIdWidgetResultTO | null;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  timestamp: number;
}

export interface SubmitOpenIdFormResponseTO {
  result: WidgetResult | null;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  timestamp: number;
}

export interface SubmitPayFormRequestTO {
  result: PayWidgetResultTO | null;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  timestamp: number;
}

export interface SubmitPayFormResponseTO {
  result: number;
}

export interface SubmitPhotoUploadFormRequestTO {
  result: UnicodeWidgetResultTO | null;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  timestamp: number;
}

export interface SubmitPhotoUploadFormResponseTO {
  result: number;
}

export interface SubmitRangeSliderFormRequestTO {
  result: FloatListWidgetResultTO | null;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  timestamp: number;
}

export interface SubmitRangeSliderFormResponseTO {
  result: number;
}

export interface SubmitSignFormRequestTO {
  result: SignWidgetResultTO | null;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  timestamp: number;
}

export interface SubmitSignFormResponseTO {
  result: number;
}

export interface SubmitSingleSelectFormRequestTO {
  result: UnicodeWidgetResultTO | null;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  timestamp: number;
}

export interface SubmitSingleSelectFormResponseTO {
  result: number;
}

export interface SubmitSingleSliderFormRequestTO {
  result: FloatWidgetResultTO | null;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  timestamp: number;
}

export interface SubmitSingleSliderFormResponseTO {
  result: number;
}

export interface SubmitTextBlockFormRequestTO {
  result: UnicodeWidgetResultTO | null;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  timestamp: number;
}

export interface SubmitTextBlockFormResponseTO {
  result: number;
}

export interface SubmitTextLineFormRequestTO {
  result: UnicodeWidgetResultTO | null;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  timestamp: number;
}

export interface SubmitTextLineFormResponseTO {
  result: number;
}

export interface TargetInfoAssetTO {
  id: string | null;
  type: string | null;
}

export interface TargetInfoTO {
  assets: TargetInfoAssetTO[];
  name: string | null;
}

export interface TestFormRequestTO {
  id: number;
  version: number;
}

export interface TestFormResponseTO {
}

export interface TextAnnouncementTO {
  description: string | null;
  title: string | null;
  readonly type: MapAnnouncementType.TEXT;
}

export interface TextBlockFormMessageTO {
  attachments: AttachmentTO[];
  form: TextBlockFormTO | null;
  member: MemberStatusTO | null;
  alert_flags: number;
  branding: string | null;
  context: string | null;
  default_priority: number;
  default_sticky: boolean;
  flags: number;
  key: string | null;
  message: string | null;
  message_type: number;
  parent_key: string | null;
  priority: number;
  sender: string | null;
  threadTimestamp: number;
  thread_avatar_hash: string | null;
  thread_background_color: string | null;
  thread_size: number;
  thread_text_color: string | null;
  timestamp: number;
}

export interface TextBlockFormTO {
  widget: TextBlockTO | null;
  javascript_validation: string | null;
  negative_button: string | null;
  negative_button_ui_flags: number;
  negative_confirmation: string | null;
  positive_button: string | null;
  positive_button_ui_flags: number;
  positive_confirmation: string | null;
  type: string | null;
}

export interface TextBlockTO {
  keyboard_type: string | null;
  max_chars: number;
  place_holder: string | null;
  value: string | null;
}

export interface TextInputComponentTO {
  validators: FormValidatorTO[];
  description: string | null;
  id: string | null;
  keyboard_type: string | null;
  multiline: boolean;
  placeholder: string | null;
  sensitive: boolean;
  title: string | null;
  readonly type: FormComponentType.TEXT_INPUT;
}

export interface TextInputComponentValueTO {
  value: string | null;
  id: string | null;
  readonly type: FormComponentType.TEXT_INPUT;
}

export interface TextLineFormMessageTO {
  attachments: AttachmentTO[];
  form: TextLineFormTO | null;
  member: MemberStatusTO | null;
  alert_flags: number;
  branding: string | null;
  context: string | null;
  default_priority: number;
  default_sticky: boolean;
  flags: number;
  key: string | null;
  message: string | null;
  message_type: number;
  parent_key: string | null;
  priority: number;
  sender: string | null;
  threadTimestamp: number;
  thread_avatar_hash: string | null;
  thread_background_color: string | null;
  thread_size: number;
  thread_text_color: string | null;
  timestamp: number;
}

export interface TextLineFormTO {
  widget: TextLineTO | null;
  javascript_validation: string | null;
  negative_button: string | null;
  negative_button_ui_flags: number;
  negative_confirmation: string | null;
  positive_button: string | null;
  positive_button_ui_flags: number;
  positive_confirmation: string | null;
  type: string | null;
}

export interface TextLineTO {
  keyboard_type: string | null;
  max_chars: number;
  place_holder: string | null;
  value: string | null;
}

export interface TextSectionTO {
  description: string | null;
  title: string | null;
  readonly type: MapSectionType.TEXT;
}

export interface Thumbnail {
  height: number;
  url: string | null;
  width: number;
}

export interface ToggleListSectionItemTO {
  filled: boolean;
  id: string | null;
  state: string | null;
  icon: string | null;
  icon_color: string | null;
  title: string | null;
  readonly type: MapListSectionItemType.TOGGLE;
}

export interface ToggleMapItemRequestTO {
  item_id: string | null;
  state: string | null;
  tag: string | null;
  toggle_id: string | null;
}

export interface ToggleMapItemResponseTO {
  toggle_item: ToggleListSectionItemTO | null;
  item_id: string | null;
}

export interface TransferCompletedRequestTO {
  message_key: string | null;
  parent_message_key: string | null;
  result_url: string | null;
}

export interface TransferCompletedResponseTO {
}

export interface UnicodeListWidgetResultTO {
  values: string[];
}

export interface UnicodeWidgetResultTO {
  value: string | null;
}

export interface UnregisterMobileRequestTO {
  reason: string | null;
}

export interface UnregisterMobileResponseTO {
}

export interface UpdateAdvancedOrderFormRequestTO {
  result: AdvancedOrderWidgetResultTO | null;
  acked_timestamp: number;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  received_timestamp: number;
  status: number;
}

export interface UpdateAdvancedOrderFormResponseTO {
}

export interface UpdateAppAssetRequestTO {
  kind: string | null;
  scale_x: number;
  url: string | null;
}

export interface UpdateAppAssetResponseTO {
}

export interface UpdateApplePushDeviceTokenRequestTO {
  token: string | null;
}

export interface UpdateApplePushDeviceTokenResponseTO {
}

export interface UpdateAutoCompleteFormRequestTO {
  result: UnicodeWidgetResultTO | null;
  acked_timestamp: number;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  received_timestamp: number;
  status: number;
}

export interface UpdateAutoCompleteFormResponseTO {
}

export interface UpdateBadgeCountRequestTO {
  badge_count: number;
  group_id: string | null;
  group_type: string | null;
}

export interface UpdateBadgeCountResponseTO {
}

export interface UpdateChatRequestTO {
  avatar: string | null;
  parent_message_key: string | null;
  topic: string | null;
}

export interface UpdateChatResponseTO {
}

export interface UpdateDateSelectFormRequestTO {
  result: LongWidgetResultTO | null;
  acked_timestamp: number;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  received_timestamp: number;
  status: number;
}

export interface UpdateDateSelectFormResponseTO {
}

export interface UpdateEmbeddedAppRequestTO {
  description: string | null;
  name: string | null;
  serving_url: string | null;
  title: string | null;
  types: string[];
  url_regexes: string[];
  version: number;
}

export interface UpdateEmbeddedAppResponseTO {
}

export interface UpdateEmbeddedAppsRequestTO {
  embedded_apps: EmbeddedAppTO[];
}

export interface UpdateEmbeddedAppsResponseTO {
}

export interface UpdateFriendRequestTO {
  friend: FriendTO | null;
  generation: number;
  status: number;
}

export interface UpdateFriendResponseTO {
  reason: string | null;
  updated: boolean;
}

export interface UpdateFriendSelectFormRequestTO {
  result: UnicodeListWidgetResultTO | null;
  acked_timestamp: number;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  received_timestamp: number;
  status: number;
}

export interface UpdateFriendSelectFormResponseTO {
}

export interface UpdateFriendSetRequestTO {
  added_friend: FriendTO | null;
  friends: string[];
  version: number;
}

export interface UpdateFriendSetResponseTO {
  reason: string | null;
  updated: boolean;
}

export interface UpdateGPSLocationFormRequestTO {
  result: LocationWidgetResultTO | null;
  acked_timestamp: number;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  received_timestamp: number;
  status: number;
}

export interface UpdateGPSLocationFormResponseTO {
}

export interface UpdateGroupsRequestTO {
}

export interface UpdateGroupsResponseTO {
}

export interface UpdateJSEmbeddingRequestTO {
  items: JSEmbeddingItemTO[];
}

export interface UpdateJSEmbeddingResponseTO {
}

export interface UpdateMessageEmbeddedAppRequestTO {
  embedded_app: MessageEmbeddedAppTO | null;
  message_key: string | null;
  parent_message_key: string | null;
}

export interface UpdateMessageEmbeddedAppResponseTO {
  embedded_app: MessageEmbeddedAppTO | null;
  message_key: string | null;
  parent_message_key: string | null;
}

export interface UpdateMessageRequestTO {
  embedded_app: MessageEmbeddedAppTO | null;
  existence: number;
  flags: number;
  has_existence: boolean;
  has_flags: boolean;
  last_child_message: string | null;
  message: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  thread_avatar_hash: string | null;
  thread_background_color: string | null;
  thread_text_color: string | null;
}

export interface UpdateMessageResponseTO {
}

export interface UpdateMultiSelectFormRequestTO {
  result: UnicodeListWidgetResultTO | null;
  acked_timestamp: number;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  received_timestamp: number;
  status: number;
}

export interface UpdateMultiSelectFormResponseTO {
}

export interface UpdateMyDigiPassFormRequestTO {
  result: MyDigiPassWidgetResultTO | null;
  acked_timestamp: number;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  received_timestamp: number;
  status: number;
}

export interface UpdateMyDigiPassFormResponseTO {
}

export interface UpdateOauthFormRequestTO {
  result: UnicodeWidgetResultTO | null;
  acked_timestamp: number;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  received_timestamp: number;
  status: number;
}

export interface UpdateOauthFormResponseTO {
}

export interface UpdateOpenIdFormRequestTO {
  result: OpenIdWidgetResultTO | null;
  acked_timestamp: number;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  received_timestamp: number;
  status: number;
}

export interface UpdateOpenIdFormResponseTO {
}

export interface UpdatePayFormRequestTO {
  result: PayWidgetResultTO | null;
  acked_timestamp: number;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  received_timestamp: number;
  status: number;
}

export interface UpdatePayFormResponseTO {
}

export interface UpdatePaymentAssetRequestTO {
  available_balance: PaymentAssetBalanceTO | null;
  required_action: PaymentAssetRequiredActionTO | null;
  total_balance: PaymentAssetBalanceTO | null;
  currency: string | null;
  enabled: boolean;
  has_balance: boolean;
  has_transactions: boolean;
  id: string | null;
  name: string | null;
  provider_id: string | null;
  type: string | null;
  verified: boolean;
}

export interface UpdatePaymentAssetResponseTO {
}

export interface UpdatePaymentAssetsRequestTO {
  assets: PaymentProviderAssetTO[];
  provider_ids: string[];
}

export interface UpdatePaymentAssetsResponseTO {
}

export interface UpdatePaymentProviderRequestTO {
  asset_types: string[];
  background_color: string | null;
  black_white_logo: string | null;
  button_color: string | null;
  currencies: string[];
  description: string | null;
  embedded_app_id: string | null;
  enabled: boolean;
  id: string | null;
  logo_url: string | null;
  name: string | null;
  oauth_authorize_url: string | null;
  text_color: string | null;
  version: number;
}

export interface UpdatePaymentProviderResponseTO {
}

export interface UpdatePaymentProvidersRequestTO {
  payment_providers: AppPaymentProviderTO[];
  provider_ids: string[];
}

export interface UpdatePaymentProvidersResponseTO {
}

export interface UpdatePaymentStatusRequestTO {
  status: string | null;
  transaction_id: string | null;
}

export interface UpdatePaymentStatusResponseTO {
}

export interface UpdatePhotoUploadFormRequestTO {
  result: UnicodeWidgetResultTO | null;
  acked_timestamp: number;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  received_timestamp: number;
  status: number;
}

export interface UpdatePhotoUploadFormResponseTO {
}

export interface UpdateProfileAddressRequestTO {
  geo_location: GeoPointTO | null;
  bus_nr: string | null;
  city: string | null;
  distance: number;
  house_nr: string | null;
  label: string | null;
  street_name: string | null;
  type: number;
  uid: string | null;
  zip_code: string | null;
}

export interface UpdateProfileAddressResponseTO {
  geo_location: GeoPointTO | null;
  bus_nr: string | null;
  city: string | null;
  distance: number;
  house_nr: string | null;
  label: string | null;
  street_name: string | null;
  type: number;
  uid: string | null;
  zip_code: string | null;
}

export interface UpdateProfilePhoneNumberRequestTO {
  label: string | null;
  number: string | null;
  type: number;
  uid: string | null;
}

export interface UpdateProfilePhoneNumberResponseTO {
  label: string | null;
  number: string | null;
  type: number;
  uid: string | null;
}

export interface UpdateRangeSliderFormRequestTO {
  result: FloatListWidgetResultTO | null;
  acked_timestamp: number;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  received_timestamp: number;
  status: number;
}

export interface UpdateRangeSliderFormResponseTO {
}

export interface UpdateSettingsRequestTO {
  settings: SettingsTO | null;
}

export interface UpdateSettingsResponseTO {
}

export interface UpdateSignFormRequestTO {
  result: SignWidgetResultTO | null;
  acked_timestamp: number;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  received_timestamp: number;
  status: number;
}

export interface UpdateSignFormResponseTO {
}

export interface UpdateSingleSelectFormRequestTO {
  result: UnicodeWidgetResultTO | null;
  acked_timestamp: number;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  received_timestamp: number;
  status: number;
}

export interface UpdateSingleSelectFormResponseTO {
}

export interface UpdateSingleSliderFormRequestTO {
  result: FloatWidgetResultTO | null;
  acked_timestamp: number;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  received_timestamp: number;
  status: number;
}

export interface UpdateSingleSliderFormResponseTO {
}

export interface UpdateTextBlockFormRequestTO {
  result: UnicodeWidgetResultTO | null;
  acked_timestamp: number;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  received_timestamp: number;
  status: number;
}

export interface UpdateTextBlockFormResponseTO {
}

export interface UpdateTextLineFormRequestTO {
  result: UnicodeWidgetResultTO | null;
  acked_timestamp: number;
  button_id: string | null;
  message_key: string | null;
  parent_message_key: string | null;
  received_timestamp: number;
  status: number;
}

export interface UpdateTextLineFormResponseTO {
}

export interface UpdateUserDataRequestTO {
  app_data: string | null;
  data: string | null;
  keys: string[];
  service: string | null;
  type: string | null;
  user_data: string | null;
  values: string[];
}

export interface UpdateUserDataResponseTO {
}

export interface UploadChunkRequestTO {
  chunk: string | null;
  content_type: string | null;
  message_key: string | null;
  number: number;
  parent_message_key: string | null;
  photo_hash: string | null;
  service_identity_user: string | null;
  total_chunks: number;
}

export interface UploadChunkResponseTO {
}

export interface UserDetailsTO {
  app_id: string | null;
  avatar_url: string | null;
  email: string | null;
  language: string | null;
  name: string | null;
}

export interface UserScannedRequestTO {
  app_id: string | null;
  email: string | null;
  service_email: string | null;
}

export interface UserScannedResponseTO {
}

export interface ValueTO {
  next_action: NextActionTO | null;
  image_url: string | null;
  label: string | null;
  value: string | null;
}

export interface VerifyPaymentAssetRequestTO {
  asset_id: string | null;
  code: string | null;
  provider_id: string | null;
}

export interface VerifyPaymentAssetResponseTO {
  error: ErrorPaymentTO | null;
  success: boolean;
}

export interface VoteSectionTO {
  options: MapVoteOptionTO[];
  id: string | null;
  readonly type: MapSectionType.VOTE;
}

export interface WeekDayTextTO {
  lines: MapItemLineTextPartTO[];
  day: string | null;
}

export interface Widget {
}

export interface WidgetResult {
}

export interface ZipCodeTO {
  name: string | null;
  zip_code: string | null;
}
