import axios from 'axios';

class CredentialsService {
  static addCredential(data = {}) {
    return axios({
      method: 'post',
      url: `${process.env.REACT_APP_CREDENTIALS_SERVICE}`,
      xsrfCookieName: process.env.REACT_APP_AUTH_TOKEN,
      xsrfHeaderName: process.env.REACT_APP_AUTH_HEADER,
      timeout: process.env.REACT_APP_AJAX_TIMEOUT,
      data: data
    });
  }

  deleteCredential(id) {
    return axios({
      method: 'delete',
      url: `${process.env.REACT_APP_CREDENTIALS_SERVICE}${id}/`,
      xsrfCookieName: process.env.REACT_APP_AUTH_TOKEN,
      xsrfHeaderName: process.env.REACT_APP_AUTH_HEADER,
      timeout: process.env.REACT_APP_AJAX_TIMEOUT
    });
  }

  deleteCredentials(data = []) {
    return Promise.all.apply(this, data.map(id => this.deleteCredential(id)));
  }

  getCredential(id) {
    return this.getCredentials(id);
  }

  getCredentials(id = '', query = {}) {
    return axios({
      url: `${process.env.REACT_APP_CREDENTIALS_SERVICE}${id}`,
      timeout: process.env.REACT_APP_AJAX_TIMEOUT,
      params: query
    });
  }

  static updateCredential(id, data = {}) {
    return axios({
      method: 'put',
      url: `${process.env.REACT_APP_CREDENTIALS_SERVICE}${id}/`,
      xsrfCookieName: process.env.REACT_APP_AUTH_TOKEN,
      xsrfHeaderName: process.env.REACT_APP_AUTH_HEADER,
      timeout: process.env.REACT_APP_AJAX_TIMEOUT,
      data: data
    });
  }
}

export default new CredentialsService();
