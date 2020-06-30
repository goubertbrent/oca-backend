import { ScrollingModule } from '@angular/cdk/scrolling';
import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';

import { IonicModule } from '@ionic/angular';
import { TranslateModule } from '@ngx-translate/core';
import { BackButtonModule } from '@oca/shared';
import { NewsListComponent } from '../../news-list/news-list.component';
import { CalendarIconComponent } from './calendar-icon/calendar-icon.component';
import { EventFilterComponent } from './event-filter/event-filter.component';

import { EventsPage } from './events.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    RouterModule.forChild([{ path: '', component: EventsPage }]),
    TranslateModule,
    BackButtonModule,
    ScrollingModule,
  ],
  declarations: [EventsPage, NewsListComponent, CalendarIconComponent, EventFilterComponent],
})
export class EventsPageModule {
}
