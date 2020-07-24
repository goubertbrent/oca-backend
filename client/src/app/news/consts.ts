import { Gender, MediaType } from '@oca/web-shared';

export const GENDER_OPTIONS = [
  { value: Gender.MALE_OR_FEMALE, label: 'oca.gender-male-female' },
  { value: Gender.MALE, label: 'oca.gender-male' },
  { value: Gender.FEMALE, label: 'oca.gender-female' },
];

export const NEWS_MEDIA_TYPE_OPTIONS = [
  { value: null, label: 'oca.none' },
  { value: MediaType.IMAGE, label: 'oca.image' },
  { value: MediaType.YOUTUBE_VIDEO, label: 'oca.video' },
];

export const BUDGET_RATE = 2.0;  // 10k views / 5000 cent
