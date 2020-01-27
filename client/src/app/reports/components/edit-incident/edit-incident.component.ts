import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { NgForm } from '@angular/forms';
import { Incident, INCIDENT_STATUSES } from '../../reports';

@Component({
  selector: 'oca-edit-incident',
  templateUrl: './edit-incident.component.html',
  styleUrls: ['./edit-incident.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EditIncidentComponent implements OnInit {
  @Input() incident: Incident;
  @Input() disabled = false;
  @Output() saveClicked = new EventEmitter<Incident>();
  statuses = INCIDENT_STATUSES;

  constructor() {
  }

  ngOnInit() {
  }

  submit(form: NgForm) {
    if (form.form.valid) {
      this.saveClicked.emit(this.incident);
    }
  }
}
