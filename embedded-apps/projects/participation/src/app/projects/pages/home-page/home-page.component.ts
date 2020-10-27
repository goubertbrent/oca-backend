import { AfterViewInit, ChangeDetectionStrategy, Component, OnDestroy, OnInit, ViewChild, ViewEncapsulation } from '@angular/core';
import { IonTabs, Platform } from '@ionic/angular';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { JoyrideService } from 'ngx-joyride';
import { Observable, Subject } from 'rxjs';
import { delay, take, takeUntil } from 'rxjs/operators';
import { filterNull } from '../../../util';
import { UserSettings } from '../../projects';
import { GetProjectsAction, GetUserSettingsAction, SaveUserSettingsAction } from '../../projects.actions';
import { ProjectsService } from '../../projects.service';
import { getUserSettings, ProjectsState } from '../../projects.state';

@Component({
  templateUrl: './home-page.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class HomePageComponent implements AfterViewInit, OnInit, OnDestroy {
  @ViewChild(IonTabs, { static: true, read: IonTabs }) tabs: IonTabs;
  userSettings$ = new Observable<UserSettings>();
  backButtonIcon = 'arrow-left';
  private currentTab$ = new Subject<string>();
  pageTitle$ = this.currentTab$.asObservable();

  private destroyed$ = new Subject();

  constructor(private store: Store<ProjectsState>,
              private service: ProjectsService,
              private joyrideService: JoyrideService,
              private translate: TranslateService,
              private platform: Platform) {
  }

  ngOnInit() {
    const isIOS = this.platform.is('ios');
    this.backButtonIcon = isIOS ? 'menu' : 'arrow-back';
    this.store.dispatch(new GetProjectsAction());
    this.store.dispatch(new GetUserSettingsAction());
    this.userSettings$ = this.store.pipe(select(getUserSettings), takeUntil(this.destroyed$), filterNull());
  }

  ngAfterViewInit(): void {
    // Delay is needed to allow for the elements to be in their correct place.
    // Else the tour is shown at the wrong position.
    this.userSettings$.pipe(take(1), delay(500)).subscribe(result => {
      if (result.hasOwnProperty('tour_date') && !result.tour_date) {
        this.joyrideService.startTour({ showCounter: false, stepDefaultPosition: 'top', steps: ['infoStep'] }).subscribe(
          step => {
          }, err => {
            console.error(err);
          }, () => {
            this.tourDone();
          });
      }
    });
  }

  ngOnDestroy(): void {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  exit() {
    rogerthat.app.exit();
  }

  tourDone() {
    this.userSettings$.pipe(take(1)).subscribe(settings => {
      settings = { ...settings, tour_date: new Date() };
      this.store.dispatch(new SaveUserSettingsAction(settings));
    });
  }

  tabChanged($event: { tab: string }) {
    this.currentTab$.next($event.tab);
  }
}
