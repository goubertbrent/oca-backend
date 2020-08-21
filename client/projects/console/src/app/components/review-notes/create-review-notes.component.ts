import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { ApiRequestStatus } from '../../../../framework/client/rpc';
import { ClearReviewNotesAction, CreateReviewNotesAction } from '../../actions';
import { getCreateReviewNotesStatus } from '../../console.state';
import { ReviewNotes } from '../../interfaces';

@Component({
  selector: 'rcc-create-review-notes',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <rcc-edit-review-notes-form
      [reviewNotes]="reviewNotes"
      [status]="status$ | async"
      (save)="onSave($event)"></rcc-edit-review-notes-form>`,
})
export class CreateReviewNotesComponent implements OnInit, OnDestroy {
  reviewNotes: ReviewNotes;
  status$: Observable<ApiRequestStatus>;

  _statusSubscription: Subscription;

  constructor(private store: Store,
              private route: ActivatedRoute,
              private router: Router) {
  }

  ngOnInit() {
    this.store.dispatch(new ClearReviewNotesAction());
    this.status$ = this.store.select(getCreateReviewNotesStatus);
    this.reviewNotes = {
      name: '',
      first_name: '',
      last_name: '',
      phone_number: '',
      demo_user: '',
      demo_password: '',
      email_address: '',
      notes: '',
    };
    this._statusSubscription = this.status$.pipe(filter(s => s.success))
      .subscribe(() => this.router.navigate(['..'], { relativeTo: this.route }));
  }

  ngOnDestroy() {
    this._statusSubscription.unsubscribe();
  }

  onSave(reviewNotes: ReviewNotes) {
    this.store.dispatch(new CreateReviewNotesAction({ ...reviewNotes }));
  }

}
