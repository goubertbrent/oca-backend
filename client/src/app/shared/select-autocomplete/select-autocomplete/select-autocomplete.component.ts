import { ChangeDetectionStrategy, ChangeDetectorRef, Component, forwardRef, Input, OnDestroy, OnInit } from '@angular/core';
import { ControlValueAccessor, FormControl, NG_VALUE_ACCESSOR } from '@angular/forms';
import { MatOption } from '@angular/material/core';
import { MatSelectChange } from '@angular/material/select';
import { Subject } from 'rxjs';
import { debounceTime } from 'rxjs/operators';
import { FormControlTyped } from '../../util/forms';

type SelectValueType = string | number;

export interface SelectAutocompleteOption {
  label: string;
  value: SelectValueType;
  disabled?: boolean;
}

interface SelectAutocompleteOptionInternal extends SelectAutocompleteOption {
  sortLabel: string;
}

function sortOptions(first: SelectAutocompleteOptionInternal, second: SelectAutocompleteOptionInternal): number {
  return first.sortLabel.localeCompare(second.sortLabel);
}

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
  @Input() hint: string;
  /** Maximum amount of options that can be selected */
  @Input() max = 50;
  @Input() disabled = false;
  @Input() required = false;
  @Input() errorMsg: string;
  @Input() selectedOptions: SelectValueType | SelectValueType[];
  @Input() multiple = true;
  @Input() maxDisplayedOptions = 50;

  formControl: FormControlTyped<null | SelectValueType | SelectValueType[]> = new FormControl();

  filteredOptions$ = new Subject<SelectAutocompleteOptionInternal[]>();
  filterFormControl: FormControlTyped<string> = new FormControl();
  private destroyed$ = new Subject();

  private _options: SelectAutocompleteOptionInternal[] = [];

  @Input() set options(value: SelectAutocompleteOption[] | null) {
    this._options = (value ?? []).map((o => ({ ...o, sortLabel: o.label.toLowerCase() })));
    this.setOptions();
  }

  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }

  ngOnInit() {
    this.filterFormControl.valueChanges.pipe(debounceTime(200)).subscribe(() => this.setOptions());
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  onSelectionChange(val: MatSelectChange) {
    this.formControl.setValue(val.value);
    if (this.formControl.valid) {
      this.onChange(val.value);
    }
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
    const lowerValue = this.filterFormControl.value?.toLowerCase().trim() ?? '';
    const filtered = [];
    const value = this.formControl.value;
    let selectedValues: SelectValueType[] = [];
    if (Array.isArray(value)) {
      selectedValues = value;
    } else {
      if (value != null) {
        selectedValues = [value];
      }
    }
    const selected = [];
    for (const option of this._options) {
      // must always include selected options, otherwise the value could be incorrect
      if (selectedValues.includes(option.value)) {
        selected.push(option);
      } else if (lowerValue && option.sortLabel.includes(lowerValue)) {
        filtered.push(option);
      }
    }
    const ls = filtered
      .sort((first, second) => {
        let cmp = sortOptions(first, second);
        if (first.sortLabel.startsWith(lowerValue)) {
          const lenDiff = first.sortLabel.length - second.sortLabel.length;
          if (lenDiff > 1) {
            cmp = 1;
          } else if (lenDiff < 0) {
            cmp = -1;
          } else {
            cmp = 0;
          }
        }
        return cmp;
      });
    this.filteredOptions$.next(ls
      .slice(0, this.maxDisplayedOptions)
      .concat(selected.sort(sortOptions)));
  }
}
