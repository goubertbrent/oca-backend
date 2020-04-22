import { ChangeDetectionStrategy, ChangeDetectorRef, Component, forwardRef, Input, OnDestroy, OnInit } from '@angular/core';
import { ControlValueAccessor, FormControl, NG_VALUE_ACCESSOR } from '@angular/forms';
import { MatSelectChange } from '@angular/material/select';
import { Subject } from 'rxjs';

type SelectValueType = string | number;

export interface SelectAutocompleteOption {
  label: string;
  value: SelectValueType;
  disabled?: boolean;
}

@Component({
  selector: 'oca-select-autocomplete',
  templateUrl: './select-autocomplete.component.html',
  styleUrls: ['./select-autocomplete.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [{
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => SelectAutocompleteComponent),
    multi: true,
  }],
})
/**
 * Basically a mat-select but with an added textfield at the top of the options.
 * Entering text in the textfield will will filter the options.
 */
export class SelectAutocompleteComponent implements OnInit, OnDestroy, ControlValueAccessor {
  @Input() label: string;
  @Input() searchPlaceholder: string;
  @Input() placeholder: string;
  @Input() disabled = false;
  @Input() required = false;
  @Input() errorMsg: string;
  @Input() selectedOptions: SelectValueType | SelectValueType[];
  @Input() multiple = true;

  filteredOptions$ = new Subject<SelectAutocompleteOption[]>();
  formControl = new FormControl();
  filterFormControl = new FormControl();
  private destroyed$ = new Subject();

  constructor(private changeDetectorRef: ChangeDetectorRef) {
  }

  private _options: SelectAutocompleteOption[] = [];

  @Input() set options(value: SelectAutocompleteOption[]) {
    this._options = value;
    this.setOptions();
  }

  ngOnInit() {
    this.filterFormControl.valueChanges.subscribe(() => this.setOptions());
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  onSelectionChange(val: MatSelectChange) {
    this.formControl.setValue(val.value);
    this.onChange(val.value);
  }

  trackByFn(index: number, item: SelectAutocompleteOption) {
    return item.value;
  }

  registerOnChange(fn: any): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
    if (isDisabled) {
      this.formControl.disable();
    } else {
      this.formControl.enable();
    }
    this.changeDetectorRef.markForCheck();
  }

  writeValue(value: SelectValueType): void {
    this.formControl.setValue(value);
    this.changeDetectorRef.markForCheck();
  }

  private onChange = (_: any) => {
  };

  private onTouched = () => {
  };

  private setOptions() {
    const lowerValue = this.filterFormControl.value?.toLowerCase().trim();
    const options = lowerValue ? this._options.filter(item => item.label.toLowerCase().includes(lowerValue)) : this._options;
    this.filteredOptions$.next(options);
  }
}
