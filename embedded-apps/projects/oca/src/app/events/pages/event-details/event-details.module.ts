import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatExpansionModule } from '@angular/material/expansion';
import { RouterModule } from '@angular/router';
import { IonicModule } from '@ionic/angular';
import { TranslateModule } from '@ngx-translate/core';
import { BackButtonModule, MarkdownModule } from '@oca/shared';
import { EventDateLineComponent } from './event-date-line/event-date-line.component';
import { EventDetailsPage } from './event-details.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    RouterModule.forChild([{ path: '', component: EventDetailsPage }]),
    TranslateModule,
    BackButtonModule,
    MarkdownModule,
    MatExpansionModule,
  ],
  declarations: [EventDetailsPage, EventDateLineComponent],
})
export class EventDetailsPageModule {
}
