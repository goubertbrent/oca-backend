import { Pipe, PipeTransform } from '@angular/core';
import { encodeURIObject } from '@oca/shared';
import { MerchantAddress } from './cirklo';

@Pipe({
  name: 'merchantAddressUrl',
  pure: true,
})
export class MerchantAddressUrlPipe implements PipeTransform {

  transform(value: MerchantAddress): string {
    const params: any = {
      api: 1,
      destination: `${value.street} ${value.street_number}, ${value.postal_code} ${value.locality}`,
    };
    if (value.place_id) {
      params.destination_place_id = value.place_id;
    }
    // TODO move encodeURIObject to local
    return `https://www.google.com/maps/dir/?${encodeURIObject(params)}`;
  }

}
