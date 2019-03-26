import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import { FormSettings } from '../../../interfaces/forms.interfaces';
import { Loadable } from '../../../interfaces/loadable';

interface Tab {
  label: string;
  list: FormSettings[];
}

@Component({
  selector: 'oca-forms-list',
  templateUrl: './form-list.component.html',
  styleUrls: [ './form-list.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormListComponent implements OnChanges {
  @Input() forms: Loadable<FormSettings[]>;
  @Output() createForm = new EventEmitter();
  @Output() deleteForm = new EventEmitter<FormSettings>();
  now = new Date();
  tabs: Tab[] = [
    { label: 'oca.current', list: [] },
    { label: 'oca.finished', list: [] },
  ];

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.forms && changes.forms.currentValue) {
      const forms: Loadable<FormSettings[]> = changes.forms.currentValue;
      if(forms.data) {
        this.tabs[ 0 ].list = forms.data.filter(f => !f.visible_until || f.visible_until > this.now);
        this.tabs[ 1 ].list = forms.data.filter(f => f.visible_until && f.visible_until <= this.now);
      }
    }
  }

  trackById(element: FormSettings, index: number) {
    return element.id;
  }
}
