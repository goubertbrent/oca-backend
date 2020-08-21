import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, ViewEncapsulation } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable, Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { DialogService } from '../../../../framework/client/dialog';
import { ApiRequestStatus } from '../../../../framework/client/rpc';
import { GetDeveloperAccountsAction, RemoveDeveloperAccountAction } from '../../actions';
import { getDeveloperAccounts, getDeveloperAccountsStatus, getRemoveDeveloperAccountStatus } from '../../console.state';
import { DeveloperAccount } from '../../interfaces';
import { ApiErrorService } from '../../services';

@Component({
  selector: 'rcc-developer-accounts',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.Emulated,
  templateUrl: 'developer-accounts.component.html',
  styles: [`.developer-card {
    width: 250px;
    margin: 16px;
    display: inline-block;
  }`],
})
export class DeveloperAccountsComponent implements OnInit, OnDestroy {
  developerAccounts$: Observable<DeveloperAccount[]>;
  status$: Observable<ApiRequestStatus>;
  private sub: Subscription;

  constructor(private store: Store,
              private translate: TranslateService,
              private dialogService: DialogService,
              private errorService: ApiErrorService) {
  }

  ngOnInit() {
    this.developerAccounts$ = this.store.pipe(select(getDeveloperAccounts));
    this.status$ = this.store.pipe(select(getDeveloperAccountsStatus));
    this.store.dispatch(new GetDeveloperAccountsAction());
    this.sub = this.store.pipe(select(getRemoveDeveloperAccountStatus), filter(s => s.error !== null))
      .subscribe((status: ApiRequestStatus) => this.errorService.showErrorDialog(status.error));
  }

  ngOnDestroy() {
    this.sub.unsubscribe();
  }

  confirmRemove(developerAccount: DeveloperAccount) {
    const config = {
      message: this.translate.instant('rcc.are_you_sure_you_want_to_remove_developer_account'),
      title: this.translate.instant('rcc.confirmation'),
      ok: this.translate.instant('rcc.yes'),
      cancel: this.translate.instant('rcc.no'),
    };
    const sub = this.dialogService.openConfirm(config).afterClosed().subscribe((accept: boolean) => {
      if (accept) {
        this.store.dispatch(new RemoveDeveloperAccountAction(developerAccount));
      }
      sub.unsubscribe();
    });
  }
}
