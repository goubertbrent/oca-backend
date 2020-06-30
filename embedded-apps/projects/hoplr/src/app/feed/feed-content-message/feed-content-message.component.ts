import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { DomSanitizer, SafeUrl } from '@angular/platform-browser';
import { HoplrMessage, HoplrSurvey } from '../../hoplr';

@Component({
  selector: 'hoplr-feed-content-message',
  templateUrl: './feed-content-message.component.html',
  styleUrls: ['./feed-content-message.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FeedContentMessageComponent {
  @Input() baseUrl: string;

  safeVideoUrl: SafeUrl | null = null;

  constructor(private sanitizer: DomSanitizer) {
  }

  private _message: HoplrMessage;

  get message() {
    return this._message;
  }

  @Input() set message(value: HoplrMessage) {
    this._message = value;
    this.safeVideoUrl = value.data.EmbeddedVideoUrl ? this.sanitizer.bypassSecurityTrustResourceUrl(value.data.EmbeddedVideoUrl) : null;
  }

  canParticipateInSurvey(survey: HoplrSurvey) {
    return new Date() < new Date(survey.Survey.End);
  }
}
