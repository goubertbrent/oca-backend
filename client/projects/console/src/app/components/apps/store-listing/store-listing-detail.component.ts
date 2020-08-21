import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { filterNull } from '../../../ngrx';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import * as actions from '../../../actions/index';
import { App, Contact, DeveloperAccount, ReviewNotes } from '../../../interfaces';
import * as states from '../../../console.state';
import { ConsoleState } from '../../../reducers';

@Component({
  selector: 'rcc-store-listing-detail',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <rcc-store-listing-detail-form
      [app]="app$ | async"
      [developerAccounts]="developerAccounts$ | async"
      [reviewNotes]="reviewNotes$ | async"
      [contacts]="contacts$ | async"
      [updateAppStatus]="updateAppStatus$ | async"
      (save)="onSave($event)">
    </rcc-store-listing-detail-form>`,
})
export class StoreListingDetailComponent implements OnInit {
  app$: Observable<App>;
  reviewNotes$: Observable<ReviewNotes[]>;
  updateAppStatus$: Observable<ApiRequestStatus>;
  developerAccounts$: Observable<DeveloperAccount[]>;
  contacts$: Observable<Contact[]>;

  constructor(private store: Store) {
  }

  ngOnInit() {
    this.app$ = this.store.select(states.getApp).pipe(filterNull());
    this.reviewNotes$ = this.store.select(states.getReviewNotesList);
    this.updateAppStatus$ = this.store.select(states.updateAppStatus);
    this.developerAccounts$ = this.store.select(states.getDeveloperAccounts);
    this.contacts$ = this.store.select(states.getContacts);
    this.store.dispatch(new actions.InitStoreListingAction());
    this.store.dispatch(new actions.GetReviewNotesListAction());
    this.store.dispatch(new actions.GetDeveloperAccountsAction());
    this.store.dispatch(new actions.GetContactsAction());
  }

  onSave(app: App) {
    this.store.dispatch(new actions.UpdateAppAction(app));
  }
}
