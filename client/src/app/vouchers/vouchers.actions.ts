import { createAction, props } from '@ngrx/store';
import { CirkloCity, CirkloSettings, VoucherService, VouchersServiceList } from './vouchers';

export const GetServicesAction = createAction(
  '[Vouchers] Get services',
);

export const GetServicesSuccessAction = createAction(
  '[Vouchers] Get services success',
  props<{ payload: VouchersServiceList }>(),
);

export const GetServicesFailedAction = createAction(
  '[Vouchers] Get services failed',
  props<{ error: string }>(),
);

export const WhitelistVoucherServiceAction = createAction(
  '[Vouchers] Whitelist voucher service',
  props<{ id: string, email: string, accepted: boolean }>(),
);

export const WhitelistVoucherServiceSuccessAction = createAction(
  '[Vouchers] Whitelist voucher provider success',
  props<{ id: string; email: string, service: VoucherService }>(),
);

export const WhitelistVoucherServiceFailedAction = createAction(
  '[Vouchers] Whitelist voucher provider failed',
  props<{ error: string }>(),
);

export const GetCirkloSettingsAction = createAction(
  '[Vouchers] Get cirklo settings',
);

export const GetCirkloSettingsCompleteAction = createAction(
  '[Vouchers] Get cirklo settings success',
  props<{ payload: CirkloSettings }>(),
);


export const GetCirkloSettingsFailedAction = createAction(
  '[Vouchers] Get cirklo settings failed',
  props<{ error: string }>(),
);

export const SaveCirkloSettingsAction = createAction(
  '[Vouchers] Save cirklo settings',
  props<{ payload: CirkloSettings }>(),
);

export const SaveCirkloSettingsCompleteAction = createAction(
  '[Vouchers] Save cirklo settings success',
  props<{ payload: CirkloSettings }>(),
);

export const SaveCirkloSettingsFailedAction = createAction(
  '[Vouchers] Save cirklo settings failed',
  props<{ error: string }>(),
);

export const GetCirkloCities = createAction(
  '[Vouchers] Get cirklo cities',
  props<{ staging: boolean }>(),
);

export const GetCirkloCitiesComplete = createAction(
  '[Vouchers] Get cirklo cities success',
  props<{ cities: CirkloCity[] }>(),
);

export const GetCirkloCitiesFailed = createAction(
  '[Vouchers] Get cirklo cities failed',
  props<{ error: string }>(),
);

export const ExportMerchants = createAction(
  '[Vouchers] Export merchants',
);

export const ExportMerchantsComplete = createAction(
  '[Vouchers] Export merchants success',
  props<{ url: string }>(),
);

export const ExportMerchantsFailed = createAction(
  '[Vouchers] Export merchants failed',
  props<{ error: string }>(),
);
