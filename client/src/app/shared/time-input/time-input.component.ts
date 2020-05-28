import { BooleanInput, coerceBooleanProperty } from '@angular/cdk/coercion';
import {
  BACKSPACE,
  DELETE,
  DOWN_ARROW,
  EIGHT,
  FIVE,
  FOUR,
  LEFT_ARROW,
  NINE,
  NUMPAD_EIGHT,
  NUMPAD_FIVE,
  NUMPAD_FOUR,
  NUMPAD_NINE,
  NUMPAD_ONE,
  NUMPAD_SEVEN,
  NUMPAD_SIX,
  NUMPAD_THREE,
  NUMPAD_TWO,
  NUMPAD_ZERO,
  ONE,
  RIGHT_ARROW,
  SEVEN,
  SIX,
  TAB,
  THREE,
  TWO,
  UP_ARROW,
  ZERO,
} from '@angular/cdk/keycodes';
import {
  Attribute,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  DoCheck,
  ElementRef,
  Input,
  OnChanges,
  OnDestroy,
  OnInit,
  Optional,
  Self,
  SimpleChanges,
} from '@angular/core';
import { ControlValueAccessor, FormBuilder, FormGroup, FormGroupDirective, NgControl, NgForm, Validators } from '@angular/forms';
import {
  CanDisable,
  CanDisableCtor,
  CanUpdateErrorState,
  CanUpdateErrorStateCtor,
  ErrorStateMatcher,
  HasTabIndex,
  HasTabIndexCtor,
  mixinDisabled,
  mixinErrorState,
  mixinTabIndex,
} from '@angular/material/core';
import { MatFormFieldControl } from '@angular/material/form-field';
import { TranslateService } from '@ngx-translate/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

let nextUniqueId = 0;
const NUMBER_KEYCODES = [ZERO, ONE, TWO, THREE, FOUR, FIVE, SIX, SEVEN, EIGHT, NINE,
  NUMPAD_ZERO, NUMPAD_ONE, NUMPAD_TWO, NUMPAD_THREE, NUMPAD_FOUR, NUMPAD_FIVE, NUMPAD_SIX, NUMPAD_SEVEN, NUMPAD_EIGHT, NUMPAD_NINE];

class TimeInputMixinBase {
  constructor(public _elementRef: ElementRef,
              public _defaultErrorStateMatcher: ErrorStateMatcher,
              public _parentForm: NgForm,
              public _parentFormGroup: FormGroupDirective,
              public ngControl: NgControl) {
  }
}

const _TimeInputMixinBase:
  CanDisableCtor &
  HasTabIndexCtor &
  CanUpdateErrorStateCtor &
  typeof TimeInputMixinBase = mixinTabIndex(mixinDisabled(mixinErrorState(TimeInputMixinBase)));


