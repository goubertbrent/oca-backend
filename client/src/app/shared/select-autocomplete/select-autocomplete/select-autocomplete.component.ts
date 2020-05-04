import { ChangeDetectionStrategy, ChangeDetectorRef, Component, forwardRef, Input, OnDestroy, OnInit } from '@angular/core';
import { ControlValueAccessor, FormControl, NG_VALUE_ACCESSOR } from '@angular/forms';
import { MatOption } from '@angular/material/core';
import { MatSelectChange } from '@angular/material/select';
import { Subject } from 'rxjs';
import { FormControlTyped } from '../../util/forms';

type SelectValueType = string | number;

export interface SelectAutocompleteOption {
  label: string;
  value: SelectValueType;
  disabled?: boolean;
}

const sortOptions = (first: SelectAutocompleteOption, second: SelectAutocompleteOption): number => first.label.localeCompare(second.label);

@Component({
  selector: 'oca-select-autocomplete',
  templateUrl: './select-autocomplete.component.html',
  styleUrls: ['./select-autocomplete.component.scss'],
  changeDetection: ChangeDetectionStrategy.Default,
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

  constructor(private changeDetectorRef: ChangeDetectorRef) {
  }

  @Input() label: string;
  @Input() searchPlaceholder: string;
  @Input() placeholder: string;
  @Input() disabled = false;
  @Input() required = false;
  @Input() errorMsg: string;
  @Input() selectedOptions: SelectValueType | SelectValueType[];
  @Input() multiple = true;
  @Input() maxOptions = 20;

  formControl: FormControlTyped<null | SelectValueType | SelectValueType[]> = new FormControl();

  filteredOptions$ = new Subject<SelectAutocompleteOption[]>();
  filterFormControl: FormControlTyped<string> = new FormControl();

  @Input() set options(value: SelectAutocompleteOption[] | null) {
    this._options = value ?? [];
    this.setOptions();
  }

  private destroyed$ = new Subject();

  private _options: SelectAutocompleteOption[] = [];

  registerOnTouched(fn: any): void {
    this.onTouched = fn;
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

  selectClosed() {
    this.filterFormControl.reset();
  }

  trackByFn(index: number, item: SelectAutocompleteOption) {
    return item.value;
  }

  registerOnChange(fn: any): void {
    this.onChange = fn;
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
    this.formControl.markAsDirty();
    this.formControl.markAsTouched();
    this.changeDetectorRef.markForCheck();
  }

  private onChange = (_: any) => {
  };

  private onTouched = () => {
  };

  /**
   * The options are already sorted in setOptions, but we need to overwrite the comparator to avoid mat-select sorting it by value
   */
  sortOptionsComparator(first: MatOption, second: MatOption, options: MatOption[]): number {
    return 0;
  }

  private setOptions() {
    const lowerValue = this.filterFormControl.value?.toLowerCase().trim();
    const filtered: SelectAutocompleteOption[] = [];
    const value = this.formControl.value;
    let selectedValues: SelectValueType[] = [];
    if (Array.isArray(value)) {
      selectedValues = value;
    } else {
      if (value != null) {
        selectedValues = [value];
      }
    }
    const selected: SelectAutocompleteOption[] = [];
    for (const option of this._options) {
      // must always include selected options, otherwise the value could be incorrect
      if (selectedValues.includes(option.value)) {
        selected.push(option);
      } else if (filtered.length < this.maxOptions && option.label.toLowerCase().includes(lowerValue)) {
        filtered.push(option);
      }
    }
    this.filteredOptions$.next(filtered.sort(sortOptions).concat(selected.sort(sortOptions)));
  }
}
