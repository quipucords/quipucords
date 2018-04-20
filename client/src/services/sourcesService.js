import axios from 'axios';

class SourcesService {
  static addSource(data = {}, query = {}) {
    return axios({
      method: 'post',
      url: process.env.REACT_APP_SOURCES_SERVICE,
      xsrfCookieName: process.env.REACT_APP_AUTH_TOKEN,
      xsrfHeaderName: process.env.REACT_APP_AUTH_HEADER,
      timeout: process.env.REACT_APP_AJAX_TIMEOUT,
      data: data,
      params: query
    });
  }

  deleteSource(id) {
    return axios({
      method: 'delete',
      url: `${process.env.REACT_APP_SOURCES_SERVICE}${id}/`,
      xsrfCookieName: process.env.REACT_APP_AUTH_TOKEN,
      xsrfHeaderName: process.env.REACT_APP_AUTH_HEADER,
      timeout: process.env.REACT_APP_AJAX_TIMEOUT
    });
  }

  deleteSources(data = []) {
    return Promise.all.apply(this, data.map(id => this.deleteSource(id)));
  }

  getSource(id) {
    return this.getSources(id);
  }

  getSources(id = '', query = {}) {
    return axios({
      url: `${process.env.REACT_APP_SOURCES_SERVICE}${id}`,
      timeout: process.env.REACT_APP_AJAX_TIMEOUT,
      params: query
    });
  }

  static updateSource(id, data = {}) {
    return axios({
      method: 'put',
      url: `${process.env.REACT_APP_SOURCES_SERVICE}${id}/`,
      xsrfCookieName: process.env.REACT_APP_AUTH_TOKEN,
      xsrfHeaderName: process.env.REACT_APP_AUTH_HEADER,
      timeout: process.env.REACT_APP_AJAX_TIMEOUT,
      data: data
    });
  }
}

export default new SourcesService();
