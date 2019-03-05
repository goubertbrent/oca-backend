import { ChangeDetectionStrategy, Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { FormComponentType } from '../interfaces/enums';
import { DynamicForm, FormStatistics, InputComponents } from '../interfaces/forms.interfaces';

@Component({
  selector: 'oca-form-statistics',
  templateUrl: './form-statistics.component.html',
  styleUrls: [ './form-statistics.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormStatisticsComponent implements OnChanges {
  FormComponentType = FormComponentType;
  @Input() form: DynamicForm;
  @Input() statistics: FormStatistics;

  private responseCount: { [ key: string ]: { [ key: string ]: number } } = {};
  private responseCountMapping = {
    '=0': 'oca.response_count.none',
    '=1': 'oca.response_count.singular',
    other: 'oca.response_count.plural',
  };

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.statistics && changes.statistics.currentValue) {
      this.responseCount = this.getResponseCount(changes.statistics.currentValue);
    }
  }

  getCount(sectionId: string, component: InputComponents) {
    return this.responseCount[ sectionId ] && this.responseCount[ sectionId ][ component.id ] || 0;
  }

  private getResponseCount(stats: FormStatistics) {
    const responseCount = {};
    for (const sectionId of Object.keys(stats.statistics)) {
      if (!(sectionId in responseCount)) {
        responseCount[ sectionId ] = {};
      }
      for (const componentId of Object.keys(stats.statistics[ sectionId ])) {
        if (!(componentId in responseCount[ sectionId ])) {
          responseCount[ sectionId ][ componentId ] = 0;
        }
        const componentStats = stats.statistics[ sectionId ][ componentId ];
        if (Array.isArray(componentStats)) {
          responseCount[ sectionId ][ componentId ] += 1;
        } else if (typeof componentStats === 'object') {
          for (const value of Object.values(componentStats)) {
            responseCount[ sectionId ][ componentId ] += value;
          }
        }
      }
    }
    return responseCount;
  }

}
