import { ChangeDetectionStrategy, Component, OnInit, ViewEncapsulation } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { ToolbarItem, ToolbarItemTypes } from '../interfaces';
import { getToolbarItems } from '../toolbar.state';

@Component({
  selector: 'toolbar-items',
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'toolbar-items.component.html',
})
export class ToolbarItemsComponent implements OnInit {
  toolbarItems$: Observable<ToolbarItem[]>;

  constructor(private store: Store) {
  }

  ngOnInit() {
    this.toolbarItems$ = this.store.pipe(select(getToolbarItems));
  }

  isButton(item: ToolbarItem) {
    return item.type === ToolbarItemTypes.BUTTON;
  }

  isIcon(item: ToolbarItem) {
    return item.type === ToolbarItemTypes.ICON;
  }

  click(item: ToolbarItem) {
    if (item.onclick) {
      item.onclick();
    }
  }

}
