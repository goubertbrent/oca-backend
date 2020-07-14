export interface TrashStreet {
  number: number;
  name: string;
}

export interface GetStreetsResult {
  items: TrashStreet[];
  street_number_via_input: boolean;
}

export interface TrashHouseNumber {
  number: number;
  bus: string;
}

export interface HouseInfoInput {
  input: string;
}

export type HouseNumberRequest = HouseInfoInput | TrashHouseNumber;

export interface SaveAddressRequest {
  info: {
    street: {
      number: number;
      name: string;
    };
    house: HouseNumberRequest;
  };
}

export interface SaveNotificationsRequest {
  notifications: string[];
}

export interface TrashActivity {
  key: string;
  name: string;
  icon: string;
}

export interface TrashCollection {
  epoch: number;
  year: number;
  month: number;
  day: number;
  activity: TrashActivity;
}

export interface UiTrashActivity {
  iconUrl: string;
  name: string;
}

export interface UITrashCollection {
  date: Date;
  epoch: number;
  activities: UiTrashActivity[];
}
