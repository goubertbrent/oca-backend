import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ActivatedRoute } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { SimpleDialogComponent, SimpleDialogData, SimpleDialogResult } from '@oca/web-shared';
import { Observable } from 'rxjs';
import { ListEmbeddedAppsAction } from '../../../actions';
import { getEmbeddedApps } from '../../../console.state';
import { EmbeddedApp } from '../../../interfaces';
import { getCommunityHomeScreen, isHomeScreenLoading } from '../../communities.selectors';
import { getHomeScreen, publishHomeScreen, testHomeScreen, updateHomeScreen } from '../../community.actions';
import { HomeScreenService } from '../home-screen.service';
import { HomeScreenDefaultTranslation } from '../homescreen';
import { HomeScreen } from '../models';

@Component({
  selector: 'rcc-home-screen-page',
  templateUrl: './home-screen-page.component.html',
  styleUrls: ['./home-screen-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HomeScreenPageComponent implements OnInit {
  homeScreen$: Observable<HomeScreen | null>;
  homeScreenLoading$: Observable<boolean>;
  embeddedApps$: Observable<EmbeddedApp[]>;
  defaultTranslations$: Observable<HomeScreenDefaultTranslation[]>;

  private communityId: number;
  private homeScreenId: string;

  constructor(private store: Store,
              private route: ActivatedRoute,
              private matDialog: MatDialog,
              private homeScreenService: HomeScreenService) {
  }

  ngOnInit(): void {
    this.communityId = parseInt(this.route.snapshot.parent!!.params.communityId, 10);
    this.homeScreenId = this.route.snapshot.params.homeScreenId;
    this.store.dispatch(getHomeScreen({ communityId: this.communityId, homeScreenId: this.homeScreenId }));
    this.homeScreen$ = this.store.pipe(select(getCommunityHomeScreen));
    this.homeScreenLoading$ = this.store.pipe(select(isHomeScreenLoading));
    this.store.dispatch(new ListEmbeddedAppsAction());
    this.embeddedApps$ = this.store.pipe(select(getEmbeddedApps));
    this.defaultTranslations$ = this.homeScreenService.getDefaultTranslations();
  }

  updateHomeScreen(homeScreen: HomeScreen) {
    this.store.dispatch(updateHomeScreen({ communityId: this.communityId, homeScreenId: this.homeScreenId, homeScreen }));
  }

  publishHomeScreen() {
    this.store.dispatch(publishHomeScreen({ communityId: this.communityId, homeScreenId: this.homeScreenId }));
  }

  testHomeScreen() {
    const data: SimpleDialogData = {
      cancel: 'Cancel',
      inputType: 'email',
      message: 'Enter the test user email',
      title: 'Test home screen',
      ok: 'Submit',
      required: true,
    };
    this.matDialog.open<SimpleDialogComponent, SimpleDialogData, SimpleDialogResult>(SimpleDialogComponent, { data })
      .afterClosed().subscribe(result => {
      if (result?.submitted) {
        this.store.dispatch(testHomeScreen({
          communityId: this.communityId,
          homeScreenId: this.homeScreenId,
          testUser: result.value!,
        }));
      }
    });
  }
}
