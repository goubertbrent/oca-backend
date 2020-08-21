// a map of error code and message (translation key) for service api exceptions (rogerthat backend)
export const SERVICE_API_ERRORS: { [ key: number ]: string } = {
  50001: 'invalid_qr_code_color_specification',
  50002: 'invalid_qr_code_description',
  50003: 'invalid_qr_code_template_size',
};
