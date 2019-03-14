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
import { FormStatisticsView, OcaForm } from '../../../interfaces/forms.interfaces';
import { Loadable } from '../../../interfaces/loadable';
import { UserDetailsTO } from '../../../users/interfaces';

export const enum FormDetailTab {
  QUESTIONS,
  TOMBOLA_WINNERS,
  // RESPONSES,
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
  @Output() save = new EventEmitter<OcaForm>();
  @Output() tabChanged = new EventEmitter<number>();
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
