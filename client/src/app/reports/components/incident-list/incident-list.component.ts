import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { Incident, IncidentList, IncidentStatus } from '../../reports';

@Component({
  selector: 'oca-incident-list',
  templateUrl: './incident-list.component.html',
  styleUrls: ['./incident-list.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class IncidentListComponent {
  @Input() incidents: IncidentList;
  @Output() loadMore = new EventEmitter<{ cursor: string }>();

  trackById(index: number, incident: Incident) {
    return incident.id;
  }
}
