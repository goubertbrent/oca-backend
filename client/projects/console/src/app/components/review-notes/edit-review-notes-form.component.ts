import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { ApiRequestStatus } from '../../../../framework/client/rpc';
import { ReviewNotes } from '../../interfaces';

@Component({
  selector: 'rcc-edit-review-notes-form',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'edit-review-notes-form.component.html',
})
export class EditReviewNotesFormComponent {
  @Input() status: ApiRequestStatus;
  @Output() save = new EventEmitter<ReviewNotes>();

  private _reviewNotes: ReviewNotes;

  get reviewNotes() {
    return this._reviewNotes;
  }

  @Input()
  set reviewNotes(value: ReviewNotes) {
    this._reviewNotes = { ...value };
  }

  submit() {
    this.save.emit({ ...this.reviewNotes });
  }
}
