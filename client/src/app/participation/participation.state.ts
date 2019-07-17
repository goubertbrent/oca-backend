import { createFeatureSelector, createSelector } from '@ngrx/store';
import { DEFAULT_LIST_LOADABLE, DEFAULT_LOADABLE, Loadable } from '../shared/loadable/loadable';
import { CitySettings, Project, ProjectStatistics } from './projects';


export interface ParticipationState {
  projects: Loadable<Project[]>;
  projectDetails: Loadable<Project>;
  projectStatistics: Loadable<ProjectStatistics>;
  settings: Loadable<CitySettings>;
}


export const initialState: ParticipationState = {
  projects: DEFAULT_LIST_LOADABLE,
  projectDetails: DEFAULT_LOADABLE,
  projectStatistics: DEFAULT_LOADABLE,
  settings: DEFAULT_LOADABLE,
};

const featureSelector = createFeatureSelector<ParticipationState>('psp');

export const getProjects = createSelector(featureSelector, s => s.projects);
export const getProjectDetails = createSelector(featureSelector, s => s.projectDetails);
export const getProjectStatistics = createSelector(featureSelector, s => s.projectStatistics);
export const getSettings = createSelector(featureSelector, s => s.settings);


