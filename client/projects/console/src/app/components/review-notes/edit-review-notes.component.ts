import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { filterNull } from '../../ngrx';
import { ApiRequestStatus } from '../../../../framework/client/rpc';
import { GetReviewNotesAction, UpdateReviewNotesAction } from '../../actions';
import { getCurrentReviewNotes, getUpdateReviewNotesStatus } from '../../console.state';
import { ReviewNotes } from '../../interfaces';

@Component({
  selector: 'rcc-edit-review-notes',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <rcc-edit-review-notes-form [reviewNotes]="reviewNotes$ | async"
                                [status]="status$ | async"
                                (save)="save($event)"></rcc-edit-review-notes-form>`,
})
export class EditReviewNotesComponent implements OnInit, OnDestroy {
  reviewNotes$: Observable<ReviewNotes>;
  status$: Observable<ApiRequestStatus>;
  private sub: Subscription;

  constructor(private store: Store,
              private route: ActivatedRoute,
              private router: Router) {
  }

  ngOnInit() {
    this.reviewNotes$ = this.store.select(getCurrentReviewNotes).pipe(filterNull());
    this.status$ = this.store.select(getUpdateReviewNotesStatus);
    this.store.dispatch(new GetReviewNotesAction(this.route.snapshot.params.reviewNotesId));
    this.sub = this.status$.pipe(filter(s => s.success)).subscribe(ignored => {
      this.router.navigate([ '../' ], { relativeTo: this.route });
    });
  }

  ngOnDestroy() {
    this.sub.unsubscribe();
  }


  save(reviewNotes: ReviewNotes) {
    this.store.dispatch(new UpdateReviewNotesAction({ ...reviewNotes }));
  }

}
