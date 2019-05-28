import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { Loadable } from '../../../shared/loadable/loadable';
import { ProjectStatistics } from '../../projects';

@Component({
  selector: 'oca-project-statistics',
  templateUrl: './project-statistics.component.html',
  styleUrls: [ './project-statistics.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProjectStatisticsComponent {
  @Input() statistics: Loadable<ProjectStatistics>;
  @Output() loadMore = new EventEmitter();
}
