import { createFeatureSelector, createSelector } from '@ngrx/store';
import { DateFormat, FormComponentType } from '../interfaces/enums';
import {
  ComponentStatistics,
  ComponentStatisticsValues,
  ComponentStatsType,
  DatesComponentStatistics,
  DatetimeComponent,
  FormComponent,
  FormSettings,
  FormStatistics,
  FormStatisticsValue,
  FormStatisticsView,
  isFormStatisticsLocationArray,
  isFormStatisticsNumber,
  OcaForm,
  SectionStatistics,
  TimesComponentStatistics,
} from '../interfaces/forms.interfaces';
import { DEFAULT_LIST_LOADABLE, DEFAULT_LOADABLE, Loadable } from '../interfaces/loadable';
import { UserDetailsTO } from '../users/interfaces';

export const initialFormsState: FormsState = {
  forms: DEFAULT_LIST_LOADABLE,
  form: DEFAULT_LOADABLE,
  formStatistics: DEFAULT_LOADABLE,
  updatedForm: DEFAULT_LOADABLE,
  createdForm: DEFAULT_LOADABLE,
  tombolaWinners: DEFAULT_LIST_LOADABLE,
};

export interface FormsState {
  forms: Loadable<FormSettings[]>;
  form: Loadable<OcaForm>;
  formStatistics: Loadable<FormStatistics>;
  updatedForm: Loadable<OcaForm>;
  createdForm: Loadable<OcaForm>;
  tombolaWinners: Loadable<UserDetailsTO[]>;
}


const featureSelector = createFeatureSelector<FormsState>('forms');

export const getForms = createSelector(featureSelector, s => ({
  ...s.forms,
  data: (s.forms.data || []).map(f => ({ ...f, visible_until: f.visible_until ? new Date(f.visible_until) : null }
  )),
}));
export const getForm = createSelector(featureSelector, s => s.form);
export const getRawFormStatistics = createSelector(featureSelector, s => s.formStatistics);
export const getTombolaWinners = createSelector(featureSelector, s => s.tombolaWinners.data || []);

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
  for (const section of form.form.sections) {
    const sectionStats = statistics.statistics[ section.id ];
    const components: ComponentStatistics[] = [];
    for (const component of section.components) {
      if (component.type !== FormComponentType.PARAGRAPH) {
        const stats: ComponentStatistics = {
          id: component.id,
          title: component.title,
          responses: 0,
          values: null,
        };
        if (sectionStats) {
          const componentStats: FormStatisticsValue = sectionStats[ component.id ];
          if (componentStats) {
            const { responseCount, values } = getComponentStatsValues(component, componentStats);
            stats.responses = responseCount;
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
  let responseCount = 0;
  if (isFormStatisticsNumber(componentStats)) {
    responseCount = Object.values<number>(componentStats).reduce((partial, val) => partial + val);
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
    responseCount = componentStats.length;
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
        value: componentStats,
      };
    }
  }
  return { responseCount, values };
}
