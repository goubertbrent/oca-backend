import { Injectable, OnDestroy } from '@angular/core';
import { MatStepperIntl } from '@angular/material/stepper';
import { TranslateService } from '@ngx-translate/core';
import { Subscription } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class MatStepperIntlImpl extends MatStepperIntl implements OnDestroy {
  private onLangChange: Subscription;

  constructor(private translate: TranslateService) {
    super();
    this.onLangChange = this.translate.onLangChange.subscribe(() => this.init());
    this.init();
  }

  private async init() {
    this.optionalLabel = await this.translate.get('oca.optional').toPromise();
    this.changes.next();
  }

  ngOnDestroy() {
    this.onLangChange.unsubscribe();
  }
}
