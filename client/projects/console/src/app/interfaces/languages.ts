export interface Language {
  code: string;
  name: string;
}

export const LANGUAGES: Language[] = [
  { name: 'Afrikaans', code: 'af' },
  { name: 'Albanian', code: 'sq' },
  { name: 'Amharic', code: 'am' },
  { name: 'Arabic - Algeria', code: 'ar-dz' },
  { name: 'Arabic - Bahrain', code: 'ar-bh' },
  { name: 'Arabic - Egypt', code: 'ar-eg' },
  { name: 'Arabic - Iraq', code: 'ar-iq' },
  { name: 'Arabic - Jordan', code: 'ar-jo' },
  { name: 'Arabic - Kuwait', code: 'ar-kw' },
  { name: 'Arabic - Lebanon', code: 'ar-lb' },
  { name: 'Arabic - Libya', code: 'ar-ly' },
  { name: 'Arabic - Morocco', code: 'ar-ma' },
  { name: 'Arabic - Oman', code: 'ar-om' },
  { name: 'Arabic - Qatar', code: 'ar-qa' },
  { name: 'Arabic - Saudi Arabia', code: 'ar-sa' },
  { name: 'Arabic - Syria', code: 'ar-sy' },
  { name: 'Arabic - Tunisia', code: 'ar-tn' },
  { name: 'Arabic - United Arab Emirates', code: 'ar-ae' },
  { name: 'Arabic - Yemen', code: 'ar-ye' },
  { name: 'Armenian', code: 'hy' },
  { name: 'Assamese', code: 'as' },
  { name: 'Azeri - Cyrillic', code: 'az-az' },
  { name: 'Azeri - Latin', code: 'az-az' },
  { name: 'Basque', code: 'eu' },
  { name: 'Belarusian', code: 'be' },
  { name: 'Bengali - Bangladesh', code: 'bn' },
  { name: 'Bengali - India', code: 'bn' },
  { name: 'Bosnian', code: 'bs' },
  { name: 'Bulgarian', code: 'bg' },
  { name: 'Burmese', code: 'my' },
  { name: 'Catalan', code: 'ca' },
  { name: 'Chinese - China', code: 'zh-cn' },
  { name: 'Chinese - Hong Kong SAR', code: 'zh-hk' },
  { name: 'Chinese - Macau SAR', code: 'zh-mo' },
  { name: 'Chinese - Singapore', code: 'zh-sg' },
  { name: 'Chinese - Taiwan', code: 'zh-tw' },
  { name: 'Croatian', code: 'hr' },
  { name: 'Czech', code: 'cs' },
  { name: 'Danish', code: 'da' },
  { name: 'Divehi', code: 'Maldivian' },
  { name: 'Dutch', code: 'nl' },
  { name: 'Dutch - Belgium', code: 'nl-be' },
  { name: 'Dutch - Netherlands', code: 'nl-nl' },
  { name: 'English', code: 'en' },
  { name: 'English - Australia', code: 'en-au' },
  { name: 'English - Belize', code: 'en-bz' },
  { name: 'English - Canada', code: 'en-ca' },
  { name: 'English - Caribbean', code: 'en-cb' },
  { name: 'English - Great Britain', code: 'en-gb' },
  { name: 'English - India', code: 'en-in' },
  { name: 'English - Ireland', code: 'en-ie' },
  { name: 'English - Jamaica', code: 'en-jm' },
  { name: 'English - New Zealand', code: 'en-nz' },
  { name: 'English - Phillippines', code: 'en-ph' },
  { name: 'English - Southern Africa', code: 'en-za' },
  { name: 'English - Trinidad', code: 'en-tt' },
  { name: 'English - United States', code: 'en-us' },
  { name: 'Estonian', code: 'et' },
  { name: 'FYRO Macedonia', code: 'mk' },
  { name: 'Faroese', code: 'fo' },
  { name: 'Farsi - Persian', code: 'fa' },
  { name: 'Finnish', code: 'fi' },
  { name: 'French', code: 'fr' },
  { name: 'French - Belgium', code: 'fr-be' },
  { name: 'French - Canada', code: 'fr-ca' },
  { name: 'French - France', code: 'fr-fr' },
  { name: 'French - Luxembourg', code: 'fr-lu' },
  { name: 'French - Switzerland', code: 'fr-ch' },
  { name: 'Gaelic - Ireland', code: 'gd-ie' },
  { name: 'Gaelic - Scotland', code: 'gd' },
  { name: 'German', code: 'de' },
  { name: 'German - Austria', code: 'de-at' },
  { name: 'German - Germany', code: 'de-de' },
  { name: 'German - Liechtenstein', code: 'de-li' },
  { name: 'German - Luxembourg', code: 'de-lu' },
  { name: 'German - Switzerland', code: 'de-ch' },
  { name: 'Greek', code: 'el' },
  { name: 'Guarani - Paraguay', code: 'gn' },
  { name: 'Gujarati', code: 'gu' },
  { name: 'Hebrew', code: 'he' },
  { name: 'Hindi', code: 'hi' },
  { name: 'Hungarian', code: 'hu' },
  { name: 'Icelandic', code: 'is' },
  { name: 'Indonesian', code: 'id' },
  { name: 'Italian', code: 'it' },
  { name: 'Italian - Italy', code: 'it-it' },
  { name: 'Italian - Switzerland', code: 'it-ch' },
  { name: 'Japanese', code: 'ja' },
  { name: 'Kannada', code: 'kn' },
  { name: 'Kashmiri', code: 'ks' },
  { name: 'Kazakh', code: 'kk' },
  { name: 'Khmer', code: 'km' },
  { name: 'Korean', code: 'ko' },
  { name: 'Lao', code: 'lo' },
  { name: 'Latin', code: 'la' },
  { name: 'Latvian', code: 'lv' },
  { name: 'Lithuanian', code: 'lt' },
  { name: 'Malay - Brunei', code: 'ms-bn' },
  { name: 'Malay - Malaysia', code: 'ms-my' },
  { name: 'Malayalam', code: 'ml' },
  { name: 'Maltese', code: 'mt' },
  { name: 'Maori', code: 'mi' },
  { name: 'Marathi', code: 'mr' },
  { name: 'Mongolian', code: 'mn' },
  { name: 'Mongolian', code: 'mn' },
  { name: 'Nepali', code: 'ne' },
  { name: 'Norwegian', code: 'no-no' },
  { name: 'Oriya', code: 'or' },
  { name: 'Polish', code: 'pl' },
  { name: 'Portuguese - Brazil', code: 'pt-br' },
  { name: 'Portuguese - Portugal', code: 'pt-pt' },
  { name: 'Punjabi', code: 'pa' },
  { name: 'Raeto-Romance', code: 'rm' },
  { name: 'Romanian - Moldova', code: 'ro-mo' },
  { name: 'Romanian - Romania', code: 'ro' },
  { name: 'Russian', code: 'ru' },
  { name: 'Russian - Moldova', code: 'ru-mo' },
  { name: 'Sanskrit', code: 'sa' },
  { name: 'Serbian - Cyrillic', code: 'sr-sp' },
  { name: 'Serbian - Latin', code: 'sr-sp' },
  { name: 'Setsuana', code: 'tn' },
  { name: 'Sindhi', code: 'sd' },
  { name: 'Sinhala', code: 'si' },
  { name: 'Slovak', code: 'sk' },
  { name: 'Slovenian', code: 'sl' },
  { name: 'Somali', code: 'so' },
  { name: 'Sorbian', code: 'sb' },
  { name: 'Spanish', code: 'es' },
  { name: 'Spanish - Argentina', code: 'es-ar' },
  { name: 'Spanish - Bolivia', code: 'es-bo' },
  { name: 'Spanish - Chile', code: 'es-cl' },
  { name: 'Spanish - Colombia', code: 'es-co' },
  { name: 'Spanish - Costa Rica', code: 'es-cr' },
  { name: 'Spanish - Dominican Republic', code: 'es-do' },
  { name: 'Spanish - Ecuador', code: 'es-ec' },
  { name: 'Spanish - El Salvador', code: 'es-sv' },
  { name: 'Spanish - Guatemala', code: 'es-gt' },
  { name: 'Spanish - Honduras', code: 'es-hn' },
  { name: 'Spanish - Mexico', code: 'es-mx' },
  { name: 'Spanish - Nicaragua', code: 'es-ni' },
  { name: 'Spanish - Panama', code: 'es-pa' },
  { name: 'Spanish - Paraguay', code: 'es-py' },
  { name: 'Spanish - Peru', code: 'es-pe' },
  { name: 'Spanish - Puerto Rico', code: 'es-pr' },
  { name: 'Spanish - Spain (Traditional)', code: 'es-es' },
  { name: 'Spanish - Uruguay', code: 'es-uy' },
  { name: 'Spanish - Venezuela', code: 'es-ve' },
  { name: 'Swahili', code: 'sw' },
  { name: 'Swedish - Finland', code: 'sv-fi' },
  { name: 'Swedish - Sweden', code: 'sv-se' },
  { name: 'Tajik', code: 'tg' },
  { name: 'Tamil', code: 'ta' },
  { name: 'Tatar', code: 'tt' },
  { name: 'Telugu', code: 'te' },
  { name: 'Thai', code: 'th' },
  { name: 'Tibetan', code: 'bo' },
  { name: 'Tsonga', code: 'ts' },
  { name: 'Turkish', code: 'tr' },
  { name: 'Turkmen', code: 'tk' },
  { name: 'Ukrainian', code: 'uk' },
  { name: 'Unicode', code: 'UTF-8' },
  { name: 'Urdu', code: 'ur' },
  { name: 'Uzbek - Cyrillic', code: 'uz-uz' },
  { name: 'Uzbek - Latin', code: 'uz-uz' },
  { name: 'Vietnamese', code: 'vi' },
  { name: 'Welsh', code: 'cy' },
  { name: 'Xhosa', code: 'xh' },
  { name: 'Yiddish', code: 'yi' },
  { name: 'Zulu', code: 'zu' } ];
