import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { DynamicForm } from '../interfaces/forms.interfaces';
import { Loadable } from '../interfaces/loadable';

@Component({
  selector: 'oca-forms-list',
  templateUrl: './form-list.component.html',
  styleUrls: [ './form-list.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormListComponent {
  @Input() forms: Loadable<DynamicForm[]>;
  @Output() showFormDetails = new EventEmitter<DynamicForm>();
}
