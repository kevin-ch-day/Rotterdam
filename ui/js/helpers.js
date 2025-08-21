const BASE_PATH = '/ui';

$(function () {
  $('#header').load(`${BASE_PATH}/partials/header.html`);
  $('#footer').load(`${BASE_PATH}/partials/footer.html`);
  $('#sidebar').load(`${BASE_PATH}/partials/sidebar.html`, function () {
    const page = window.location.pathname.split('/').pop();
    $(`#sidebar a[href='${page}']`).addClass('active');
  });
});

window.API_HEADERS = { 'X-API-Key': 'secret' };

window.api = {
  get: (path) =>
    $.ajax({ url: path, headers: API_HEADERS, dataType: 'json' }),
  post: (path, data) =>
    $.ajax({
      url: path,
      method: 'POST',
      headers: API_HEADERS,
      contentType: 'application/json',
      data: JSON.stringify(data),
      dataType: 'json',
    }),
  delete: (path) =>
    $.ajax({ url: path, method: 'DELETE', headers: API_HEADERS }),
};
