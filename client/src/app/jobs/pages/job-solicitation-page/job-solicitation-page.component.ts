import { AfterViewChecked, ChangeDetectionStrategy, Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable, Subject } from 'rxjs';
import { map, startWith, takeUntil, withLatestFrom } from 'rxjs/operators';
import { RootState } from '../../../reducers';
import { filterNull } from '../../../shared/util';
import { JobSolicitation, JobSolicitationStatus, UIJobSolicitationMessage } from '../../jobs';
import { SendSolicitationMessageAction } from '../../jobs.actions';
import {
  areSolicitationMessagesLoading,
  getCurrentJobId,
  getCurrentSolicitation,
  getNewSolicitationMessage,
  getSolicitationMessages,
  isNewSolicitationMessageLoading,
} from '../../jobs.state';

@Component({
  selector: 'oca-job-solicitation-page',
  templateUrl: './job-solicitation-page.component.html',
  styleUrls: ['./job-solicitation-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class JobSolicitationPageComponent implements OnInit, OnDestroy, AfterViewChecked {
  solicitation$: Observable<JobSolicitation>;
  canSendMessage$: Observable<boolean>;
  isSendingMessage$: Observable<boolean>;
  solicitationMessages$: Observable<UIJobSolicitationMessage[]>;
  messagesLoading$: Observable<boolean>;
  @ViewChild('scrollContainer') private scrollContainer: ElementRef;
  newMessage = '';
  private autoScrollDown = true;
  private destroyed$ = new Subject();

  constructor(private store: Store<RootState>) {
  }

  ngOnInit(): void {
    this.solicitation$ = this.store.pipe(select(getCurrentSolicitation), filterNull());
    this.canSendMessage$ = this.solicitation$.pipe(map(solicitation => solicitation.status !== JobSolicitationStatus.DISABLED))
      .pipe(startWith(true));
    this.solicitationMessages$ = this.store.pipe(select(getSolicitationMessages));
    this.isSendingMessage$ = this.store.pipe(select(isNewSolicitationMessageLoading));
    this.messagesLoading$ = this.store.pipe(select(areSolicitationMessagesLoading));
    this.store.pipe(select(getNewSolicitationMessage), takeUntil(this.destroyed$)).subscribe(newMessage => {
      this.newMessage = newMessage?.message || '';
    });
  }

  ngAfterViewChecked() {
    this.scrollToBottom();
  }

  ngOnDestroy(): void {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  sendNewMessage() {
    this.autoScrollDown = true;
    this.scrollToBottom();
    this.newMessage = this.newMessage.trim();
    if (this.newMessage) {
      this.store.pipe(
        select(getCurrentJobId),
        filterNull(),
        withLatestFrom(this.solicitation$),
        takeUntil(this.destroyed$)).subscribe(([jobId, solicitation]: [number, JobSolicitation]) => {
        this.store.dispatch(new SendSolicitationMessageAction({
          jobId,
          solicitationId: solicitation.id,
          message: { message: this.newMessage },
        }));
      });
    }
  }

  trackMessages(index: number, item: UIJobSolicitationMessage) {
    return item.id;
  }

  onScroll() {
    // If user scrolled up, don't automatically scroll down
    const element = this.scrollContainer.nativeElement;
    const atBottom = element.scrollHeight - element.scrollTop === element.clientHeight;
    this.autoScrollDown = atBottom;
  }


  private scrollToBottom(): void {
    if (this.autoScrollDown) {
      try {
        this.scrollContainer.nativeElement.scrollTop = this.scrollContainer.nativeElement.scrollHeight;
      } catch (err) {
      }
    }
  }
}
