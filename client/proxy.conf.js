const PROXY_CONFIG = [
  {
    context: [
      '/static',
      '/common',
      '/_ah',
      '/admin/api',
      '/api',
      '/unauthenticated',
    ],
    target: "http://localhost:8080",
    secure: false
  }
];

module.exports = PROXY_CONFIG;
