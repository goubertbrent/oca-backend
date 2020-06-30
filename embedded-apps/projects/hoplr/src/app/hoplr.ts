export interface RegisterUserRequest {
  Username: string; // email address
  Password: string;
  Firstname: string;
  LastName: string;
  NeighbourhoodId: number;
  Street: string;
  StreetNumber: string;
  Address: string;
  CityName: string;
  Longitude: number;
  Latitude: number;
  Code: string | null;
}

export interface BaseNeighbourhood {
  Id: number;
  Title: string;
  NeighbourhoodType: number;
}

export interface Neighbourhood extends BaseNeighbourhood {
  PolygonEncoded: string;
  Place: {
    Id: number;
    Name: string;
    CityId: number;
    CityName: string;
    RegionId: number;
    RegionName: string;
    CountryId: number;
    CountryName: string;
  }
}

export interface LookupNeighbourhoodRequest {
  cityName: string;
  streetName: string;
  streetNumber: string;
  invitationCode: string;
}

export interface NeighbourhoodLocation {
  lat: number;
  lon: number;
  fullAddress: string;
}

export interface LookUpResultSuccess {
  success: true;
  neighbourhood: Neighbourhood;
}

export interface LookUpResultError {
  success: false;
  message: string;
}

export interface LookupNeighbourhoodResult {
  location: NeighbourhoodLocation;
  result: LookUpResultSuccess | LookUpResultError;
}

export interface GetUserInformationResult {
  registered: boolean;
  info: UserInformation | null;
}

export interface UserInformation {
  user: {
    Id: number;
    FirstName: string;
    LastName: string;
    ProfileName: string;
  };
  neighbourhood: BaseNeighbourhood;
}

export interface HoplrCategory {
  Id: number;
  Name: string;
  Title: string;
}

export interface HoplrImage {
  Id: number;
  ImageUrl: string;
  ImageWidth: number;
  ImageHeight: number;
}

export interface HoplrMessageImage {
  Id: number;
  ImageUrl: string;
  ThumbUrl: string;
  IconUrl: string;
}

export interface HoplrComment {
  Id: number;
  Comment: string;
  IsHidden?: boolean;
  DateTime: string;
  UserId: number;
  NeighbourhoodId: number;
  User: HoplrUser;
  BusinessId: number | null;
  Business: HoplrBusiness | null;
}

export interface HoplrBusiness {
  BusinessId: number;
  Title: string;
  ThumbUrl: string;
}

export interface HoplrProject {
  // properties unknown
}

export interface HoplrUser {
  Id?: number;
  UserId?: number;
  FirstName?: string | null;
  LastName?: string | null;
  ProfileName: string;
  ProfileNameUrl?: string;
  IconUrl?: string;
  ThumbUrl: string;
  Street?: string;
  Profile?: {
    FunctionTitle: string | null;
    FunctionDescription: string | null;
    FunctionIcon: string | null;
    FunctionColor: string | null;
  }
}

export const enum HoplrRateType {
  EMOTE,
  UNKNOWN,
  UPVOTE,
  DOWNVOTE,
  PERCEPTION,
  POLL_ANSWER,
}

export const enum HoplrEmoticonType {
  Nice,
  Thanks,
  Wow,
  Haha,
  Sad,
  Wave
}

export interface BaseHoplrRate {
  Id: number;
  EmoticonType: HoplrEmoticonType;
  NeighbourhoodId?: number;
  UserId: number;
  /**
   * Een rate kan mogelijks ook een CommentId bevatten, in dit geval is het geen like van het bericht, maar van een comment op dat bericht
   */
  CommentId: number | null;
  User: HoplrUser;
}

export interface HoplrRateEmote extends BaseHoplrRate {
  DateTime: string;
  readonly RateType: HoplrRateType.EMOTE;
}

export interface HoplrRatePerception extends BaseHoplrRate {
  readonly RateType: HoplrRateType.PERCEPTION;
  NeighbourhoodId?: number;
  OptionId: null;
  Value: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10;
}

export interface HoplrRateUpvote extends BaseHoplrRate {
  readonly RateType: HoplrRateType.UPVOTE;
  CommentId: null;
}

export interface HoplrRateDownvote extends BaseHoplrRate {
  readonly RateType: HoplrRateType.DOWNVOTE;
  CommentId: null;
}

export interface HoplrPollRate extends BaseHoplrRate {
  readonly RateType: HoplrRateType.POLL_ANSWER;
  Value: null;
  OptionId: number;
}

export type HoplrRate = HoplrRateEmote | HoplrRatePerception | HoplrRateUpvote | HoplrRateDownvote | HoplrPollRate;

