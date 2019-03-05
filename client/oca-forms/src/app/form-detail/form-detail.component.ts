import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { FormStatistics, OcaForm } from '../interfaces/forms.interfaces';
import { Loadable } from '../interfaces/loadable';
import { UserDetailsTO } from '../users/interfaces';

export const enum FormDetailTab {
  QUESTIONS,
  TOMBOLA,
  // RESPONSES,
  STATISTICS,
}

@Component({
  selector: 'oca-form-detail',
  templateUrl: './form-detail.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormDetailComponent {
  @Input() form: OcaForm;
  @Input() statistics: Loadable<FormStatistics>;
  @Input() tombolaWinners: UserDetailsTO[];
  @Output() save = new EventEmitter<OcaForm>();
  @Output() tabChanged = new EventEmitter<number>();
}
