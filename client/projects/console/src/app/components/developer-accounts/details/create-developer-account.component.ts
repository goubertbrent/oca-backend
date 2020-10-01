import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { filter, withLatestFrom } from 'rxjs/operators';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { ClearDeveloperAccountAction, CreateDeveloperAccountAction } from '../../../actions';
import { getCreateDeveloperAccountStatus, getDeveloperAccount } from '../../../console.state';
import { CreateDeveloperAccountPayload, DeveloperAccount } from '../../../interfaces';

@Component({
  selector: 'rcc-create-developer-account',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <rcc-create-developer-account-form
      [status]="status$ | async"
      (create)="onCreate($event)"></rcc-create-developer-account-form>`,
})
export class CreateDeveloperAccountComponent implements OnInit, OnDestroy {
  status$: Observable<ApiRequestStatus>;
  private sub: Subscription;

  constructor(private store: Store,
              private route: ActivatedRoute,
              private router: Router) {
  }

  ngOnInit() {
    this.store.dispatch(new ClearDeveloperAccountAction());
    this.status$ = this.store.select(getCreateDeveloperAccountStatus);
    this.sub = this.status$.pipe(
      filter(s => s.success),
      withLatestFrom(this.store.select(getDeveloperAccount) as Observable<DeveloperAccount>))
      .subscribe(([ _, developerAccount ]) => this.router.navigate([ '..', developerAccount.id ], { relativeTo: this.route }),
      );
  }

  ngOnDestroy() {
    this.sub.unsubscribe();
  }

  onCreate(developerAccount: CreateDeveloperAccountPayload) {
    this.store.dispatch(new CreateDeveloperAccountAction({ ...developerAccount }));
  }

}
