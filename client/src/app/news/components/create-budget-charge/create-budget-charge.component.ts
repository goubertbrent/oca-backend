import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';
import { Actions, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { map } from 'rxjs/operators';
import { AddBudgetAction, SharedActionTypes } from '../../../shared/shared.actions';
import { getBudget } from '../../../shared/shared.state';

@Component({
  templateUrl: './create-budget-charge.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreateBudgetChargeComponent implements OnInit, OnDestroy {
  formGroup = new FormGroup({
    confirm: new FormControl(false),
    vat: new FormControl('', Validators.required),
  });
  isLoading$: Observable<boolean>;
  private sub: Subscription;

  constructor(private dialogRef: MatDialogRef<CreateBudgetChargeComponent>,
              private store: Store,
              private actions$: Actions) {
  }

  ngOnInit() {
    this.isLoading$ = this.store.pipe(select(getBudget), map(r => r.loading));
    this.sub = this.actions$.pipe(ofType(SharedActionTypes.ADD_BUDGET_COMPLETE)).subscribe(() => {
      this.dialogRef.close(this.formGroup.value);
    });
  }

  ngOnDestroy() {
    this.sub.unsubscribe();
  }

  confirmCharge() {
    this.store.dispatch(new AddBudgetAction({vat: this.formGroup.value.vat}));
  }
}
