export type AssetType = 'account' | 'bank' | 'creditcard' | 'cryptocurrency_wallet';
export const ASSET_TYPES: AssetType[] = [ 'account', 'bank', 'creditcard', 'cryptocurrency_wallet' ];

export interface PaymentProviderOAuthSettings {
  client_id: string;
  secret: string;
  base_url: string;
  authorize_path: string;
  token_path: string;
  scope: string;
}

export type ColorSchemes = 'light' | 'primary' | 'secondary' | 'danger' | 'dark';
export const COLOR_SCHEMES: ColorSchemes[] = [ 'light', 'primary', 'secondary', 'danger', 'dark' ];

export interface PaymentProvider {
  id: string;
  name: string;
  logo: string | null;
  description: string | null;
  black_white_logo: string | null;
  background_color: string;
  text_color: string;
  button_color: ColorSchemes;
  version: number;
  oauth_settings: PaymentProviderOAuthSettings;
  asset_types: AssetType[];
  currencies: string[];
  settings: { [ key: string ]: any };
  app_ids: string[];
  embedded_application: string | null;
}


export interface Currency {
  currency: string;
  code: string;
}

/**
 * Ripped from http://data.okfn.org/data/core/currency-codes
 * currencies.split('\n').map(s => {
 *   let split = s.split(',');
 *   return {
 *     entity: split[ 0 ],
 *     currency: split[ 1 ],
 *     code:'split[2],
 *   };
 * });
 */

