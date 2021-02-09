import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable, Subject } from 'rxjs';
import { debounceTime, map, tap } from 'rxjs/operators';
import { ServiceOpeningHours } from '../../../shared/interfaces/oca';
import { deepCopy } from '../../../shared/util';
import { GetOpeningHoursAction, SaveOpeningHoursAction } from '../../settings.actions';
import { getOpeningHours, openingHoursLoading, SettingsState } from '../../settings.state';

@Component({
  selector: 'oca-opening-hours-settings-page',
  templateUrl: './opening-hours-settings-page.component.html',
  styleUrls: ['./opening-hours-settings-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OpeningHoursSettingsPageComponent implements OnInit, OnDestroy {
  openingHours$: Observable<ServiceOpeningHours | null>;
  isLoading$: Observable<boolean>;

  private settings: ServiceOpeningHours;
  private autoSave$ = new Subject<ServiceOpeningHours>();

  constructor(private store: Store<SettingsState>) {
  }

  ngOnInit() {
    this.store.dispatch(new GetOpeningHoursAction());
    this.openingHours$ = this.store.pipe(select(getOpeningHours), map(hours => hours && deepCopy(hours)));
    this.isLoading$ = this.store.pipe(select(openingHoursLoading));
    this.autoSave$.pipe(
      tap(s => this.settings = s),
      debounceTime(7500),
    ).subscribe(settings => this.onOpeningHoursSaved(settings));
  }

  ngOnDestroy(): void {
    this.autoSave$.complete();
  }

  manualSave() {
    if (this.settings) {
      this.onOpeningHoursSaved(this.settings);
    }
  }

  onOpeningHoursSaved($event: ServiceOpeningHours) {
    this.store.dispatch(new SaveOpeningHoursAction($event));
  }

  autoSave($event: ServiceOpeningHours) {
    this.autoSave$.next($event);
  }
}
