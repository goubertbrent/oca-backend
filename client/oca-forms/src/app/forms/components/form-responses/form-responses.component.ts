import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormComponentType } from '../../../interfaces/enums';
import { SingleFormResponse } from '../../../interfaces/forms.interfaces';
import { Loadable } from '../../../interfaces/loadable';

@Component({
  selector: 'oca-form-responses',
  templateUrl: './form-responses.component.html',
  styleUrls: [ './form-responses.component.css' ],
})
export class FormResponsesComponent {
  @Input() response: Loadable<SingleFormResponse>;
  @Output() nextResponse = new EventEmitter<number | null>();
  @Output() removeResponse = new EventEmitter<{formId: number, submissionId: number}>();
  FormComponentType = FormComponentType;
}
