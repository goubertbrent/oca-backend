import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { FormControl, FormGroup } from '@angular/forms';
import { select, Store } from '@ngrx/store';
import { Observable, Subject } from 'rxjs';
import { GetCirkloSettingsAction, SaveCirkloSettingsAction } from '../vouchers.actions';
import { areCirkloSettingsLoading, getCirkloSettings } from '../vouchers.selectors';

@Component({
  selector: 'oca-cirklo-settings-page',
  templateUrl: './cirklo-settings-page.component.html',
  styleUrls: ['./cirklo-settings-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CirkloSettingsPageComponent implements OnInit, OnDestroy {
  formGroup = new FormGroup({
    city_id: new FormControl(null),
    logo_url: new FormControl(null),
  });
  cirkloSettingsLoading$: Observable<boolean>;
  destroyed$ = new Subject();

  constructor(private store: Store) {
  }

  ngOnInit(): void {
    this.store.dispatch(new GetCirkloSettingsAction());
    this.cirkloSettingsLoading$ = this.store.pipe(select(areCirkloSettingsLoading));
    this.store.pipe(select(getCirkloSettings)).subscribe(settings => {
      if (settings) {
        this.formGroup.setValue(settings);
      }
    });
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  save() {
    if (this.formGroup.valid) {
      this.store.dispatch(new SaveCirkloSettingsAction(this.formGroup.value));
    }
  }

}