export const enum HoplrMessageType {
  SHOUT = 'shout',
  MESSAGE = 'message',
  EVENT = 'event',
}

export const enum HoplrRsvpType {
  GOING,
  INTERESTED,
}

export interface HoplrRsvp {
  Id: number;
  UserId: number;
  User: HoplrUser;
  RsvpType: HoplrRsvpType;
  DateTime: string;
  NeighbourhoodId: number;
}

export interface BaseHoplrMessage {
  Id: number;
  Title: string;
  Text: string;
  Comments: HoplrComment[];
  Rates: HoplrRate[];
  Projects: HoplrProject[];
  CreatedAt: string;
  UpdatedAt: string;
  Category: HoplrCategory;
  CategoryId: number;
}

export interface HoplrShoutBusiness {
  Id: number;
  CreatedAt: string;
  BusinessId: number;
  Business: {
    Id: number;  // same as BusinessId
    Title: string
  };
  ShoutType: HoplrShoutType,
  PulledDate: null | string;
}

export interface HoplrShoutData extends BaseHoplrMessage {
  Rating: number;
  Category2Id: number | null;
  Category3Id: number | null;
  IsCommentsDisabled: boolean;
  IsPublic: boolean;
  NeighbourhoodId: number;
  IsDisabled: boolean;
  Neighbourhood: BaseNeighbourhood;
  Category2: HoplrCategory | null;
  Category3: HoplrCategory | null;
  User: HoplrUser;
  UserId: number;
  Images: HoplrImage[];
  Reports: unknown[];
  Attachments: HoplrAttachment[];
  Businesses: HoplrShoutBusiness[];
  ProjectId: null | number;
}

export interface HoplrShout {
  type: HoplrMessageType.SHOUT;
  data: HoplrShoutData
}

export interface MessageNeighbourhood {
  NeighbourhoodId: number;
  NeighbourhoodType?: number;
  Title: string;
  TitleUrl: string | null;
}

export const enum HoplrSurveyType {
  UNKNOWN = 0,
}

export interface HoplrSurvey {
  Id: number;
  Survey: {
    Id: number;
    Title: string;
    Description: string;
    Start: string;
    End: string;
    SurveyType: HoplrSurveyType;
    PublicCode: string;
    Sessions: unknown[];
  };
}

export interface HoplrPollOptions {
  Id: number;
  Text: string;
}

export interface HoplrAttachment {
  Id: number;
  ShoutId: 0;
  Filename: string;
  Url: string;
  CreatedAt: string;
}

export const enum HoplrShoutType {
  NORMAL = 0,
  UPVOTE_DOWNVOTE,
  PERCEPTION,
  POLL,
  SURVEY,
}

export interface HoplrMessageData extends BaseHoplrMessage {
  IsCommentsDisabled: boolean;
  IsNeighbourhoodSplitEnabled: boolean;
  MessageType: HoplrShoutType;
  PublicationType: 0;  // also no idea
  IsPoll: boolean;
  Business: HoplrBusiness;
  Neighbourhoods: MessageNeighbourhood[];
  Images: HoplrMessageImage[];
  Attachments: HoplrAttachment[];
  PollOptions: HoplrPollOptions[];
  User: HoplrUser;
  Streets: string[];
  Category2: HoplrCategory | null;
  Surveys: HoplrSurvey[];
  VideoUrl: string | null;
  EmbeddedVideoUrl: string | null;
}

export interface HoplrMessage {
  type: HoplrMessageType.MESSAGE;
  data: HoplrMessageData;
}

export interface HoplrEventData extends BaseHoplrMessage {
  Price: number;
  From: string;
  Until: string;
  Rating: number;
  Address: string;
  Latitude: string;
  Longitude: string;
  Category2Id: number | null;
  Category3Id: number | null;
  IsNeighbourhoodSplitEnabled: boolean;
  IsCityWide: boolean;
  PublicationType: 0;
  User: HoplrUser;
  Images: HoplrImage[];
  Business: HoplrBusiness | null;
  Neighbourhoods: MessageNeighbourhood[];
  Rsvps: HoplrRsvp[];
  SeedId: number | null;
  SeedOwnerId: number | null;
  SeedOwnerName: string | null;
  SeedProvider: unknown | null;
  SeedUrl: string | null;
}

export interface HoplrEvent {
  type: HoplrMessageType.EVENT;
  data: HoplrEventData;
}

export type HoplrFeedItem = HoplrShout | HoplrMessage | HoplrEvent;

export interface HoplrFeed {
  results: HoplrFeedItem[];
  mediaBaseUrl: string;
  baseUrl: string;
  page: number;
  more: boolean;
}
