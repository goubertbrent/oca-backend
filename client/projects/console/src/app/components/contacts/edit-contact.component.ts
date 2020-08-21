import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { filterNull } from '../../ngrx';
import { ApiRequestStatus } from '../../../../framework/client/rpc';
import { GetContactAction, UpdateContactAction } from '../../actions';
import { getCurrentContact, getUpdateContactStatus } from '../../console.state';
import { Contact } from '../../interfaces';

@Component({
  selector: 'rcc-edit-contact',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <rcc-edit-contact-form [contact]="contact$ | async"
                           [status]="status$ | async"
                           (save)="save($event)"></rcc-edit-contact-form>`,
})
export class EditContactComponent implements OnInit, OnDestroy {
  contact$: Observable<Contact>;
  status$: Observable<ApiRequestStatus>;
  private sub: Subscription;

  constructor(private store: Store,
              private route: ActivatedRoute,
              private router: Router) {
  }

  ngOnInit() {
    this.contact$ = this.store.select(getCurrentContact).pipe(filterNull());
    this.status$ = this.store.select(getUpdateContactStatus);
    this.store.dispatch(new GetContactAction(this.route.snapshot.params.contactId));
    this.sub = this.status$.pipe(filter((s: ApiRequestStatus) => s.success)).subscribe(ignored => {
      this.router.navigate([ '../' ], { relativeTo: this.route });
    });
  }

  ngOnDestroy() {
    this.sub.unsubscribe();
  }

  save(contact: Contact) {
    this.store.dispatch(new UpdateContactAction({ ...contact }));
  }
}
