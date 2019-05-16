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
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import { TranslateService } from '@ngx-translate/core';
import { Observable, Subject, Subscription } from 'rxjs';
import { withLatestFrom } from 'rxjs/operators';
import { NextAction, UINextAction, Value } from '../../interfaces/forms';
import { UploadImageDialogComponent, UploadImageDialogConfig } from '../upload-image-dialog/upload-image-dialog.component';

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
  @ViewChildren('labelInput') labelInputElements: QueryList<ElementRef<HTMLInputElement>>;
  @ViewChild('newInput') newInput: ElementRef<HTMLInputElement>;

  @Input() formId: number;
  @Input() readonlyIds: boolean;
  @Input() name: string;
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

  constructor(private _changeDetectorRef: ChangeDetectorRef,
              private _translate: TranslateService,
              private _matDialog: MatDialog) {
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
    this.valueChanges$ = this.labelInputElements.changes;
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
    const original = this.values[ index ];
    this.values[ index ] = { ...original, value: original.value };
    this.onChange(this.values);
  }

  labelUpdated(value: string, index: number) {
    const original = this.values[ index ];
    this.values[ index ] = { ...original, label: value, value: this.readonlyIds ? original.value : value };
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
    const element = this.labelInputElements.toArray()[ index + 1 ];
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

  editImage(value: Value, index: number) {
    const config: MatDialogConfig<UploadImageDialogConfig> = {
      data: {
        formId: this.formId,
        cropOptions: { aspectRatio: undefined },
        croppedCanvasOptions: { maxWidth: 720 },
        title: this._translate.instant('oca.insert_image'),
      },
    };
    this._matDialog.open(UploadImageDialogComponent, config).afterClosed().subscribe((result?: string) => {
      if (result) {
        this.values[ index ] = { ...value, image_url: result };
        this.onChange(this.values);
      }
    });
  }

  removeImage(value: Value, index: number) {
    this.values[ index ] = { ...value, image_url: null };
    this.onChange(this.values);
  }
}
