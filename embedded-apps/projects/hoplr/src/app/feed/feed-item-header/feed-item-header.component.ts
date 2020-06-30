import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

@Component({
  selector: 'hoplr-feed-item-header',
  templateUrl: './feed-item-header.component.html',
  styleUrls: ['./feed-item-header.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FeedItemHeaderComponent {
  @Input() avatarUrl: string;
  @Input() header: string;
  @Input() subheader: string;
}