@Component({
  selector: 'oca-time-input',
  templateUrl: './time-input.component.html',
  styleUrls: ['./time-input.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  inputs: ['disabled', 'tabIndex'],
  host: {
    '[attr.id]': 'id',
    '[attr.tabindex]': 'tabIndex',
    '[attr.aria-required]': 'required.toString()',
    '[attr.aria-disabled]': 'disabled.toString()',
    '[attr.aria-invalid]': 'errorState',
    '[attr.aria-describedby]': '_ariaDescribedby || null',
  },
  providers: [
    { provide: MatFormFieldControl, useExisting: TimeInputComponent },
  ],
})
export class TimeInputComponent extends _TimeInputMixinBase implements OnInit, OnChanges, DoCheck, OnDestroy, ControlValueAccessor,
  CanDisable, HasTabIndex, MatFormFieldControl<Date>, CanUpdateErrorState {

  static ngAcceptInputType_disabled: BooleanInput;
  static ngAcceptInputType_readonly: BooleanInput;
  static ngAcceptInputType_required: BooleanInput;

  partsGroup: FormGroup;
  error$: Observable<string | null>;
  disabled = false;
  focusedInputs = new Set<HTMLInputElement>();
  /** A name for this control that can be used by `mat-form-field`. */
  readonly controlType = 'time-input';
  focused = false;
  /** The aria-describedby attribute on the select for improved a11y. */
  _ariaDescribedby: string;
  /** Unique id for this input. */
  private _uid = `mat-select-${nextUniqueId++}`;

  constructor(elementRef: ElementRef,
              formBuilder: FormBuilder,
              _defaultErrorStateMatcher: ErrorStateMatcher,
              @Optional() _parentForm: NgForm,
              @Optional() _parentFormGroup: FormGroupDirective,
              @Attribute('tabindex') tabIndex: string,
              @Self() @Optional() public ngControl: NgControl,
              private translate: TranslateService,
              private changeDetectorRef: ChangeDetectorRef) {
    super(elementRef, _defaultErrorStateMatcher, _parentForm, _parentFormGroup, ngControl);
    this.partsGroup = formBuilder.group({
      hour: [null, [Validators.required, Validators.minLength(1), Validators.min(0), Validators.max(23)]],
      minute: [null, [Validators.required, Validators.minLength(1), Validators.min(0), Validators.max(59)]],
    });
    if (this.ngControl) {
      // Note: we provide the value accessor through here, instead of
      // the `providers` to avoid running into a circular import.
      this.ngControl.valueAccessor = this;
    }
    this.tabIndex = parseInt(tabIndex, 10) || 0;
    // Force setter to be called in case id was not specified.
    this.id = this.id;
    this.error$ = this.partsGroup.statusChanges.pipe(map(() => {
      if (this.partsGroup.controls.hour.errors?.max) {
        return this.translate.instant('oca.hours_cannot_exceed', { hours: 23 });
      } else if (this.partsGroup.controls.minute.errors?.max) {
        return this.translate.instant('oca.minutes_cannot_exceed', { minutes: 59 });
      }
      return null;
    }));
  }

  get shouldLabelFloat() {
    // return this.focused && !this.empty;
    return true;
  };


  /** Whether filling out the time is required in the form. */
  private _required = false;

  /** Whether the component is required. */
  @Input()
  get required(): boolean {
    return this._required;
  }

  set required(value: boolean) {
    this._required = coerceBooleanProperty(value);
    this.stateChanges.next();
  }

  @Input()
  get value(): Date | null {
    if (this.partsGroup.valid) {
      const { hour, minute } = this.partsGroup.value;
      const value = new Date(0);
      value.setHours(parseInt(hour, 10));
      value.setMinutes(parseInt(minute, 10));
      return value;
    }
    return null;
  }

  set value(value: Date | null) {
    const hour = this._getTextValue(value?.getHours());
    const minute = this._getTextValue(value?.getMinutes());
    this.partsGroup.setValue({ hour, minute });
    this.stateChanges.next();
  }

  private _id: string;

  /** Unique id of the element. */
  @Input()
  get id(): string {
    return this._id;
  }

  set id(value: string) {
    this._id = value || this._uid;
    this.stateChanges.next();
  }

  /** The placeholder displayed in the trigger of the select. */
  private _placeholder: string;

  /** Placeholder to be shown if no value has been selected. */
  @Input()
  get placeholder(): string {
    return this._placeholder;
  }

  set placeholder(value: string) {
    this._placeholder = value;
    this.stateChanges.next();
  }

  get empty() {
    return this.value === null;
  }

  ngOnInit() {
    this.stateChanges.next();
  }

  ngDoCheck() {
    if (this.ngControl) {
      this.updateErrorState();
    }
  }

  ngOnChanges(changes: SimpleChanges) {
    // Updating the disabled state is handled by `mixinDisabled`, but we need to additionally let
    // the parent form field know to run change detection when the disabled state changes.
    if (changes.disabled) {
      this.stateChanges.next();
    }
  }

  ngOnDestroy() {
    this.stateChanges.complete();
  }

  registerOnChange(fn: any): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }

  /**
   * Disables the inputs. Part of the ControlValueAccessor interface required to integrate with Angular's core forms API.
   *
   * @param isDisabled Sets whether the component is disabled.
   */
  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
    this.disabled ? this.partsGroup.disable() : this.partsGroup.enable();
    this.stateChanges.next();
  }

  writeValue(date: Date | null): void {
    if (date?.getTime() !== this.value?.getTime()) {
      this.value = date;
      this.stateChanges.next();
      this.changeDetectorRef.markForCheck();
    }
  }

  onContainerClick(event: MouseEvent): void {
  }

  /**
   * Implemented as part of MatFormFieldControl.
   */
  setDescribedByIds(ids: string[]): void {
    this._ariaDescribedby = ids.join(' ');
  }

  _onFocus($event: Event) {
    const target = $event.target;
    if (!this.disabled && target instanceof HTMLInputElement) {
      this.focused = true;
      this.focusedInputs.add(target);
      this.stateChanges.next();
    }
  }

  _onBlur($event: Event) {
    const target = $event.target;
    if (!this.disabled && target instanceof HTMLInputElement) {
      this.focusedInputs.delete(target);
      if (this.focusedInputs.size === 0) {
        this.onTouched();
        this.focused = false;
        this.changeDetectorRef.markForCheck();
        this.stateChanges.next();
      }
    }
  }

  _handleKeydown($event: KeyboardEvent, element: 'hour' | 'minute') {
    if (!this.disabled) {
      const keyCode = $event.keyCode;
      if (keyCode === UP_ARROW) {
        $event.preventDefault();
        this.incrementValue(element);
      } else if (keyCode === DOWN_ARROW) {
        $event.preventDefault();
        this.decrementValue(element);
      } else if ([BACKSPACE, DELETE, TAB, LEFT_ARROW, RIGHT_ARROW].includes(keyCode)) {
        // ok
      } else {
        if (!NUMBER_KEYCODES.includes(keyCode)) {
          // Don't allow entering non-number characters
          $event.preventDefault();
        }
      }
    }
  }

  _handleInput() {
    this.onChange(this.value);
  }

  private incrementValue(element: 'hour' | 'minute') {
    if (element === 'hour') {
      let hour = parseInt(this.partsGroup.value.hour);
      if (hour === null || hour >= 23) {
        hour = 0;
      } else {
        hour++;
      }
      this.partsGroup.patchValue({ hour: this._getTextValue(hour) });
    } else if (element === 'minute') {
      let minute = parseInt(this.partsGroup.value.minute);
      if (minute === null || minute >= 59) {
        minute = 0;
      } else {
        minute++;
      }
      this.partsGroup.patchValue({ minute: this._getTextValue(minute) });
    }
    this._handleInput();
  }

  private decrementValue(element: 'hour' | 'minute') {
    if (element === 'hour') {
      let hour = parseInt(this.partsGroup.value.hour);
      if (hour && hour <= 23) {
        hour--;
      } else {
        hour = 23;
      }
      this.partsGroup.patchValue({ hour: this._getTextValue(hour) });
    } else if (element === 'minute') {
      let minute = parseInt(this.partsGroup.value.minute);
      if (minute && minute <= 59) {
        minute--;
      } else {
        minute = 59;
      }
      this.partsGroup.patchValue({ minute: this._getTextValue(minute) });
    }
    this._handleInput();
  }

  private _getTextValue(value?: number): string | null {
    return value?.toString().padStart(2, '0') ?? null;
  }

  private onChange = (_: any) => {
  };

  private onTouched = () => {
  };
}
