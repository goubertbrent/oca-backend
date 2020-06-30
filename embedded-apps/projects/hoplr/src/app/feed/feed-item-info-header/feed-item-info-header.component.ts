import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

@Component({
  selector: 'hoplr-feed-item-info-header',
  templateUrl: './feed-item-info-header.component.html',
  styleUrls: ['./feed-item-info-header.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FeedItemInfoHeaderComponent {
  @Input() title: string;
  @Input() description: string;
  moreInfoShown = false;
}
