import { createEntityAdapter, EntityState } from '@ngrx/entity';
import { createFeatureSelector, createSelector } from '@ngrx/store';
import { DEFAULT_LIST_LOADABLE, DEFAULT_LOADABLE, Loadable, NonNullLoadable } from '../shared/loadable/loadable';
import { UserDetailsTO } from '../shared/users/users';
import { DateFormat, FormComponentType } from './interfaces/enums';
import {
  ComponentResponse,
  FormComponentValue,
  MergedFormResponse,
  ResponseFormComponent,
  ResponseFormSectionValue,
} from './interfaces/form-values';
import {
  ComponentStatistics,
  ComponentStatisticsValues,
  ComponentStatsType,
  DatesComponentStatistics,
  DatetimeComponent,
  DynamicForm,
  FormComponent,
  FormResponse,
  FormSettings,
  FormStatistics,
  FormStatisticsValue,
  FormStatisticsView,
  isFormStatisticsLocationArray,
  isFormStatisticsNumber,
  OcaForm,
  SectionStatistics,
  SingleFormResponse,
  TimesComponentStatistics,
} from './interfaces/forms';
import { FormIntegrationConfiguration } from './interfaces/integrations';

function selectFormResponseId(formResponse: FormResponse) {
  return formResponse.id;
}

export const responsesAdapter = createEntityAdapter<FormResponse>({ selectId: selectFormResponseId });
export const responsesSelectors = responsesAdapter.getSelectors();

export const initialFormsState: FormsState = {
  forms: DEFAULT_LIST_LOADABLE,
  form: DEFAULT_LOADABLE,
  formStatistics: DEFAULT_LOADABLE,
  updatedForm: DEFAULT_LOADABLE,
  createdForm: DEFAULT_LOADABLE,
  tombolaWinners: DEFAULT_LIST_LOADABLE,
  formResponses: { ...DEFAULT_LOADABLE, data: responsesAdapter.getInitialState({ cursor: null, more: true }) },
  selectedFormResponseId: null,
  integrations: DEFAULT_LIST_LOADABLE,
};

export interface FormResponsesState extends EntityState<FormResponse> {
  cursor: string | null;
  more: boolean;
}

export interface FormsState {
  forms: Loadable<FormSettings[]>;
  form: Loadable<OcaForm>;
  formStatistics: Loadable<FormStatistics>;
  updatedForm: Loadable<OcaForm>;
  createdForm: Loadable<OcaForm>;
  tombolaWinners: Loadable<UserDetailsTO[]>;
  formResponses: NonNullLoadable<FormResponsesState>;
  selectedFormResponseId: number | null;
  integrations: NonNullLoadable<FormIntegrationConfiguration[]>;
}

const featureSelector = createFeatureSelector<FormsState>('forms');

export const getResponsesData = createSelector(featureSelector, s => s.formResponses.data);
export const selectAllResponses = createSelector(getResponsesData, responsesSelectors.selectEntities);
export const selectAllResponseIds = createSelector(featureSelector, s => responsesSelectors.selectIds(s.formResponses.data));

export const getForms = createSelector(featureSelector, s => ({
  ...s.forms,
  data: (s.forms.data || []).map(f => ({ ...f, visible_until: f.visible_until ? new Date(f.visible_until) : null }
  )).sort((item1, item2) => item1.title.localeCompare(item2.title)),
}));
export const getForm = createSelector(featureSelector, s => s.form);
export const getRawFormStatistics = createSelector(featureSelector, s => s.formStatistics);
export const getTombolaWinners = createSelector(featureSelector, s => s.tombolaWinners.data || []);
export const getIntegrations = createSelector(featureSelector, s => s.integrations);
export const getActiveIntegrations = createSelector(featureSelector, s => s.integrations.data
  .filter(i => i.enabled && i.visible)
  .map(i => i.provider));

export const selectedFormResponseId = createSelector(featureSelector, s => s.selectedFormResponseId);

