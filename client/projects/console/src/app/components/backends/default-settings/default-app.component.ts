import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Store } from '@ngrx/store';
import { Subscription } from 'rxjs';
import { SetDefaultRogerthatAppAction } from '../../../actions/backends.actions';
import { getBackendRogerthatApps } from '../../../console.state';
import { RogerthatApp } from '../../../interfaces/apps.interfaces';

@Component({
  selector: 'rcc-backend-default-app',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'default-app.component.html',
})
export class BackendDefaultAppComponent implements OnInit, OnDestroy {
  defaultApp: string;
  apps: RogerthatApp[] = [];
  private subscription: Subscription;

  constructor(private store: Store,
              private cdRef: ChangeDetectorRef,
              private route: ActivatedRoute,
              private router: Router) {
  }

  ngOnInit() {
    this.subscription = this.store.select(getBackendRogerthatApps).subscribe((apps: RogerthatApp[]) => {
      this.apps = apps;
      if (this.apps.length) {
        const app = apps.find(a => a.is_default);
        if (app) {
          this.defaultApp = app.id;
          this.cdRef.markForCheck();
        }
      }
    });
  }

  ngOnDestroy() {
    this.subscription.unsubscribe();
  }

  submit() {
    this.store.dispatch(new SetDefaultRogerthatAppAction(this.defaultApp));
    this.router.navigate([ '..' ], { relativeTo: this.route });
  }
}
