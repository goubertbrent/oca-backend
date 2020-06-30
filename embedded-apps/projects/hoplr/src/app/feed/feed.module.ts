import { CommonModule, DatePipe } from '@angular/common';
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { IonicModule } from '@ionic/angular';
import { TranslateModule } from '@ngx-translate/core';
import { BackButtonModule, DynamicDateModule, DynamicDatePipe, MarkdownModule } from '@oca/shared';
import { EventDatePipe } from './event-date.pipe';
import { EventHeaderComponent } from './event-header/event-header.component';
import { EventRsvpsComponent } from './event-rsvps/event-rsvps.component';
import { FeedCommentComponent } from './feed-comment/feed-comment.component';
import { FeedContentMessageComponent } from './feed-content-message/feed-content-message.component';
import { FeedImagesComponent } from './feed-images/feed-images.component';
import { FeedItemHeaderComponent } from './feed-item-header/feed-item-header.component';
import { FeedItemInfoHeaderComponent } from './feed-item-info-header/feed-item-info-header.component';
import { FeedItemComponent } from './feed-item/feed-item.component';
import { FeedPageComponent } from './feed-page/feed-page.component';
import { FeedRatesComponent } from './feed-rates/feed-rates.component';
import { FeedTextBoxComponent } from './feed-text-box/feed-text-box.component';
import { ImageViewerComponent } from './image-viewer/image-viewer.component';
import { ItemSubHeaderPipe } from './item-sub-header.pipe';
import { RatesModalComponent } from './rates-modal/rates-modal.component';
import { RsvpListModalComponent } from './rsvp-list-modal/rsvp-list-modal.component';
import { UserListItemComponent } from './user-list-item/user-list-item.component';

const routes: Routes = [
  { path: '', component: FeedPageComponent },
];

@NgModule({
  declarations: [
    FeedPageComponent,
    FeedCommentComponent,
    FeedItemHeaderComponent,
    FeedTextBoxComponent,
    FeedContentMessageComponent,
    FeedImagesComponent,
    FeedImagesComponent,
    FeedRatesComponent,
    EventHeaderComponent,
    EventRsvpsComponent,
    RatesModalComponent,
    RsvpListModalComponent,
    ImageViewerComponent,
    ItemSubHeaderPipe,
    EventDatePipe,
    UserListItemComponent,
    FeedItemInfoHeaderComponent,
    FeedItemComponent,
  ],
  imports: [
    CommonModule,
    IonicModule,
    RouterModule.forChild(routes),
    BackButtonModule,
    TranslateModule,
    DynamicDateModule,
    MarkdownModule,
  ],
  providers: [DynamicDatePipe, DatePipe],
})
export class FeedModule {
}
