import { ChangeDetectionStrategy, Component, HostBinding, Input, OnChanges, SimpleChanges } from '@angular/core';
import { ModalController } from '@ionic/angular';
import { TranslateService } from '@ngx-translate/core';
import { HoplrEmoticonType, HoplrPollOptions, HoplrRate, HoplrRatePerception, HoplrRateType, HoplrShoutType } from '../../hoplr';
import { RateOption, RatesModalComponent } from '../rates-modal/rates-modal.component';

@Component({
  selector: 'hoplr-feed-rates',
  templateUrl: './feed-rates.component.html',
  styleUrls: ['./feed-rates.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FeedRatesComponent implements OnChanges {
  @Input() messageType?: HoplrShoutType;
  @Input() pollOptions: HoplrPollOptions[] = [];
  @Input() rates: HoplrRate[] = [];
  @HostBinding('class.small-rates') @Input() small = false;

  votesPluralMap = {
    '=1': 'app.hoplr.one_vote',
    other: 'app.hoplr.x_votes',
  };

  emoticonChips: RateOption[] = [];
  votes: null | { rates: RateOption[]; upvoteAmount: number; upvotePercent: number; } = null;
  perception: {
    items: { score: number; amount: number; height: string; }[];
    score: string;
    totalVotes: number;
  } | null = null;
  poll: {
    totalVotes: number;
    options: { percent: number; label: string; best: boolean; }[]
  } | null = null;

  constructor(private translate: TranslateService,
              private modalController: ModalController) {
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes.pollOptions || changes.rates) {
      this.update();
    }
  }

  update() {
    // icons are nicked from hoplr website
    const emoteMapping: { [key in HoplrEmoticonType]: RateOption } = {
      [ HoplrEmoticonType.Nice ]: {
        label: 'app.hoplr.nice',
        iconUrl: '/assets/emoticon-nice.png',
        rates: [],
      },
      [ HoplrEmoticonType.Thanks ]: {
        label: 'app.hoplr.thanks',
        iconUrl: '/assets/emoticon-thanks.png',
        rates: [],
      },
      [ HoplrEmoticonType.Wow ]: {
        label: 'app.hoplr.wow',
        iconUrl: '/assets/emoticon-wow.png',
        rates: [],
      },
      [ HoplrEmoticonType.Haha ]: {
        label: 'app.hoplr.haha',
        iconUrl: '/assets/emoticon-haha.png',
        rates: [],
      },
      [ HoplrEmoticonType.Sad ]: {
        label: 'app.hoplr.sad',
        iconUrl: '/assets/emoticon-sad.png',
        rates: [],
      },
      [ HoplrEmoticonType.Wave ]: {
        label: 'app.hoplr.welcome',
        iconUrl: '/assets/emoticon-wave.png',
        rates: [],
      },
    };
    const voteMapping: { [ HoplrRateType.UPVOTE ]: RateOption; [ HoplrRateType.DOWNVOTE ]: RateOption } = {
      [ HoplrRateType.UPVOTE ]: {
        label: 'app.hoplr.upvotes',
        iconName: 'thumbs-up',
        rates: [],
      },
      [ HoplrRateType.DOWNVOTE ]: {
        label: 'app.hoplr.downvotes',
        iconName: 'thumbs-down',
        rates: [],
      },
    };
    const pollMapping = new Map();
    for (const rate of this.rates) {
      switch (rate.RateType) {
        case HoplrRateType.EMOTE:
          if (rate.EmoticonType in emoteMapping) {
            emoteMapping[ rate.EmoticonType ].rates.push(rate);
          }
          break;
        case HoplrRateType.UPVOTE:
        case HoplrRateType.DOWNVOTE:
          voteMapping[ rate.RateType ].rates.push(rate);
          break;
        case HoplrRateType.POLL_ANSWER:
          const pollAmount = (pollMapping.get(rate.OptionId) ?? 0) + 1;
          pollMapping.set(rate.OptionId, pollAmount);
          break;
      }
    }
    this.emoticonChips = Object.values(emoteMapping).filter(m => m.rates.length > 0);
    const upVotes = voteMapping[ HoplrRateType.UPVOTE ];
    const downVotes = voteMapping[ HoplrRateType.DOWNVOTE ];
    const upVotesCount = upVotes.rates.length;
    const downVotesCount = downVotes.rates.length;
    if (upVotesCount === 0 && downVotesCount === 0) {
      // Don't show votes if there are none since we have no other way to know if this message contains a vote
      this.votes = null;
    } else {
      const upvoteAmount = upVotesCount / (upVotesCount + downVotesCount);
      this.votes = {
        rates: [upVotes, downVotes],
        upvoteAmount,
        upvotePercent: Math.round(upvoteAmount * 100),
      };
    }

    if (this.messageType === HoplrShoutType.PERCEPTION) {
      this.setPerception(this.rates as HoplrRatePerception[]);
    }
    if (this.pollOptions?.length) {
      let totalPollOptionsSelected = 0;
      let highest: { id: number; amount: number; } | null = null;
      for (const [optionId, amount] of pollMapping.entries()) {
        totalPollOptionsSelected += amount;
        if (!highest || highest.amount > amount) {
          highest = { id: optionId, amount };
        }
      }
      this.poll = {
        totalVotes: totalPollOptionsSelected,
        options: this.pollOptions.map(option => ({
          label: option.Text,
          best: option.Id === highest?.id,
          percent: Math.round((pollMapping.get(option.Id) ?? 0 / totalPollOptionsSelected) * 100),
        })),
      };
    }
  }

  async showDetails(item: RateOption) {
    const modal = await this.modalController.create({
      component: RatesModalComponent,
      componentProps: { rates: [item] },
    });
    await modal.present();
  }

  async showUpvotes() {
    const modal = await this.modalController.create({
      component: RatesModalComponent,
      // tslint:disable-next-line:no-non-null-assertion
      componentProps: { rates: this.votes!.rates, label: '' },
    });
    await modal.present();
  }

  private setPerception(rates: HoplrRatePerception[]) {
    const rateScores = {
      1: 0,
      2: 0,
      3: 0,
      4: 0,
      5: 0,
      6: 0,
      7: 0,
      8: 0,
      9: 0,
      10: 0,
    };
    for (const rate of rates) {
      rateScores[ rate.Value ]++;
    }
    let totalVotes = 0;
    let maxAmount = 1;
    for (const amount of Object.values(rateScores)) {
      totalVotes += amount;
      if (amount > maxAmount) {
        maxAmount = amount;
      }
    }
    const items = Object.entries(rateScores)
      .map(([score, amount]) => ({
        score: parseInt(score, 10),
        amount,
        height: `${10 + (100 * amount / maxAmount)}px`,
      }));
    this.perception = {
      items,
      score: (items.reduce((acc, item) => {
        acc += item.amount * item.score;
        return acc;
      }, 0) / totalVotes).toFixed(1),
      totalVotes,
    };
  }
}
