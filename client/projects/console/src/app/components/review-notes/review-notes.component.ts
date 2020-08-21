import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, ViewEncapsulation } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable, Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { DialogService } from '../../../../framework/client/dialog';
import { ApiRequestStatus } from '../../../../framework/client/rpc';
import { ClearReviewNotesAction, GetReviewNotesListAction, RemoveReviewNotesAction } from '../../actions';
import { getRemoveReviewNotesStatus, getReviewNotesList, getReviewNotesListStatus } from '../../console.state';
import { ReviewNotes } from '../../interfaces';
import { ApiErrorService } from '../../services';

@Component({
  selector: 'rcc-review-notes',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.Emulated,
  templateUrl: 'review-notes.component.html',
  styles: [ `.review-notes-card {
    width: 250px;
    display: inline-block;
    margin: 16px;
  }` ],
})
export class ReviewNotesComponent implements OnInit, OnDestroy {
  reviewNotes$: Observable<ReviewNotes[]>;
  status$: Observable<ApiRequestStatus>;
  private _removeSubscription: Subscription;

  constructor(private store: Store,
              private translate: TranslateService,
              private errorService: ApiErrorService,
              private dialogService: DialogService) {
  }

  ngOnInit() {
    this.store.dispatch(new GetReviewNotesListAction());
    this.store.dispatch(new ClearReviewNotesAction());
    this.reviewNotes$ = this.store.pipe(select(getReviewNotesList));
    this.status$ = this.store.pipe(select(getReviewNotesListStatus));
    this._removeSubscription = this.store.pipe(select(getRemoveReviewNotesStatus), filter(s => s.error !== null))
      .subscribe((status: ApiRequestStatus) => this.errorService.showErrorDialog(status.error));
  }

  ngOnDestroy() {
    this._removeSubscription.unsubscribe();
  }

  confirmRemoveReviewNotes(reviewNotes: ReviewNotes) {
    const config = {
      message: this.translate.instant('rcc.are_you_sure_you_want_to_remove_review_notes', {
        name: reviewNotes.name,
      }),
      title: this.translate.instant('rcc.confirmation'),
      ok: this.translate.instant('rcc.yes'),
      cancel: this.translate.instant('rcc.no'),
    };
    this.dialogService.openConfirm(config).afterClosed().subscribe((accept: boolean) => {
      if (accept) {
        this.store.dispatch(new RemoveReviewNotesAction(reviewNotes));
      }
    });
  }
}
