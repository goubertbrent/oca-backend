import { Injectable } from '@angular/core';
import {
  HoplrAttachment,
  HoplrBusiness,
  HoplrComment,
  HoplrFeedItem,
  HoplrImage,
  HoplrMessageImage,
  HoplrMessageType,
  HoplrRate,
  HoplrRsvp,
  HoplrUser,
} from './hoplr';

@Injectable({ providedIn: 'root' })
export class HoplrService {

  constructor() {
  }

  convertItems(baseMediaUrl: string, items: HoplrFeedItem[]) {
    return items.map(item => convertFeedItem(baseMediaUrl, item));
  }
}

function convertFeedItem(baseMediaUrl: string, feedItem: HoplrFeedItem): HoplrFeedItem {
  switch (feedItem.type) {
    case HoplrMessageType.SHOUT:
      return {
        ...feedItem,
        data: {
          ...feedItem.data,
          User: convertUser(baseMediaUrl, feedItem.data.User),
          Images: feedItem.data.Images.map(img => convertImage(baseMediaUrl, img)),
          Rates: feedItem.data.Rates.map(r=>convertRate(baseMediaUrl, r)),
          Comments: feedItem.data.Comments.map(c=>convertComment(baseMediaUrl, c)),
          Attachments: feedItem.data.Attachments.map(a=>convertAttachment(baseMediaUrl, a))
        },
      };
    case HoplrMessageType.MESSAGE:
      return {
        ...feedItem,
        data: {
          ...feedItem.data,
          User: convertUser(baseMediaUrl, feedItem.data.User),
          Images: feedItem.data.Images.map(img => convertMessageImage(baseMediaUrl, img)),
          Rates: feedItem.data.Rates.map(r => convertRate(baseMediaUrl, r)),
          Comments: feedItem.data.Comments.map(c => convertComment(baseMediaUrl, c)),
          Business: convertBusiness(baseMediaUrl, feedItem.data.Business),
        },
      };
    case HoplrMessageType.EVENT:
      return {
        ...feedItem,
        data: {
          ...feedItem.data,
          User: convertUser(baseMediaUrl, feedItem.data.User),
          Images: feedItem.data.Images.map(img => convertImage(baseMediaUrl, img)),
          Rates: feedItem.data.Rates.map(r=>convertRate(baseMediaUrl, r)),
          Comments: feedItem.data.Comments.map(c=>convertComment(baseMediaUrl, c)),
          Rsvps: feedItem.data.Rsvps.map(r=>convertRsvp(baseMediaUrl, r)),
        },
      };
  }
}

function convertAttachment(baseMediaUrl: string, attachment: HoplrAttachment): HoplrAttachment {
  return {
    ...attachment,
    Url: `${baseMediaUrl}/attachments/${attachment.Url}`,
  };
}

function convertUser(baseMediaUrl: string, user: HoplrUser): HoplrUser {
  return {
    ...user,
    IconUrl: user.IconUrl ? getImageUrl(baseMediaUrl, user.IconUrl) as string : undefined,
    ThumbUrl: getImageUrl(baseMediaUrl, user.ThumbUrl) as string,
    ProfileName: user.ProfileName.trim(),
  };
}

function convertImage(baseMediaUrl: string, image: HoplrImage): HoplrImage {
  return { ...image, ImageUrl: getImageUrl(baseMediaUrl,image.ImageUrl) as string };
}

function convertMessageImage(baseMediaUrl: string, { ImageUrl, IconUrl, ...rest }: HoplrMessageImage): HoplrMessageImage {
  return {
    ...rest,
    ImageUrl: getImageUrl(baseMediaUrl, ImageUrl) as string,
    ThumbUrl: getImageUrl(baseMediaUrl, IconUrl) as string,
    IconUrl: getImageUrl(baseMediaUrl, IconUrl) as string,
  };
}

function convertRate(baseMediaUrl: string, { User, ...rest }: HoplrRate): HoplrRate {
  return { ...rest, User: convertUser(baseMediaUrl, User) };
}

function convertComment(baseMediaUrl: string, { User, Business, ...rest }: HoplrComment): HoplrComment {
  return { ...rest, User: convertUser(baseMediaUrl,User), Business: Business ? convertBusiness(baseMediaUrl,Business) : Business };
}

function convertBusiness(baseMediaUrl: string, business: HoplrBusiness): HoplrBusiness {
  return business ? { ...business, ThumbUrl: getImageUrl(baseMediaUrl, business.ThumbUrl) as string } : business;
}

function convertRsvp(baseMediaUrl: string, { User, ...rest }: HoplrRsvp): HoplrRsvp {
  return { ...rest, User: convertUser(baseMediaUrl,User) };
}

function getImageUrl(baseMediaUrl: string, filename: string | undefined): string | undefined {
  return filename ? `${baseMediaUrl}/images/${filename}` : filename;
}
