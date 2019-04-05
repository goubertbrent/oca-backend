import { coerceBooleanProperty } from '@angular/cdk/coercion';
import {
  AfterViewInit,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  forwardRef,
  Input,
  OnDestroy,
  QueryList,
  ViewChild,
  ViewChildren,
} from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { TranslateService } from '@ngx-translate/core';
import { Observable, Subject, Subscription } from 'rxjs';
import { withLatestFrom } from 'rxjs/operators';
import { NextAction, NextActionSection, NextActionType, UINextAction, Value } from '../../interfaces/forms.interfaces';

@Component({
  selector: 'oca-select-input-list',
  templateUrl: './select-input-list.component.html',
  styleUrls: [ './select-input-list.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [ {
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => SelectInputListComponent),
    multi: true,
  } ],
})
export class SelectInputListComponent implements AfterViewInit, ControlValueAccessor, OnDestroy {
  @ViewChildren('valueInput') valueInputElements: QueryList<ElementRef<HTMLInputElement>>;
  @ViewChild('newInput') newInput: ElementRef<HTMLInputElement>;

  @Input()
  set multiple(value: any) {
    this._multiple = coerceBooleanProperty(value);
  }

  get multiple() {
    return this._multiple;
  }

  @Input() nextActions: UINextAction[] = [];

  set values(values: Value[]) {
    // Don't set 'changed' in case of initial value
    if (this._values) {
      this.onChange(values);
    }
    this._values = values;
  }

  get values(): Value[] {
    return this._values;
  }

  temporaryValue = '';

  private _values: Value[];
  private _multiple = false;
  private valueChanges$: Observable<QueryList<ElementRef<HTMLInputElement>>>;
  private valueFocus$ = new Subject();
  private valueFocusSubscription: Subscription = Subscription.EMPTY;
  private onChange = (_: any) => {
  }
  private onTouched = () => {
  }

  constructor(private _changeDetectorRef: ChangeDetectorRef, private _translate: TranslateService) {
  }

  registerOnChange(fn: any): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
  }

  writeValue(values?: Value[]): void {
    if (values) {
      this._values = values;
      this._changeDetectorRef.markForCheck();
    }
  }

  ngAfterViewInit(): void {
    this.valueChanges$ = this.valueInputElements.changes;
    this.valueFocusSubscription = this.valueChanges$.pipe(withLatestFrom(this.valueFocus$)).subscribe(([ queryList ]) => {
      // Timeout because for some reason it doesn't always work (e.g. when triggered from click event)
      setTimeout(() => queryList.last.nativeElement.select(), 0);
    });
  }

  ngOnDestroy(): void {
    this.valueFocusSubscription.unsubscribe();
  }

  trackValues(index: number, item: Value) {
    return index;
  }

  valueUpdated(value: string, index: number) {
    this.values[ index ] = { ...this.values[ index ], label: value, value };
    this.onChange(this.values);
  }

  actionUpdated(action: NextAction, index: number) {
    this.values[ index ] = { ...this.values[ index ], next_action: action };
    this.onChange(this.values);
  }

  removeValue(value: Value) {
    this.values = this.values.filter(v => v !== value);
  }

  selectNext(index: number) {
    const element = this.valueInputElements.toArray()[ index + 1 ];
    if (element) {
      element.nativeElement.focus();
    } else {
      this.newInput.nativeElement.focus();
    }
  }

  addChoice() {
    let value = this.temporaryValue;
    if (value) {
      this.temporaryValue = '';
    } else {
      const count = this.values.length + 1;
      value = this._translate.instant('oca.option_x', { number: count });
    }
    this.values = [ ...this.values, { value, label: value } ];
    this.valueFocus$.next();
  }

  compareAction(first: NextAction, second?: NextAction) {
    if (!second) {
      return first.type === NextActionType.NEXT;
    }
    const sameType = first.type === second.type;
    if (sameType && first.type === NextActionType.SECTION) {
      return first.section === (second as NextActionSection).section;
    }
    return sameType;
  }

  trackActions(index: number, action: NextAction) {
    return action.type === NextActionType.SECTION ? `${NextActionType.SECTION}_${action.section}` : action.type;
  }
}
