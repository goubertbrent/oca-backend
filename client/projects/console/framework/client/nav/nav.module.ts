import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FlexLayoutModule } from '@angular/flex-layout';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatMenuModule } from '@angular/material/menu';
import { MatSelectModule } from '@angular/material/select';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { RouterModule } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { SecondarySidenavComponent } from './secondary-sidenav.component';
import { ToolbarItemsComponent } from './toolbar'

@NgModule({
  imports: [
    CommonModule,
    MatButtonModule,
    MatSidenavModule,
    MatSelectModule,
    MatIconModule,
    MatToolbarModule,
    MatMenuModule,
    MatListModule,
    RouterModule.forChild([]),
    FlexLayoutModule,
    TranslateModule,
  ],
  declarations: [SecondarySidenavComponent, ToolbarItemsComponent],
  providers: [],
  exports: [SecondarySidenavComponent, ToolbarItemsComponent],
})
export class NavModule {
}
