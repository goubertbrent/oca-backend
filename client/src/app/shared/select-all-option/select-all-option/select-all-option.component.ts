import { ChangeDetectionStrategy, Component, Input, OnInit, ViewEncapsulation } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatCheckboxChange } from '@angular/material/checkbox';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

@Component({
  selector: 'oca-select-all-option',
  templateUrl: './select-all-option.component.html',
  styleUrls: ['./select-all-option.component.scss'],
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SelectAllOptionComponent implements OnInit {
  @Input() control: FormControl;
  @Input() values = [];
  @Input() text = '';
  isChecked$: Observable<boolean>;
  isIndeterminate$: Observable<boolean>;

  ngOnInit(): void {
    this.isChecked$ = this.control.valueChanges.pipe(map((value: any[]) =>
      value != null && this.values.length > 0 && value.length === this.values.length));
    this.isIndeterminate$ = this.control.valueChanges.pipe(map((value: any[]) =>
      value != null && this.values.length > 0 && value.length > 0 && value.length < this.values.length));
  }

  toggleSelection(change: MatCheckboxChange): void {
    if (change.checked) {
      this.control.setValue(this.values);
    } else {
      this.control.setValue([]);
    }
  }
}
