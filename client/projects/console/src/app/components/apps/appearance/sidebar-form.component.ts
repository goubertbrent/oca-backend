import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { HomescreenStyle } from '../../../constants';
import { AppSidebar, BuildSettings } from '../../../interfaces';
import { cloneDeep } from '../../../util';

@Component({
  selector: 'rcc-app-sidebar-form',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'sidebar-form.component.html',
})
export class SidebarFormComponent {
  @Input() status: ApiRequestStatus;
  @Input() buildSettings: BuildSettings;
  @Input() homescreenStyles: HomescreenStyle[];
  @Output() save = new EventEmitter<AppSidebar>();
  FOOTER_ALIGNMENTS = [ 'normal', 'bottom' ];

  private _sidebar: AppSidebar;


  get sidebar() {
    return this._sidebar;
  }

  @Input() set sidebar(value: AppSidebar) {
    this._sidebar = cloneDeep(value);
  }

  is3x3() {
    return this.sidebar.style === '3x3';
  }

  submit() {
    this.save.emit(this.sidebar);
  }
}

