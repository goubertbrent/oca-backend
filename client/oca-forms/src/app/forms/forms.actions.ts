import { HttpErrorResponse } from '@angular/common/http';
import { Action } from '@ngrx/store';
import { FormSettings, FormStatistics, OcaForm, SaveForm } from '../interfaces/forms.interfaces';
import { UserDetailsTO } from '../users/interfaces';

export const enum FormsActionTypes {
  GET_FORMS = '[forms] Get forms',
  GET_FORMS_COMPLETE = '[forms] Get forms complete',
  GET_FORMS_FAILED = '[forms] Get forms failed',
  GET_FORM = '[forms] Get form',
  GET_FORM_COMPLETE = '[forms] Get form complete',
  GET_FORM_FAILED = '[forms] Get form failed',
  GET_FORM_STATISTICS = '[forms] Get form statistics',
  GET_FORM_STATISTICS_COMPLETE = '[forms] Get form statistics complete',
  GET_FORM_STATISTICS_FAILED = '[forms] Get form statistics failed',
  SAVE_FORM = '[forms] Save form',
  SAVE_FORM_COMPLETE = '[forms] Save form complete',
  SAVE_FORM_FAILED = '[forms] Save form failed',
  CREATE_FORM = '[forms] Create form',
  CREATE_FORM_COMPLETE = '[forms] Create form complete',
  CREATE_FORM_FAILED = '[forms] Create form failed',
  GET_TOMBOLA_WINNERS = '[forms] Get tombola winners',
  GET_TOMBOLA_WINNERS_COMPLETE = '[forms] Get tombola winners complete',
  GET_TOMBOLA_WINNERS_FAILED = '[forms] Get tombola winners failed',
  TEST_FORM = '[forms] Test form',
  TEST_FORM_COMPLETE = '[forms] Test form complete',
  TEST_FORM_FAILED = '[forms] Test form failed',
  SHOW_DELETE_ALL_RESPONSES = '[forms] Show delete all responses',
  SHOW_DELETE_ALL_RESPONSES_CANCELED = '[forms] Show delete all responses canceled',
  DELETE_ALL_RESPONSES = '[forms] Delete all responses',
  DELETE_ALL_RESPONSES_COMPLETE = '[forms] Delete all responses complete',
  DELETE_ALL_RESPONSES_FAILED = '[forms] Delete all responses failed',
  DELETE_FORM = '[forms] Delete form',
  DELETE_FORM_COMPLETE = '[forms] Delete form complete',
  DELETE_FORM_FAILED = '[forms] Delete form failed',
}

export class GetFormsAction implements Action {
  readonly type = FormsActionTypes.GET_FORMS;
}

export class GetFormsCompleteAction implements Action {
  readonly type = FormsActionTypes.GET_FORMS_COMPLETE;

  constructor(public forms: FormSettings[]) {
  }
}

export class GetFormsFailedAction implements Action {
  readonly type = FormsActionTypes.GET_FORMS_FAILED;

  constructor(public error: HttpErrorResponse) {
  }
}

export class GetFormAction implements Action {
  readonly type = FormsActionTypes.GET_FORM;

  constructor(public id: number) {
  }
}

export class GetFormCompleteAction implements Action {
  readonly type = FormsActionTypes.GET_FORM_COMPLETE;

  constructor(public form: OcaForm) {
  }
}

export class GetFormFailedAction implements Action {
  readonly type = FormsActionTypes.GET_FORM_FAILED;

  constructor(public error: HttpErrorResponse) {
  }
}

export class GetFormStatisticsAction implements Action {
  readonly type = FormsActionTypes.GET_FORM_STATISTICS;

  constructor(public id: number) {
  }
}

export class GetFormStatisticsCompleteAction implements Action {
  readonly type = FormsActionTypes.GET_FORM_STATISTICS_COMPLETE;

  constructor(public stats: FormStatistics) {
  }
}

export class GetFormStatisticsFailedAction implements Action {
  readonly type = FormsActionTypes.GET_FORM_STATISTICS_FAILED;

  constructor(public error: HttpErrorResponse) {
  }
}

export class SaveFormAction implements Action {
  readonly type = FormsActionTypes.SAVE_FORM;

  constructor(public payload: SaveForm) {
  }
}

export class SaveFormCompleteAction implements Action {
  readonly type = FormsActionTypes.SAVE_FORM_COMPLETE;

