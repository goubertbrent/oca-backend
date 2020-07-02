import { Pipe, PipeTransform } from '@angular/core';
import { CirkloVoucher } from './cirklo';

@Pipe({
  name: 'voucherQrData',
  pure: true,
})
export class VoucherQrDataPipe implements PipeTransform {

  transform(value: CirkloVoucher): string {
    return JSON.stringify({ voucher: value.id });
  }

}
