import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  SimpleChanges,
  ViewEncapsulation,
} from '@angular/core';
import { MatTabChangeEvent } from '@angular/material';
import { Loadable } from '../../../shared/loadable/loadable';
import { UserDetailsTO } from '../../../shared/users/interfaces';
import { OptionsMenuOption } from '../../interfaces/consts';
import { FormStatisticsView, LoadResponses, OcaForm, SaveForm, SingleFormResponse } from '../../interfaces/forms.interfaces';

export const enum FormDetailTab {
  QUESTIONS,
  TOMBOLA_WINNERS,
  RESPONSES,
  STATISTICS,
}

@Component({
  selector: 'oca-form-detail',
  templateUrl: './form-detail.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class FormDetailComponent implements OnChanges {
  @Input() form: OcaForm;
  @Input() statistics: Loadable<FormStatisticsView>;
  @Input() tombolaWinners: UserDetailsTO[];
  @Input() formResponse: Loadable<SingleFormResponse>;
  @Output() save = new EventEmitter<SaveForm>();
  @Output() tabChanged = new EventEmitter<number>();
  @Output() menuOptionClicked = new EventEmitter<OptionsMenuOption>();
  @Output() createNews = new EventEmitter();
  @Output() testForm = new EventEmitter<UserDetailsTO>();
  @Output() loadResponses = new EventEmitter<LoadResponses>();
  @Output() nextResponse = new EventEmitter<number | null>();
  @Output() removeResponse = new EventEmitter<{formId: number, submissionId: number}>();
  showTombolaWinners = false;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes && changes.form && changes.form.currentValue) {
      this.showTombolaWinners = this.form.settings.finished && this.form.settings.tombola !== null;
    }
  }

  changeTab(event: MatTabChangeEvent) {
    if (!this.showTombolaWinners && event.index > FormDetailTab.QUESTIONS) {
      this.tabChanged.emit(event.index + 1);
    } else {
      this.tabChanged.emit(event.index);
    }
  }
}