  constructor(public form: OcaForm) {
  }
}

export class SaveFormFailedAction implements Action {
  readonly type = FormsActionTypes.SAVE_FORM_FAILED;

  constructor(public error: HttpErrorResponse) {
  }
}

export class CreateFormAction implements Action {
  readonly type = FormsActionTypes.CREATE_FORM;
}

export class CreateFormCompleteAction implements Action {
  readonly type = FormsActionTypes.CREATE_FORM_COMPLETE;

  constructor(public form: OcaForm) {
  }
}

export class CreateFormFailedAction implements Action {
  readonly type = FormsActionTypes.CREATE_FORM_FAILED;

  constructor(public error: HttpErrorResponse) {
  }
}

export class DeleteFormAction implements Action {
  readonly type = FormsActionTypes.DELETE_FORM;

  constructor(public form: FormSettings) {
  }
}

export class DeleteFormCompleteAction implements Action {
  readonly type = FormsActionTypes.DELETE_FORM_COMPLETE;

  constructor(public form: FormSettings) {
  }
}

export class DeleteFormFailedAction implements Action {
  readonly type = FormsActionTypes.DELETE_FORM_FAILED;

  constructor(public error: HttpErrorResponse) {
  }
}

export class GetTombolaWinnersAction implements Action {
  readonly type = FormsActionTypes.GET_TOMBOLA_WINNERS;

  constructor(public formId: number) {
  }
}

export class GetTombolaWinnersCompleteAction implements Action {
  readonly type = FormsActionTypes.GET_TOMBOLA_WINNERS_COMPLETE;

  constructor(public payload: UserDetailsTO[]) {
  }
}

export class GetTombolaWinnersFailedAction implements Action {
  readonly type = FormsActionTypes.GET_TOMBOLA_WINNERS_FAILED;

  constructor(public error: HttpErrorResponse) {
  }
}

export class TestFormAction implements Action {
  readonly type = FormsActionTypes.TEST_FORM;

  constructor(public formId: number, public testers: string[]) {
  }
}

export class TestFormCompleteAction implements Action {
  readonly type = FormsActionTypes.TEST_FORM_COMPLETE;
}

export class TestFormFailedAction implements Action {
  readonly type = FormsActionTypes.TEST_FORM_FAILED;

  constructor(public error: HttpErrorResponse) {
  }
}

export class ShowDeleteAllResponsesAction implements Action {
  readonly type = FormsActionTypes.SHOW_DELETE_ALL_RESPONSES;

  constructor(public formId: number, public message: string) {
  }
}

export class ShowDeleteAllResponsesCanceledAction implements Action {
  readonly type = FormsActionTypes.SHOW_DELETE_ALL_RESPONSES_CANCELED;
}

export class DeleteAllResponsesAction implements Action {
  readonly type = FormsActionTypes.DELETE_ALL_RESPONSES;

  constructor(public formId: number) {
  }
}

export class DeleteAllResponsesCompleteAction implements Action {
  readonly type = FormsActionTypes.DELETE_ALL_RESPONSES_COMPLETE;
}

export class DeleteAllResponsesFailedAction implements Action {
  readonly type = FormsActionTypes.DELETE_ALL_RESPONSES_FAILED;

  constructor(public error: HttpErrorResponse) {
  }
}


export type FormsActions =
  GetFormsAction
  | GetFormsCompleteAction
  | GetFormsFailedAction
  | GetFormAction
  | GetFormCompleteAction
  | GetFormFailedAction
  | GetFormStatisticsAction
  | GetFormStatisticsCompleteAction
  | GetFormStatisticsFailedAction
  | SaveFormAction
  | SaveFormCompleteAction
  | SaveFormFailedAction
  | CreateFormAction
  | CreateFormCompleteAction
  | CreateFormFailedAction
  | DeleteFormAction
  | DeleteFormCompleteAction
  | DeleteFormFailedAction
  | GetTombolaWinnersAction
  | GetTombolaWinnersCompleteAction
  | GetTombolaWinnersFailedAction
  | TestFormAction
  | TestFormCompleteAction
  | TestFormFailedAction
  | ShowDeleteAllResponsesAction
  | ShowDeleteAllResponsesCanceledAction
  | DeleteAllResponsesAction
  | DeleteAllResponsesCompleteAction
  | DeleteAllResponsesFailedAction;
