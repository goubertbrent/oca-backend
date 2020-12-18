import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  forwardRef,
  Input,
  OnChanges,
  OnDestroy,
  SimpleChanges,
} from '@angular/core';
import { ControlValueAccessor, FormBuilder, FormGroup, NG_VALUE_ACCESSOR } from '@angular/forms';
import { IFormBuilder, IFormGroup } from '@rxweb/types';
import { Subject } from 'rxjs';
import { debounceTime, skip, takeUntil } from 'rxjs/operators';
import { Value } from '../../interfaces/forms';
import { TOPDeskCategory, TOPDeskSubCategory } from '../integrations';

interface CategoryMapping {
  [ key: string ]: string | null;
}

@Component({
  selector: 'oca-topdesk-category-mapping',
  templateUrl: './topdesk-category-mapping.component.html',
  styleUrls: ['./topdesk-category-mapping.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [{
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => TOPDeskCategoryMappingComponent),
    multi: true,
  }],
})
export class TOPDeskCategoryMappingComponent implements OnChanges, OnDestroy, ControlValueAccessor {
  @Input() categories: TOPDeskCategory[] | null = null;
  @Input() subcategories: TOPDeskSubCategory[] | null = null;
  @Input() choices: Value[] = [];

  categoryForm = new FormGroup({}) as IFormGroup<CategoryMapping>;

  private categoryMapping: CategoryMapping = {};
  private onChange: (value: any) => {};
  private onTouched: () => {};
  private formBuilder: IFormBuilder;
  private destroyed$ = new Subject();

  constructor(private changeDetectorRef: ChangeDetectorRef,
              formBuilder: FormBuilder) {
    this.formBuilder = formBuilder;
    this.categoryForm.valueChanges.pipe(
      debounceTime(500),
      skip(1),
      takeUntil(this.destroyed$)
    ).subscribe((value: CategoryMapping) => {
      const valueWithoutNulls = Object.fromEntries(Object.entries(value).filter(([choiceValue, categoryId]) => categoryId !== null));
      this.onChange(valueWithoutNulls);
    });
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes.choices) {
      this.buildForm();
    }
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  registerOnChange(fn: any): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    if (isDisabled) {
      this.categoryForm.disable();
    } else {
      this.categoryForm.enable();
    }
  }

  writeValue(obj: any): void {
    this.categoryMapping = obj;
    this.categoryForm.patchValue(obj, { emitEvent: false });
    this.changeDetectorRef.markForCheck();
  }

  private buildForm() {
    for (const controlName of Object.keys(this.categoryForm.controls)) {
      this.categoryForm.removeControl(controlName);
    }
    for (const choice of this.choices) {
      this.categoryForm.addControl(choice.value, this.formBuilder.control(null));
    }
    this.categoryForm.patchValue(this.categoryMapping, { emitEvent: false });
  }

}
