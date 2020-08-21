import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { CreateDefaultBrandingAction } from '../../../actions';
import { getDefaultBrandingEditStatus } from '../../../console.state';
import { CreateDefaultBrandingPayload, DEFAULT_BRANDING_TYPES } from '../../../interfaces';

@Component({
  selector: 'rcc-create-default-branding',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <rcc-app-branding
            [apps]="[]"
            [branding]="branding"
            [allowCreateDefault]="false"
            [edit]="false"
            [status]="resourceStatus$ | async"
            (save)="submit($event)"></rcc-app-branding>`,
})
export class CreateDefaultBrandingComponent implements OnInit, OnDestroy {
  branding: CreateDefaultBrandingPayload = {
    branding_type: DEFAULT_BRANDING_TYPES[ 0 ].value,
    branding: '',
    is_default: false,
    app_ids: [],
    file: null,
  };
  file: any;
  resourceStatus$: Observable<ApiRequestStatus>;
  private subscription: Subscription;

  constructor(private store: Store,
              private router: Router,
              private route: ActivatedRoute) {
  }

  public ngOnInit(): void {
    this.resourceStatus$ = this.store.select(getDefaultBrandingEditStatus);
    this.subscription = this.resourceStatus$.subscribe((status: ApiRequestStatus) => {
      if (status.success) {
        // Redirect to resources overview
        this.router.navigate([ '..' ], { relativeTo: this.route });
      }
    });
  }

  ngOnDestroy() {
    this.subscription.unsubscribe();
  }

  submit(branding: CreateDefaultBrandingPayload) {
    this.store.dispatch(new CreateDefaultBrandingAction(branding));
  }
}