export const getFormResponse = createSelector(featureSelector, getForm, selectAllResponses, selectedFormResponseId, selectAllResponseIds,
  (s, form, responses, id, allIds) => {
    let data: SingleFormResponse | null = null;
    if (id && form.data) {
      const response = responses[ id ];
      if (response) {
        const index = (allIds as number[]).indexOf(id as number);
        const previousIndex = index === 0 ? null : index - 1;
        const nextIndex = (allIds.length - 1 > index) ? index + 1 : null;
        data = {
          cursor: s.formResponses.data.cursor,
          more: s.formResponses.data.more,
          previous: previousIndex === null ? null : allIds[ previousIndex ] as number,
          next: nextIndex === null ? null : allIds[ nextIndex ] as number,
          result: convertResponse(response, form.data.form),
        };
      }
    }
    return {
      loading: s.formResponses.loading,
      success: s.formResponses.success,
      error: s.formResponses.error,
      data,
    };
  });

export const getTransformedStatistics = createSelector(getForm, getRawFormStatistics, (form, statistics) => {
  if (!form.success || !statistics.success) {
    return {
      loading: form.loading || statistics.loading,
      success: form.success && statistics.success,
      error: form.error && statistics.error,
      data: null,
    } as Loadable<null>;
  }
  return {
    loading: false,
    success: true,
    error: null,
    data: {
      submissions: (statistics.data as FormStatistics).submissions,
      sections: getSectionStatistics(form.data as OcaForm, statistics.data as FormStatistics),
    },
  } as Loadable<FormStatisticsView>;
});

function getSectionStatistics(form: OcaForm, statistics: FormStatistics): SectionStatistics[] {
  const sections: SectionStatistics[] = [];
  for (let i = 0; i < form.form.sections.length; i++) {
    const section = form.form.sections[ i ];
    const sectionStats = statistics.statistics[ section.id ];
    const components: ComponentStatistics[] = [];
    for (const component of section.components) {
      if (component.type !== FormComponentType.PARAGRAPH) {
        const stats: ComponentStatistics = {
          id: component.id,
          title: component.title,
          hasResponses: false,
          values: null,
        };
        if (sectionStats) {
          const componentStats: FormStatisticsValue = sectionStats[ component.id ];
          if (componentStats) {
            const { hasResponses, values } = getComponentStatsValues(component, componentStats);
            stats.hasResponses = hasResponses;
            stats.values = values;
          }
        }
        components.push(stats);
      }
    }
    // SKip sections without any components
    if (components.length) {
      sections.push({
        id: section.id,
        title: section.title,
        number: i + 1,
        components,
      });
    }
  }
  return sections;
}


function getDateTimeComponentValues(component: DatetimeComponent, stats: { [ key: string ]: number }): DatesComponentStatistics
  | TimesComponentStatistics {
  const values: string[] = Object.keys(stats);
  if (component.format === DateFormat.DATE || component.format === DateFormat.DATETIME) {
    return {
      format: component.format === DateFormat.DATETIME ? 'medium' : 'mediumDate',
      type: ComponentStatsType.DATES,
      value: values.filter(key => key.length > 5).map(key => ({
        value: new Date(key),
        amount: stats[ key ],
      })),
    };
  } else {
    return {
      format: 'shortTime',
      type: ComponentStatsType.TIMES,
      value: values.filter(key => key.length < 5).map(key => {
        const hour = parseInt(key.length === 4 ? key.slice(0, 2) : key.slice(0, 1), 10);
        const minute = parseInt(key.slice(2), 10);
        return {
          value: new Date(0, 0, 0, hour, minute, 0),
          amount: stats[ key ],
        };
      }),
    };
  }
}

