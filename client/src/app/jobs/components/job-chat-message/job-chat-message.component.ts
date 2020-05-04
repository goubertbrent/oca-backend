import { animate, state, style, transition, trigger } from '@angular/animations';
import { ChangeDetectionStrategy, Component, HostBinding, Input } from '@angular/core';

@Component({
  selector: 'oca-job-chat-message',
  templateUrl: './job-chat-message.component.html',
  styleUrls: ['./job-chat-message.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [
    trigger('new-animation', [
      state('in', style({ opacity: 1, transform: 'translateX(0)' })),
      transition('void => in', [
        style({ opacity: 0, transform: 'translateX(50%)' }),
        animate(80),
      ]),
    ]),
  ],
})
export class JobChatMessageComponent {
  @Input() message: string;
  @Input() sender: string | null;
  @Input() date: Date;
  @HostBinding('class.reply') @Input() reply: boolean;
  animationState = 'in';
}
