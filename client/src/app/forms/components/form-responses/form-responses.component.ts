import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { Loadable } from '../../../shared/loadable/loadable';
import { FormComponentType } from '../../interfaces/enums';
import { SingleFormResponse } from '../../interfaces/forms';

@Component({
  selector: 'oca-form-responses',
  templateUrl: './form-responses.component.html',
  styleUrls: [ './form-responses.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormResponsesComponent {
  @Input() response: Loadable<SingleFormResponse>;
  @Output() nextResponse = new EventEmitter<number | null>();
  @Output() removeResponse = new EventEmitter<{formId: number, submissionId: number}>();
  FormComponentType = FormComponentType;
}
