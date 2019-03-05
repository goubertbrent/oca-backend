import { createFeatureSelector, createSelector } from '@ngrx/store';
import { DynamicForm, FormStatistics, OcaForm } from '../interfaces/forms.interfaces';
import { DEFAULT_LOADABLE, Loadable } from '../interfaces/loadable';
import { UserDetailsTO } from '../users/interfaces';

export const initialFormsState: FormsState = {
  forms: DEFAULT_LOADABLE,
  form: DEFAULT_LOADABLE,
  formStatistics: DEFAULT_LOADABLE,
  updatedForm: DEFAULT_LOADABLE,
  createdForm: DEFAULT_LOADABLE,
  tombolaWinners: DEFAULT_LOADABLE,
};

export interface FormsState {
  forms: Loadable<DynamicForm[]>;
  form: Loadable<OcaForm>;
  formStatistics: Loadable<FormStatistics>;
  updatedForm: Loadable<OcaForm>;
  createdForm: Loadable<OcaForm>;
  tombolaWinners: Loadable<UserDetailsTO[]>;
}


const featureSelector = createFeatureSelector<FormsState>('forms');

export const getForms = createSelector(featureSelector, s => s.forms);
export const getForm = createSelector(featureSelector, s => s.form);
export const getFormStatistics = createSelector(featureSelector, s => s.formStatistics);
export const getTombolaWinners = createSelector(featureSelector, s => s.tombolaWinners.data || [] );
