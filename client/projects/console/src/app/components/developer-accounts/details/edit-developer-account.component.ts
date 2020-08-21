import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, ViewEncapsulation } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { filterNull } from '../../../ngrx';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { UpdateDeveloperAccountAction } from '../../../actions';
import { getDeveloperAccount, getUpdateDeveloperAccountStatus } from '../../../console.state';
import { DeveloperAccount } from '../../../interfaces';

@Component({
  selector: 'rcc-edit-developer-account',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  template: `
    <rcc-edit-developer-account-form
      [developerAccount]="developerAccount$ | async"
      [status]="status$ | async"
      (save)="save($event)"></rcc-edit-developer-account-form>`,
})
export class EditDeveloperAccountComponent implements OnInit, OnDestroy {
  developerAccount$: Observable<DeveloperAccount>;
  status$: Observable<ApiRequestStatus>;
  private sub: Subscription;

  constructor(private store: Store,
              private route: ActivatedRoute,
              private router: Router) {
  }

  ngOnInit() {
    this.developerAccount$ = this.store.pipe(select(getDeveloperAccount), filterNull());
    this.status$ = this.store.pipe(select(getUpdateDeveloperAccountStatus));
    this.sub = this.status$.pipe(filter(s => s.success))
      .subscribe(ignored => this.router.navigate([ '../../' ], { relativeTo: this.route }));
  }

  ngOnDestroy() {
    this.sub.unsubscribe();
  }

  save(developerAccount: DeveloperAccount) {
    this.store.dispatch(new UpdateDeveloperAccountAction(developerAccount));
  }
}
