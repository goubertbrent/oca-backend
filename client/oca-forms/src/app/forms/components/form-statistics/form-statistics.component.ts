import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { FormComponentType } from '../../../interfaces/enums';
import { ComponentStatsType, FormStatisticsView } from '../../../interfaces/forms.interfaces';

@Component({
  selector: 'oca-form-statistics',
  templateUrl: './form-statistics.component.html',
  styleUrls: [ './form-statistics.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormStatisticsComponent {
  FormComponentType = FormComponentType;
  @Input() statistics: FormStatisticsView;
  ComponentStatsType = ComponentStatsType;

  private responseCountMapping = {
    '=0': 'oca.response_count.none',
    '=1': 'oca.response_count.singular',
    other: 'oca.response_count.plural',
  };

}