function getComponentStatsValues(component: FormComponent, componentStats: FormStatisticsValue) {
  let values: ComponentStatisticsValues = null;
  let hasResponses = false;
  if (isFormStatisticsNumber(componentStats)) {
    for (const number of Object.values<number>(componentStats)) {
      if (number) {
        hasResponses = true;
        break;
      }
    }
    if (component.type === FormComponentType.DATETIME) {
      values = getDateTimeComponentValues(component, componentStats);
    } else {
      const value = Object.keys(componentStats)
        .map(key => ({ value: key, amount: componentStats[ key ] }))
        .sort((a, b) => a.value ? a.value.localeCompare(b.value) : 2);
      if ([ FormComponentType.SINGLE_SELECT, FormComponentType.MULTI_SELECT ].includes(component.type)) {
        values = { type: ComponentStatsType.CHOICES, value };
      } else {
        values = { type: ComponentStatsType.VALUES, value };
      }
    }
  } else {
    hasResponses = componentStats.length > 0;
    if (isFormStatisticsLocationArray(componentStats)) {
      values = {
        type: ComponentStatsType.LOCATIONS,
        value: componentStats.map(array => ({
          lat: array[ 0 ],
          lng: array[ 1 ],
        })),
      };
    } else {
      values = {
        type: ComponentStatsType.FILES,
        value: componentStats.map(array => ({
          url: array[ 0 ],
          fileName: array[ 1 ],
          icon: getIconFromMime(array[ 2 ]),
        })),
      };
    }
  }
  return { hasResponses, values };
}

export function getIconFromMime(mimeType: string) {
  if (mimeType.startsWith('image')) {
    return 'image';
  } else if (mimeType.startsWith('video')) {
    return 'videocam';
  } else if (mimeType.startsWith('audio')) {
    return 'audiotrack';
  } else if (mimeType === 'application/pdf') {
    return 'picture_as_pdf';
  }
  return 'insert_drive_file';
}

function convertResponse(formResponse: FormResponse, form: DynamicForm): MergedFormResponse {
  const sections: ResponseFormSectionValue[] = [];
  let sectionNumber = 0;
  for (const section of form.sections) {
    sectionNumber++;
    // SKip sections without any components
    if (!section.components.length) {
      continue;
    }
    const components: ResponseFormComponent[] = [];
    const responseSection = formResponse.sections.find(s => s.id === section.id);
    if (responseSection) {
      const initialVal: { [ key: string ]: FormComponentValue } = {};
      const mapping = responseSection.components.reduce((acc, comp) => {
        acc[ comp.id ] = comp;
        return acc;
      }, initialVal);
      for (const component of section.components) {
        if (component.type !== FormComponentType.PARAGRAPH && component.id in mapping) {
          const value = mapping[ component.id ];
          let response: ComponentResponse | null = null;
          switch (value.type) {
            case FormComponentType.SINGLE_SELECT:
              if (component.type === FormComponentType.SINGLE_SELECT) {
                response = {
                  type: component.type,
                  value: value.value,
                  choices: component.choices,
                };
              }
              break;
            case FormComponentType.MULTI_SELECT:
              if (component.type === FormComponentType.MULTI_SELECT) {
                response = {
                  type: component.type,
                  choices: component.choices.map(c => ({ ...c, selected: value.values.includes(c.value) })),
                };
              }
              break;
            case FormComponentType.DATETIME:
              let format: string;
              switch ((component as DatetimeComponent).format) {
                case DateFormat.DATE:
                  format = 'mediumDate';
                  break;
                case DateFormat.DATETIME:
                  format = 'medium';
                  break;
                case DateFormat.TIME:
                  format = 'mediumTime';
                  break;
                default:
                  format = 'medium';
              }
              if (component.type === FormComponentType.DATETIME) {
                response = {
                  type: component.type,
                  format,
                  date: new Date(value.year, value.month, value.day, value.hour, value.minute),
                };
              }
              break;
            case FormComponentType.FILE:
              if (value.type === FormComponentType.FILE) {
                response = { ...value, icon: getIconFromMime(value.file_type) };
              }
              break;
            default:
              response = value;
              break;
          }
          // Can be null in case the question type had been changed after this answer was submitted
          if (response) {
            components.push({ id: component.id, title: component.title, response });
          }
        }
      }
    }
    if (components.length) {
      sections.push({ id: section.id, title: section.title, number: sectionNumber, components });
    }
  }
  return {
    formId: form.id,
    submissionId: formResponse.id,
    submitted_date: formResponse.submitted_date,
    external_reference: formResponse.external_reference,
    sections,
  };
}