/* tslint:disable */
//@formatter:off
export const CURRENCIES: Currency[] = [ { code: 'AFN', currency: 'Afghani' }, { code: 'EUR', currency: 'Euro' }, {
  code: 'ALL',
  currency: 'Lek',
}, { code: 'DZD', currency: 'Algerian Dinar' }, { code: 'USD', currency: 'US Dollar' }, { code: 'AOA', currency: 'Kwanza' }, {
  code: 'XCD',
  currency: 'East Caribbean Dollar',
}, { code: 'ARS', currency: 'Argentine Peso' }, { code: 'AMD', currency: 'Armenian Dram' }, {
  code: 'AWG',
  currency: 'Aruban Florin',
}, { code: 'AUD', currency: 'Australian Dollar' }, { code: 'AZN', currency: 'Azerbaijanian Manat' }, {
  code: 'BSD',
  currency: 'Bahamian Dollar',
}, { code: 'BHD', currency: 'Bahraini Dinar' }, { code: 'BDT', currency: 'Taka' }, {
  code: 'BBD',
  currency: 'Barbados Dollar',
}, { code: 'BYN', currency: 'Belarusian Ruble' }, { code: 'BZD', currency: 'Belize Dollar' }, {
  code: 'XOF',
  currency: 'CFA Franc BCEAO',
}, { code: 'BMD', currency: 'Bermudian Dollar' }, { code: 'INR', currency: 'Indian Rupee' }, {
  code: 'BTN',
  currency: 'Ngultrum',
}, { code: 'BOB', currency: 'Boliviano' }, { code: 'BOV', currency: 'Mvdol' }, {
  code: 'US Dollar',
  currency: ' SINT EUSTATIUS AND SABA\"',
}, { code: 'BAM', currency: 'Convertible Mark' }, { code: 'BWP', currency: 'Pula' }, {
  code: 'NOK',
  currency: 'Norwegian Krone',
}, { code: 'BRL', currency: 'Brazilian Real' }, { code: 'BND', currency: 'Brunei Dollar' }, {
  code: 'BGN',
  currency: 'Bulgarian Lev',
}, { code: 'BIF', currency: 'Burundi Franc' }, { code: 'CVE', currency: 'Cabo Verde Escudo' }, {
  code: 'KHR',
  currency: 'Riel',
}, { code: 'XAF', currency: 'CFA Franc BEAC' }, { code: 'CAD', currency: 'Canadian Dollar' }, {
  code: 'KYD',
  currency: 'Cayman Islands Dollar',
}, { code: 'CLP', currency: 'Chilean Peso' }, { code: 'CLF', currency: 'Unidad de Fomento' }, {
  code: 'CNY',
  currency: 'Yuan Renminbi',
}, { code: 'COP', currency: 'Colombian Peso' }, { code: 'COU', currency: 'Unidad de Valor Real' }, {
  code: 'KMF',
  currency: 'Comoro Franc',
}, { code: 'CDF', currency: 'Congolese Franc' }, { code: 'NZD', currency: 'New Zealand Dollar' }, {
  code: 'CRC',
  currency: 'Costa Rican Colon',
}, { code: 'HRK', currency: 'Kuna' }, { code: 'CUP', currency: 'Cuban Peso' }, { code: 'CUC', currency: 'Peso Convertible' }, {
  code: 'ANG',
  currency: 'Netherlands Antillean Guilder',
}, { code: 'CZK', currency: 'Czech Koruna' }, { code: 'DKK', currency: 'Danish Krone' }, {
  code: 'DJF',
  currency: 'Djibouti Franc',
}, { code: 'DOP', currency: 'Dominican Peso' }, { code: 'EGP', currency: 'Egyptian Pound' }, {
  code: 'SVC',
  currency: 'El Salvador Colon',
}, { code: 'ERN', currency: 'Nakfa' }, { code: 'ETB', currency: 'Ethiopian Birr' }, {
  code: 'FKP',
  currency: 'Falkland Islands Pound',
}, { code: 'FJD', currency: 'Fiji Dollar' }, { code: 'XPF', currency: 'CFP Franc' }, { code: 'GMD', currency: 'Dalasi' }, {
  code: 'GEL',
  currency: 'Lari',
}, { code: 'GHS', currency: 'Ghana Cedi' }, { code: 'GIP', currency: 'Gibraltar Pound' }, {
  code: 'GTQ',
  currency: 'Quetzal',
}, { code: 'GBP', currency: 'Pound Sterling' }, { code: 'GNF', currency: 'Guinea Franc' }, {
  code: 'GYD',
  currency: 'Guyana Dollar',
}, { code: 'HTG', currency: 'Gourde' }, { code: 'HNL', currency: 'Lempira' }, { code: 'HKD', currency: 'Hong Kong Dollar' }, {
  code: 'HUF',
  currency: 'Forint',
}, { code: 'ISK', currency: 'Iceland Krona' }, { code: 'IDR', currency: 'Rupiah' }, {
  code: 'XDR',
  currency: 'SDR (Special Drawing Right)',
}, { code: 'IRR', currency: 'Iranian Rial' }, { code: 'IQD', currency: 'Iraqi Dinar' }, {
  code: 'ILS',
  currency: 'New Israeli Sheqel',
}, { code: 'JMD', currency: 'Jamaican Dollar' }, { code: 'JPY', currency: 'Yen' }, {
  code: 'JOD',
  currency: 'Jordanian Dinar',
}, { code: 'KZT', currency: 'Tenge' }, { code: 'KES', currency: 'Kenyan Shilling' }, {
  code: 'KPW',
  currency: 'North Korean Won',
}, { code: 'KRW', currency: 'Won' }, { code: 'KWD', currency: 'Kuwaiti Dinar' }, { code: 'KGS', currency: 'Som' }, {
  code: 'LAK',
  currency: 'Kip',
}, { code: 'LBP', currency: 'Lebanese Pound' }, { code: 'LSL', currency: 'Loti' }, { code: 'ZAR', currency: 'Rand' }, {
  code: 'LRD',
  currency: 'Liberian Dollar',
}, { code: 'LYD', currency: 'Libyan Dinar' }, { code: 'CHF', currency: 'Swiss Franc' }, { code: 'MOP', currency: 'Pataca' }, {
  code: 'MKD',
  currency: 'Denar',
}, { code: 'MGA', currency: 'Malagasy Ariary' }, { code: 'MWK', currency: 'Malawi Kwacha' }, {
  code: 'MYR',
  currency: 'Malaysian Ringgit',
}, { code: 'MVR', currency: 'Rufiyaa' }, { code: 'MRO', currency: 'Ouguiya' }, { code: 'MUR', currency: 'Mauritius Rupee' }, {
  code: 'XUA',
  currency: 'ADB Unit of Account',
}, { code: 'MXN', currency: 'Mexican Peso' }, { code: 'MXV', currency: 'Mexican Unidad de Inversion (UDI)' }, {
  code: 'MDL',
  currency: 'Moldovan Leu',
}, { code: 'MNT', currency: 'Tugrik' }, { code: 'MAD', currency: 'Moroccan Dirham' }, {
  code: 'MZN',
  currency: 'Mozambique Metical',
}, { code: 'MMK', currency: 'Kyat' }, { code: 'NAD', currency: 'Namibia Dollar' }, {
  code: 'NPR',
  currency: 'Nepalese Rupee',
}, { code: 'NIO', currency: 'Cordoba Oro' }, { code: 'NGN', currency: 'Naira' }, { code: 'OMR', currency: 'Rial Omani' }, {
  code: 'PKR',
  currency: 'Pakistan Rupee',
}, { code: 'No universal currency', currency: ' STATE OF\"' }, { code: 'PAB', currency: 'Balboa' }, {
  code: 'PGK',
  currency: 'Kina',
}, { code: 'PYG', currency: 'Guarani' }, { code: 'PEN', currency: 'Sol' }, { code: 'PHP', currency: 'Philippine Peso' }, {
  code: 'PLN',
  currency: 'Zloty',
}, { code: 'QAR', currency: 'Qatari Rial' }, { code: 'RON', currency: 'Romanian Leu' }, {
  code: 'RUB',
  currency: 'Russian Ruble',
}, { code: 'RWF', currency: 'Rwanda Franc' }, { code: 'Saint Helena Pound', currency: ' ASCENSION AND TRISTAN DA CUNHA\"' }, {
  code: 'WST',
  currency: 'Tala',
}, { code: 'STD', currency: 'Dobra' }, { code: 'SAR', currency: 'Saudi Riyal' }, { code: 'RSD', currency: 'Serbian Dinar' }, {
  code: 'SCR',
  currency: 'Seychelles Rupee',
}, { code: 'SLL', currency: 'Leone' }, { code: 'SGD', currency: 'Singapore Dollar' }, { code: 'XSU', currency: 'Sucre' }, {
  code: 'SBD',
  currency: 'Solomon Islands Dollar',
}, { code: 'SOS', currency: 'Somali Shilling' }, { code: 'SSP', currency: 'South Sudanese Pound' }, {
  code: 'LKR',
  currency: 'Sri Lanka Rupee',
}, { code: 'SDG', currency: 'Sudanese Pound' }, { code: 'SRD', currency: 'Surinam Dollar' }, {
  code: 'SZL',
  currency: 'Lilangeni',
}, { code: 'SEK', currency: 'Swedish Krona' }, { code: 'CHE', currency: 'WIR Euro' }, { code: 'CHW', currency: 'WIR Franc' }, {
  code: 'SYP',
  currency: 'Syrian Pound',
}, { code: 'TWD', currency: 'New Taiwan Dollar' }, { code: 'TJS', currency: 'Somoni' }, {
  code: 'TZS',
  currency: ' UNITED REPUBLIC OF\"',
}, { code: 'THB', currency: 'Baht' }, { code: 'TOP', currency: 'Pa’anga' }, {
  code: 'TTD',
  currency: 'Trinidad and Tobago Dollar',
}, { code: 'TND', currency: 'Tunisian Dinar' }, { code: 'TRY', currency: 'Turkish Lira' }, {
  code: 'TMT',
  currency: 'Turkmenistan New Manat',
}, { code: 'UGX', currency: 'Uganda Shilling' }, { code: 'UAH', currency: 'Hryvnia' }, {
  code: 'AED',
  currency: 'UAE Dirham',
}, { code: 'USN', currency: 'US Dollar (Next day)' }, { code: 'UYU', currency: 'Peso Uruguayo' }, {
  code: 'UYI',
  currency: 'Uruguay Peso en Unidades Indexadas (URUIURUI)',
}, { code: 'UZS', currency: 'Uzbekistan Sum' }, { code: 'VUV', currency: 'Vatu' }, { code: 'VEF', currency: 'Bolívar' }, {
  code: 'VND',
  currency: 'Dong',
}, { code: 'YER', currency: 'Yemeni Rial' }, { code: 'ZMW', currency: 'Zambian Kwacha' }, {
  code: 'ZWL',
  currency: 'Zimbabwe Dollar',
}, { code: 'XBA', currency: 'Bond Markets Unit European Composite Unit (EURCO)' }, {
  code: 'XBB',
  currency: 'Bond Markets Unit European Monetary Unit (E.M.U.-6)',
}, { code: 'XBC', currency: 'Bond Markets Unit European Unit of Account 9 (E.U.A.-9)' }, {
  code: 'XBD',
  currency: 'Bond Markets Unit European Unit of Account 17 (E.U.A.-17)',
}, { code: 'XTS', currency: 'Codes specifically reserved for testing purposes' }, {
  code: 'XXX',
  currency: 'The codes assigned for transactions where no currency is involved',
}, { code: 'XAU', currency: 'Gold' }, { code: 'XPD', currency: 'Palladium' }, { code: 'XPT', currency: 'Platinum' }, {
  code: 'XAG',
  currency: 'Silver',
}, { code: 'AFA', currency: 'Afghani' }, { code: 'FIM', currency: 'Markka' }, { code: 'ALK', currency: 'Old Lek' }, {
  code: 'ADP',
  currency: 'Andorran Peseta',
}, { code: 'ESP', currency: 'Spanish Peseta' }, { code: 'FRF', currency: 'French Franc' }, {
  code: 'AOK',
  currency: 'Kwanza',
}, { code: 'AON', currency: 'New Kwanza' }, { code: 'AOR', currency: 'Kwanza Reajustado' }, {
  code: 'ARA',
  currency: 'Austral',
}, { code: 'ARP', currency: 'Peso Argentino' }, { code: 'ARY', currency: 'Peso' }, {
  code: 'RUR',
  currency: 'Russian Ruble',
}, { code: 'ATS', currency: 'Schilling' }, { code: 'AYM', currency: 'Azerbaijan Manat' }, {
  code: 'AZM',
  currency: 'Azerbaijanian Manat',
}, { code: 'BYR', currency: 'Belarusian Ruble' }, { code: 'BYB', currency: 'Belarusian Ruble' }, {
  code: 'BEC',
  currency: 'Convertible Franc',
}, { code: 'BEF', currency: 'Belgian Franc' }, { code: 'BEL', currency: 'Financial Franc' }, {
  code: 'BOP',
  currency: 'Peso boliviano',
}, { code: 'BAD', currency: 'Dinar' }, { code: 'BRB', currency: 'Cruzeiro' }, { code: 'BRC', currency: 'Cruzado' }, {
  code: 'BRE',
  currency: 'Cruzeiro',
}, { code: 'BRN', currency: 'New Cruzado' }, { code: 'BRR', currency: 'Cruzeiro Real' }, {
  code: 'BGJ',
  currency: 'Lev A/52',
}, { code: 'BGK', currency: 'Lev A/62' }, { code: 'BGL', currency: 'Lev' }, { code: 'BUK', currency: '-' }, {
  code: 'CNX',
  currency: 'Peoples Bank Dollar',
}, { code: 'HRD', currency: 'Croatian Dinar' }, { code: 'CYP', currency: 'Cyprus Pound' }, {
  code: 'CSJ',
  currency: 'Krona A/53',
}, { code: 'CSK', currency: 'Koruna' }, { code: 'ECS', currency: 'Sucre' }, {
  code: 'ECV',
  currency: 'Unidad de Valor Constante (UVC)',
}, { code: 'GQE', currency: 'Ekwele' }, { code: 'EEK', currency: 'Kroon' }, {
  code: 'XEU',
  currency: 'European Currency Unit (E.C.U)',
}, { code: 'GEK', currency: 'Georgian Coupon' }, { code: 'DDM', currency: 'Mark der DDR' }, {
  code: 'DEM',
  currency: 'Deutsche Mark',
}, { code: 'GHC', currency: 'Cedi' }, { code: 'GHP', currency: 'Ghana Cedi' }, { code: 'GRD', currency: 'Drachma' }, {
  code: 'GNE',
  currency: 'Syli',
}, { code: 'GNS', currency: 'Syli' }, { code: 'GWE', currency: 'Guinea Escudo' }, {
  code: 'GWP',
  currency: 'Guinea-Bissau Peso',
}, { code: 'ITL', currency: 'Italian Lira' }, { code: 'ISJ', currency: 'Old Krona' }, {
  code: 'IEP',
  currency: 'Irish Pound',
}, { code: 'ILP', currency: 'Pound' }, { code: 'ILR', currency: 'Old Shekel' }, { code: 'LAJ', currency: 'Kip Pot Pol' }, {
  code: 'LVL',
  currency: 'Latvian Lats',
}, { code: 'LVR', currency: 'Latvian Ruble' }, { code: 'LSM', currency: 'Maloti' }, {
  code: 'ZAL',
  currency: 'Financial Rand',
}, { code: 'LTL', currency: 'Lithuanian Litas' }, { code: 'LTT', currency: 'Talonas' }, {
  code: 'LUC',
  currency: 'Luxembourg Convertible Franc',
}, { code: 'LUF', currency: 'Luxembourg Franc' }, { code: 'LUL', currency: 'Luxembourg Financial Franc' }, {
  code: 'MGF',
  currency: 'Malagasy Franc',
}, { code: 'MVQ', currency: 'Maldive Rupee' }, { code: 'MLF', currency: 'Mali Franc' }, {
  code: 'MTL',
  currency: 'Maltese Lira',
}, { code: 'MTP', currency: 'Maltese Pound' }, { code: 'MXP', currency: 'Mexican Peso' }, {
  code: 'Russian Ruble',
  currency: ' REPUBLIC OF\"',
}, { code: 'MZE', currency: 'Mozambique Escudo' }, { code: 'MZM', currency: 'Mozambique Metical' }, {
  code: 'NLG',
  currency: 'Netherlands Guilder',
}, { code: 'NIC', currency: 'Cordoba' }, { code: 'PEH', currency: 'Sol' }, { code: 'PEI', currency: 'Inti' }, {
  code: 'PES',
  currency: 'Sol',
}, { code: 'PLZ', currency: 'Zloty' }, { code: 'PTE', currency: 'Portuguese Escudo' }, { code: 'ROK', currency: 'Leu A/52' }, {
  code: 'ROL',
  currency: 'Old Leu',
}, { code: 'CSD', currency: 'Serbian Dinar' }, { code: 'SKK', currency: 'Slovak Koruna' }, {
  code: 'SIT',
  currency: 'Tolar',
}, { code: 'RHD', currency: 'Rhodesian Dollar' }, { code: 'ESA', currency: 'Spanish Peseta' }, {
  code: 'ESB',
  currency: 'Account (convertible Peseta Account)',
}, { code: 'SDD', currency: 'Sudanese Dinar' }, { code: 'SDP', currency: 'Sudanese Pound' }, {
  code: 'SRG',
  currency: 'Surinam Guilder',
}, { code: 'CHC', currency: 'WIR Franc (for electronic)' }, { code: 'TJR', currency: 'Tajik Ruble' }, {
  code: 'TPE',
  currency: 'Timor Escudo',
}, { code: 'TRL', currency: 'Old Turkish Lira' }, { code: 'TMM', currency: 'Turkmenistan Manat' }, {
  code: 'UGS',
  currency: 'Uganda Shilling',
}, { code: 'UGW', currency: 'Old Shilling' }, { code: 'UAK', currency: 'Karbovanet' }, { code: 'SUR', currency: 'Rouble' }, {
  code: 'USS',
  currency: 'US Dollar (Same day)',
}, { code: 'UYN', currency: 'Old Uruguay Peso' }, { code: 'UYP', currency: 'Uruguayan Peso' }, {
  code: 'VEB',
  currency: 'Bolivar',
}, { code: 'VNC', currency: 'Old Dong' }, { code: 'Yemeni Dinar', currency: ' DEMOCRATIC\"' }, {
  code: 'YUD',
  currency: 'New Yugoslavian Dinar',
}, { code: 'YUM', currency: 'New Dinar' }, { code: 'YUN', currency: 'Yugoslavian Dinar' }, {
  code: 'ZRN',
  currency: 'New Zaire',
}, { code: 'ZRZ', currency: 'Zaire' }, { code: 'ZMK', currency: 'Zambian Kwacha' }, {
  code: 'ZWC',
  currency: 'Rhodesian Dollar',
}, { code: 'ZWD', currency: 'Zimbabwe Dollar (old)' }, { code: 'ZWN', currency: 'Zimbabwe Dollar (new)' }, {
  code: 'ZWR',
  currency: 'Zimbabwe Dollar',
}, { code: 'XFO', currency: 'Gold-Franc' }, { code: 'XRE', currency: 'RINET Funds Code' }, { code: 'XFU', currency: 'UIC-Franc' } ];
/* tslint: enable */
// @formatter:on
