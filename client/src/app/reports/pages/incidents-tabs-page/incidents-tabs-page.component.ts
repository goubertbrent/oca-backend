import { ChangeDetectionStrategy, Component } from '@angular/core';
import { IncidentStatus } from '../reports';

@Component({
  selector: 'oca-incidents-tabs-page',
  templateUrl: './incidents-tabs-page.component.html',
  styleUrls: ['./incidents-tabs-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class IncidentsTabsPageComponent {
  tabs = [
    { route: [IncidentStatus.NEW], label: 'oca.new', icon: 'report' },
    { route: [IncidentStatus.IN_PROGRESS], label: 'oca.in_progress', icon: 'timelapse' },
    { route: [IncidentStatus.RESOLVED], label: 'oca.resolved', icon: 'done' },
  ];
}
