import { OverlayContainer } from '@angular/cdk/overlay';
import { ChangeDetectionStrategy, Component, HostBinding, OnInit, ViewEncapsulation } from '@angular/core';
import { ThemingService } from './theming.service';

@Component({
  selector: 'web-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class AppComponent implements OnInit {
  @HostBinding('class') public cssClass = 'light-theme';

  constructor(private themingService: ThemingService,
              private overlayContainer: OverlayContainer) {
  }

  ngOnInit() {
    this.themingService.theme.subscribe(theme => {
      const overlayClassList = this.overlayContainer.getContainerElement().classList;
      overlayClassList.remove(this.cssClass);
      this.cssClass = theme;
      overlayClassList.add(theme);
    });
  }
}
