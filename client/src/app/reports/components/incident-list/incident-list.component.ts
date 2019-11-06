import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { Incident, IncidentList, IncidentStatus } from '../../pages/reports';

@Component({
  selector: 'oca-incident-list',
  templateUrl: './incident-list.component.html',
  styleUrls: ['./incident-list.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class IncidentListComponent {
  @Input() incidents: IncidentList;
  @Output() loadMore = new EventEmitter<{ cursor: string }>();
  iconsForStatus = {
    [ IncidentStatus.NEW ]: 'report',
    [ IncidentStatus.IN_PROGRESS ]: 'timelapse',
    [ IncidentStatus.RESOLVED ]: 'done',
  };

  trackById(index: number, incident: Incident) {
    return incident.id;
  }
}
