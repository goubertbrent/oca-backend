import { Action } from '@ngrx/store';
import {
  GetUserInformationResult,
  HoplrFeed,
  LookupNeighbourhoodRequest,
  LookupNeighbourhoodResult,
  RegisterUserRequest,
  UserInformation,
} from './hoplr';


export const enum HoplrActionTypes {
  LOOKUP_NEIGHBOURHOOD = '[Hoplr] Lookup neighbourhood',
  LOOKUP_NEIGHBOURHOOD_SUCCESS = '[Hoplr] Lookup neighbourhood success',
  LOOKUP_NEIGHBOURHOOD_FAILED = '[Hoplr] Lookup neighbourhood failed',
  GET_USER_INFORMATION = '[Hoplr] Get user information',
  GET_USER_INFORMATION_SUCCESS = '[Hoplr] Get user information success',
  GET_USER_INFORMATION_FAILED = '[Hoplr] Get user information failed',
  REGISTER = '[Hoplr] Register',
  REGISTER_SUCCESS = '[Hoplr] Register success',
  REGISTER_FAILED = '[Hoplr] Register failed',
  LOGIN = '[Hoplr] Login',
  LOGIN_SUCCESS = '[Hoplr] Login success',
  LOGIN_FAILED = '[Hoplr] Login failed',
  LOGOUT = '[Hoplr] Logout',
  LOGOUT_SUCCESS = '[Hoplr] Logout success',
  LOGOUT_FAILED = '[Hoplr] Logout failed',
  GET_FEED = '[Hoplr] Get feed',
  GET_FEED_SUCCESS = '[Hoplr] Get feed success',
  GET_FEED_FAILED = '[Hoplr] Get feed failed',
}

export class LookupNeighbourhoodAction implements Action {
  readonly type = HoplrActionTypes.LOOKUP_NEIGHBOURHOOD;

  constructor(public payload: LookupNeighbourhoodRequest) {
  }
}

export class LookupNeighbourhoodSuccessAction implements Action {
  readonly type = HoplrActionTypes.LOOKUP_NEIGHBOURHOOD_SUCCESS;

  constructor(public payload: LookupNeighbourhoodResult) {
  }
}

export class LookupNeighbourhoodFailedAction implements Action {
  readonly type = HoplrActionTypes.LOOKUP_NEIGHBOURHOOD_FAILED;

  constructor(public error: string) {
  }
}

export class GetUserInformationAction implements Action {
  readonly type = HoplrActionTypes.GET_USER_INFORMATION;
}

export class GetUserInformationSuccessAction implements Action {
  readonly type = HoplrActionTypes.GET_USER_INFORMATION_SUCCESS;

  constructor(public payload: GetUserInformationResult) {
  }
}

export class GetUserInformationFailedAction implements Action {
  readonly type = HoplrActionTypes.GET_USER_INFORMATION_FAILED;

  constructor(public error: string) {
  }
}

export class RegisterAction implements Action {
  readonly type = HoplrActionTypes.REGISTER;

  constructor(public payload: { info: RegisterUserRequest }) {
  }
}

export class RegisterSuccessAction implements Action {
  readonly type = HoplrActionTypes.REGISTER_SUCCESS;

  constructor(public payload: GetUserInformationResult) {
  }
}

export class RegisterFailedAction implements Action {
  readonly type = HoplrActionTypes.REGISTER_FAILED;

  constructor(public error: string) {
  }
}

export class LoginAction implements Action {
  readonly type = HoplrActionTypes.LOGIN;

  constructor(public payload: { username: string; password: string; }) {
  }
}

export class LoginSuccessAction implements Action {
  readonly type = HoplrActionTypes.LOGIN_SUCCESS;

  constructor(public payload: GetUserInformationResult) {
  }
}

export class LoginFailedAction implements Action {
  readonly type = HoplrActionTypes.LOGIN_FAILED;

  constructor(public error: string) {
  }
}

export class LogoutAction implements Action {
  readonly type = HoplrActionTypes.LOGOUT;
}

export class LogoutSuccessAction implements Action {
  readonly type = HoplrActionTypes.LOGOUT_SUCCESS;
}

export class LogoutFailedAction implements Action {
  readonly type = HoplrActionTypes.LOGOUT_FAILED;

  constructor(public error: string) {
  }
}

export class GetFeedAction implements Action {
  readonly type = HoplrActionTypes.GET_FEED;

  constructor(public payload: { page?: number }) {
  }
}

export class GetFeedSuccessAction implements Action {
  readonly type = HoplrActionTypes.GET_FEED_SUCCESS;

  constructor(public payload: HoplrFeed) {
  }
}

export class GetFeedFailedAction implements Action {
  readonly type = HoplrActionTypes.GET_FEED_FAILED;

  constructor(public error: string) {
  }
}


export type HoplrActions =
  LookupNeighbourhoodAction
  | LookupNeighbourhoodSuccessAction
  | LookupNeighbourhoodFailedAction
  | GetUserInformationAction
  | GetUserInformationSuccessAction
  | GetUserInformationFailedAction
  | RegisterAction
  | RegisterSuccessAction
  | RegisterFailedAction
  | LoginAction
  | LoginSuccessAction
  | LoginFailedAction
  | LogoutAction
  | LogoutSuccessAction
  | LogoutFailedAction
  | GetFeedAction
  | GetFeedSuccessAction
  | GetFeedFailedAction;
