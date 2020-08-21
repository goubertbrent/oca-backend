import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, ViewEncapsulation } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable, Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { DialogService } from '../../../../framework/client/dialog';
import { ApiRequestStatus } from '../../../../framework/client/rpc';
import { GetContactsAction, RemoveContactAction } from '../../actions';
import { getContacts, getContactsStatus, getRemoveContactStatus } from '../../console.state';
import { Contact } from '../../interfaces';
import { ApiErrorService } from '../../services';

@Component({
  selector: 'rcc-contacts',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.Emulated,
  templateUrl: 'contacts.component.html',
  styles: [ `.contact-card {
    width: 250px;
    display: inline-block;
    margin: 16px;
  }

  mat-card-header {
    overflow: hidden;
  }

  .contact-card mat-card-title, .contact-card mat-card-subtitle {
    white-space: nowrap;
    overflow: hidden;
  }` ],
})
export class ContactsComponent implements OnInit, OnDestroy {
  contacts$: Observable<Contact[]>;
  status$: Observable<ApiRequestStatus>;
  private _removeContactSubscription: Subscription;

  constructor(private store: Store,
              private translate: TranslateService,
              private errorService: ApiErrorService,
              private dialogService: DialogService) {
  }

  ngOnInit() {
    this.store.dispatch(new GetContactsAction());
    this.contacts$ = this.store.pipe(select(getContacts));
    this.status$ = this.store.pipe(select(getContactsStatus));
    this._removeContactSubscription = this.store.pipe(
      select(getRemoveContactStatus),
      filter(s => s.error !== null))
      .subscribe(status => this.errorService.showErrorDialog(status.error));
  }

  ngOnDestroy() {
    this._removeContactSubscription.unsubscribe();
  }

  confirmRemoveContact(contact: Contact) {
    const config = {
      message: this.translate.instant('rcc.are_you_sure_you_want_to_remove_contact', {
        first_name: contact.first_name,
        last_name: contact.last_name,
      }),
      title: this.translate.instant('rcc.confirmation'),
      ok: this.translate.instant('rcc.yes'),
      cancel: this.translate.instant('rcc.no'),
    };
    this.dialogService.openConfirm(config).afterClosed().subscribe((accept: boolean) => {
      if (accept) {
        this.store.dispatch(new RemoveContactAction(contact));
      }
    });
  }
}
