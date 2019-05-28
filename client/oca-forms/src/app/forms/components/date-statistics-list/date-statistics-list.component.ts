import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { DatesComponentStatistics, TimesComponentStatistics } from '../../interfaces/forms';

@Component({
  selector: 'oca-date-statistics-list',
  templateUrl: './date-statistics-list.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DateStatisticsListComponent {
  @Input() statistics: DatesComponentStatistics | TimesComponentStatistics;
}
