import { Injectable, OnDestroy } from '@angular/core';
import { MatStepperIntl } from '@angular/material/stepper';
import { TranslateService } from '@ngx-translate/core';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Injectable({ providedIn: 'root' })
export class MatStepperIntlImpl extends MatStepperIntl implements OnDestroy {
  private destroyed$ = new Subject();

  constructor(private translate: TranslateService) {
    super();
    this.translate.onLangChange.pipe(takeUntil(this.destroyed$)).subscribe(() => this.init());
    this.init();
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  private init() {
    this.translate.get('oca.Optional').pipe(takeUntil(this.destroyed$)).subscribe(label => {
      this.optionalLabel = label;
      this.changes.next();
    });
  }
}
