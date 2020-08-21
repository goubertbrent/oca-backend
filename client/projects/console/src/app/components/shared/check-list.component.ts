import { ChangeDetectionStrategy, Component } from '@angular/core';
import { ControlValueAccessor } from '@angular/forms';
import { CheckListItem } from '../../interfaces';
import { AbstractControlValueAccessor, makeNgModelProvider } from '../../util';

// TODO might want to change this by MatSelectionList
@Component({
  selector: 'rcc-check-list',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'check-list.component.html',
  providers: [ makeNgModelProvider(CheckListComponent) ],
})
export class CheckListComponent extends AbstractControlValueAccessor implements ControlValueAccessor {
  get items() {
    return this.value || [];  // From AbstractControlValueAccessor
  }

  set items(items: CheckListItem[]) {
    this.value = items; // From AbstractControlValueAccessor
    this.onTouched();
  }

  get allChecked() {
    return this.items.every(i => i.checked);
  }

  get allUnchecked() {
    return this.items.every(i => !i.checked);
  }

  setAll(checked: boolean) {
    this.items = this.items.map(item => ({ ...item, checked }));
  }

  onModelChange(value: CheckListItem) {
    this.items = JSON.parse(JSON.stringify((this.items)));
  }

}
