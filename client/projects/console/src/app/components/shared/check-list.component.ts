import { ChangeDetectionStrategy, Component, Input, ViewChild } from '@angular/core';
import { ControlValueAccessor, FormControl } from '@angular/forms';
import { MatSelectionList, MatSelectionListChange } from '@angular/material/list';
import { CheckListItem } from '../../interfaces';
import { AbstractControlValueAccessor, makeNgModelProvider } from '../../util';

@Component({
  selector: 'rcc-check-list',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'check-list.component.html',
  providers: [makeNgModelProvider(CheckListComponent)],
})
export class CheckListComponent extends AbstractControlValueAccessor implements ControlValueAccessor {
  @ViewChild(MatSelectionList, { static: true }) selectionList: MatSelectionList;
  formControl = new FormControl([]);

  @Input() options: CheckListItem[] = [];

  get allChecked() {
    return this.value?.length === this.options.length;
  }

  get allUnchecked() {
    return this.value?.length === 0;
  }

  writeValue(value: any) {
    super.writeValue(value);
    this.formControl.setValue(value, { emitEvent: false });
  }

  private setValue(value: any[]){
    this.value = value;
    this.onTouched();
  }

  selectionChange($event: MatSelectionListChange) {
    this.setValue($event.source._value as any[]);
  }

  selectAll() {
    this.selectionList.selectAll();
    this.setValue(this.selectionList._value as any[]);
  }

  deselectAll() {
    this.selectionList.deselectAll();
    this.setValue(this.selectionList._value as any[]);
  }
}
