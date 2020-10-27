import { createFeatureSelector, createSelector } from '@ngrx/store';
import { initialStateResult, ResultState } from '@oca/shared';
import { AppMerchant, AppMerchantList, City, Project, ProjectDetails, UserSettings } from './projects';

export interface ProjectsState {
  currentProjectId: number | null;
  projects: ResultState<Project[]>;
  projectDetails: ResultState<ProjectDetails>;
  merchants: ResultState<AppMerchantList>;
  city: ResultState<City>;
  merchantDetails: ResultState<AppMerchant>;
  userSettings: ResultState<UserSettings>;
}

const getFeatureState = createFeatureSelector<ProjectsState>('projects');

export const initialProjectsState: ProjectsState = {
  currentProjectId: null,
  projects: initialStateResult,
  projectDetails: initialStateResult,
  merchants: initialStateResult,
  city: initialStateResult,
  merchantDetails: initialStateResult,
  userSettings: initialStateResult,
};

export const getCurrentProjectId = createSelector(getFeatureState, s => s.currentProjectId);
export const getCurrentProject = createSelector(getFeatureState, s => s.projectDetails);
export const getProjects = createSelector(getFeatureState, s => s.projects);
export const getMerchants = createSelector(getFeatureState, s => s.merchants.result);
export const getMerchantDetails = createSelector(getFeatureState, s => s.merchantDetails.result);
export const getCity = createSelector(getFeatureState, s => s.city);
export const getUserSettings = createSelector(getFeatureState, s => s.userSettings.result);


