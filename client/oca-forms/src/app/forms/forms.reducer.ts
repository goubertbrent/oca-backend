import { onLoadableError, onLoadableLoad, onLoadableSuccess } from '../interfaces/loadable';
import { FormsActions, FormsActionTypes } from './forms.actions';
import { FormsState, initialFormsState } from './forms.state';

export function formsReducer(state: FormsState = initialFormsState, action: FormsActions): FormsState {
  switch (action.type) {
    case FormsActionTypes.GET_FORMS:
      return { ...state, forms: onLoadableLoad(initialFormsState.forms.data) };
    case FormsActionTypes.GET_FORMS_COMPLETE:
      return { ...state, forms: onLoadableSuccess(action.forms) };
    case FormsActionTypes.GET_FORMS_FAILED:
      return { ...state, forms: onLoadableError(action.error) };
    case FormsActionTypes.GET_FORM:
      return { ...state, form: onLoadableLoad(initialFormsState.form.data), tombolaWinners: initialFormsState.tombolaWinners };
    case FormsActionTypes.GET_FORM_COMPLETE:
      return { ...state, form: onLoadableSuccess(action.form) };
    case FormsActionTypes.GET_FORM_FAILED:
      return { ...state, form: onLoadableError(action.error) };
    case FormsActionTypes.GET_FORM_STATISTICS:
      return { ...state, formStatistics: onLoadableLoad(initialFormsState.formStatistics.data) };
    case FormsActionTypes.GET_FORM_STATISTICS_COMPLETE:
      return { ...state, formStatistics: onLoadableSuccess(action.stats) };
    case FormsActionTypes.GET_FORM_STATISTICS_FAILED:
      return { ...state, formStatistics: onLoadableError(action.error) };
    case FormsActionTypes.SAVE_FORM:
      return { ...state, updatedForm: onLoadableLoad(initialFormsState.updatedForm.data) };
    case FormsActionTypes.SAVE_FORM_COMPLETE:
      return { ...state, form: onLoadableSuccess(action.form), updatedForm: onLoadableSuccess(action.form) };
    case FormsActionTypes.SAVE_FORM_FAILED:
      return { ...state, updatedForm: onLoadableError(action.error) };
    case FormsActionTypes.CREATE_FORM:
      return { ...state, createdForm: onLoadableLoad(initialFormsState.createdForm.data) };
    case FormsActionTypes.CREATE_FORM_COMPLETE:
      return { ...state, form: onLoadableSuccess(action.form), createdForm: onLoadableSuccess(action.form) };
    case FormsActionTypes.CREATE_FORM_FAILED:
      return { ...state, createdForm: onLoadableError(action.error) };
    case FormsActionTypes.GET_TOMBOLA_WINNERS:
      return { ...state, tombolaWinners: onLoadableLoad(initialFormsState.tombolaWinners.data) };
    case FormsActionTypes.GET_TOMBOLA_WINNERS_COMPLETE:
      return { ...state, tombolaWinners: onLoadableSuccess(action.payload) };
    case FormsActionTypes.GET_TOMBOLA_WINNERS_FAILED:
      return { ...state, tombolaWinners: onLoadableError(action.error) };
    case FormsActionTypes.DELETE_ALL_RESPONSES_COMPLETE:
      return { ...state, formStatistics: onLoadableSuccess({ submissions: 0, statistics: {} }) };
  }
  return state;
}