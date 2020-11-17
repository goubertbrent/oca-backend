import { ChangeDetectionStrategy, Component, forwardRef, OnInit } from '@angular/core';
import { ControlValueAccessor, FormControl, NG_VALUE_ACCESSOR } from '@angular/forms';
import { Observable } from 'rxjs';
import { auditTime, map, tap } from 'rxjs/operators';
import { filterIcons, FontAwesomeIcon, iconValidator } from '../../../constants';

@Component({
  selector: 'rcc-icon-selector',
  templateUrl: './icon-selector.component.html',
  styleUrls: ['./icon-selector.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [{
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => IconSelectorComponent),
    multi: true,
  }],
})
export class IconSelectorComponent implements OnInit, ControlValueAccessor {
  filteredIcons$: Observable<FontAwesomeIcon[]>;
  internalControl = new FormControl(null, [iconValidator]);
  private onChange: (value: string | null) => void;
  private onTouched: () => void;

  ngOnInit(): void {
    this.filteredIcons$ = this.internalControl.valueChanges.pipe(
      auditTime(300),
      map(text => Array.from(filterIcons(text ?? ''))),
      tap(results => {
        if (results.length === 1) {
          this.onChange(results[ 0 ].icon);
        } else if (results.length === 0 && !this.internalControl.value) {
          this.onChange(null);
        }
      }),
    );
  }

  registerOnChange(fn: any): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    if (isDisabled) {
      this.internalControl.disable();
    } else {
      this.internalControl.enable();
    }
  }

  writeValue(obj: string | null): void {
    this.internalControl.setValue(obj, { emitEvent: false });
  }

}
