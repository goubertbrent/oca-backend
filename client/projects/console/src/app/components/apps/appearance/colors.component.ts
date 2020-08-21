import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { filterNull } from '../../../ngrx';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { GetAppColorsAction, UpdateAppColorsAction } from '../../../actions';
import { AppColors } from '../../../interfaces';
import { getAppColors, getAppColorsStatus } from '../../../console.state';
import { ConsoleState } from '../../../reducers';

@Component({
  selector: 'rcc-appearance-colors',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="default-component-margin">
      <rcc-app-colors-form [colors]="colors$ | async"
                           [status]="status$ | async"
                           (save)="save($event)"></rcc-app-colors-form>
    </div>`,
})
export class AppearanceColorsComponent implements OnInit {
  colors$: Observable<AppColors>;
  status$: Observable<ApiRequestStatus>;

  constructor(private store: Store) {
  }

  ngOnInit() {
    this.store.dispatch(new GetAppColorsAction());
    this.colors$ = this.store.select(getAppColors).pipe(filterNull());
    this.status$ = this.store.select(getAppColorsStatus);
  }

  save(colors: AppColors) {
    this.store.dispatch(new UpdateAppColorsAction(colors));
  }
}
