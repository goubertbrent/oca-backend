import { NonNullLoadable, onLoadableError, onLoadableLoad, onLoadableSuccess } from '../shared/loadable/loadable';
import { insertItem, removeItem, updateItem } from '../shared/util/redux';
import { FormsActions, FormsActionTypes } from './forms.actions';
import { FormResponsesState, FormsState, initialFormsState, responsesAdapter } from './forms.state';
import { FormSettings } from './interfaces/forms';

export function formsReducer(state: FormsState = initialFormsState, action: FormsActions): FormsState {
  switch (action.type) {
    case FormsActionTypes.GET_FORMS:
      return { ...state, forms: onLoadableLoad(initialFormsState.forms.data) };
    case FormsActionTypes.GET_FORMS_COMPLETE:
      return { ...state, forms: onLoadableSuccess(action.forms) };
    case FormsActionTypes.GET_FORMS_FAILED:
      return { ...state, forms: onLoadableError(action.error, state.forms.data) };
    case FormsActionTypes.GET_FORM:
      return {
        ...state,
        form: onLoadableLoad(initialFormsState.form.data),
        tombolaWinners: initialFormsState.tombolaWinners,
        formResponses: initialFormsState.formResponses,
        selectedFormResponseId: initialFormsState.selectedFormResponseId,
      };
    case FormsActionTypes.GET_FORM_COMPLETE:
      return { ...state, form: onLoadableSuccess(action.form) };
    case FormsActionTypes.GET_FORM_FAILED:
      return { ...state, form: onLoadableError(action.error, state.form.data) };
    case FormsActionTypes.GET_FORM_STATISTICS:
      return { ...state, formStatistics: onLoadableLoad(initialFormsState.formStatistics.data) };
    case FormsActionTypes.GET_FORM_STATISTICS_COMPLETE:
      return { ...state, formStatistics: onLoadableSuccess(action.stats) };
    case FormsActionTypes.GET_FORM_STATISTICS_FAILED:
      return { ...state, formStatistics: onLoadableError(action.error, state.formStatistics.data) };
    case FormsActionTypes.SAVE_FORM:
      return { ...state, updatedForm: onLoadableLoad(initialFormsState.updatedForm.data) };
    case FormsActionTypes.SAVE_FORM_COMPLETE:
      return {
        ...state,
        form: onLoadableSuccess(action.form),
        updatedForm: onLoadableSuccess(action.form),
        forms: { ...state.forms, data: updateItem(state.forms.data as FormSettings[], action.form.settings, 'id') },
      };
    case FormsActionTypes.SAVE_FORM_FAILED:
      return { ...state, updatedForm: onLoadableError(action.error, state.updatedForm.data) };
    case FormsActionTypes.CREATE_FORM:
      return { ...state, createdForm: onLoadableLoad(initialFormsState.createdForm.data) };
    case FormsActionTypes.CREATE_FORM_COMPLETE:
      return {
        ...state,
        form: onLoadableSuccess(action.form),
        createdForm: onLoadableSuccess(action.form),
        forms: { ...state.forms, data: insertItem(state.forms.data as FormSettings [], action.form.settings) },
      };
    case FormsActionTypes.CREATE_FORM_FAILED:
      return { ...state, createdForm: onLoadableError(action.error, state.createdForm.data) };
    case FormsActionTypes.GET_TOMBOLA_WINNERS:
      return { ...state, tombolaWinners: onLoadableLoad(initialFormsState.tombolaWinners.data) };
    case FormsActionTypes.GET_TOMBOLA_WINNERS_COMPLETE:
      return { ...state, tombolaWinners: onLoadableSuccess(action.payload) };
    case FormsActionTypes.GET_TOMBOLA_WINNERS_FAILED:
      return { ...state, tombolaWinners: onLoadableError(action.error, state.tombolaWinners.data) };
    case FormsActionTypes.DELETE_ALL_RESPONSES_COMPLETE:
      return {
        ...state,
        formStatistics: onLoadableSuccess({ submissions: 0, statistics: {} }),
        selectedFormResponseId: initialFormsState.selectedFormResponseId,
        formResponses: initialFormsState.formResponses,
      };
    case FormsActionTypes.DELETE_RESPONSE_COMPLETE:
      return {
        ...state,
        selectedFormResponseId: getNextItemInArray(state.formResponses.data.ids as number[], action.payload.submissionId),
        formResponses: onLoadableSuccess(responsesAdapter.removeOne(action.payload.submissionId, state.formResponses.data)),
      };
    case FormsActionTypes.DELETE_FORM_COMPLETE:
      return { ...state, forms: { ...state.forms, data: removeItem(state.forms.data as FormSettings[], action.form.id, 'id') } };
    case FormsActionTypes.GET_RESPONSE:
      return {
        ...state,
        selectedFormResponseId: action.payload.id,
      };
    case FormsActionTypes.GET_RESPONSES:
      const responses = action.clear ? responsesAdapter.removeAll(state.formResponses.data) : state.formResponses.data;
      return {
        ...state,
        formResponses: onLoadableLoad(responses) as NonNullLoadable<FormResponsesState>,
      };
    case FormsActionTypes.GET_RESPONSES_COMPLETE:
      return {
        ...state,
        selectedFormResponseId: action.payload.results.length ? action.payload.results[ 0 ].id : state.selectedFormResponseId,
        formResponses: onLoadableSuccess(
          responsesAdapter.upsertMany(action.payload.results, {
            ...state.formResponses.data,
            cursor: action.payload.cursor,
            more: action.payload.more,
          })),
      };
    case FormsActionTypes.GET_INTEGRATIONS:
      return { ...state, integrations: onLoadableLoad(initialFormsState.integrations.data) };
    case FormsActionTypes.GET_INTEGRATIONS_COMPLETE:
      return { ...state, integrations: onLoadableSuccess(action.payload) };
    case FormsActionTypes.GET_INTEGRATIONS_FAILED:
      return { ...state, integrations: onLoadableError(action.error, initialFormsState.integrations.data) };
    case FormsActionTypes.UPDATE_INTEGRATION:
      return { ...state, integrations: onLoadableLoad(state.integrations.data) };
    case FormsActionTypes.UPDATE_INTEGRATION_COMPLETE:
      return { ...state, integrations: onLoadableSuccess(updateItem(state.integrations.data, action.payload, 'provider')) };
    case FormsActionTypes.UPDATE_INTEGRATION_FAILED:
      return { ...state, integrations: onLoadableError(action.error, state.integrations.data) };
    case FormsActionTypes.IMPORT_FORM:
      return {
        ...state,
        form: state.form.data ? {
          ...state.form,
            data: {...state.form.data, form: {...state.form.data.form, ...action.payload.form}}
        } : state.form
      };
  }
  return state;
}

function getNextItemInArray(array: number[], currentItem: number): number | null {
  const currentIndex = array.indexOf(currentItem);
  const index = currentIndex + 1 === array.length ? currentIndex - 1 : currentIndex + 1;
  if (index in array) {
    return array[ index ];
  }
  return null;
}
