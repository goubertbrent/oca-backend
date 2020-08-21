import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { ApiRequestStatus } from '../../../../framework/client/rpc';
import { ClearContactAction, CreateContactAction } from '../../actions';
import { getCreateContactStatus } from '../../console.state';
import { Contact } from '../../interfaces';

@Component({
  selector: 'rcc-create-contact',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <rcc-edit-contact-form
      [contact]="contact"
      [status]="status$ | async"
      (save)="create($event)"></rcc-edit-contact-form>`,
})
export class CreateContactComponent implements OnInit, OnDestroy {
  contact: Contact;
  status$: Observable<ApiRequestStatus>;

  private _statusSubscription: Subscription;

  constructor(private store: Store,
              private route: ActivatedRoute,
              private router: Router) {
  }

  ngOnInit() {
    this.status$ = this.store.select(getCreateContactStatus);
    this.store.dispatch(new ClearContactAction());
    this.contact = {
      first_name: '',
      last_name: '',
      address_line_1: '',
      postal_code: '',
      city: '',
      country: '',
      email: '',
      phone_number: '',
      support_email: '',
    };
    this._statusSubscription = this.status$.pipe(filter(s => s.success))
      .subscribe(() => this.router.navigate(['../'], { relativeTo: this.route }));
  }

  ngOnDestroy() {
    this._statusSubscription.unsubscribe();
  }

  create(contact: Contact) {
    this.store.dispatch(new CreateContactAction({ ...contact }));
  }

}
